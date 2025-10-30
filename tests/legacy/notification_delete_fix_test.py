#!/usr/bin/env python3
"""
通知削除機能の修正と詳細テスト
発見された問題を解決し、通知削除が正しく動作することを確認します
"""
import sys
import os
import logging
import json
import tempfile
import shutil
import time
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

class NotificationDeleteFixTest:
    """通知削除機能の修正テスト"""
    
    def __init__(self):
        self.test_temp_dir = None
        self.notification_service = None
        self.gemini_service = None
        self.test_results = []
        
    def setup_test_environment(self):
        """テスト環境のセットアップ"""
        try:
            # 一時ディレクトリの作成
            self.test_temp_dir = tempfile.mkdtemp(prefix="notification_delete_test_")
            logger.info(f"テスト用一時ディレクトリ作成: {self.test_temp_dir}")
            
            # モック環境の設定
            setup_mock_environment()
            
            # 依存関係のインポート
            from services.notification_service import NotificationService
            from services.gemini_service import GeminiService
            
            # Gemini AIをモック化
            with patch('google.generativeai.configure'), \
                 patch('google.generativeai.GenerativeModel') as mock_model:
                
                # モックレスポンスを設定
                mock_response = Mock()
                mock_response.text = '{"datetime": "2024-12-25 10:00", "title": "テスト通知", "message": "テストメッセージ", "priority": "medium", "repeat": "none"}'
                mock_model.return_value.generate_content.return_value = mock_response
                
                # サービスの初期化
                self.gemini_service = GeminiService(MOCK_GEMINI_API_KEY)
                
                # 通知データファイルのパスを一時ディレクトリに設定
                notifications_file = os.path.join(self.test_temp_dir, "test_notifications.json")
                
                # 環境変数を設定してNotificationServiceがテスト用パスを使用するように
                os.environ['NOTIFICATION_STORAGE_PATH'] = notifications_file
                
                self.notification_service = NotificationService(
                    storage_path=notifications_file,
                    gemini_service=self.gemini_service,
                    line_bot_api=None  # テスト用
                )
                
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
        
        # 環境変数をクリア
        if 'NOTIFICATION_STORAGE_PATH' in os.environ:
            del os.environ['NOTIFICATION_STORAGE_PATH']
    
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
    
    def test_notification_creation_and_retrieval(self):
        """通知作成と取得の基本機能テスト"""
        logger.info("=== 通知作成・取得テスト開始 ===")
        
        test_user_id = "delete_test_user"
        
        # 複数の通知を作成
        notification_ids = []
        created_titles = []
        
        for i in range(3):
            title = f"削除テスト通知{i+1}"
            created_titles.append(title)
            
            notification_id = self.notification_service.add_notification(
                user_id=test_user_id,
                title=title,
                message=f"削除テスト用のメッセージ{i+1}",
                datetime_str=f"2024-12-{25+i} 1{i}:00",
                priority="medium",
                repeat="none"
            )
            
            if notification_id:
                notification_ids.append(notification_id)
                logger.info(f"通知{i+1}作成成功: {notification_id}")
            else:
                logger.error(f"通知{i+1}作成失敗")
        
        # 作成した通知の取得
        notifications = self.notification_service.get_notifications(test_user_id)
        retrieved_count = len(notifications)
        expected_count = len(notification_ids)
        
        success = retrieved_count == expected_count
        self.log_test_result(
            "複数通知作成・取得",
            success,
            f"作成: {expected_count}件, 取得: {retrieved_count}件",
            {
                "created_ids": notification_ids,
                "created_titles": created_titles,
                "retrieved_titles": [n.title for n in notifications]
            }
        )
        
        return notification_ids, test_user_id
    
    def test_individual_notification_deletion(self, notification_ids, user_id):
        """個別通知削除のテスト"""
        logger.info("=== 個別通知削除テスト開始 ===")
        
        if not notification_ids:
            self.log_test_result("個別削除前提", False, "テスト用通知が存在しません")
            return
        
        # 削除前の状態確認
        notifications_before = self.notification_service.get_notifications(user_id)
        count_before = len(notifications_before)
        
        logger.info(f"削除前の通知数: {count_before}")
        logger.info(f"削除前の通知一覧: {[n.title for n in notifications_before]}")
        
        # 最初の通知を削除
        target_id = notification_ids[0]
        target_title = notifications_before[0].title if notifications_before else "不明"
        
        logger.info(f"削除対象: ID={target_id}, Title={target_title}")
        
        # 削除実行前にファイル状態を確認
        storage_path = self.notification_service.storage_path
        if os.path.exists(storage_path):
            with open(storage_path, 'r', encoding='utf-8') as f:
                file_data_before = json.load(f)
            logger.info(f"削除前ファイル内容: {len(file_data_before)} ユーザー")
        
        # 削除実行
        delete_success = self.notification_service.delete_notification(user_id, target_id)
        logger.info(f"削除処理結果: {delete_success}")
        
        # 少し待機してファイル保存を確実にする
        time.sleep(0.1)
        
        # 削除後の状態確認
        notifications_after = self.notification_service.get_notifications(user_id)
        count_after = len(notifications_after)
        
        logger.info(f"削除後の通知数: {count_after}")
        logger.info(f"削除後の通知一覧: {[n.title for n in notifications_after]}")
        
        # ファイル内容の確認
        if os.path.exists(storage_path):
            with open(storage_path, 'r', encoding='utf-8') as f:
                file_data_after = json.load(f)
            logger.info(f"削除後ファイル内容: {len(file_data_after)} ユーザー")
            
            # ユーザーの通知数をファイルから確認
            file_user_notifications = file_data_after.get(user_id, {})
            file_count = len(file_user_notifications)
            logger.info(f"ファイル内の{user_id}の通知数: {file_count}")
        
        # 削除対象が含まれていないかチェック
        deleted_correctly = not any(n.id == target_id for n in notifications_after)
        count_decreased = count_after == count_before - 1
        
        success = delete_success and deleted_correctly and count_decreased
        
        self.log_test_result(
            "個別通知削除",
            success,
            f"削除実行: {delete_success}, 数変化: {count_before} -> {count_after}, 対象削除: {deleted_correctly}",
            {
                "target_id": target_id,
                "target_title": target_title,
                "before_count": count_before,
                "after_count": count_after,
                "deleted_correctly": deleted_correctly
            }
        )
        
        return success
    
    def test_all_notifications_deletion(self, user_id):
        """全通知削除のテスト"""
        logger.info("=== 全通知削除テスト開始 ===")
        
        # 残っている通知の確認
        notifications_before = self.notification_service.get_notifications(user_id)
        count_before = len(notifications_before)
        
        logger.info(f"全削除前の通知数: {count_before}")
        
        if count_before == 0:
            # 新しい通知を作成してテスト
            for i in range(2):
                notification_id = self.notification_service.add_notification(
                    user_id=user_id,
                    title=f"全削除テスト通知{i+1}",
                    message=f"全削除テスト用メッセージ{i+1}",
                    datetime_str=f"2024-12-{27+i} 1{i}:00",
                    priority="medium",
                    repeat="none"
                )
                logger.info(f"全削除テスト用通知作成: {notification_id}")
            
            notifications_before = self.notification_service.get_notifications(user_id)
            count_before = len(notifications_before)
            logger.info(f"全削除前の通知数（再確認）: {count_before}")
        
        # 全削除実行
        deleted_count = self.notification_service.delete_all_notifications(user_id)
        logger.info(f"全削除処理結果: {deleted_count}件削除")
        
        # 少し待機
        time.sleep(0.1)
        
        # 削除後の確認
        notifications_after = self.notification_service.get_notifications(user_id)
        count_after = len(notifications_after)
        
        logger.info(f"全削除後の通知数: {count_after}")
        
        # ファイル内容の確認
        storage_path = self.notification_service.storage_path
        if os.path.exists(storage_path):
            with open(storage_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            
            user_exists_in_file = user_id in file_data
            logger.info(f"ファイル内の{user_id}存在: {user_exists_in_file}")
            
            if user_exists_in_file:
                file_count = len(file_data[user_id])
                logger.info(f"ファイル内の{user_id}通知数: {file_count}")
        
        # 全削除の成功判定
        all_deleted = count_after == 0
        correct_count = deleted_count == count_before
        
        success = all_deleted and correct_count
        
        self.log_test_result(
            "全通知削除",
            success,
            f"削除報告: {deleted_count}件, 削除前: {count_before}件, 削除後: {count_after}件",
            {
                "before_count": count_before,
                "after_count": count_after,
                "deleted_count": deleted_count,
                "all_deleted": all_deleted,
                "correct_count": correct_count
            }
        )
        
        return success
    
    def test_storage_file_operations(self):
        """ストレージファイル操作のテスト"""
        logger.info("=== ストレージ操作テスト開始 ===")
        
        test_user_id = "storage_test_user"
        storage_path = self.notification_service.storage_path
        
        # テスト通知を作成
        notification_id = self.notification_service.add_notification(
            user_id=test_user_id,
            title="ストレージテスト通知",
            message="ストレージテスト用メッセージ",
            datetime_str="2024-12-25 15:00",
            priority="medium",
            repeat="none"
        )
        
        # ファイル保存の確認
        if os.path.exists(storage_path):
            with open(storage_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            
            user_in_file = test_user_id in file_data
            notification_in_file = notification_id in file_data.get(test_user_id, {}) if user_in_file else False
            
            self.log_test_result(
                "ファイル保存確認",
                user_in_file and notification_in_file,
                f"ユーザー存在: {user_in_file}, 通知存在: {notification_in_file}",
                {
                    "file_path": storage_path,
                    "user_id": test_user_id,
                    "notification_id": notification_id
                }
            )
        else:
            self.log_test_result(
                "ファイル保存確認",
                False,
                f"ストレージファイルが存在しません: {storage_path}"
            )
        
        # 削除後のファイル確認
        delete_success = self.notification_service.delete_notification(test_user_id, notification_id)
        
        time.sleep(0.1)  # ファイル保存待機
        
        if os.path.exists(storage_path):
            with open(storage_path, 'r', encoding='utf-8') as f:
                file_data_after = json.load(f)
            
            user_in_file_after = test_user_id in file_data_after
            notification_in_file_after = notification_id in file_data_after.get(test_user_id, {}) if user_in_file_after else False
            
            self.log_test_result(
                "削除後ファイル確認",
                not notification_in_file_after,
                f"削除成功: {delete_success}, 通知残存: {notification_in_file_after}",
                {
                    "delete_success": delete_success,
                    "notification_removed": not notification_in_file_after
                }
            )
    
    def run_all_tests(self):
        """全テストの実行"""
        logger.info("🚀 通知削除機能修正テストスイート開始")
        
        if not self.setup_test_environment():
            logger.error("❌ テスト環境セットアップに失敗")
            return False
        
        try:
            # テスト実行
            notification_ids, user_id = self.test_notification_creation_and_retrieval()
            
            if notification_ids:
                self.test_individual_notification_deletion(notification_ids, user_id)
                self.test_all_notifications_deletion(user_id)
            
            self.test_storage_file_operations()
            
            # テスト結果の集計
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result['success'])
            failed_tests = total_tests - passed_tests
            
            logger.info(f"=== テスト結果集計 ===")
            logger.info(f"総テスト数: {total_tests}")
            logger.info(f"成功: {passed_tests}")
            logger.info(f"失敗: {failed_tests}")
            logger.info(f"成功率: {(passed_tests/total_tests*100):.1f}%")
            
            # 失敗したテストの詳細
            if failed_tests > 0:
                logger.warning("=== 失敗したテスト ===")
                for result in self.test_results:
                    if not result['success']:
                        logger.warning(f"❌ {result['test_name']}: {result['message']}")
                        if result['details']:
                            logger.warning(f"   詳細: {result['details']}")
            
            # テスト結果をファイルに保存
            results_file = "notification_delete_fix_test_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            logger.info(f"テスト結果を保存: {results_file}")
            
            return failed_tests == 0
            
        finally:
            self.cleanup_test_environment()

def main():
    """メイン実行関数"""
    test_suite = NotificationDeleteFixTest()
    
    try:
        success = test_suite.run_all_tests()
        if success:
            logger.info("🎉 全てのテストが成功しました！")
        else:
            logger.error("❌ 一部のテストが失敗しました。通知削除機能に問題があります。")
            
            # 問題の分析と解決策の提案
            logger.info("\n=== 問題分析と解決策 ===")
            logger.info("1. 通知削除でロック取得に失敗している可能性があります")
            logger.info("2. ファイル保存処理が正しく完了していない可能性があります")
            logger.info("3. メモリ上のデータとファイル上のデータが同期していない可能性があります")
            logger.info("\n解決策:")
            logger.info("- _save_notifications メソッドでロック失敗時の処理を改善")
            logger.info("- 削除処理の成功判定を厳密化")
            logger.info("- ファイル保存後の検証を強化")
        
        return success
        
    except KeyboardInterrupt:
        logger.info("⚠️ テストが中断されました")
        return False
    except Exception as e:
        logger.error(f"❌ テスト実行中にエラーが発生: {str(e)}")
        return False

if __name__ == "__main__":
    main() 