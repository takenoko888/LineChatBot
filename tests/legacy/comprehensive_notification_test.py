#!/usr/bin/env python3
"""
通知機能と通知削除機能の包括的テストスイート
通知機能の様々な条件とエッジケースをテストし、動作の問題を特定します
"""
import sys
import os
import logging
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pytz

# ログ設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# モック用のダミーAPIキー
MOCK_GEMINI_API_KEY = "mock_gemini_api_key_for_testing"

def setup_mock_environment():
    """テスト用のモック環境変数を設定"""
    if not os.getenv('GEMINI_API_KEY'):
        os.environ['GEMINI_API_KEY'] = MOCK_GEMINI_API_KEY
        logger.info("🔧 モック用GEMINI_API_KEY設定")

class NotificationTestSuite:
    """通知機能の包括的テストスイート"""
    
    def __init__(self):
        self.test_temp_dir = None
        self.notification_service = None
        self.gemini_service = None
        self.message_handler = None
        self.test_results = []
        
    def setup_test_environment(self):
        """テスト環境のセットアップ"""
        try:
            # 一時ディレクトリの作成
            self.test_temp_dir = tempfile.mkdtemp(prefix="notification_test_")
            logger.info(f"テスト用一時ディレクトリ作成: {self.test_temp_dir}")
            
            # モック環境の設定
            setup_mock_environment()
            
            # 依存関係のインポート
            from services.notification_service import NotificationService
            from services.gemini_service import GeminiService
            from handlers.message_handler import MessageHandler
            
            # Gemini AIをモック化
            with patch('google.generativeai.configure'), \
                 patch('google.generativeai.GenerativeModel') as mock_model:
                
                # モックレスポンスを設定
                mock_response = Mock()
                mock_response.text = '{"datetime": "2024-05-24 07:00", "title": "起床", "message": "毎日7時に起きる", "priority": "medium", "repeat": "daily"}'
                mock_model.return_value.generate_content.return_value = mock_response
                
                # サービスの初期化
                self.gemini_service = GeminiService(MOCK_GEMINI_API_KEY)
                
                # 通知データファイルのパスを一時ディレクトリに設定
                notifications_file = os.path.join(self.test_temp_dir, "test_notifications.json")
                
                self.notification_service = NotificationService(
                    storage_path=notifications_file,
                    gemini_service=self.gemini_service,
                    line_bot_api=None  # テスト用
                )
                
                self.message_handler = MessageHandler()
                
                logger.info("✅ テスト環境セットアップ完了")
                return True
                
        except Exception as e:
            logger.error(f"❌ テスト環境セットアップエラー: {str(e)}")
            return False
    
    def cleanup_test_environment(self):
        """テスト環境のクリーンアップ"""
        if self.test_temp_dir and os.path.exists(self.test_temp_dir):
            shutil.rmtree(self.test_temp_dir)
            logger.info(f"テスト用一時ディレクトリ削除: {self.test_temp_dir}")
    
    def log_test_result(self, test_name, success, message="", details=None):
        """テスト結果をログに記録"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        logger.info(f"{status} {test_name}: {message}")
        if details:
            logger.debug(f"詳細: {details}")
    
    def test_notification_creation(self):
        """通知作成のテスト"""
        logger.info("=== 通知作成テスト開始 ===")
        
        test_user_id = "test_user_001"
        
        # テスト1: 基本的な通知作成
        try:
            notification_id = self.notification_service.add_notification(
                user_id=test_user_id,
                title="テスト通知",
                message="テストメッセージ",
                datetime_str="2024-12-31 23:59",
                priority="high",
                repeat="none"
            )
            
            success = notification_id is not None
            self.log_test_result(
                "基本的な通知作成",
                success,
                f"通知ID: {notification_id}" if success else "通知作成に失敗"
            )
            
        except Exception as e:
            self.log_test_result("基本的な通知作成", False, f"エラー: {str(e)}")
        
        # テスト2: 繰り返し通知の作成
        try:
            notification_id = self.notification_service.add_notification(
                user_id=test_user_id,
                title="毎日の通知",
                message="毎日実行されるタスク",
                datetime_str="2024-12-25 09:00",
                priority="medium",
                repeat="daily"
            )
            
            success = notification_id is not None
            self.log_test_result(
                "繰り返し通知作成",
                success,
                f"通知ID: {notification_id}" if success else "繰り返し通知作成に失敗"
            )
            
        except Exception as e:
            self.log_test_result("繰り返し通知作成", False, f"エラー: {str(e)}")
        
        # テスト3: 不正な日時フォーマットでの通知作成
        try:
            notification_id = self.notification_service.add_notification(
                user_id=test_user_id,
                title="不正フォーマット",
                message="不正な日時フォーマットテスト",
                datetime_str="invalid_datetime",
                priority="low",
                repeat="none"
            )
            
            # 不正フォーマットの場合はNoneが返されるべき
            success = notification_id is None
            self.log_test_result(
                "不正日時フォーマット処理",
                success,
                "不正フォーマットが正しく処理された" if success else "不正フォーマットが受け入れられた"
            )
            
        except Exception as e:
            self.log_test_result("不正日時フォーマット処理", True, f"例外で正しく処理: {str(e)}")
        
        # テスト4: 自然言語からの通知作成
        try:
            with patch.object(self.gemini_service, 'parse_notification_request') as mock_parse:
                mock_parse.return_value = {
                    "datetime": "2024-12-25 10:00",
                    "title": "朝のミーティング",
                    "message": "チームミーティングに参加",
                    "priority": "high",
                    "repeat": "none"
                }
                
                success, message = self.notification_service.add_notification_from_text(
                    test_user_id, "明日の10時にチームミーティング"
                )
                
                self.log_test_result(
                    "自然言語通知作成",
                    success,
                    message
                )
                
        except Exception as e:
            self.log_test_result("自然言語通知作成", False, f"エラー: {str(e)}")
    
    def test_notification_retrieval(self):
        """通知取得のテスト"""
        logger.info("=== 通知取得テスト開始 ===")
        
        test_user_id = "test_user_002"
        
        # 事前にテスト用通知を作成
        notification_ids = []
        for i in range(3):
            notification_id = self.notification_service.add_notification(
                user_id=test_user_id,
                title=f"テスト通知{i+1}",
                message=f"テストメッセージ{i+1}",
                datetime_str=f"2024-12-{25+i} 10:0{i}",
                priority="medium",
                repeat="none"
            )
            if notification_id:
                notification_ids.append(notification_id)
        
        # テスト1: 全通知の取得
        try:
            notifications = self.notification_service.get_notifications(test_user_id)
            success = len(notifications) == len(notification_ids)
            self.log_test_result(
                "全通知取得",
                success,
                f"取得数: {len(notifications)}, 期待数: {len(notification_ids)}"
            )
            
        except Exception as e:
            self.log_test_result("全通知取得", False, f"エラー: {str(e)}")
        
        # テスト2: 通知リストのフォーマット
        try:
            notifications = self.notification_service.get_notifications(test_user_id)
            formatted = self.notification_service.format_notification_list(notifications)
            success = isinstance(formatted, str) and len(formatted) > 0
            self.log_test_result(
                "通知リストフォーマット",
                success,
                f"フォーマット済み文字数: {len(formatted)}"
            )
            
        except Exception as e:
            self.log_test_result("通知リストフォーマット", False, f"エラー: {str(e)}")
        
        # テスト3: 存在しないユーザーの通知取得
        try:
            notifications = self.notification_service.get_notifications("non_existent_user")
            success = len(notifications) == 0
            self.log_test_result(
                "存在しないユーザー通知取得",
                success,
                f"取得数: {len(notifications)} (期待: 0)"
            )
            
        except Exception as e:
            self.log_test_result("存在しないユーザー通知取得", False, f"エラー: {str(e)}")
    
    def test_notification_deletion(self):
        """通知削除のテスト"""
        logger.info("=== 通知削除テスト開始 ===")
        
        test_user_id = "test_user_003"
        
        # 事前にテスト用通知を作成
        notification_id = self.notification_service.add_notification(
            user_id=test_user_id,
            title="削除テスト通知",
            message="削除テスト用のメッセージ",
            datetime_str="2024-12-30 15:00",
            priority="medium",
            repeat="none"
        )
        
        if not notification_id:
            self.log_test_result("削除テスト用通知作成", False, "事前通知作成に失敗")
            return
        
        # テスト1: 正常な通知削除
        try:
            # 削除前の通知数を確認
            notifications_before = self.notification_service.get_notifications(test_user_id)
            count_before = len(notifications_before)
            
            # 通知を削除
            success = self.notification_service.delete_notification(test_user_id, notification_id)
            
            # 削除後の通知数を確認
            notifications_after = self.notification_service.get_notifications(test_user_id)
            count_after = len(notifications_after)
            
            deletion_success = success and (count_after == count_before - 1)
            self.log_test_result(
                "正常な通知削除",
                deletion_success,
                f"削除成功: {success}, 通知数変化: {count_before} -> {count_after}"
            )
            
        except Exception as e:
            self.log_test_result("正常な通知削除", False, f"エラー: {str(e)}")
        
        # テスト2: 存在しない通知の削除
        try:
            success = self.notification_service.delete_notification(test_user_id, "non_existent_id")
            expected_result = False  # 存在しない通知の削除は失敗すべき
            test_success = success == expected_result
            self.log_test_result(
                "存在しない通知削除",
                test_success,
                f"削除結果: {success} (期待: {expected_result})"
            )
            
        except Exception as e:
            self.log_test_result("存在しない通知削除", False, f"エラー: {str(e)}")
        
        # テスト3: 存在しないユーザーの通知削除
        try:
            success = self.notification_service.delete_notification("non_existent_user", notification_id)
            expected_result = False  # 存在しないユーザーの通知削除は失敗すべき
            test_success = success == expected_result
            self.log_test_result(
                "存在しないユーザー通知削除",
                test_success,
                f"削除結果: {success} (期待: {expected_result})"
            )
            
        except Exception as e:
            self.log_test_result("存在しないユーザー通知削除", False, f"エラー: {str(e)}")
    
    def test_all_notifications_deletion(self):
        """全通知削除のテスト"""
        logger.info("=== 全通知削除テスト開始 ===")
        
        test_user_id = "test_user_004"
        
        # 事前に複数のテスト用通知を作成
        notification_ids = []
        for i in range(5):
            notification_id = self.notification_service.add_notification(
                user_id=test_user_id,
                title=f"全削除テスト通知{i+1}",
                message=f"全削除テスト用のメッセージ{i+1}",
                datetime_str=f"2024-12-{20+i} 1{i}:00",
                priority="medium",
                repeat="none"
            )
            if notification_id:
                notification_ids.append(notification_id)
        
        # テスト1: 全通知削除
        try:
            # 削除前の通知数を確認
            notifications_before = self.notification_service.get_notifications(test_user_id)
            count_before = len(notifications_before)
            
            # 全通知を削除
            deleted_count = self.notification_service.delete_all_notifications(test_user_id)
            
            # 削除後の通知数を確認
            notifications_after = self.notification_service.get_notifications(test_user_id)
            count_after = len(notifications_after)
            
            success = (deleted_count == count_before) and (count_after == 0)
            self.log_test_result(
                "全通知削除",
                success,
                f"削除数: {deleted_count}, 削除前: {count_before}, 削除後: {count_after}"
            )
            
        except Exception as e:
            self.log_test_result("全通知削除", False, f"エラー: {str(e)}")
        
        # テスト2: 空のユーザーの全通知削除
        try:
            deleted_count = self.notification_service.delete_all_notifications("empty_user")
            success = deleted_count == 0
            self.log_test_result(
                "空ユーザー全通知削除",
                success,
                f"削除数: {deleted_count} (期待: 0)"
            )
            
        except Exception as e:
            self.log_test_result("空ユーザー全通知削除", False, f"エラー: {str(e)}")
    
    def test_notification_time_handling(self):
        """通知時刻処理のテスト"""
        logger.info("=== 通知時刻処理テスト開始 ===")
        
        test_user_id = "test_user_005"
        
        # 様々な時刻フォーマットでのテスト
        time_formats = [
            ("2024-12-25 09:00", "標準フォーマット"),
            ("2024/12/25 09:00", "スラッシュ区切り"),
            ("2024-12-25T09:00:00", "ISO形式"),
        ]
        
        for datetime_str, format_name in time_formats:
            try:
                notification_id = self.notification_service.add_notification(
                    user_id=test_user_id,
                    title=f"時刻テスト ({format_name})",
                    message=f"時刻フォーマットテスト: {datetime_str}",
                    datetime_str=datetime_str,
                    priority="medium",
                    repeat="none"
                )
                
                success = notification_id is not None
                self.log_test_result(
                    f"時刻フォーマット処理 ({format_name})",
                    success,
                    f"通知ID: {notification_id}" if success else "時刻解析に失敗"
                )
                
            except Exception as e:
                self.log_test_result(f"時刻フォーマット処理 ({format_name})", False, f"エラー: {str(e)}")
    
    def test_notification_sending_logic(self):
        """通知送信ロジックのテスト"""
        logger.info("=== 通知送信ロジックテスト開始 ===")
        
        test_user_id = "test_user_006"
        
        # モックのLINE Bot APIを作成
        mock_line_api = Mock()
        self.notification_service.line_bot_api = mock_line_api
        
        # 現在時刻に近い通知を作成
        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.now(jst)
        future_time = now + timedelta(minutes=1)
        past_time = now - timedelta(minutes=1)
        
        # テスト1: 将来の通知（送信されないべき）
        try:
            notification_id = self.notification_service.add_notification(
                user_id=test_user_id,
                title="将来の通知",
                message="将来時刻のテスト",
                datetime_str=future_time.strftime("%Y-%m-%d %H:%M"),
                priority="medium",
                repeat="none"
            )
            
            # 通知チェックを実行
            self.notification_service.check_and_send_notifications()
            
            # LINE APIが呼ばれていないことを確認
            api_called = mock_line_api.push_message.called
            success = not api_called  # 将来の通知は送信されないべき
            self.log_test_result(
                "将来通知の送信抑制",
                success,
                f"API呼び出し: {api_called} (期待: False)"
            )
            
        except Exception as e:
            self.log_test_result("将来通知の送信抑制", False, f"エラー: {str(e)}")
        
        # テスト2: 過去の通知（送信されるべき）
        try:
            mock_line_api.reset_mock()  # モックをリセット
            
            notification_id = self.notification_service.add_notification(
                user_id=test_user_id,
                title="過去の通知",
                message="過去時刻のテスト",
                datetime_str=past_time.strftime("%Y-%m-%d %H:%M"),
                priority="medium",
                repeat="none"
            )
            
            # 通知チェックを実行
            self.notification_service.check_and_send_notifications()
            
            # LINE APIが呼ばれたことを確認
            api_called = mock_line_api.push_message.called
            success = api_called  # 過去の通知は送信されるべき
            self.log_test_result(
                "過去通知の送信実行",
                success,
                f"API呼び出し: {api_called} (期待: True)"
            )
            
        except Exception as e:
            self.log_test_result("過去通知の送信実行", False, f"エラー: {str(e)}")
    
    def test_edge_cases(self):
        """エッジケースのテスト"""
        logger.info("=== エッジケーステスト開始 ===")
        
        # テスト1: 空の文字列での通知作成
        try:
            notification_id = self.notification_service.add_notification(
                user_id="",
                title="",
                message="",
                datetime_str="",
                priority="medium",
                repeat="none"
            )
            
            success = notification_id is None  # 空の値では作成されないべき
            self.log_test_result(
                "空文字列通知作成",
                success,
                "空文字列が正しく処理された" if success else "空文字列が受け入れられた"
            )
            
        except Exception as e:
            self.log_test_result("空文字列通知作成", True, f"例外で正しく処理: {str(e)}")
        
        # テスト2: 非常に長いテキストでの通知作成
        try:
            long_title = "あ" * 1000  # 1000文字のタイトル
            long_message = "い" * 5000  # 5000文字のメッセージ
            
            notification_id = self.notification_service.add_notification(
                user_id="test_user_long",
                title=long_title,
                message=long_message,
                datetime_str="2024-12-25 10:00",
                priority="medium",
                repeat="none"
            )
            
            success = notification_id is not None
            self.log_test_result(
                "長文通知作成",
                success,
                f"通知ID: {notification_id}" if success else "長文通知作成に失敗"
            )
            
        except Exception as e:
            self.log_test_result("長文通知作成", False, f"エラー: {str(e)}")
        
        # テスト3: 特殊文字を含む通知作成
        try:
            special_title = "🔔⏰💡🎯📅"  # 絵文字
            special_message = "改行\nタブ\t特殊文字!@#$%^&*()"
            
            notification_id = self.notification_service.add_notification(
                user_id="test_user_special",
                title=special_title,
                message=special_message,
                datetime_str="2024-12-25 10:00",
                priority="medium",
                repeat="none"
            )
            
            success = notification_id is not None
            self.log_test_result(
                "特殊文字通知作成",
                success,
                f"通知ID: {notification_id}" if success else "特殊文字通知作成に失敗"
            )
            
        except Exception as e:
            self.log_test_result("特殊文字通知作成", False, f"エラー: {str(e)}")
    
    def run_all_tests(self):
        """全テストの実行"""
        logger.info("🚀 包括的通知テストスイート開始")
        
        if not self.setup_test_environment():
            logger.error("❌ テスト環境セットアップに失敗")
            return False
        
        try:
            # 各テストカテゴリを実行
            self.test_notification_creation()
            self.test_notification_retrieval()
            self.test_notification_deletion()
            self.test_all_notifications_deletion()
            self.test_notification_time_handling()
            self.test_notification_sending_logic()
            self.test_edge_cases()
            
            # テスト結果の集計
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result['success'])
            failed_tests = total_tests - passed_tests
            
            logger.info(f"=== テスト結果集計 ===")
            logger.info(f"総テスト数: {total_tests}")
            logger.info(f"成功: {passed_tests}")
            logger.info(f"失敗: {failed_tests}")
            logger.info(f"成功率: {(passed_tests/total_tests*100):.1f}%")
            
            # 失敗したテストの詳細を表示
            if failed_tests > 0:
                logger.warning("=== 失敗したテスト ===")
                for result in self.test_results:
                    if not result['success']:
                        logger.warning(f"❌ {result['test_name']}: {result['message']}")
            
            # テスト結果をファイルに保存
            results_file = "comprehensive_notification_test_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            logger.info(f"テスト結果を保存: {results_file}")
            
            return failed_tests == 0
            
        finally:
            self.cleanup_test_environment()

def main():
    """メイン実行関数"""
    test_suite = NotificationTestSuite()
    
    try:
        success = test_suite.run_all_tests()
        if success:
            logger.info("🎉 全てのテストが成功しました！")
            exit(0)
        else:
            logger.error("❌ 一部のテストが失敗しました。詳細を確認してください。")
            exit(1)
    except KeyboardInterrupt:
        logger.info("⚠️ テストが中断されました")
        exit(130)
    except Exception as e:
        logger.error(f"❌ テスト実行中にエラーが発生: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main() 