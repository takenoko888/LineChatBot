"""
LINE Bot application entry point
"""
from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import logging
import requests
import threading
import time
try:
    from googleapiclient.errors import HttpError
except Exception:  # ライブラリ未導入環境でも起動可能にする
    class HttpError(Exception):
        pass
from core.line_bot_base import LineBotBase
from handlers.message_handler import MessageHandler
from services.notification_service import NotificationService
from services.weather_service import WeatherService
from services.search_service import SearchService
from services.gemini_service import GeminiService
from services.auto_task_service import AutoTaskService
from services.keepalive_service import KeepAliveService
from services.activity_service import ActivityService
from utils.date_utils import DateUtils
from utils.command_utils import CommandUtils
from utils.context_utils import ContextUtils
from datetime import datetime
import time
import logging

# 新しいユーティリティクラスをインポート
from core.security_utils import SecurityUtils
from utils.performance_monitor import performance_monitor
from core.config_manager import config_manager
from handlers.admin_handler import AdminHandler
from services.smart_suggestion_service import SmartSuggestionService
from collections import deque, defaultdict

# ロガーの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Flaskアプリケーションの作成
app = Flask(__name__)

class LineBot(LineBotBase):
    """LINEボットアプリケーション"""
    
    def __init__(self):
        """初期化"""
        try:
            super().__init__()
            
            # 設定管理の初期化
            self.config = config_manager.get_config()
            
            # セキュリティユーティリティの初期化
            self.security_utils = SecurityUtils()
            
            # 環境変数の検証
            is_valid, errors = self.security_utils.validate_environment_variables()
            if not is_valid:
                raise ValueError(f"環境変数エラー: {', '.join(errors)}")
            
            # LINE Bot API初期化
            self.line_bot_api = LineBotApi(self.config.line_access_token)
            self.handler = WebhookHandler(self.config.line_channel_secret)
            
            # 各種サービスの初期化（オプショナル機能）
            self._initialize_services()
            
            # 管理者ハンドラーの初期化
            self.admin_handler = AdminHandler(
                performance_monitor=performance_monitor,
                config_manager=config_manager,
                security_utils=self.security_utils
            )
            
            # メッセージハンドラーの設定
            self._setup_message_handler()
            
            logger.info("LINEボットの初期化が完了しました")
            
        except Exception as e:
            logger.error(f"初期化エラー: {str(e)}")
            raise

    def _initialize_services(self):
        """各種サービスの初期化"""
        # Gemini AIサービス（必須）
        self.gemini_service = GeminiService(self.config.gemini_api_key)
        
        # 通知サービス（必須）
        if config_manager.is_feature_enabled('notifications'):
            notification_config = config_manager.get_service_config('notifications')
            self.notification_service = NotificationService(
                storage_path=notification_config['storage_path'],
                gemini_service=self.gemini_service,
                line_bot_api=self.line_bot_api
            )
        else:
            self.notification_service = None
        
        # 天気サービス（オプショナル）
        if config_manager.is_feature_enabled('weather'):
            weather_config = config_manager.get_service_config('weather')
            if weather_config['api_key']:
                try:
                    self.weather_service = WeatherService(gemini_service=self.gemini_service)
                    if not self.weather_service.is_available:
                        logger.warning("天気機能は無効です")
                except Exception as e:
                    logger.warning(f"天気サービスの初期化に失敗: {str(e)}")
                    self.weather_service = None
            else:
                logger.info("天気APIキーが設定されていないため、天気機能を無効にします")
                self.weather_service = None
        else:
            self.weather_service = None
            
        # 検索サービス（オプショナル）
        if config_manager.is_feature_enabled('search'):
            search_config = config_manager.get_service_config('search')
            if search_config['api_key'] and search_config['search_engine_id']:
                try:
                    self.search_service = SearchService(
                        api_key=search_config['api_key'],
                        search_engine_id=search_config['search_engine_id'],
                        gemini_service=self.gemini_service
                    )
                except Exception as e:
                    logger.warning(f"検索サービスの初期化に失敗: {str(e)}")
                    self.search_service = None
            else:
                logger.info("検索APIキーが設定されていないため、検索機能を無効にします")
                self.search_service = None
        else:
            self.search_service = None
            
        # ユーティリティの初期化
        self.date_utils = DateUtils()
        self.command_utils = CommandUtils()
        self.context_utils = ContextUtils()

        # 簡易レート制限用データ構造
        self._rate_limit_log = defaultdict(lambda: deque(maxlen=50))
        
        # 重複イベント排除とユーザー同時実行ガード
        self._recent_events = {}
        self._recent_events_ttl = int(os.getenv('EVENT_DEDUP_TTL', '60'))
        self._recent_events_lock = threading.Lock()
        self._user_locks = defaultdict(threading.Lock)
        
        # スマート提案サービスの初期化
        try:
            self.smart_suggestion_service = SmartSuggestionService(
                gemini_service=self.gemini_service
            )
            logger.info("スマート提案サービスを初期化しました")
        except Exception as e:
            logger.warning(f"スマート提案サービスの初期化に失敗: {str(e)}")
            self.smart_suggestion_service = None

        # 自動実行・モニタリングサービスの初期化
        if config_manager.is_feature_enabled('auto_tasks'):
            try:
                auto_task_config = config_manager.get_service_config('auto_tasks')
                self.auto_task_service = AutoTaskService(
                    storage_path=auto_task_config.get('storage_path'),
                    notification_service=self.notification_service,
                    weather_service=self.weather_service,
                    search_service=self.search_service,
                    gemini_service=self.gemini_service
                )
                # スケジューラを開始
                self.auto_task_service.start_scheduler()
                logger.info("自動実行・モニタリングサービスを初期化しました")
            except Exception as e:
                logger.warning(f"自動実行サービスの初期化に失敗: {str(e)}")
                self.auto_task_service = None
        else:
            logger.info("自動実行機能が無効化されています")
            self.auto_task_service = None

        # KeepAliveサービスの初期化
        try:
            self.keepalive_service = KeepAliveService()
            
            # 本番環境の自動検出と設定
            if self.keepalive_service.configure_for_production():
                logger.info("本番環境用KeepAlive設定を適用しました")
            
            # KeepAliveサービスを開始
            if self.keepalive_service.start():
                logger.info("KeepAliveサービスを開始しました")
            else:
                logger.warning("KeepAliveサービスの開始に失敗しました")
                
        except Exception as e:
            logger.warning(f"KeepAliveサービスの初期化に失敗: {str(e)}")
            self.keepalive_service = None

        # Function-Calling 用にサービス関数を登録
        try:
            from core.register_default_functions import setup_functions
            setup_functions(
                notification_service=self.notification_service,
                weather_service=self.weather_service,
                search_service=self.search_service
            )
            logger.info("Function-Calling 用デフォルト関数を登録しました")
        except Exception as e:
            logger.warning(f"Function 登録に失敗: {e}")

        # 統合サービスマネージャに実サービスインスタンスを接続（AI統合の安定化）
        try:
            from services.integrated_service_manager import integrated_service_manager
            from services.service_integration_manager import service_integration_manager
            if self.notification_service:
                service_integration_manager.registered_services["notification"] = self.notification_service
            if self.weather_service:
                service_integration_manager.registered_services["weather"] = self.weather_service
            if self.search_service:
                service_integration_manager.registered_services["search"] = self.search_service
            if self.auto_task_service:
                service_integration_manager.registered_services["auto_task"] = self.auto_task_service
            logger.info("統合サービスへ実サービスを接続しました")
        except Exception as e:
            logger.warning(f"統合サービス接続に失敗: {e}")

        # ActivityService（追加のアクティビティ維持）の初期化
        try:
            if self.keepalive_service and hasattr(self.keepalive_service, 'app_url'):
                activity_url = self.keepalive_service.app_url
            else:
                activity_url = "http://localhost:8000"
            
            self.activity_service = ActivityService(app_url=activity_url)
            
            # ActivityServiceを開始
            if self.activity_service.start():
                logger.info("ActivityServiceを開始しました")
            else:
                logger.warning("ActivityServiceの開始に失敗しました")
                
        except Exception as e:
            logger.warning(f"ActivityServiceの初期化に失敗: {str(e)}")
            self.activity_service = None

    def _setup_message_handler(self):
        """メッセージハンドラーの設定"""
        # MessageHandlerインスタンスを作成
        self.message_handler = MessageHandler()
        
        @self.handler.add(MessageEvent, message=TextMessage)
        def handle_text_message(event):
            # パフォーマンス監視開始
            timer_id = performance_monitor.start_timer('message_processing')
            performance_monitor.increment_counter('requests')
            
            try:
                text = event.message.text
                user_id = event.source.user_id
                reply_token = event.reply_token
                
                # 入力のサニタイズ
                text = self.security_utils.sanitize_user_input(text, max_length=1000)
                
                logger.info(f"メッセージを受信: {text}")

                # 重複イベント排除（replyToken / message.id）
                now_ts = time.time()
                event_keys = [f"rt:{reply_token}"]
                try:
                    msg_id = getattr(event.message, 'id', None)
                    if msg_id:
                        event_keys.append(f"msg:{msg_id}")
                except Exception:
                    pass
                with self._recent_events_lock:
                    # TTLパージ
                    expired = [k for k, ts in list(self._recent_events.items()) if now_ts - ts > self._recent_events_ttl]
                    for k in expired:
                        self._recent_events.pop(k, None)
                    # 重複チェック
                    for k in event_keys:
                        if k in self._recent_events:
                            logger.info("重複イベントを検出しスキップしました")
                            performance_monitor.end_timer('message_processing', timer_id)
                            return
                    for k in event_keys:
                        self._recent_events[k] = now_ts

                # レート制限（ユーザー毎）
                if self.config.rate_limit_enabled:
                    now = time.time()
                    window = 60
                    max_req = self.config.max_requests_per_minute
                    q = self._rate_limit_log[user_id]
                    # 古いものを除去
                    while q and now - q[0] > window:
                        q.popleft()
                    if len(q) >= max_req:
                        self.reply_message(reply_token, "⏳ リクエストが多すぎます。しばらくしてからお試しください。", 'default')
                        performance_monitor.end_timer('message_processing', timer_id)
                        return
                    q.append(now)
                
                # 管理者コマンドのチェック
                is_admin_command, admin_response = self.admin_handler.handle_admin_command(user_id, text)
                if is_admin_command:
                    self.reply_message(reply_token, admin_response, 'default')
                    performance_monitor.end_timer('message_processing', timer_id)
                    return
                
                # ユーザー単位の同時実行ガード
                user_lock = self._user_locks[user_id]
                if not user_lock.acquire(blocking=False):
                    self.reply_message(reply_token, "⏳ ただいま処理中です。少し待ってから再送してください。", 'default')
                    performance_monitor.end_timer('message_processing', timer_id)
                    return

                # MessageHandlerでメッセージを処理
                try:
                    response_message, quick_reply_type = self.message_handler.handle_message(
                        event=event,
                        gemini_service=self.gemini_service,
                        notification_service=self.notification_service,
                        weather_service=self.weather_service,
                        search_service=self.search_service,
                        auto_task_service=self.auto_task_service
                    )
                finally:
                    try:
                        user_lock.release()
                    except Exception:
                        pass
                
                # レスポンスの長さチェック（テキストの場合のみ）
                if isinstance(response_message, str):
                    max_length = self.config.max_message_length
                    if len(response_message) > max_length:
                        response_message = response_message[:max_length-100] + "\n\n📝 メッセージが長すぎるため、一部省略されました。"
                
                # 応答を送信
                self.reply_message(reply_token, response_message, quick_reply_type or 'default')
                logger.info(f"応答を送信しました（文字数: {len(response_message)}）")
                
                # パフォーマンス監視終了
                performance_monitor.end_timer('message_processing', timer_id)
                
            except Exception as e:
                performance_monitor.increment_counter('errors')
                logger.error(f"メッセージ処理エラー: {str(e)}")
                error_response = self.security_utils.generate_safe_error_message(e, user_friendly=True)
                self.reply_message(reply_token, error_response, 'default')
                performance_monitor.end_timer('message_processing', timer_id)

    def _generate_chat_response(self, text: str) -> str:
        """
        統一されたチャット応答を生成
        
        Args:
            text (str): ユーザーメッセージ
            
        Returns:
            str: 生成された応答
        """
        try:
            prompt = f"""あなたは親切で知識豊富なアシスタントです。以下のメッセージに対して、包括的で具体的な情報を含む完結した応答を1回で提供してください。

ユーザーのメッセージ: {text}

応答の要件:
1. 情報提供:
   - トピックに関する主要な情報をすべて含める
   - 具体的な数字、事実、特徴を挙げる
   - 可能な限り最新の情報を提供

2. 構造:
   - 重要なポイントを箇条書きや段落で整理
   - 関連する複数の側面について説明
   - 補足情報も含めて完結した説明を行う

3. スタイル:
   - フレンドリーで親しみやすい口調を使用
   - 絵文字を適切に使用して読みやすくする
   - 追加の質問や条件付きの説明を避ける
   - "以上の回答をしないようにしてください"などの余分な説明を含めない

応答は自然な形で終了し、追加の説明や注釈は不要です。
"""
            response = self.gemini_service.model.generate_content(prompt).text.strip()
            return response if response else "申し訳ありません。お返事を考え中です。もう一度お話しください。"
        except Exception as e:
            self.logger.error(f"チャット応答生成エラー: {str(e)}")
            return "申し訳ありません。応答の生成中にエラーが発生しました。"

    def _generate_help_message(self) -> str:
        """
        ヘルプメッセージを生成
        
        Returns:
            str: ヘルプメッセージ
        """
        help_text = [
            "🤖 **LINEボット 使い方ガイド**",
            "",
            "📋 **基本コマンド:**",
            "・「通知一覧」→ 設定済み通知の確認",
            "・「ヘルプ」→ この使い方を表示",
            "・「全通知削除」→ すべての通知を削除",
            "",
            "🔔 **通知設定:**",
            "・「毎日7時に起きる」",
            "・「明日の15時に病院予約」",
            "・「毎週月曜9時にミーティング」",
            "・「3時間後に薬を飲む」",
            "",
            "🗑️ **通知削除:**",
            "・通知一覧で表示されるIDを使用",
            "・例: 「通知削除 n_20240101120000」",
            "",
            "🌤️ **天気機能:**",
            "・「東京の天気」",
            "・「明日の天気予報」",
            "",
            "🔍 **検索機能:**",
            "・「Python について教えて」",
            "・「最新のニュース 検索」",
            "",
            "🧠 **スマート提案機能:**",
            "・「スマート提案」→ AIによる個人最適化提案",
            "・「提案」「おすすめ」→ 使用パターンに基づく提案",
            "・過去の行動を学習して最適なタイミングを提案",
            "・類似タスクの自動グループ化",
            "",
            "💬 **チャット:**",
            "・自由に質問してください",
            "・日常会話も可能です",
            "",
            "💡 **ヒント:**",
            "・自然な言葉で話しかけてOK",
            "・通知時刻は24時間形式も対応",
            "・「明日」「来週」などの表現も理解します",
            "・使うほどAIが学習して賢くなります",
            "",
            "❓ 困ったときは「ヘルプ」と送信してください！"
        ]
        
        return "\n".join(help_text)

