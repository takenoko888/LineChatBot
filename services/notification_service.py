"""
Notification service implementation
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import logging
import os
import pytz
import random
from dataclasses import dataclass, asdict
from threading import Lock
from .gemini_service import GeminiService
from linebot.models import TextSendMessage, QuickReply, QuickReplyButton, MessageAction
from datetime import time
from services.notification.notification_model import Notification
from services.notification.notification_service_base import NotificationServiceBase
from utils.context_utils import ContextUtils
from core.config_manager import config_manager

class NotificationService(NotificationServiceBase):
    """通知サービス"""

    def __init__(
        self,
        storage_path: str = None,
        gemini_service: Optional[GeminiService] = None,
        line_bot_api = None
    ):
        """
        通知サービスの初期化

        Args:
            storage_path (str, optional): 通知データの保存パス。未指定の場合はデフォルトパスを使用
            gemini_service (Optional[GeminiService]): Gemini AI サービス
            line_bot_api: LINE Bot API クライアント
        """
        super().__init__(storage_path, gemini_service, line_bot_api)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("NotificationService __init__ start")
        self.context_utils = ContextUtils()
        self.logger.debug("NotificationService context_utils initialized")

    def check_and_send_notifications(self) -> None:
        """通知をチェックして、実行時刻になったものを送信"""
        if not self.line_bot_api:
            self.logger.warning("LINE Bot APIが設定されていません")
            return

        try:
            # タイムゾーンを考慮した現在時刻の取得
            jst = pytz.timezone('Asia/Tokyo')
            now = datetime.now(jst).replace(second=0, microsecond=0)
            self.logger.info(f"通知チェック開始: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # LINE APIの制限状態をチェック
            if hasattr(self, '_api_limit_until') and self._api_limit_until > now:
                remaining_time = (self._api_limit_until - now).total_seconds() / 60
                self.logger.warning(f"API制限中: 残り約{int(remaining_time)}分")
                return

            # 通知データの再読み込み
            self._load_notifications()

            total_notifications = sum(len(notifications) for notifications in self.notifications.values())
            self.logger.info(f"チェック対象の通知数: {total_notifications}")

            if not self.notifications:
                self.logger.debug("通知が設定されていません")
                return

            # 通知のチェック（ロック内で実行）
            with self.lock:
                notifications_sent = 0
                data_modified = False
                
                for user_id, user_notifications in list(self.notifications.items()):
                    self.logger.info(f"ユーザー {user_id} の通知をチェック中 ({len(user_notifications)}件)")
                    notifications_to_remove = []
                    notifications_to_update = []

                    for notification_id, notification in list(user_notifications.items()):
                        try:
                            # 通知時刻をJSTとして解釈
                            formats = ['%Y-%m-%d %H:%M', '%Y/%m/%d %H:%M', '%Y-%m-%dT%H:%M:%S']
                            notification_time = None
                            for fmt in formats:
                                try:
                                    notification_time = datetime.strptime(notification.datetime, fmt)
                                    notification_time = jst.localize(notification_time)
                                    break
                                except ValueError:
                                    continue
                            if notification_time is None:
                                self.logger.error(f"通知時刻の解析に失敗: {notification.datetime}")
                                continue

                            # 現在時刻との差分を計算（秒単位）
                            time_diff = (notification_time - now).total_seconds()

                            # 通知時刻のデバッグ情報
                            self.logger.debug(
                                f"通知ID: {notification_id}, "
                                f"タイトル: {notification.title}, "
                                f"予定時刻: {notification_time.strftime('%Y-%m-%d %H:%M')}, "
                                f"現在時刻: {now.strftime('%Y-%m-%d %H:%M')}, "
                                f"差分: {time_diff}秒, "
                                f"繰り返し: {notification.repeat}"
                            )

                            # 過去の通知（-30分以上前）
                            if time_diff < -1800:  # 30分以上過去
                                if notification.repeat and notification.repeat != 'none':
                                    # 繰り返し通知は削除せず、次の発生時刻にロールフォワード
                                    rolled_time = notification_time
                                    safety_counter = 0
                                    # 次回実行時刻が未来（>60秒先）になるまで繰り返し
                                    while (rolled_time - now).total_seconds() <= 60:
                                        rolled_time = self._calculate_next_notification_time(rolled_time, notification.repeat)
                                        safety_counter += 1
                                        if safety_counter > 100:
                                            self.logger.warning(f"ロールフォワード安全上限に到達: {notification_id}, last={rolled_time}")
                                            break
                                    notifications_to_update.append({
                                        'id': notification_id,
                                        'datetime': rolled_time.strftime('%Y-%m-%d %H:%M')
                                    })
                                    self.logger.info(
                                        f"過去の繰り返し通知を次回に更新: {notification_id} -> {rolled_time.strftime('%Y-%m-%d %H:%M')}"
                                    )
                                    continue
                                else:
                                    # 一回限りは削除
                                    self.logger.info(f"期限切れの通知を削除: {notification_id} ({notification_time.strftime('%Y-%m-%d %H:%M')})")
                                    notifications_to_remove.append(notification_id)
                                    continue

                            # 通知実行条件の改善
                            should_send = False
                            
                            # より柔軟な時刻マッチング
                            if time_diff <= 0 and time_diff >= -60:
                                # 0-60秒前の通知を実行
                                should_send = True
                                self.logger.debug(f"時刻範囲による通知実行: {notification_id}")
                            elif notification_time.hour == now.hour and notification_time.minute == now.minute:
                                # 同じ時分の場合も実行（秒数は無視）
                                should_send = True
                                self.logger.debug(f"時分一致による通知実行: {notification_id}")

                            if should_send:
                                # 重複送信防止のチェック
                                last_sent_key = f"_last_sent_{notification_id}"
                                last_sent_time = getattr(self, last_sent_key, None)
                                
                                if last_sent_time:
                                    time_since_last = (now - last_sent_time).total_seconds()
                                    if time_since_last < 300:  # 5分以内の重複送信を防止
                                        self.logger.debug(f"重複送信防止: {notification_id} (前回送信から{int(time_since_last)}秒)")
                                        continue

                                # 通知メッセージを送信
                                try:
                                    # クイックリプライの作成
                                    quick_reply_items = [
                                        QuickReplyButton(
                                            action=MessageAction(label="✅ 確認", text=f"通知確認 {notification_id}")
                                        ),
                                        QuickReplyButton(
                                            action=MessageAction(label="🗑️ 削除", text=f"通知削除 {notification_id}")
                                        ),
                                        QuickReplyButton(
                                            action=MessageAction(label="📋 一覧", text="通知一覧")
                                        )
                                    ]
                                    
                                    try:
                                        quick_reply = QuickReply(items=quick_reply_items)
                                    except Exception as e:
                                        self.logger.error(f"クイックリプライ作成エラー: {str(e)}")
                                        quick_reply = None

                                    # 通知メッセージの作成
                                    message = f"🔔 通知: {notification.title}\n📝 {notification.message}"
                                    
                                    # LINE API送信
                                    self.line_bot_api.push_message(
                                        user_id,
                                        TextSendMessage(text=message, quick_reply=quick_reply)
                                    )
                                    
                                    # 送信時刻を記録
                                    setattr(self, last_sent_key, now)
                                    notifications_sent += 1
                                    data_modified = True
                                    
                                    self.logger.info(f"通知を送信: ユーザー={user_id}, タイトル={notification.title}, 時刻={notification_time.strftime('%Y-%m-%d %H:%M')}")

                                    if notification.repeat == 'none':
                                        # 一回限りの通知は削除リストに追加
                                        notifications_to_remove.append(notification_id)
                                        self.logger.debug(f"一回限りの通知を削除リストに追加: {notification_id}")
                                    else:
                                        # 定期通知は次回の時刻を設定
                                        next_time = self._calculate_next_notification_time(notification_time, notification.repeat)
                                        notifications_to_update.append({
                                            'id': notification_id,
                                            'datetime': next_time.strftime('%Y-%m-%d %H:%M')
                                        })
                                        self.logger.info(f"次回の通知を設定: {next_time.strftime('%Y-%m-%d %H:%M')}")

                                except Exception as e:
                                    if hasattr(e, 'status_code') and e.status_code == 429:
                                        # LINE APIの月間制限エラー（429）の場合
                                        self.logger.warning("LINE APIの月間制限に達しました")
                                        # ユーザーに制限到達を通知
                                        try:
                                            self.line_bot_api.push_message(
                                                user_id,
                                                TextSendMessage(text="⚠️ LINE APIの月間制限に達したため、通知の送信を一時停止します。")
                                            )
                                        except Exception:
                                            pass
                                        # API制限時刻を記録（60分後まで）
                                        self._api_limit_until = now + timedelta(hours=1)
                                        break
                                    else:
                                        self.logger.error(f"通知送信エラー: {str(e)}")

                        except Exception as e:
                            self.logger.error(f"通知処理エラー（{notification_id}）: {str(e)}")
                            continue

                    # データ変更があった場合のみ保存処理を実行
                    if notifications_to_remove or notifications_to_update:
                        # 削除処理
                        for notification_id in notifications_to_remove:
                            if notification_id in user_notifications:
                                del user_notifications[notification_id]
                                self.logger.info(f"一回限りの通知を削除: {notification_id}")
                                data_modified = True

                        # 更新処理
                        for update_info in notifications_to_update:
                            notification_id = update_info['id']
                            new_datetime = update_info['datetime']
                            if notification_id in user_notifications:
                                user_notifications[notification_id].datetime = new_datetime
                                self.logger.info(f"定期通知の次回時刻を更新: {notification_id} -> {new_datetime}")
                                data_modified = True

                        # ユーザーの通知が空になった場合、ユーザーエントリを削除
                        if not user_notifications:
                            if user_id in self.notifications:
                                del self.notifications[user_id]
                                self.logger.info(f"ユーザー {user_id} の通知がすべて完了しました")
                                data_modified = True

                # データが変更された場合は保存（ロック内なのでlock_acquired=True）
                if data_modified:
                    try:
                        self._save_notifications(lock_acquired=True)
                        self.logger.info(f"通知データの変更を保存しました (送信数: {notifications_sent})")
                    except Exception as save_error:
                        self.logger.error(f"通知データの保存に失敗: {str(save_error)}")

            self.logger.info(f"通知チェック完了: {notifications_sent}件送信")

        except Exception as e:
            self.logger.error(f"通知チェックエラー: {str(e)}")
            # エラー時もデータを保存して整合性を保つ
            try:
                if hasattr(self, 'lock'):
                    with self.lock:
                        self._save_notifications(lock_acquired=True)
            except Exception as save_error:
                self.logger.error(f"エラー時のデータ保存に失敗: {str(save_error)}")

    def add_notification_from_text(self, user_id: str, text: str) -> tuple[bool, str]:
        """
        テキストから通知を追加

        Args:
            user_id (str): ユーザーID
            text (str): 通知設定テキスト

        Returns:
            tuple[bool, str]: (成功したか, メッセージ)
        """
        try:
            self.logger.info(f"通知設定開始: user_id={user_id}, text='{text}'")
            
            # 上限チェック（ユーザーあたり）
            try:
                max_per_user = config_manager.get_config().max_notifications_per_user
            except Exception:
                max_per_user = 100
            current_count = len(self.get_notifications(user_id))
            if current_count >= max_per_user:
                limit_msg = (
                    f"⚠️ 通知の上限（{max_per_user}件）に達しています。\n"
                    "不要な通知を削除してから、もう一度お試しください。\n"
                    "例:『通知一覧』『通知削除 n_...』"
                )
                return False, limit_msg

            # 重複通知のチェック
            existing_notifications = self.get_notifications(user_id)
            for notification in existing_notifications:
                # 同じメッセージまたは非常に類似したメッセージの場合は重複として扱う
                if (notification.message.strip() == text.strip() or 
                    self._is_similar_notification(notification.message, text)):
                    self.logger.info(f"重複通知検出: 既存='{notification.message}', 新規='{text}'")
                    return False, f"⚠️ 類似した通知が既に設定されています:\n「{notification.title}」({notification.datetime})\n\n新しい通知を追加する場合は、時刻や内容を変更してください。"
            
            # まずGemini AIで通知内容を解析
            result = None
            try:
                result = self.gemini_service.parse_notification_request(text)
                self.logger.debug(f"Gemini解析結果: {result}")
            except Exception as e:
                self.logger.warning(f"Gemini解析に失敗、フォールバック処理へ: {str(e)}")
            
            # Gemini解析が失敗した場合はシンプルパターンで解析
            if not result:
                self.logger.info("Gemini解析失敗のため、シンプルパターンで解析を試行")
                result = self.gemini_service._simple_notification_parse(text)
                self.logger.debug(f"シンプル解析結果: {result}")
            
            if not result:
                self.logger.warning("通知解析が完全に失敗")
                return False, "通知の形式が正しくありません。「3時に起きる」「12時40分に課題をやる」のように指定してください。"

            # あいまい時間候補がある場合は、選択肢を提示
            if result and not result.get('datetime') and result.get('time_candidates'):
                try:
                    conv = self.gemini_service._get_conversation_memory()
                    if conv:
                        conv.set_user_temp(user_id, 'pending_notification_text', text)
                except Exception:
                    pass
                candidates = result.get('time_candidates')[:4]
                try:
                    if conv:
                        conv.set_user_temp(user_id, 'time_candidates', candidates)
                except Exception:
                    pass
                buttons = []
                for c in candidates:
                    buttons.append({
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": f"{c} にする",
                            "text": f"通知時間 {c}"
                        }
                    })
                flex = {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": "時間を選択してください", "weight": "bold", "size": "lg"},
                            {"type": "text", "text": "候補:", "size": "sm", "color": "#999999"}
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": buttons,
                        "flex": 0
                    }
                }
                return True, flex

            # スマート時間解析を試行
            notification_time = None

            # 解析結果に日時が含まれている場合はそれを使用
            if 'datetime' in result and result['datetime']:
                self.logger.debug(f"解析済み時刻: {result['datetime']}")
                formats = ['%Y-%m-%d %H:%M', '%Y/%m/%d %H:%M', '%Y-%m-%dT%H:%M:%S']
                for fmt in formats:
                    try:
                        notification_time = datetime.strptime(result['datetime'], fmt)
                        notification_time = pytz.timezone('Asia/Tokyo').localize(notification_time)
                        self.logger.debug(f"時刻解析成功: {notification_time}")
                        break
                    except ValueError:
                        continue
                else:
                    self.logger.debug(f"時刻形式が標準形式ではありません: {result['datetime']}")

            # 解析が失敗した場合やスマート解析が必要な場合
            if not notification_time:
                self.logger.debug("スマート時間解析を実行")
                # オリジナルのテキストからスマート解析を試行
                notification_time = self.parse_smart_time(text)
                if not notification_time:
                    self.logger.error(f"通知時刻の解析に失敗: text='{text}'")
                    return False, "通知時刻を解析できませんでした。「明日の朝9時」「12時40分に課題」のように指定してください。"

            # 解析された時刻をフォーマット
            result['datetime'] = notification_time.strftime('%Y-%m-%d %H:%M')
            self.logger.info(f"最終的な通知時刻: {result['datetime']}")

            # 通知を追加
            notification_id = self.add_notification(
                user_id=user_id,
                title=result.get('title', 'リマインダー'),
                message=result.get('message', text),
                datetime_str=result['datetime'],
                priority=result.get('priority', 'medium'),
                repeat=result.get('repeat', 'none')
            )

            if notification_id:
                self.logger.info(f"通知追加成功: ID={notification_id}")
                # メッセージの生成
                notification_time = datetime.strptime(result['datetime'], '%Y-%m-%d %H:%M')
                now = datetime.now(pytz.timezone('Asia/Tokyo'))
                time_diff = notification_time - now.replace(tzinfo=None)
                hours_diff = time_diff.total_seconds() / 3600

                response = [f"✅ 通知を設定しました"]
                response.append(f"📅 日時: {notification_time.strftime('%Y年%m月%d日 %H時%M分')}")

                # 残り時間の表示
                if hours_diff < 24:
                    response.append(f"⏰ 残り約{int(hours_diff)}時間")
                else:
                    days = int(hours_diff / 24)
                    hours = int(hours_diff % 24)
                    response.append(f"⏰ 残り約{days}日{hours}時間")

                if result.get('repeat') != 'none':
                    repeat_text = {
                        'daily': '毎日',
                        'weekly': '毎週',
                        'monthly': '毎月'
                    }[result['repeat']]
                    response.append(f"🔄 {repeat_text}繰り返し")

                response.append(f"📝 内容: {result.get('message', text)}")

                return True, "\n".join(response)
            else:
                self.logger.error(f"通知追加に失敗: user_id={user_id}")
                return False, "通知の設定に失敗しました。"

        except Exception as e:
            self.logger.error(f"通知設定エラー: {str(e)}", exc_info=True)
            return False, f"通知の設定中にエラーが発生しました: {str(e)}"

    def _is_similar_notification(self, message1: str, message2: str) -> bool:
        """
        2つの通知メッセージが類似しているかを判定
        
        Args:
            message1 (str): メッセージ1
            message2 (str): メッセージ2
            
        Returns:
            bool: 類似している場合True
        """
        # 簡単な類似性判定（同じキーワードが含まれているかチェック）
        msg1_words = set(message1.lower().replace('毎日', '').replace('時', '').replace('分', '').split())
        msg2_words = set(message2.lower().replace('毎日', '').replace('時', '').replace('分', '').split())
        
        # 共通の重要な単語の割合を計算
        if len(msg1_words) == 0 or len(msg2_words) == 0:
            return False
            
        common_words = msg1_words.intersection(msg2_words)
        similarity_ratio = len(common_words) / max(len(msg1_words), len(msg2_words))
        
        # 70%以上の単語が共通している場合は類似と判定
        return similarity_ratio >= 0.7

    def add_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        datetime_str: str,
        priority: str = 'medium',
        repeat: str = 'none',
        template_id: str = None
    ) -> Union[str, None]:
        """
        新しい通知を追加

        Args:
            user_id (str): ユーザーID
            title (str): 通知タイトル
            message (str): 通知メッセージ
            datetime_str (str): 通知日時
            priority (str, optional): 優先度
            repeat (str, optional): 繰り返し設定
            template_id (str, optional): テンプレートID

        Returns:
            Union[str, None]: 通知ID、失敗時はNone
        """
        try:
            with self.lock:
                # 既存データを読み込み（重要：既存通知を上書きしないため）
                self._load_notifications()
                
                # 入力検証
                if not user_id or not title.strip() or not message.strip() or not datetime_str.strip():
                    self.logger.warning("通知作成: 必須フィールドが空です")
                    return None
                
                # ユーザー上限チェック
                try:
                    max_per_user = config_manager.get_config().max_notifications_per_user
                except Exception:
                    max_per_user = 100
                current_count = len(self.notifications.get(user_id, {}))
                if current_count >= max_per_user:
                    self.logger.info(f"通知上限超過: user={user_id}, current={current_count}, max={max_per_user}")
                    return None

                # 日時フォーマットの検証
                valid_formats = ['%Y-%m-%d %H:%M', '%Y/%m/%d %H:%M', '%Y-%m-%dT%H:%M:%S']
                datetime_valid = False
                for fmt in valid_formats:
                    try:
                        datetime.strptime(datetime_str, fmt)
                        datetime_valid = True
                        break
                    except ValueError:
                        continue
                
                if not datetime_valid:
                    self.logger.warning(f"通知作成: 無効な日時フォーマット: {datetime_str}")
                    return None
                
                # 一意な通知IDを生成（ミリ秒 + ランダム要素）
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]  # マイクロ秒の最初の3桁（ミリ秒）
                random_suffix = f"{random.randint(100, 999)}"
                notification_id = f"n_{timestamp}_{random_suffix}"

                # 通知オブジェクトを作成
                notification = Notification(
                    id=notification_id,
                    user_id=user_id,
                    title=title,
                    message=message,
                    datetime=datetime_str,
                    priority=priority,
                    repeat=repeat,
                    template_id=template_id,
                    history=[{
                        'type': 'created',
                        'timestamp': datetime.now(pytz.UTC).isoformat()
                    }]
                )

                # ユーザーの通知辞書を取得または作成
                if user_id not in self.notifications:
                    self.notifications[user_id] = {}

                # 追加前の件数をログ出力
                before_count = len(self.notifications[user_id])
                self.logger.debug(f"通知追加前: ユーザー {user_id} の通知数 = {before_count}")

                # 通知を保存
                self.notifications[user_id][notification_id] = notification
                
                # 追加後の件数をログ出力
                after_count = len(self.notifications[user_id])
                self.logger.debug(f"通知追加後: ユーザー {user_id} の通知数 = {after_count}")
                
                self._save_notifications(lock_acquired=True)

                return notification_id

        except Exception as e:
            self.logger.error(f"通知追加エラー: {str(e)}")
            return None

    def delete_notification(self, user_id: str, notification_id: str) -> bool:
        """
        指定された通知を削除

        Args:
            user_id (str): ユーザーID
            notification_id (str): 通知ID

        Returns:
            bool: 削除成功時True
        """
        try:
            with self.lock:
                # 削除前に最新データを読み込み
                self._load_notifications()
                
                if user_id not in self.notifications:
                    self.logger.warning(f"ユーザー {user_id} が見つかりません")
                    return False

                if notification_id not in self.notifications[user_id]:
                    self.logger.warning(f"通知 {notification_id} が見つかりません")
                    return False

                # 削除前の状態を記録
                before_count = len(self.notifications[user_id])
                self.logger.info(f"削除対象: ユーザー {user_id} の通知 {notification_id} (合計{before_count}件中)")
                
                # メモリから削除
                del self.notifications[user_id][notification_id]
                
                # ユーザーの通知が空になった場合、ユーザーエントリも削除
                if not self.notifications[user_id]:
                    del self.notifications[user_id]

                # ファイルに保存（ロック取得済みなのでlock_acquired=True）
                try:
                    self._save_notifications(lock_acquired=True)
                    
                    # 保存後の検証
                    self._load_notifications()
                    
                    # 削除が正しく反映されているかチェック
                    if user_id in self.notifications and notification_id in self.notifications[user_id]:
                        self.logger.error(f"削除後の検証に失敗: 通知 {notification_id} がまだ存在します")
                        return False
                    
                    self.logger.info(f"通知を削除しました: {notification_id}")
                    return True
                    
                except Exception as save_error:
                    self.logger.error(f"通知削除の保存に失敗: {str(save_error)}")
                    # 保存に失敗した場合は、メモリ上の変更を元に戻す
                    if user_id not in self.notifications:
                        self.notifications[user_id] = {}
                    # 削除した通知を復元（可能であれば）
                    return False

        except Exception as e:
            self.logger.error(f"通知削除エラー: {str(e)}")
            return False

    def delete_all_notifications(self, user_id: str) -> int:
        """
        指定されたユーザーの全通知を削除

        Args:
            user_id (str): ユーザーID
            
        Returns:
            int: 削除された通知の数
        """
        try:
            with self.lock:
                # 削除前に最新データを読み込み
                self._load_notifications()
                
                if user_id not in self.notifications:
                    self.logger.warning(f"ユーザー {user_id} が見つかりません")
                    return 0

                deleted_count = len(self.notifications[user_id])
                self.logger.info(f"削除対象: ユーザー {user_id} の {deleted_count}件の通知")
                
                # メモリから削除
                del self.notifications[user_id]
                
                # ファイルに保存（ロック取得済みなのでlock_acquired=True）
                try:
                    self._save_notifications(lock_acquired=True)
                    
                    # 保存後の検証
                    self._load_notifications()
                    
                    # 削除が正しく反映されているかチェック
                    if user_id in self.notifications:
                        remaining_count = len(self.notifications[user_id])
                        self.logger.error(f"全削除後の検証に失敗: {remaining_count}件の通知が残っています")
                        return 0
                    
                    self.logger.info(f"ユーザー {user_id} の全通知を削除しました: {deleted_count}件")
                    return deleted_count
                    
                except Exception as save_error:
                    self.logger.error(f"全通知削除の保存に失敗: {str(save_error)}")
                    # 保存に失敗した場合は、メモリ上の変更を元に戻す
                    self.notifications[user_id] = {}  # 空の辞書で復元
                    return 0

        except Exception as e:
            self.logger.error(f"全通知削除エラー: {str(e)}")
            return 0

    def update_notification(self, user_id: str, notification_id: str, updates: dict) -> bool:
        """
        通知を更新

        Args:
            user_id (str): ユーザーID
            notification_id (str): 通知ID
            updates (dict): 更新する項目の辞書

        Returns:
            bool: 更新成功時True
        """
        try:
            with self.lock:
                self.logger.debug(f"update_notification called for user_id: {user_id}, notification_id: {notification_id}")
                if user_id in self.notifications and notification_id in self.notifications[user_id]:
                    notification = self.notifications[user_id][notification_id]
                    
                    # 更新可能な項目のみを更新
                    updatable_fields = ['title', 'message', 'datetime', 'priority', 'repeat']
                    updated_fields = []
                    
                    for field, value in updates.items():
                        if field in updatable_fields and hasattr(notification, field):
                            old_value = getattr(notification, field)
                            setattr(notification, field, value)
                            updated_fields.append(f"{field}: {old_value} -> {value}")
                    
                    if updated_fields:
                        # 更新時刻を記録
                        notification.updated_at = datetime.now(pytz.UTC).isoformat()
                        
                        # 履歴にイベントを追加
                        if notification.history is None:
                            notification.history = []
                        notification.history.append({
                            'type': 'updated',
                            'timestamp': notification.updated_at,
                            'changes': updated_fields
                        })
                        
                        self._save_notifications(lock_acquired=True)
                        self.logger.debug(f"Notification updated successfully: {notification_id}, changes: {updated_fields}")
                        return True
                    else:
                        self.logger.debug(f"No valid updates provided for notification: {notification_id}")
                        return False
                else:
                    self.logger.debug(f"Notification not found for update: {notification_id}")
                    return False
        except Exception as e:
            self.logger.error(f"通知更新エラー: {str(e)}")
            return False

    def create_template(self, user_id: str, notification: Union[Notification, Dict[str, Any]]) -> Union[str, None]:
        """
        通知テンプレートを作成
        
        Args:
            user_id (str): ユーザーID
            notification (Union[Notification, Dict[str, Any]]): 通知データ
            
        Returns:
            Union[str, None]: テンプレートID、失敗時はNone
        """
        try:
            with self.lock:
                # 一意なテンプレートIDを生成
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]
                random_suffix = f"{random.randint(100, 999)}"
                template_id = f"t_{timestamp}_{random_suffix}"
                
                if isinstance(notification, dict):
                    template = Notification(
                        id=template_id,
                        user_id=user_id,
                        title=notification['title'],
                        message=notification['message'],
                        datetime=notification.get('datetime', ''),
                        priority=notification.get('priority', 'medium'),
                        repeat=notification.get('repeat', 'none'),
                        is_template=True
                    )
                else:
                    template = Notification(
                        id=template_id,
                        user_id=user_id,
                        title=notification.title,
                        message=notification.message,
                        datetime=notification.datetime,
                        priority=notification.priority,
                        repeat=notification.repeat,
                        is_template=True
                    )

                if user_id not in self.notifications:
                    self.notifications[user_id] = {}

                self.notifications[user_id][template.id] = template
                self._save_notifications(lock_acquired=True)
                return template.id

        except Exception as e:
            self.logger.error(f"テンプレート作成エラー: {str(e)}")
            return None

    def get_templates(self, user_id: str) -> List[Notification]:
        """
        ユーザーのテンプレート一覧を取得
        """
        return super().get_templates(user_id)

    def process_natural_language_input(self, user_id: str, text: str) -> dict:
        """
        自然言語入力の処理
        """
        try:
            # GeminiServiceで自然言語解析
            parsed = self.gemini_service.parse_natural_language(text)
            
            if parsed.get('intent') == 'list_notifications':
                notifications = self.get_notifications(user_id)
                return {"intent": "list_notifications", "notifications": notifications}
            
            if parsed.get('intent') == 'delete_notification':
                notification_id = parsed.get('notification_id')
                if notification_id:
                    success = self.delete_notification(user_id, notification_id)
                    return {"intent": "delete_notification", "success": success, "notification_id": notification_id}
                else:
                    return {"intent": "delete_notification", "success": False, "error": "通知IDが指定されていません"}
            
            
            # 文脈分析
            context = self.context_utils.analyze_conversation_context(user_id)
            # 通知最適化
            #optimized = self.optimize_reminder_based_on_context(parsed, context)
            
            # 類似通知分析
            #patterns = self.analyze_notification_patterns(user_id)
            
            return parsed
            #return {
            #    "original": parsed,
            #    "optimized": optimized,
            #    "patterns": patterns,
            #    "suggestions": self._generate_suggestions(optimized, patterns)
            #}
            
        except Exception as e:
            self.logger.error(f"自然言語処理エラー: {str(e)}")
            return {"error": "自然言語の処理に失敗しました"}

    def get_notifications(self, user_id: str) -> List[Notification]:
        """
        ユーザーの通知一覧を取得
        """
        # データの再読み込みを強制実行（最新状態を取得）
        self._load_notifications()
        
        self.logger.debug(f"get_notifications called for user_id: {user_id}")
        self.logger.debug(f"ユーザーID: {user_id} の通知一覧を取得開始") # ログ追加
        if user_id not in self.notifications:
            self.logger.debug(f"ユーザーID: {user_id} の通知が見つかりませんでした") # ログ追加
            return []
        notifications = list(self.notifications[user_id].values())
        self.logger.debug(f"ユーザーID: {user_id} の通知一覧を取得完了 (件数: {len(notifications)})") # ログ追加
        self.logger.debug(f"Returning notifications: {notifications}")
        return notifications

    def analyze_notification_patterns(self, user_id: str) -> dict:
        """
        類似通知パターンを分析
        """
        notifications = self.get_notifications(user_id)
        if not notifications:
            return {}

        # 時系列分析
        time_patterns = self._analyze_time_distribution(notifications)
        
        # コンテンツ類似性分析
        content_similarity = []
        if notifications: # 通知が存在する場合のみ類似性分析を実行
            content_similarity = self._calculate_content_similarity(notifications)
        # 優先度トレンド分析
        priority_trends = self._identify_priority_trends(notifications)
        
        return {
            "time_patterns": time_patterns,
            "content_similarity": content_similarity,
            "priority_trends": priority_trends
        }

    def optimize_reminder_based_on_context(self, reminder_data: dict, context: dict) -> dict:
        """
        文脈に基づいてリマインダーを最適化
        """
        optimized = reminder_data.copy()
        
        # 優先度の調整
        optimized['priority'] = self._adjust_priority_based_on_context(
            reminder_data['priority'],
            context
        )
        
        # 通知タイミングの最適化
        optimized['datetime'] = self._optimize_notification_time(
            reminder_data['datetime'],
            context
        )
        
        # 重複通知のチェック
        if self._is_duplicate_notification(optimized, context):
            optimized['status'] = 'duplicate'
            
        return optimized

    def _analyze_time_distribution(self, notifications: list) -> dict:
        """通知時間の分布を分析"""
        time_dist = {
            'morning': 0,
            'afternoon': 0,
            'evening': 0,
            'night': 0
        }
        
        for n in notifications:
            dt = datetime.strptime(n.datetime, '%Y-%m-%d %H:%M')
            hour = dt.hour
            if 5 <= hour < 10:
                time_dist['morning'] += 1
            elif 10 <= hour < 17:
                time_dist['afternoon'] += 1
            elif 17 <= hour < 22:
                time_dist['evening'] += 1
            else:
                time_dist['night'] += 1
                
        return time_dist

    def _calculate_content_similarity(self, notifications: list) -> list:
        """
        通知内容の類似性を計算
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        texts = [n.message for n in notifications]
        if len(texts) < 2:
            return []
            
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        return similarity_matrix.tolist()

    def _identify_priority_trends(self, notifications: list) -> dict:
        """
        優先度のトレンドを分析
        """
        priority_count = {
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for n in notifications:
            priority_count[n.priority] += 1
            
        return {
            'counts': priority_count,
            'trend': self._detect_priority_trend(notifications)
        }

    def _detect_priority_trend(self, notifications: list) -> str:
        """優先度の時系列トレンドを検出"""
        # 実装詳細...
        return "stable"

    def _adjust_priority_based_on_context(self, priority: str, context: dict) -> str:
        """
        文脈に基づいて優先度を調整
        """
        # コンテキストからキーワードを分析
        keywords = context.get('priority_keywords', [])
        if any(kw in ['urgent', 'asap'] for kw in keywords):
            return 'high'
        if any(kw in ['low', 'whenever'] for kw in keywords):
            return 'low'
        return priority

    def _optimize_notification_time(self, datetime_str: str, context: dict) -> str:
        """
        最適な通知時刻を計算
        """
        dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        
        # ユーザーの活動時間帯を考慮
        preferred_hours = context.get('preferred_hours', [9, 12, 18])
        closest_hour = min(preferred_hours, key=lambda x: abs(x - dt.hour))
        
        optimized_dt = dt.replace(hour=closest_hour, minute=0)
        return optimized_dt.strftime('%Y-%m-%d %H:%M')

    def _is_duplicate_notification(self, notification: dict, context: dict) -> bool:
        """
        重複通知かどうかを判定
        """
        similarity_threshold = 0.8
        for existing in context.get('existing_notifications', []):
            if existing['message'] == notification['message']:
                return True
            if self._calculate_similarity(existing['message'], notification['message']) > similarity_threshold:
                return True
        return False

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        テキスト類似度を計算
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer()
        tfidf = vectorizer.fit_transform([text1, text2])
        return (tfidf * tfidf.T).A[0][1]

    def _generate_suggestions(self, optimized: dict, patterns: dict) -> list:
        """
        最適化提案を生成
        """
        suggestions = []
        
        # 時間帯提案
        time_slot = datetime.strptime(optimized['datetime'], '%Y-%m-%d %H:%M').hour
        if time_slot in [22, 23, 0, 1, 2, 3, 4]:
            suggestions.append("深夜の通知は控えめにすることを提案します")
            
        # 優先度提案
        if optimized['priority'] == 'high' and patterns['priority_trends']['counts']['high'] > 5:
            suggestions.append("高優先度通知が多数あります。優先度の見直しを提案します")
            
        # 類似通知チェック
        if patterns['content_similarity']:
            max_sim = max([max(row) for row in patterns['content_similarity']])
            if max_sim > 0.7:
                suggestions.append("類似した内容の通知が複数存在します")
                
        return suggestions

    def create_from_template(self, user_id: str, template_id: str, datetime_str: str) -> Union[str, None]:
        """
        テンプレートから新しい通知を作成
        
        Args:
            user_id (str): ユーザーID
            template_id (str): テンプレートID
            datetime_str (str): 通知日時
            
        Returns:
            Union[str, None]: 通知ID、失敗時はNone
        """
        try:
            with self.lock:
                if user_id not in self.notifications or template_id not in self.notifications[user_id]:
                    return None

                template = self.notifications[user_id][template_id]
                if not template.is_template:
                    return None

                return self.add_notification(
                    user_id=user_id,
                    title=template.title,
                    message=template.message,
                    datetime_str=datetime_str,
                    priority=template.priority,
                    repeat=template.repeat,
                    template_id=template_id
                )

        except Exception as e:
            self.logger.error(f"テンプレートからの通知作成エラー: {str(e)}")
            return None

    def acknowledge_notification(self, user_id: str, notification_id: str) -> bool:
        """
        通知を確認済みとしてマーク
        """
        try:
            with self.lock:
                if user_id in self.notifications and notification_id in self.notifications[user_id]:
                    notification = self.notifications[user_id][notification_id]
                    notification.acknowledged = True
                    notification.updated_at = datetime.now(pytz.UTC).isoformat()

                    # 履歴にイベントを追加
                    if notification.history is None:
                        notification.history = []
                    notification.history.append({
                        'type': 'acknowledged',
                        'timestamp': notification.updated_at
                    })

                    self._save_notifications(lock_acquired=True)
                    return True
            return False
        except Exception as e:
            self.logger.error(f"通知確認エラー: {str(e)}")
            return False

    # -----------------------
    # 一括操作（フィルタ＋操作）
    # -----------------------
    def filter_notifications(self, user_id: str, *, day_scope: str | None = None, priority: str | None = None) -> List[Notification]:
        """簡易フィルタ（day_scope: today/this_week, priority: high/medium/low）"""
        items = self.get_notifications(user_id)
        if not items:
            return []
        from datetime import datetime, timedelta
        now = datetime.now()
        result = []
        for n in items:
            try:
                dt = datetime.strptime(n.datetime, '%Y-%m-%d %H:%M')
            except Exception:
                dt = None
            if day_scope == 'today' and dt and dt.date() != now.date():
                continue
            if day_scope == 'this_week' and dt and (dt - now).days > 7:
                continue
            if priority and n.priority != priority:
                continue
            result.append(n)
        return result

    def bulk_snooze(self, user_id: str, notifications: List[Notification], minutes: int) -> int:
        from datetime import datetime, timedelta
        count = 0
        for n in notifications:
            try:
                dt = datetime.strptime(n.datetime, '%Y-%m-%d %H:%M') + timedelta(minutes=minutes)
                if self.update_notification(user_id, n.id, {'datetime': dt.strftime('%Y-%m-%d %H:%M')}):
                    count += 1
            except Exception:
                continue
        return count

    def bulk_delete(self, user_id: str, notifications: List[Notification]) -> int:
        count = 0
        for n in notifications:
            if self.delete_notification(user_id, n.id):
                count += 1
        return count

    def format_notifications(self, notifications: List[Notification]) -> str:
        """このメソッドは非推奨です。代わりにformat_notification_listを使用してください"""
        return self.format_notification_list(notifications, format_type='detailed')

    def format_notification_list(self, notifications: List[Notification], format_type: str = 'default') -> Union[str, Dict[str, Any]]:
        """
        通知リストを整形

        Args:
            notifications (List[Notification]): 通知オブジェクトのリスト
            format_type (str): 整形タイプ ('default', 'flex_message')

        Returns:
            Union[str, Dict[str, Any]]: 整形された通知リスト（文字列またはFlex Message JSON）
        """
        if not notifications:
            if format_type == 'flex_message':
                return {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "現在、設定されている通知はありません。",
                                "wrap": True
                            }
                        ]
                    }
                }
            return "現在、設定されている通知はありません。"

        if format_type == 'flex_message':
            # 1) 通知を予定日時順にソート（解析できないものは末尾）
            def _parse_dt(n):
                try:
                    return datetime.strptime(n.datetime, '%Y-%m-%d %H:%M')
                except ValueError:
                    return datetime.max
            notifications_sorted = sorted(notifications, key=_parse_dt)

            bubbles = []

            # 2) 概要バブルを先頭に追加
            total_count = len(notifications_sorted)
            priority_counts = {p: 0 for p in ['high', 'medium', 'low']}
            for n in notifications_sorted:
                priority_counts[n.priority] = priority_counts.get(n.priority, 0) + 1

            summary_contents = [
                {"type": "text", "text": "📊 通知概要", "weight": "bold", "size": "xl"},
                {"type": "text", "text": f"合計: {total_count} 件", "margin": "md"},
                {"type": "text", "text": f"⏫ 高: {priority_counts['high']}  ⏺ 中: {priority_counts['medium']}  ⏬ 低: {priority_counts['low']}", "margin": "sm"}
            ]

            summary_bubble = {
                "type": "bubble",
                "size": "mega",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": summary_contents
                }
            }
            bubbles.append(summary_bubble)

            # 3) 各通知バブルを生成
            for notification in notifications_sorted:
                # 日時を整形
                try:
                    dt_obj = datetime.strptime(notification.datetime, '%Y-%m-%d %H:%M')
                    formatted_datetime = dt_obj.strftime('%Y年%m月%d日 %H時%M分')
                except ValueError:
                    formatted_datetime = notification.datetime # 解析失敗時はそのまま表示

                # 残り時間を計算
                remaining_text = ""
                try:
                    if 'dt_obj' in locals():
                        now_jst = datetime.now(pytz.timezone('Asia/Tokyo'))
                        delta = dt_obj - now_jst
                        if delta.total_seconds() > 0:
                            hours = int(delta.total_seconds() // 3600)
                            days, hours = divmod(hours, 24)
                            if days > 0:
                                remaining_text = f"あと約{days}日{hours}時間"
                            else:
                                remaining_text = f"あと約{hours}時間"
                except Exception:
                    pass

                # 繰り返し設定の表示
                repeat_text = {
                    'none': '',
                    'daily': '毎日',
                    'weekly': '毎週',
                    'monthly': '毎月'
                }.get(notification.repeat, '')
                if repeat_text: repeat_text = f" ({repeat_text}繰り返し)"

                bubble = {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": notification.title,
                                "weight": "bold",
                                "size": "xl",
                                "wrap": True
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "margin": "lg",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "baseline",
                                        "spacing": "sm",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "日時",
                                                "color": "#aaaaaa",
                                                "size": "sm",
                                                "flex": 1
                                            },
                                            {
                                                "type": "text",
                                                "text": f"{formatted_datetime}{repeat_text}",
                                                "wrap": True,
                                                "color": "#666666",
                                                "size": "sm",
                                                "flex": 5
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "baseline",
                                        "spacing": "sm",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "残り",
                                                "color": "#aaaaaa",
                                                "size": "sm",
                                                "flex": 1
                                            },
                                            {
                                                "type": "text",
                                                "text": remaining_text or "-",
                                                "wrap": True,
                                                "color": "#666666",
                                                "size": "sm",
                                                "flex": 5
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "baseline",
                                        "spacing": "sm",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "内容",
                                                "color": "#aaaaaa",
                                                "size": "sm",
                                                "flex": 1
                                            },
                                            {
                                                "type": "text",
                                                "text": notification.message,
                                                "wrap": True,
                                                "color": "#666666",
                                                "size": "sm",
                                                "flex": 5
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "baseline",
                                        "spacing": "sm",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "ID",
                                                "color": "#aaaaaa",
                                                "size": "sm",
                                                "flex": 1
                                            },
                                            {
                                                "type": "text",
                                                "text": notification.id,
                                                "wrap": True,
                                                "color": "#666666",
                                                "size": "sm",
                                                "flex": 5
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "baseline",
                                        "spacing": "sm",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "優先度",
                                                "color": "#aaaaaa",
                                                "size": "sm",
                                                "flex": 1
                                            },
                                            {
                                                "type": "text",
                                                "text": self._format_priority_label(notification.priority),
                                                "wrap": True,
                                                "color": "#666666",
                                                "size": "sm",
                                                "flex": 5
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "button",
                                "style": "link",
                                "height": "sm",
                                "action": {
                                    "type": "message",
                                    "label": "編集",
                                    "text": f"通知編集 {notification.id}"
                                }
                            },
                            {
                                "type": "button",
                                "style": "link",
                                "height": "sm",
                                "action": {
                                    "type": "message",
                                    "label": "削除",
                                    "text": f"通知削除 {notification.id}"
                                }
                            }
                        ],
                        "flex": 0
                    }
                }
                bubbles.append(bubble)
            
            return {
                "type": "carousel",
                "contents": bubbles
            }

        # デフォルトのテキスト形式
        formatted_list = []
        if not notifications:
            return "現在、設定されている通知はありません。"

        for i, notification in enumerate(notifications):
            formatted_list.append(f"--- 通知 {i+1} ---")
            formatted_list.append(f"ID: {notification.id}")
            formatted_list.append(f"タイトル: {notification.title}")
            formatted_list.append(f"メッセージ: {notification.message}")
            formatted_list.append(f"日時: {notification.datetime}")
            formatted_list.append(f"優先度: {notification.priority}")
            formatted_list.append(f"繰り返し: {notification.repeat}")
            if notification.template_id: formatted_list.append(f"テンプレートID: {notification.template_id}")
            if notification.created_at: formatted_list.append(f"作成日時: {notification.created_at}")
            if notification.updated_at: formatted_list.append(f"更新日時: {notification.updated_at}")
            formatted_list.append("") # 空行で区切り

        return "\n".join(formatted_list)

    def parse_smart_time(self, time_expression: str) -> Union[datetime, None]:
        """
        スマートな時間表現を解析して日時に変換

        Args:
            time_expression (str): 時間表現（例: "明日の朝", "来週の水曜日", "明日の15時", "12時1分"）

        Returns:
            Union[datetime, None]: 解析された日時、失敗時はNone
        """
        try:
            self.logger.debug(f"時間解析開始: '{time_expression}'")
            
            # 現在の日時を取得（JST）
            jst = pytz.timezone('Asia/Tokyo')
            now = datetime.now(jst)
            base_date = now.date()

            # 日付に関する表現を解析
            if "明日" in time_expression:
                base_date += timedelta(days=1)
                self.logger.debug("明日として解析")
            elif "明後日" in time_expression:
                base_date += timedelta(days=2)
                self.logger.debug("明後日として解析")
            elif "来週" in time_expression:
                base_date += timedelta(weeks=1)
                self.logger.debug("来週として解析")
            elif "毎日" in time_expression:
                # 毎日の場合、次の実行を明日に設定
                base_date += timedelta(days=1)
                self.logger.debug("毎日として解析（明日から開始）")

            # 曜日の解析
            weekdays = {
                "月": 0, "火": 1, "水": 2, "木": 3, "金": 4, "土": 5, "日": 6,
                "月曜": 0, "火曜": 1, "水曜": 2, "木曜": 3, "金曜": 4, "土曜": 5, "日曜": 6
            }
            for day, idx in weekdays.items():
                if day in time_expression:
                    current_weekday = now.weekday()
                    days_until = (idx - current_weekday) % 7
                    if days_until == 0 and not any(x in time_expression for x in ["今", "本日"]):
                        days_until = 7
                    base_date += timedelta(days=days_until)
                    self.logger.debug(f"曜日として解析: {day}")
                    break

            # 時刻の解析
            hour = None
            minute = 0

            # 数字での時刻指定（分単位対応を強化）
            import re
            
            # "12時1分"のパターン
            time_match = re.search(r'(\d{1,2})時(\d{1,2})分', time_expression)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                self.logger.debug(f"時分形式で解析: {hour}時{minute}分")
            else:
                # "12:01"のパターン
                time_match = re.search(r'(\d{1,2}):(\d{1,2})', time_expression)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    self.logger.debug(f"コロン形式で解析: {hour}:{minute}")
                else:
                    # "12時"のパターン
                    time_match = re.search(r'(\d{1,2})時', time_expression)
                    if time_match:
                        hour = int(time_match.group(1))
                        minute = 0
                        self.logger.debug(f"時のみ形式で解析: {hour}時")

            # 12時間制の場合、午後の判定
            if hour is not None and hour <= 12 and ("午後" in time_expression or "pm" in time_expression.lower()):
                hour = (hour % 12) + 12
                self.logger.debug(f"午後として調整: {hour}時")

            # "朝" "昼" "夜"などの時間帯（数字指定がない場合のみ）
            if hour is None:
                if "朝" in time_expression:
                    hour = 8
                    self.logger.debug("朝として解析: 8時")
                elif "昼" in time_expression:
                    hour = 12
                    self.logger.debug("昼として解析: 12時")
                elif "午後" in time_expression:
                    hour = 14
                    self.logger.debug("午後として解析: 14時")
                elif "夕" in time_expression or "夕方" in time_expression:
                    hour = 17
                    self.logger.debug("夕方として解析: 17時")
                elif "夜" in time_expression:
                    hour = 20
                    self.logger.debug("夜として解析: 20時")

            # 時刻が指定されていない場合はデフォルト値を設定
            if hour is None:
                hour = now.hour
                minute = now.minute
                self.logger.debug(f"デフォルト時刻を使用: {hour}:{minute}")

            # 日時オブジェクトを作成
            result = datetime.combine(base_date, time(hour, minute))
            result = jst.localize(result)

            # 過去の時刻の場合は翌日に設定
            if result <= now:
                result += timedelta(days=1)
                self.logger.debug("過去の時刻のため翌日に調整")

            self.logger.info(f"時間解析完了: '{time_expression}' -> {result}")
            return result

        except Exception as e:
            self.logger.error(f"時間解析エラー: {str(e)}", exc_info=True)
            return None

    def _format_priority_label(self, priority: str) -> str:
        """
        優先度ラベルをフォーマット
        """
        priority_labels = {
            'high': '高',
            'medium': '中',
            'low': '低'
        }
        return priority_labels.get(priority, priority)