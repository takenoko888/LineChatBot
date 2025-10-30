"""
Base notification service implementation
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import logging
import os
import pytz
from dataclasses import dataclass, asdict
from threading import Lock
from ..gemini_service import GeminiService
from linebot.models import TextSendMessage, QuickReply, QuickReplyButton, MessageAction
from datetime import time
from .notification_model import Notification
from ..persistent_storage_service import PersistentStorageService

class NotificationServiceBase:
    """通知サービス基底クラス"""

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
        self.logger = logging.getLogger(__name__)

        # ストレージパスの設定（Koyeb環境を考慮した複数候補）
        if storage_path:
            potential_paths = [storage_path]
        else:
            potential_paths = [
                os.getenv('NOTIFICATION_STORAGE_PATH', '/workspace/data/notifications.json'),
                '/tmp/notifications.json',  # Koyebでも利用可能な一時ディレクトリ
                '/var/tmp/notifications.json',  # 代替一時ディレクトリ
                './notifications.json'  # 現在のディレクトリ
            ]

        self.storage_path = None
        self.backup_paths = []
        
        # 利用可能なストレージパスを見つける
        for path in potential_paths:
            try:
                abs_path = os.path.abspath(path)
                storage_dir = os.path.dirname(abs_path)
                
                # ディレクトリを作成し、書き込み権限を確認
                os.makedirs(storage_dir, mode=0o777, exist_ok=True)
                
                # 書き込みテスト
                test_file = os.path.join(storage_dir, '.write_test')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                
                if self.storage_path is None:
                    self.storage_path = abs_path
                    self.logger.info(f"メインストレージパス: {abs_path}")
                else:
                    self.backup_paths.append(abs_path)
                    self.logger.debug(f"バックアップストレージパス: {abs_path}")
                    
            except Exception as e:
                self.logger.warning(f"ストレージパス {path} は利用できません: {str(e)}")
                continue

        if self.storage_path is None:
            raise RuntimeError("利用可能なストレージパスが見つかりません")

        self.notifications: Dict[str, Dict[str, Notification]] = {}
        self.lock = Lock()
        self.line_bot_api = line_bot_api

        # Gemini AI サービスの初期化
        self.gemini_service = gemini_service or GeminiService()
        
        # 永続化サービスの初期化
        try:
            self.persistent_storage = PersistentStorageService()
            self.logger.info("永続化ストレージサービスを初期化しました")
        except Exception as e:
            self.logger.warning(f"永続化ストレージの初期化に失敗: {str(e)}")
            self.persistent_storage = None

        # 初期ファイルの作成（存在しない場合）
        try:
            if not os.path.exists(self.storage_path):
                self._create_initial_file(self.storage_path)
            
            # バックアップパスも初期化
            for backup_path in self.backup_paths:
                if not os.path.exists(backup_path):
                    self._create_initial_file(backup_path)

            self.logger.info(f"通知データストレージを初期化: メイン={self.storage_path}, バックアップ={len(self.backup_paths)}個")
        except Exception as e:
            self.logger.error(f"ストレージの初期化に失敗: {str(e)}")
            raise

        # 通知データの読み込みと初期化
        try:
            self._load_notifications()
            # 起動時に永続化ストレージからも復元を試行
            self._restore_from_persistent_storage()
        except Exception as e:
            self.logger.error(f"通知データの初期化に失敗: {str(e)}")
            self.notifications = {}

    def _create_initial_file(self, file_path: str) -> None:
        """初期ファイルを作成"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            os.chmod(file_path, 0o666)  # 読み書き権限を設定
            self.logger.debug(f"初期ファイルを作成: {file_path}")
        except Exception as e:
            self.logger.warning(f"初期ファイル作成に失敗: {file_path} - {str(e)}")
            raise

    def _calculate_next_notification_time(self, current_time: datetime, repeat_type: str) -> datetime:
        """
        次回の通知時刻を計算

        Args:
            current_time (datetime): 現在の通知時刻
            repeat_type (str): 繰り返しタイプ

        Returns:
            datetime: 次回の通知時刻
        """
        if repeat_type == 'daily':
            return current_time + timedelta(days=1)
        elif repeat_type == 'weekly':
            return current_time + timedelta(weeks=1)
        elif repeat_type == 'monthly':
            # 月の加算は少し複雑なので、日付を直接操作
            next_month = current_time.replace(day=1) + timedelta(days=32)
            return next_month.replace(day=min(current_time.day, 28))
        else:
            return current_time

    def _verify_saved_data(self) -> None:
        """保存したデータを検証"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                total_saved = sum(len(notifications) for notifications in saved_data.values())
                total_memory = sum(len(notifications) for notifications in self.notifications.values())

                if total_saved != total_memory:
                    self.logger.error(f"データ不整合: メモリ上 {total_memory} 件, ファイル上 {total_saved} 件")
                    raise ValueError("保存データの検証に失敗しました")

                self.logger.debug(f"データ検証成功: {total_saved} 件の通知を確認")
        except Exception as e:
            self.logger.error(f"データ検証エラー: {str(e)}")
            raise

    def _load_notifications(self) -> None:
        """保存された通知データを読み込む（複数のストレージパスから試行）"""
        loaded_data = None
        loaded_from = None
        
        # メインパスから読み込みを試行
        for path in [self.storage_path] + self.backup_paths:
            if not os.path.exists(path):
                continue
                
            try:
                self.logger.debug(f"通知データを読み込み中: {path}")
                
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # データが正常に読み込めた場合
                loaded_data = data
                loaded_from = path
                break
                
            except json.JSONDecodeError:
                self.logger.warning(f"通知データファイルが破損しています: {path}")
                # 破損したファイルをバックアップして続行
                try:
                    backup_path = f"{path}.corrupted_{int(datetime.now().timestamp())}"
                    os.rename(path, backup_path)
                    self.logger.info(f"破損したファイルをバックアップ: {backup_path}")
                except Exception:
                    pass
                continue
                
            except Exception as e:
                self.logger.warning(f"通知データの読み込みエラー: {path} - {str(e)}")
                continue

        # データが見つからない場合は空で初期化
        if loaded_data is None:
            self.logger.warning("有効な通知データファイルが見つかりません。空で初期化します。")
            loaded_data = {}
            loaded_from = "新規作成"

        # データの検証と変換
        loaded_count = 0
        validated_data = {}

        for user_id, notifications in loaded_data.items():
            if not isinstance(notifications, dict):
                self.logger.warning(f"無効な通知データ形式（ユーザーID: {user_id}）")
                continue

            validated_notifications = {}
            for nid, ndata in notifications.items():
                try:
                    validated_notifications[nid] = Notification(**ndata)
                    loaded_count += 1
                except (TypeError, ValueError) as e:
                    self.logger.warning(f"無効な通知データ（ID: {nid}）: {str(e)}")
                    continue

            if validated_notifications:
                validated_data[user_id] = validated_notifications

        self.notifications = validated_data
        self.logger.info(f"通知データを読み込みました: {len(self.notifications)} ユーザー, {loaded_count} 件の通知 (ソース: {loaded_from})")

        # 読み込んだデータをすべてのストレージパスに同期（必要時のみ）
        # - バックアップパスから読み込んだ場合のみ同期（メインから読み込んだ場合は不要）
        # - さらに、現在ロック保持中であれば同期はスキップ（競合回避）
        try:
            is_locked = hasattr(self.lock, "locked") and self.lock.locked()
        except Exception:
            is_locked = False

        if (
            loaded_data
            and loaded_from != "新規作成"
            and loaded_from != self.storage_path
            and not is_locked
        ):
            self._sync_to_all_storages()

    def _save_notifications(self, lock_acquired: bool = False) -> None:
        """
        通知データを保存（すべてのストレージパスに保存）

        Args:
            lock_acquired (bool): 呼び出し元で既にロックを取得している場合はTrue
        """
        if not lock_acquired:
            try:
                if not self.lock.acquire(timeout=30):
                    self.logger.error("通知データの保存をロックできません。処理を中断します。")
                    return # ロック取得失敗時はエラーにせず中断
            except Exception as e:
                self.logger.error(f"ロック取得エラー: {str(e)}")
                return

        try:
            self.logger.debug(f"通知データを保存中: メイン={self.storage_path}, バックアップ={len(self.backup_paths)}個")

            # 保存データの準備とバリデーション
            data = self._prepare_save_data()
            
            # 複数のストレージパスに保存
            save_success = False
            save_results = []
            
            for storage_path in [self.storage_path] + self.backup_paths:
                try:
                    self._save_to_single_path(data, storage_path)
                    save_results.append(f"✓ {storage_path}")
                    save_success = True
                except Exception as e:
                    save_results.append(f"✗ {storage_path}: {str(e)}")
                    self.logger.warning(f"ストレージパス {storage_path} への保存失敗: {str(e)}")

            # 結果をログに記録
            self.logger.info(f"データ保存結果: {', '.join(save_results)}")
            
            if not save_success:
                raise RuntimeError("すべてのストレージパスへの保存に失敗しました")
            
            # 永続化ストレージにもバックアップ
            self._backup_to_persistent_storage()

        except Exception as e:
            self.logger.error(f"通知データの保存エラー: {str(e)}")
        finally:
            if not lock_acquired:
                try:
                    self.lock.release()
                except Exception as e:
                    self.logger.error(f"ロック解放エラー: {str(e)}")

    def _prepare_save_data(self) -> dict:
        """保存データを準備"""
        data = {}
        total_notifications = 0

        for user_id, notifications in self.notifications.items():
            valid_notifications = {}
            for nid, n in notifications.items():
                try:
                    notification_dict = n.to_dict()
                    # 基本的なバリデーション
                    if all(key in notification_dict for key in ['id', 'user_id', 'datetime']):
                        valid_notifications[nid] = notification_dict
                        total_notifications += 1
                    else:
                        self.logger.warning(f"無効な通知データを除外: {nid}")
                except Exception as e:
                    self.logger.warning(f"通知データの変換エラー: {nid} - {str(e)}")
                    continue

            if valid_notifications:
                data[user_id] = valid_notifications

        self.logger.debug(f"保存する通知数: {total_notifications}")
        return data

    def _save_to_single_path(self, data: dict, storage_path: str) -> None:
        """単一のパスにデータを保存"""
        # 現在のファイルをバックアップ
        if os.path.exists(storage_path):
            backup_path = f"{storage_path}.bak"
            try:
                os.replace(storage_path, backup_path)
                self.logger.debug(f"既存データをバックアップ: {backup_path}")
            except Exception as e:
                self.logger.warning(f"バックアップ作成エラー: {str(e)}")

        # 一時ファイルに保存
        temp_path = f"{storage_path}.tmp"
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 一時ファイルを本番ファイルに移動
            os.replace(temp_path, storage_path)
            os.chmod(storage_path, 0o666)  # 読み書き権限を設定

            self.logger.debug(f"データ保存完了: {storage_path}")

        except Exception as e:
            # バックアップから復元を試みる
            backup_path = f"{storage_path}.bak"
            if os.path.exists(backup_path):
                try:
                    os.replace(backup_path, storage_path)
                    self.logger.info(f"バックアップから復元: {storage_path}")
                except Exception as restore_error:
                    self.logger.error(f"バックアップ復元エラー: {str(restore_error)}")
            raise

    def _sync_to_all_storages(self) -> None:
        """現在のメモリ上のデータをすべてのストレージに同期"""
        try:
            self.logger.debug("全ストレージパスにデータを同期中...")
            # すでにロック保持中なら lock_acquired=True で保存（再ロック回避）
            if hasattr(self.lock, "locked") and self.lock.locked():
                self._save_notifications(lock_acquired=True)
            else:
                self._save_notifications()
        except Exception as e:
            self.logger.error(f"データ同期エラー: {str(e)}")
    
    def _restore_from_persistent_storage(self) -> None:
        """永続化ストレージからデータを復元"""
        if not self.persistent_storage:
            return
        
        try:
            # 永続化ストレージからデータを読み込み
            persistent_data = self.persistent_storage.load_data()
            
            if persistent_data is None:
                self.logger.debug("永続化ストレージにデータが存在しません")
                return
            
            # 現在のローカルデータと比較
            current_notification_count = sum(len(notifications) for notifications in self.notifications.values())
            persistent_notification_count = sum(len(notifications) for notifications in persistent_data.values())
            
            # 永続化ストレージの方がデータが多い場合は復元
            if persistent_notification_count > current_notification_count:
                self.logger.info(f"永続化ストレージからより多くのデータを発見: 現在{current_notification_count}件 -> 復元後{persistent_notification_count}件")
                
                # データを復元
                validated_data = {}
                for user_id, notifications in persistent_data.items():
                    if not isinstance(notifications, dict):
                        continue
                    
                    validated_notifications = {}
                    for nid, ndata in notifications.items():
                        try:
                            validated_notifications[nid] = Notification(**ndata)
                        except (TypeError, ValueError) as e:
                            self.logger.warning(f"永続化データの復元でエラー（ID: {nid}）: {str(e)}")
                            continue
                    
                    if validated_notifications:
                        validated_data[user_id] = validated_notifications
                
                # メモリ上のデータを更新
                self.notifications = validated_data
                
                # ローカルファイルにも保存
                self._save_notifications()
                
                self.logger.info("永続化ストレージからのデータ復元が完了")
            else:
                self.logger.debug("ローカルデータが最新のため、復元をスキップ")
                
        except Exception as e:
            self.logger.error(f"永続化ストレージからの復元エラー: {str(e)}")
    
    def _backup_to_persistent_storage(self) -> None:
        """永続化ストレージにデータをバックアップ"""
        if not self.persistent_storage:
            return
        
        try:
            # 現在のデータを永続化ストレージ用に変換
            backup_data = {}
            for user_id, notifications in self.notifications.items():
                user_data = {}
                for nid, notification in notifications.items():
                    try:
                        user_data[nid] = notification.to_dict()
                    except Exception as e:
                        self.logger.warning(f"通知データの変換エラー（ID: {nid}）: {str(e)}")
                        continue
                
                if user_data:
                    backup_data[user_id] = user_data
            
            # 永続化ストレージに保存
            if self.persistent_storage.save_data(backup_data):
                self.logger.debug("永続化ストレージへのバックアップが完了")
            else:
                self.logger.warning("永続化ストレージへのバックアップに失敗")
                
        except Exception as e:
            self.logger.error(f"永続化ストレージへのバックアップエラー: {str(e)}")

    def get_notifications(self, user_id: str) -> List[Notification]:
        """指定されたユーザーの全通知を取得"""
        try:
            if user_id not in self.notifications:
                return []
            return list(self.notifications[user_id].values())
        except Exception as e:
            self.logger.error(f"通知取得エラー: {str(e)}")
            return []

    def format_notification_list(
        self,
        notifications: List[Notification],
        format_type: str = 'detailed'
    ) -> str:
        """
        通知リストを整形して文字列として返す
        クイックリプライはline_bot_baseで処理される
        """
        if not notifications:
            return "📝 通知は設定されていません"

        # 通知を時刻順にソート
        sorted_notifications = sorted(
            notifications, 
            key=lambda x: datetime.strptime(x.datetime, '%Y-%m-%d %H:%M')
        )

        # 現在時刻を取得（timezone-naiveに統一）
        now = datetime.now()  # timezone-naiveで統一
        
        if format_type == 'simple':
            result = ["📋 通知一覧:"]
            for i, notif in enumerate(sorted_notifications, 1):
                try:
                    time = datetime.strptime(notif.datetime, '%Y-%m-%d %H:%M')
                    time_diff = (time - now).total_seconds()
                    
                    # 過去/未来の表示
                    if time_diff < 0:
                        status = "✅ 完了"
                    elif time_diff < 3600:  # 1時間以内
                        status = "🔥 まもなく"
                    else:
                        status = "⏳ 予定"
                    
                    result.append(f"{i}. {status} {time.strftime('%m/%d %H:%M')} {notif.title}")
                except ValueError:
                    result.append(f"{i}. ❓ 時刻不明 {notif.title}")
        else:
            # 詳細表示
            result = ["📋 現在の通知一覧:"]
            
            # 未来の通知と過去の通知を分類
            future_notifications = []
            past_notifications = []
            
            for notif in sorted_notifications:
                try:
                    time = datetime.strptime(notif.datetime, '%Y-%m-%d %H:%M')
                    if time >= now:  # timezone-naive同士の比較
                        future_notifications.append(notif)
                    else:
                        past_notifications.append(notif)
                except ValueError:
                    # 時刻解析エラーの場合は未来として扱う
                    future_notifications.append(notif)
            
            # 未来の通知を表示
            if future_notifications:
                result.append("\n🔔 **予定されている通知:**")
                for i, notif in enumerate(future_notifications, 1):
                    self._format_single_notification(result, notif, i, now, "future")
            
            # 過去の通知を表示（最大5件）
            if past_notifications:
                result.append(f"\n✅ **最近完了した通知** (最新{min(len(past_notifications), 5)}件):")
                recent_past = past_notifications[-5:]  # 最新5件
                for i, notif in enumerate(recent_past, 1):
                    self._format_single_notification(result, notif, i, now, "past")
            
            # 統計情報を追加
            total_count = len(notifications)
            future_count = len(future_notifications)
            past_count = len(past_notifications)
            
            result.append(f"\n📊 **統計:**")
            result.append(f"・合計: {total_count}件")
            result.append(f"・予定: {future_count}件")
            result.append(f"・完了: {past_count}件")

        # メッセージテキストを返す（クイックリプライはline_bot_baseで処理）
        return "\n".join(result)

    def _format_single_notification(self, result: list, notif: Notification, index: int, now: datetime, time_type: str):
        """
        単一の通知をフォーマットして結果リストに追加
        
        Args:
            result (list): 結果を格納するリスト
            notif (Notification): 通知オブジェクト
            index (int): インデックス番号
            now (datetime): 現在時刻（timezone-naive）
            time_type (str): 'future' または 'past'
        """
        try:
            # 優先度に応じたアイコン
            priority_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
            priority_icon = priority_icons.get(notif.priority, '⚪')

            # 繰り返し設定のテキスト
            repeat_texts = {
                'daily': '毎日',
                'weekly': '毎週',
                'monthly': '毎月',
                'none': '一回のみ'
            }
            repeat_text = repeat_texts.get(notif.repeat, '不明')
            
            # 通知時刻
            time = datetime.strptime(notif.datetime, '%Y-%m-%d %H:%M')
            time_str = time.strftime('%m/%d %H:%M')
            
            # 時間差分の計算と表示（timezone-naive同士の比較）
            time_diff = (time - now).total_seconds()
            
            if time_type == "future":
                if time_diff < 3600:  # 1時間以内
                    time_info = f"🔥 あと{int(time_diff/60)}分"
                elif time_diff < 86400:  # 24時間以内
                    time_info = f"⏰ あと{int(time_diff/3600)}時間"
                else:
                    days = int(time_diff / 86400)
                    time_info = f"📅 あと{days}日"
            else:
                abs_diff = abs(time_diff)
                if abs_diff < 3600:  # 1時間以内
                    time_info = f"✅ {int(abs_diff/60)}分前"
                elif abs_diff < 86400:  # 24時間以内
                    time_info = f"✅ {int(abs_diff/3600)}時間前"
                else:
                    days = int(abs_diff / 86400)
                    time_info = f"✅ {days}日前"

            # 通知状態のアイコン
            status_icon = "✅" if notif.acknowledged else ("🔥" if time_type == "future" and time_diff < 3600 else "⏳")

            # テンプレートの場合はアイコンを追加
            template_info = " 📋" if notif.is_template else ""

            # メイン情報
            result.append(f"  {index}. {status_icon} {priority_icon} **{notif.title}**{template_info}")
            result.append(f"     ⏰ {time_str} ({repeat_text}) - {time_info}")
            result.append(f"     📝 {notif.message[:50]}{'...' if len(notif.message) > 50 else ''}")
            
            # IDを表示（削除用）
            result.append(f"     🆔 ID: `{notif.id}`")

        except Exception as e:
            # エラー時のフォールバック表示
            result.append(f"  {index}. ❓ **{notif.title}** (表示エラー)")
            result.append(f"     📝 {notif.message[:50]}{'...' if len(notif.message) > 50 else ''}")
            result.append(f"     🆔 ID: `{notif.id}`")

    def format_notifications(self, notifications: List[Notification]) -> str:
        """このメソッドは非推奨です。代わりにformat_notification_listを使用してください"""
        return self.format_notification_list(notifications, format_type='detailed')

    def parse_smart_time(self, time_expression: str) -> Union[datetime, None]:
        """
        スマートな時間表現を解析して日時に変換

        Args:
            time_expression (str): 時間表現（例: "明日の朝", "来週の水曜日", "明日の15時"）

        Returns:
            Union[datetime, None]: 解析された日時、失敗時はNone
        """
        try:
            # 現在の日時を取得（JST）
            jst = pytz.timezone('Asia/Tokyo')
            now = datetime.now(jst)
            base_date = now.date()

            # 日付に関する表現を解析
            if "明日" in time_expression:
                base_date += timedelta(days=1)
            elif "明後日" in time_expression:
                base_date += timedelta(days=2)
            elif "来週" in time_expression:
                base_date += timedelta(weeks=1)

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
                    break

            # 時刻の解析
            hour = None
            minute = 0

            # "朝" "昼" "夜"などの時間帯
            if "朝" in time_expression:
                hour = 8
            elif "昼" in time_expression or "午後" in time_expression:
                hour = 14
            elif "夕" in time_expression or "夕方" in time_expression:
                hour = 17
            elif "夜" in time_expression:
                hour = 20

            # 数字での時刻指定
            import re
            time_match = re.search(r'(\d{1,2})[:時](\d{1,2})?', time_expression)
            if time_match:
                hour = int(time_match.group(1))
                if time_match.group(2):
                    minute = int(time_match.group(2))

                # 12時間制の場合、午後の判定
                if hour <= 12 and ("午後" in time_expression or "pm" in time_expression.lower()):
                    hour = (hour % 12) + 12

            # 時刻が指定されていない場合はデフォルト値を設定
            if hour is None:
                hour = now.hour
                minute = now.minute

            # 日時オブジェクトを作成
            result = datetime.combine(base_date, time(hour, minute))
            result = jst.localize(result)

            # 過去の時刻の場合は翌日に設定
            if result <= now:
                result += timedelta(days=1)

            return result

        except Exception as e:
            self.logger.error(f"時間解析エラー: {str(e)}")
            return None