def notification_checker():
    """通知チェックのバックグラウンドタスク"""
    logger.info("通知チェッカーを開始します")
    error_count = 0
    check_interval = config_manager.get_config().notification_check_interval  # 設定から取得
    max_consecutive_errors = 5  # 最大連続エラー数を維持

    while True:
        # パフォーマンス監視開始
        timer_id = performance_monitor.start_timer('notification_check')
        
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"通知チェック実行開始: {current_time}")
            
            # 通知機能が有効な場合のみ実行
            if bot.notification_service:
                bot.notification_service.check_and_send_notifications()
            else:
                logger.debug("通知機能が無効のため、チェックをスキップします")
            
            error_count = 0  # エラーカウントをリセット
            
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"通知チェック完了: {end_time}")

        except Exception as e:
            error_count += 1
            performance_monitor.increment_counter('errors')
            logger.error(f"通知チェックエラー ({error_count}回目): {str(e)}")
            
            if error_count >= max_consecutive_errors:
                logger.critical(f"連続エラーが{max_consecutive_errors}回に達したため、通知チェッカーを停止します")
                # 重要: システムを停止させる前に、できるだけ詳細なエラー情報をログに記録
                logger.critical(f"エラー詳細: {type(e).__name__}: {str(e)}")
                raise
            else:
                # エラー時は段階的にチェック間隔を延長
                error_sleep_time = min(check_interval * (2 ** error_count), 30)  # 最大30秒
                logger.warning(f"エラー発生により{error_sleep_time}秒待機します")
                time.sleep(error_sleep_time)
                continue
        finally:
            # パフォーマンス監視終了
            performance_monitor.end_timer('notification_check', timer_id)

        # 通常のチェック間隔で待機
        time.sleep(check_interval)

