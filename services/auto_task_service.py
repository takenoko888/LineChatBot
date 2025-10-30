"""
Auto Task Service implementation
定期実行・モニタリング機能サービス
"""
import logging
import json
import os
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
from dataclasses import dataclass, asdict
import threading
import time
import schedule
from enum import Enum

@dataclass
class AutoTask:
    """自動実行タスク"""
    task_id: str
    user_id: str
    task_type: str  # 'weather', 'news', 'monitor', 'report'
    title: str
    description: str
    schedule_pattern: str  # 'daily', 'weekly', 'hourly', 'custom'
    schedule_time: str  # HH:MM format
    parameters: Dict[str, Any]
    is_active: bool = True
    created_at: datetime = None
    last_executed: datetime = None
    execution_count: int = 0
    
class TaskType(Enum):
    """タスクタイプ列挙"""
    WEATHER_DAILY = "weather_daily"
    NEWS_DAILY = "news_daily"
    KEYWORD_MONITOR = "keyword_monitor"
    STOCK_MONITOR = "stock_monitor"
    USAGE_REPORT = "usage_report"
    WEBSITE_MONITOR = "website_monitor"

class AutoTaskService:
    """自動実行・モニタリングサービス"""

    def __init__(self, storage_path: str = None, notification_service=None, 
                 weather_service=None, search_service=None, gemini_service=None):
        """
        初期化
        
        Args:
            storage_path (str): データ保存パス
            notification_service: 通知サービス
            weather_service: 天気サービス
            search_service: 検索サービス
            gemini_service: Gemini AIサービス
        """
        self.logger = logging.getLogger(__name__)
        self.jst = pytz.timezone('Asia/Tokyo')
        
        # サービス依存関係
        self.notification_service = notification_service
        self.weather_service = weather_service
        self.search_service = search_service
        self.gemini_service = gemini_service
        
        # ストレージ設定
        base_storage = storage_path or "/workspace/data"
        os.makedirs(base_storage, exist_ok=True)
        self.tasks_storage = os.path.join(base_storage, "auto_tasks.json")
        self.execution_log_storage = os.path.join(base_storage, "auto_task_logs.json")
        
        # データ構造
        self.tasks: Dict[str, AutoTask] = {}
        self.execution_logs: List[Dict[str, Any]] = []
        self.scheduler_thread = None
        self.is_running = False
        
        # ロック
        self.lock = threading.Lock()
        
        # データ読み込み
        self._load_data()
        
        # スケジューラ初期化
        self._setup_scheduler()
        
        self.logger.info("自動実行・モニタリングサービスを初期化しました")

    def _load_data(self) -> None:
        """保存データを読み込み"""
        try:
            # タスクの読み込み
            if os.path.exists(self.tasks_storage):
                with open(self.tasks_storage, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_id, task_data in data.items():
                        task = AutoTask(
                            task_id=task_data['task_id'],
                            user_id=task_data['user_id'],
                            task_type=task_data['task_type'],
                            title=task_data['title'],
                            description=task_data['description'],
                            schedule_pattern=task_data['schedule_pattern'],
                            schedule_time=task_data['schedule_time'],
                            parameters=task_data['parameters'],
                            is_active=task_data.get('is_active', True),
                            created_at=datetime.fromisoformat(task_data['created_at']) if task_data.get('created_at') else None,
                            last_executed=datetime.fromisoformat(task_data['last_executed']) if task_data.get('last_executed') else None,
                            execution_count=task_data.get('execution_count', 0)
                        )
                        self.tasks[task_id] = task

            # 実行ログの読み込み
            if os.path.exists(self.execution_log_storage):
                with open(self.execution_log_storage, 'r', encoding='utf-8') as f:
                    self.execution_logs = json.load(f)

        except Exception as e:
            self.logger.error(f"データ読み込みエラー: {str(e)}")

    def _save_data(self) -> None:
        """データを保存"""
        try:
            with self.lock:
                # タスクの保存
                tasks_data = {}
                for task_id, task in self.tasks.items():
                    task_dict = asdict(task)
                    if task.created_at:
                        task_dict['created_at'] = task.created_at.isoformat()
                    if task.last_executed:
                        task_dict['last_executed'] = task.last_executed.isoformat()
                    tasks_data[task_id] = task_dict

                with open(self.tasks_storage, 'w', encoding='utf-8') as f:
                    json.dump(tasks_data, f, ensure_ascii=False, indent=2)

                # 実行ログの保存（最新100件のみ保持）
                with open(self.execution_log_storage, 'w', encoding='utf-8') as f:
                    json.dump(self.execution_logs[-100:], f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"データ保存エラー: {str(e)}")

    def _setup_scheduler(self) -> None:
        """スケジューラの設定"""
        # 既存のタスクをスケジューラに登録
        for task in self.tasks.values():
            if task.is_active:
                self._schedule_task(task)

    def _schedule_task(self, task: AutoTask) -> None:
        """タスクをスケジューラに登録"""
        try:
            # サーバーローカルタイムに変換（タスクの schedule_time は JST 前提）
            local_time_str = self._convert_jst_time_to_server_local(task.schedule_time)

            if task.schedule_pattern == 'daily':
                schedule.every().day.at(local_time_str).do(self._execute_task, task.task_id).tag(task.task_id)
                # 直近1分以内に登録された daily タスクは、初回だけ1分後に即時起動するセーフティ
                try:
                    created_delta = datetime.now(self.jst) - (task.created_at or datetime.now(self.jst))
                    if created_delta.total_seconds() < 90:
                        schedule.every(1).minutes.do(self._execute_task, task.task_id).tag(f"bootstrap_{task.task_id}")
                        self.logger.info(f"ブートストラップ起動を登録: {task.title}（1分ごと、一度実行で解除）")
                except Exception:
                    pass
            elif task.schedule_pattern == 'weekly':
                # 毎週月曜日の指定時刻に実行
                schedule.every().monday.at(local_time_str).do(self._execute_task, task.task_id).tag(task.task_id)
            elif task.schedule_pattern == 'hourly':
                schedule.every().hour.do(self._execute_task, task.task_id).tag(task.task_id)
            
            self.logger.info(f"タスクをスケジュール登録: {task.title} (JST {task.schedule_time} → Server {local_time_str})")
            
        except Exception as e:
            self.logger.error(f"タスクスケジュール登録エラー: {str(e)}")

    def _convert_jst_time_to_server_local(self, schedule_time: str) -> str:
        """JST指定の HH:MM をサーバーローカルタイムの HH:MM に変換"""
        try:
            hour, minute = [int(x) for x in schedule_time.split(":")]
        except Exception:
            # フォールバック: そのまま返す（schedule 側でエラー扱いに）
            return schedule_time

        # 今日の JST 時刻を作成
        now_jst = datetime.now(self.jst)
        jst_dt = self.jst.localize(datetime(now_jst.year, now_jst.month, now_jst.day, hour, minute, 0))

        # サーバーローカルタイムゾーン
        server_tz = datetime.now().astimezone().tzinfo
        server_dt = jst_dt.astimezone(server_tz)

        return server_dt.strftime('%H:%M')

    def start_scheduler(self) -> None:
        """スケジューラを開始"""
        # フォーク後にスレッドが消えるケースに対応
        if self.is_running and self.scheduler_thread and self.scheduler_thread.is_alive():
            return
            
        self.is_running = True
        
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # 1分間隔でチェック
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("自動実行スケジューラを開始しました")

    def stop_scheduler(self) -> None:
        """スケジューラを停止"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        self.logger.info("自動実行スケジューラを停止しました")

    def create_auto_task(
        self,
        user_id: str,
        task_type: str,
        title: str,
        description: str,
        schedule_pattern: str,
        schedule_time: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        自動実行タスクを作成
        
        Returns:
            str: 作成されたタスクID
        """
        try:
            task_id = f"task_{user_id}_{datetime.now(self.jst).strftime('%Y%m%d_%H%M%S_%f')}"
            
            task = AutoTask(
                task_id=task_id,
                user_id=user_id,
                task_type=task_type,
                title=title,
                description=description,
                schedule_pattern=schedule_pattern,
                schedule_time=schedule_time,
                parameters=parameters,
                created_at=datetime.now(self.jst)
            )
            
            with self.lock:
                self.tasks[task_id] = task
            
            # スケジューラに登録
            self._schedule_task(task)
            
            # データ保存
            self._save_data()
            
            self.logger.info(f"自動実行タスクを作成: {title}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"自動実行タスク作成エラー: {str(e)}")
            return ""

    def _execute_task(self, task_id: str) -> None:
        """タスクを実行"""
        try:
            task = self.tasks.get(task_id)
            if not task or not task.is_active:
                return
            
            self.logger.info(f"タスク実行開始: {task.title}")
            
            # タスクタイプ別の実行
            result = None
            if task.task_type == TaskType.WEATHER_DAILY.value:
                result = self._execute_weather_task(task)
            elif task.task_type == TaskType.NEWS_DAILY.value:
                result = self._execute_news_task(task)
            elif task.task_type == TaskType.KEYWORD_MONITOR.value:
                result = self._execute_keyword_monitor_task(task)
            elif task.task_type == TaskType.USAGE_REPORT.value:
                result = self._execute_usage_report_task(task)
            
            # 実行記録を更新
            task.last_executed = datetime.now(self.jst)
            task.execution_count += 1
            
            # 実行ログを記録
            self.execution_logs.append({
                'task_id': task_id,
                'executed_at': task.last_executed.isoformat(),
                'result': result,
                'success': result is not None
            })
            
            # データ保存
            self._save_data()
            
            # 初回ブートストラップの解除（該当タグをクリア）
            try:
                schedule.clear(f"bootstrap_{task_id}")
            except Exception:
                pass

            self.logger.info(f"タスク実行完了: {task.title}")
            
        except Exception as e:
            self.logger.error(f"タスク実行エラー: {str(e)}")

    def _execute_weather_task(self, task: AutoTask) -> Optional[str]:
        """天気情報配信タスクを実行"""
        try:
            if not self.notification_service:
                self.logger.error("通知サービスが利用できません")
                return None
            
            location = task.parameters.get('location', '東京')
            
            # 天気サービスが利用可能な場合
            if self.weather_service and self.weather_service.is_available:
                # 天気情報を取得
                weather = self.weather_service.get_current_weather(location)
                forecast = self.weather_service.get_weather_forecast(location)

                # メッセージを作成（テキストベース、存在しない整形関数は使わない）
                parts = ["🌤️ おはようございます！今日の天気\n"]
                if weather:
                    # WeatherInfo または dict の両対応
                    if isinstance(weather, dict):
                        w_loc = weather.get('location') or weather.get('name') or location
                        desc = weather.get('description') or weather.get('condition') or ''
                        temp = weather.get('temperature') or weather.get('temp') or weather.get('temp_c')
                        feels = weather.get('feels_like') or weather.get('feelslike_c')
                        humid = weather.get('humidity')
                        wind = weather.get('wind_speed') or (weather.get('wind_kph') / 3.6 if weather.get('wind_kph') else None)
                    else:
                        w_loc = getattr(weather, 'location', location)
                        desc = getattr(weather, 'description', '')
                        temp = getattr(weather, 'temperature', None)
                        feels = getattr(weather, 'feels_like', None)
                        humid = getattr(weather, 'humidity', None)
                        wind = getattr(weather, 'wind_speed', None)

                    parts.append(f"場所: {w_loc}")
                    if desc:
                        parts.append(f"天気: {desc}")
                    if temp is not None and feels is not None:
                        try:
                            parts.append(f"気温: {float(temp):.1f}°C  体感: {float(feels):.1f}°C")
                        except Exception:
                            parts.append(f"気温: {temp}°C")
                    elif temp is not None:
                        parts.append(f"気温: {temp}°C")
                    if humid is not None or wind is not None:
                        if humid is not None and wind is not None:
                            try:
                                parts.append(f"湿度: {int(humid)}%  風速: {float(wind):.1f}m/s")
                            except Exception:
                                parts.append(f"湿度: {humid}%")
                        elif humid is not None:
                            parts.append(f"湿度: {humid}%")
                        elif wind is not None:
                            try:
                                parts.append(f"風速: {float(wind):.1f}m/s")
                            except Exception:
                                pass
                else:
                    parts.append("現在の天気を取得できませんでした。")

                # 予報の簡易サマリ（先頭3日）
                if forecast:
                    parts.append("\n📅 今後の予報:")
                    try:
                        # WeatherForecast または dict/list の柔軟対応
                        if isinstance(forecast, dict) and 'forecasts' in forecast:
                            src = forecast['forecasts']
                        elif hasattr(forecast, 'forecasts'):
                            src = forecast.forecasts
                        else:
                            src = forecast if isinstance(forecast, list) else []

                        for d in src[:3]:
                            if isinstance(d, dict):
                                date = d.get('date') or d.get('day') or ''
                                desc = d.get('description') or d.get('condition') or ''
                                tmax = d.get('max_temp') or d.get('temperature_high')
                                tmin = d.get('min_temp') or d.get('temperature_low')
                                rain = d.get('chance_of_rain') or d.get('rain_chance')
                            else:
                                date = getattr(d, 'date', '')
                                desc = getattr(d, 'description', '')
                                tmax = getattr(d, 'max_temp', None)
                                tmin = getattr(d, 'min_temp', None)
                                rain = getattr(d, 'chance_of_rain', None)
                            parts.append(f"- {date}: {desc}  最高{tmax}° 最低{tmin}°  降水{rain}%")
                    except Exception:
                        pass

                message = "\n".join(parts)
            else:
                # 天気サービスが無効な場合のフォールバック
                self.logger.warning("天気サービスが利用できないため、簡易メッセージを送信")
                message = f"🌤️ **おはようございます！**\n\n申し訳ありませんが、現在{location}の詳細な天気情報を取得できません。\n\n🔍 「{location}の天気」と送信すると、利用可能な場合は最新の天気情報をお調べします。\n\n☀️ 良い一日をお過ごしください！"
            
            # 通知として登録（テスト互換の維持）
            notification_id = self.notification_service.add_notification(
                user_id=task.user_id,
                title="🌤️ 今日の天気情報",
                message=message,
                datetime_str=datetime.now(self.jst).strftime('%Y-%m-%d %H:%M'),
                priority='medium'
            )
            
            return f"天気情報を配信しました: {notification_id}"
            
        except Exception as e:
            self.logger.error(f"天気タスク実行エラー: {str(e)}")
            return None

    def _execute_news_task(self, task: AutoTask) -> Optional[str]:
        """ニュース配信タスクを実行"""
        try:
            if not self.search_service or not self.notification_service:
                return None
            
            keywords = task.parameters.get('keywords', ['最新ニュース'])
            
            all_news = []
            for keyword in keywords:
                news_results = self.search_service.search(keyword, result_type='news', max_results=3)
                all_news.extend(news_results)
            
            if not all_news:
                return "ニュースが見つかりませんでした"
            
            # ニュースを整形
            news_message = "📰 **今日のニュース**\n\n"
            for i, news in enumerate(all_news[:5], 1):
                news_message += f"**{i}. {news.title}**\n"
                news_message += f"📝 {news.snippet[:100]}...\n"
                news_message += f"🔗 {news.link}\n\n"
            
            # 通知として登録（テスト互換の維持）
            notification_id = self.notification_service.add_notification(
                user_id=task.user_id,
                title="📰 今日のニュース配信",
                message=news_message,
                datetime_str=datetime.now(self.jst).strftime('%Y-%m-%d %H:%M'),
                priority='medium'
            )
            
            return f"ニュースを配信しました: {notification_id}"
            
        except Exception as e:
            self.logger.error(f"ニュースタスク実行エラー: {str(e)}")
            return None

    def _execute_keyword_monitor_task(self, task: AutoTask) -> Optional[str]:
        """キーワードモニタリングタスクを実行"""
        try:
            if not self.search_service or not self.notification_service:
                return None
            
            keywords = task.parameters.get('keywords', [])
            alert_threshold = task.parameters.get('alert_threshold', 3)
            
            alerts = []
            for keyword in keywords:
                results = self.search_service.search(keyword, result_type='news', max_results=5)
                if len(results) >= alert_threshold:
                    alerts.append({
                        'keyword': keyword,
                        'count': len(results),
                        'latest': results[0] if results else None
                    })
            
            if alerts:
                alert_message = "🚨 **キーワードアラート**\n\n"
                for alert in alerts:
                    alert_message += f"🔍 **{alert['keyword']}**: {alert['count']}件の新着\n"
                    if alert['latest']:
                        alert_message += f"📰 最新: {alert['latest'].title}\n"
                        alert_message += f"🔗 {alert['latest'].link}\n\n"
                
                # 通知として登録（テスト互換の維持）
                notification_id = self.notification_service.add_notification(
                    user_id=task.user_id,
                    title="🚨 キーワードアラート",
                    message=alert_message,
                    datetime_str=datetime.now(self.jst).strftime('%Y-%m-%d %H:%M'),
                    priority='high'
                )
                
                return f"キーワードアラートを送信しました: {notification_id}"
            
            return "アラート条件に該当する結果はありませんでした"
            
        except Exception as e:
            self.logger.error(f"キーワードモニタータスク実行エラー: {str(e)}")
            return None

    def _execute_usage_report_task(self, task: AutoTask) -> Optional[str]:
        """使用状況レポートタスクを実行"""
        try:
            if not self.notification_service:
                return None
            
            # 基本的な使用統計を作成
            report_message = "📊 **週間使用レポート**\n\n"
            report_message += f"⏰ レポート作成時刻: {datetime.now(self.jst).strftime('%Y-%m-%d %H:%M')}\n"
            report_message += f"🤖 自動実行タスク数: {len([t for t in self.tasks.values() if t.is_active])}件\n"
            report_message += f"📝 実行履歴: {len(self.execution_logs)}回\n\n"
            
            # アクティブなタスクの状況
            active_tasks = [t for t in self.tasks.values() if t.is_active and t.user_id == task.user_id]
            if active_tasks:
                report_message += "🔄 **アクティブなタスク:**\n"
                for active_task in active_tasks:
                    report_message += f"• {active_task.title} ({active_task.execution_count}回実行)\n"
            
            # 通知として登録（テスト互換の維持）
            notification_id = self.notification_service.add_notification(
                user_id=task.user_id,
                title="📊 週間使用レポート",
                message=report_message,
                datetime_str=datetime.now(self.jst).strftime('%Y-%m-%d %H:%M'),
                priority='low'
            )
            
            return f"使用レポートを生成しました: {notification_id}"
            
        except Exception as e:
            self.logger.error(f"使用レポートタスク実行エラー: {str(e)}")
            return None

    def get_user_tasks(self, user_id: str) -> List[AutoTask]:
        """ユーザーのタスク一覧を取得"""
        return [task for task in self.tasks.values() if task.user_id == user_id]

    def delete_task(self, user_id: str, task_id: str) -> bool:
        """タスクを削除"""
        try:
            task = self.tasks.get(task_id)
            if not task or task.user_id != user_id:
                return False
            
            with self.lock:
                del self.tasks[task_id]
            
            # スケジューラからも削除
            schedule.clear(task_id)
            
            self._save_data()
            
            self.logger.info(f"タスクを削除: {task.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"タスク削除エラー: {str(e)}")
            return False

    def toggle_task(self, user_id: str, task_id: str) -> bool:
        """タスクの有効/無効を切り替え"""
        try:
            task = self.tasks.get(task_id)
            if not task or task.user_id != user_id:
                return False
            
            task.is_active = not task.is_active
            
            if task.is_active:
                self._schedule_task(task)
            else:
                schedule.clear(task_id)
            
            self._save_data()
            
            status = "有効" if task.is_active else "無効"
            self.logger.info(f"タスクを{status}に変更: {task.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"タスク状態変更エラー: {str(e)}")
            return False

    def format_tasks_list(self, tasks: List[AutoTask]) -> str:
        """タスク一覧を整形"""
        if not tasks:
            return "設定されている自動実行タスクはありません。"
        
        formatted_lines = ["🤖 **自動実行タスク一覧**\n"]
        
        for i, task in enumerate(tasks, 1):
            status = "✅ 有効" if task.is_active else "❌ 無効"
            formatted_lines.append(f"**{i}. {task.title}**")
            formatted_lines.append(f"   📋 {task.description}")
            formatted_lines.append(f"   ⏰ スケジュール: {task.schedule_pattern} {task.schedule_time}")
            formatted_lines.append(f"   📊 実行回数: {task.execution_count}回")
            formatted_lines.append(f"   🔄 状態: {status}")
            if task.last_executed:
                formatted_lines.append(f"   📅 最終実行: {task.last_executed.strftime('%Y-%m-%d %H:%M')}")
            formatted_lines.append(f"   🆔 ID: {task.task_id}\n")
        
        return "\n".join(formatted_lines) 