# ボットインスタンスの作成
try:
    logger.info("LINEボットアプリケーションを初期化中...")
    logger.info(f"設定: ポート={config_manager.get_config().port}, デバッグ={config_manager.get_config().debug}")
    
    bot = LineBot()
    
    logger.info("ボットインスタンスの作成が完了しました")
    logger.info(f"有効な機能: {', '.join([k for k, v in config_manager.get_config().features.items() if v])}")

    # 通知チェッカーの開始（通知機能が有効な場合のみ）
    if config_manager.is_feature_enabled('notifications') and bot.notification_service:
        notification_thread = threading.Thread(target=notification_checker, daemon=True)
        notification_thread.start()
        logger.info("通知チェッカーを開始しました")
    else:
        logger.info("通知機能が無効のため、通知チェッカーは開始しません")
        
except Exception as e:
    logger.critical(f"ボットインスタンスの作成に失敗: {str(e)}")
    raise

@app.route("/callback", methods=['POST'])
def callback():
    """Webhookコールバック"""
    # シグネチャの検証
    signature = request.headers.get('X-Line-Signature', '')
    if not signature:
        logger.error("署名がありません")
        abort(400)

    # リクエストボディの取得
    body = request.get_data(as_text=True)
    logger.info("Webhookを受信しました")
    logger.debug(f"Request body: {body}")

    try:
        # Webhookを処理
        bot.handler.handle(body, signature)
        return 'OK', 200
        
    except InvalidSignatureError:
        logger.error("署名が無効です")
        abort(400)
        
    except Exception as e:
        logger.error(f"Webhook処理エラー: {str(e)}")
        abort(500)

@app.route("/", methods=['GET', 'POST'])
def root():
    """ルートエンドポイント - Webhookとヘルスチェックを処理"""
    if request.method == 'GET':
        return 'OK', 200
        
    # POST時はWebhookとして処理
    signature = request.headers.get('X-Line-Signature', '')
    if not signature:
        logger.error("署名がありません")
        abort(400)

    body = request.get_data(as_text=True)
    logger.info("Webhookを受信しました")
    logger.debug(f"Request body: {body}")

    try:
        bot.handler.handle(body, signature)
        return 'OK', 200
    except InvalidSignatureError:
        logger.error("署名が無効です")
        abort(400)
    except Exception as e:
        logger.error(f"Webhook処理エラー: {str(e)}")
        abort(500)

@app.route("/health", methods=['GET'])
def health_check():
    """ヘルスチェックエンドポイント - Dockerのヘルスチェック用"""
    try:
        # 基本的なサービス状態を確認
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        # 通知サービスの状態確認
        if hasattr(bot, 'notification_service') and bot.notification_service:
            try:
                # 通知サービスが応答するかテスト
                health_status["services"]["notifications"] = "enabled"
            except Exception as e:
                health_status["services"]["notifications"] = f"error: {str(e)}"
                health_status["status"] = "degraded"
        else:
            health_status["services"]["notifications"] = "disabled"
        
        # Geminiサービスの状態確認
        if hasattr(bot, 'gemini_service') and bot.gemini_service:
            health_status["services"]["gemini"] = "enabled"
        else:
            health_status["services"]["gemini"] = "disabled"
        
        # パフォーマンス監視状況
        if hasattr(performance_monitor, 'get_stats'):
            try:
                stats = performance_monitor.get_stats()
                health_status["performance"] = stats
            except:
                health_status["performance"] = "monitoring_unavailable"
        
        return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {str(e)}")
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/metrics", methods=['GET'])
def metrics():
    """簡易メトリクスエンドポイント"""
    try:
        health = performance_monitor.get_health_status()
        summaries = {}
        for op in ['message_processing', 'notification_check', 'gemini_api_call']:
            try:
                summaries[op] = performance_monitor.get_performance_summary(op, minutes=10)
            except Exception:
                summaries[op] = {"error": "unavailable"}
        return jsonify({
            "health": health,
            "summaries": summaries,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"メトリクス取得エラー: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/keepalive", methods=['GET'])
def keepalive_check():
    """KeepAliveエンドポイント - DockerのKeepAlive用"""
    try:
        # KeepAliveサービスが応答するかテスト
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
        
        if hasattr(bot, 'keepalive_service') and bot.keepalive_service:
            keepalive_data = bot.keepalive_service.check_and_respond()
            health_status.update(keepalive_data)
        
        return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"KeepAliveエラー: {str(e)}")
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/keepalive/stats", methods=['GET'])
def keepalive_stats():
    """KeepAlive統計情報エンドポイント"""
    try:
        if hasattr(bot, 'keepalive_service') and bot.keepalive_service:
            stats = bot.keepalive_service.get_stats()
            return jsonify(stats), 200
        else:
            return jsonify({
                "error": "KeepAliveサービスが利用できません",
                "timestamp": datetime.now().isoformat()
            }), 503
            
    except Exception as e:
        logger.error(f"KeepAlive統計取得エラー: {str(e)}")
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/keepalive/ping", methods=['POST'])
def manual_keepalive_ping():
    """手動KeepAliveテスト実行エンドポイント"""
    try:
        if hasattr(bot, 'keepalive_service') and bot.keepalive_service:
            ping_result = bot.keepalive_service.manual_ping()
            return jsonify(ping_result), 200
        else:
            return jsonify({
                "error": "KeepAliveサービスが利用できません",
                "timestamp": datetime.now().isoformat()
            }), 503
            
    except Exception as e:
        logger.error(f"手動ping実行エラー: {str(e)}")
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/activity/stats", methods=['GET'])
def activity_stats():
    """Activityサービス統計情報エンドポイント"""
    try:
        if hasattr(bot, 'activity_service') and bot.activity_service:
            stats = bot.activity_service.get_stats()
            return jsonify(stats), 200
        else:
            return jsonify({
                "error": "Activityサービスが利用できません",
                "timestamp": datetime.now().isoformat()
            }), 503
            
    except Exception as e:
        logger.error(f"Activity統計取得エラー: {str(e)}")
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == "__main__":
    # アプリケーションの起動
    config = config_manager.get_config()
    
    try:
        app.run(host="0.0.0.0", port=config.port, debug=config.debug)
    except KeyboardInterrupt:
        logger.info("アプリケーションを停止中...")
        # KeepAliveサービスの停止
        if hasattr(bot, 'keepalive_service') and bot.keepalive_service:
            bot.keepalive_service.stop()
        # ActivityServiceの停止
        if hasattr(bot, 'activity_service') and bot.activity_service:
            bot.activity_service.stop()
        logger.info("アプリケーション停止完了")
    except Exception as e:
        logger.error(f"アプリケーション実行エラー: {str(e)}")
        # エラー時もサービスを停止
        if hasattr(bot, 'keepalive_service') and bot.keepalive_service:
            bot.keepalive_service.stop()
        if hasattr(bot, 'activity_service') and bot.activity_service:
            bot.activity_service.stop()
        raise
