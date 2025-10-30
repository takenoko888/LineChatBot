#!/usr/bin/env python3
"""
最終的な通知機能包括テスト
修正後の削除機能、ID重複問題、ロック処理の検証を含む
"""

import os
import sys
import json
import tempfile
import shutil
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.notification_service import NotificationService
from services.gemini_service import GeminiService

class FinalNotificationTest:
    def __init__(self):
        self.test_results = []
        self.temp_dir = None
        self.notification_service = None
        
    def setup_test_environment(self):
        """テスト環境のセットアップ"""
        try:
            # 一時ディレクトリの作成
            self.temp_dir = tempfile.mkdtemp(prefix="final_notification_test_")
            storage_path = os.path.join(self.temp_dir, "test_notifications.json")
            
            # 通知サービスの初期化（Geminiサービスなしで初期化）
            self.notification_service = NotificationService(
                storage_path=storage_path,
                gemini_service=None,
                line_bot_api=None
            )
            
            print(f"✅ テスト環境セットアップ完了")
            print(f"   一時ディレクトリ: {self.temp_dir}")
            print(f"   ストレージパス: {storage_path}")
            return True
            
        except Exception as e:
            print(f"❌ テスト環境セットアップ失敗: {str(e)}")
            print(f"   詳細エラー: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False
    
    def cleanup_test_environment(self):
        """テスト環境のクリーンアップ"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"✅ テスト環境クリーンアップ完了")
        except Exception as e:
            print(f"⚠️ クリーンアップエラー: {str(e)}")
    
    def record_test_result(self, test_name: str, success: bool, message: str, details: dict = None):
        """テスト結果を記録"""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
    
    def test_id_generation_uniqueness(self):
        """ID生成の一意性テスト"""
        try:
            user_id = "id_test_user"
            generated_ids = []
            
            # 短時間で複数の通知を作成
            for i in range(5):
                notification_id = self.notification_service.add_notification(
                    user_id=user_id,
                    title=f"ID重複テスト{i+1}",
                    message=f"テストメッセージ{i+1}",
                    datetime_str="2025-12-31 23:59",
                    priority="medium",
                    repeat="none"
                )
                if notification_id:
                    generated_ids.append(notification_id)
                
                # 短時間待機（IDの一意性確保のため）
                time.sleep(0.1)
            
            # ID重複チェック
            unique_ids = set(generated_ids)
            is_unique = len(generated_ids) == len(unique_ids)
            
            # 作成された通知の確認
            notifications = self.notification_service.get_notifications(user_id)
            
            self.record_test_result(
                "ID生成一意性",
                is_unique and len(notifications) == 5,
                f"生成ID数: {len(generated_ids)}, 一意ID数: {len(unique_ids)}, 取得通知数: {len(notifications)}",
                {
                    "generated_ids": generated_ids,
                    "unique_count": len(unique_ids),
                    "retrieved_count": len(notifications),
                    "all_unique": is_unique
                }
            )
            
        except Exception as e:
            self.record_test_result(
                "ID生成一意性",
                False,
                f"エラー: {str(e)}"
            )
    
    def test_individual_deletion_verification(self):
        """個別削除の詳細検証"""
        try:
            user_id = "delete_test_user"
            
            # テスト通知を作成
            notification_id = self.notification_service.add_notification(
                user_id=user_id,
                title="削除テスト通知",
                message="削除対象のテストメッセージ",
                datetime_str="2025-12-31 23:59",
                priority="medium",
                repeat="none"
            )
            
            if not notification_id:
                self.record_test_result(
                    "個別削除検証",
                    False,
                    "通知作成に失敗"
                )
                return
            
            # 削除前の状態確認
            before_notifications = self.notification_service.get_notifications(user_id)
            before_count = len(before_notifications)
            
            # ファイル内容の確認（削除前）
            with open(self.notification_service.storage_path, 'r', encoding='utf-8') as f:
                before_file_data = json.load(f)
            
            # 削除実行
            delete_result = self.notification_service.delete_notification(user_id, notification_id)
            
            # 削除後の状態確認
            after_notifications = self.notification_service.get_notifications(user_id)
            after_count = len(after_notifications)
            
            # ファイル内容の確認（削除後）
            with open(self.notification_service.storage_path, 'r', encoding='utf-8') as f:
                after_file_data = json.load(f)
            
            # 削除検証
            memory_deleted = before_count > after_count
            file_deleted = (user_id not in after_file_data) or (notification_id not in after_file_data.get(user_id, {}))
            
            success = delete_result and memory_deleted and file_deleted and after_count == 0
            
            self.record_test_result(
                "個別削除検証",
                success,
                f"削除結果: {delete_result}, メモリ削除: {memory_deleted}, ファイル削除: {file_deleted}",
                {
                    "notification_id": notification_id,
                    "delete_result": delete_result,
                    "before_count": before_count,
                    "after_count": after_count,
                    "memory_deleted": memory_deleted,
                    "file_deleted": file_deleted,
                    "before_file_has_user": user_id in before_file_data,
                    "after_file_has_user": user_id in after_file_data,
                    "before_file_has_notification": notification_id in before_file_data.get(user_id, {}),
                    "after_file_has_notification": notification_id in after_file_data.get(user_id, {})
                }
            )
            
        except Exception as e:
            self.record_test_result(
                "個別削除検証",
                False,
                f"エラー: {str(e)}"
            )
    
    def test_bulk_deletion_verification(self):
        """一括削除の詳細検証"""
        try:
            user_id = "bulk_delete_test_user"
            
            # 複数の通知を作成
            created_ids = []
            for i in range(3):
                notification_id = self.notification_service.add_notification(
                    user_id=user_id,
                    title=f"一括削除テスト{i+1}",
                    message=f"テストメッセージ{i+1}",
                    datetime_str="2025-12-31 23:59",
                    priority="medium",
                    repeat="none"
                )
                if notification_id:
                    created_ids.append(notification_id)
                time.sleep(0.1)  # ID重複防止
            
            # 削除前の状態確認
            before_notifications = self.notification_service.get_notifications(user_id)
            before_count = len(before_notifications)
            
            # ファイル内容の確認（削除前）
            with open(self.notification_service.storage_path, 'r', encoding='utf-8') as f:
                before_file_data = json.load(f)
            
            # 一括削除実行
            deleted_count = self.notification_service.delete_all_notifications(user_id)
            
            # 削除後の状態確認
            after_notifications = self.notification_service.get_notifications(user_id)
            after_count = len(after_notifications)
            
            # ファイル内容の確認（削除後）
            with open(self.notification_service.storage_path, 'r', encoding='utf-8') as f:
                after_file_data = json.load(f)
            
            # 削除検証
            memory_cleared = after_count == 0
            file_cleared = user_id not in after_file_data
            count_matches = deleted_count == before_count
            
            success = memory_cleared and file_cleared and count_matches and deleted_count > 0
            
            self.record_test_result(
                "一括削除検証",
                success,
                f"削除報告: {deleted_count}件, メモリクリア: {memory_cleared}, ファイルクリア: {file_cleared}",
                {
                    "created_ids": created_ids,
                    "before_count": before_count,
                    "after_count": after_count,
                    "deleted_count": deleted_count,
                    "memory_cleared": memory_cleared,
                    "file_cleared": file_cleared,
                    "count_matches": count_matches,
                    "before_file_has_user": user_id in before_file_data,
                    "after_file_has_user": user_id in after_file_data
                }
            )
            
        except Exception as e:
            self.record_test_result(
                "一括削除検証",
                False,
                f"エラー: {str(e)}"
            )
    
    def test_concurrent_operations(self):
        """並行操作のテスト"""
        try:
            user_id = "concurrent_test_user"
            results = {"created": [], "deleted": [], "errors": []}
            
            def create_notifications():
                """通知作成スレッド"""
                try:
                    for i in range(3):
                        notification_id = self.notification_service.add_notification(
                            user_id=user_id,
                            title=f"並行作成テスト{i+1}",
                            message=f"並行テストメッセージ{i+1}",
                            datetime_str="2025-12-31 23:59",
                            priority="medium",
                            repeat="none"
                        )
                        if notification_id:
                            results["created"].append(notification_id)
                        time.sleep(0.1)
                except Exception as e:
                    results["errors"].append(f"作成エラー: {str(e)}")
            
            def delete_notifications():
                """通知削除スレッド"""
                try:
                    time.sleep(0.2)  # 作成を少し待つ
                    notifications = self.notification_service.get_notifications(user_id)
                    for notification in notifications[:2]:  # 最初の2件を削除
                        if self.notification_service.delete_notification(user_id, notification.id):
                            results["deleted"].append(notification.id)
                except Exception as e:
                    results["errors"].append(f"削除エラー: {str(e)}")
            
            # 並行実行
            create_thread = threading.Thread(target=create_notifications)
            delete_thread = threading.Thread(target=delete_notifications)
            
            create_thread.start()
            delete_thread.start()
            
            create_thread.join()
            delete_thread.join()
            
            # 最終状態確認
            final_notifications = self.notification_service.get_notifications(user_id)
            final_count = len(final_notifications)
            
            # 期待値: 3件作成 - 2件削除 = 1件残存
            expected_count = len(results["created"]) - len(results["deleted"])
            success = final_count == expected_count and len(results["errors"]) == 0
            
            self.record_test_result(
                "並行操作テスト",
                success,
                f"作成: {len(results['created'])}件, 削除: {len(results['deleted'])}件, 残存: {final_count}件, エラー: {len(results['errors'])}件",
                {
                    "created_ids": results["created"],
                    "deleted_ids": results["deleted"],
                    "final_count": final_count,
                    "expected_count": expected_count,
                    "errors": results["errors"]
                }
            )
            
        except Exception as e:
            self.record_test_result(
                "並行操作テスト",
                False,
                f"エラー: {str(e)}"
            )
    
    def test_file_persistence_verification(self):
        """ファイル永続化の検証"""
        try:
            user_id = "persistence_test_user"
            
            # 通知作成
            notification_id = self.notification_service.add_notification(
                user_id=user_id,
                title="永続化テスト",
                message="永続化テストメッセージ",
                datetime_str="2025-12-31 23:59",
                priority="high",
                repeat="daily"
            )
            
            if not notification_id:
                self.record_test_result(
                    "ファイル永続化検証",
                    False,
                    "通知作成に失敗"
                )
                return
            
            # 新しいサービスインスタンスで読み込み
            new_service = NotificationService(
                storage_path=self.notification_service.storage_path,
                gemini_service=None,
                line_bot_api=None
            )
            
            # データが正しく読み込まれるかテスト
            loaded_notifications = new_service.get_notifications(user_id)
            
            if loaded_notifications:
                loaded_notification = loaded_notifications[0]
                data_matches = (
                    loaded_notification.id == notification_id and
                    loaded_notification.title == "永続化テスト" and
                    loaded_notification.priority == "high" and
                    loaded_notification.repeat == "daily"
                )
            else:
                data_matches = False
            
            # 削除テスト
            delete_success = new_service.delete_notification(user_id, notification_id)
            
            # さらに新しいインスタンスで削除確認
            verify_service = NotificationService(
                storage_path=self.notification_service.storage_path,
                gemini_service=None,
                line_bot_api=None
            )
            
            verify_notifications = verify_service.get_notifications(user_id)
            deletion_persisted = len(verify_notifications) == 0
            
            success = data_matches and delete_success and deletion_persisted
            
            self.record_test_result(
                "ファイル永続化検証",
                success,
                f"データ一致: {data_matches}, 削除成功: {delete_success}, 削除永続化: {deletion_persisted}",
                {
                    "notification_id": notification_id,
                    "loaded_count": len(loaded_notifications),
                    "data_matches": data_matches,
                    "delete_success": delete_success,
                    "deletion_persisted": deletion_persisted,
                    "verify_count": len(verify_notifications)
                }
            )
            
        except Exception as e:
            self.record_test_result(
                "ファイル永続化検証",
                False,
                f"エラー: {str(e)}"
            )
    
    def test_edge_cases(self):
        """エッジケースのテスト"""
        try:
            edge_cases_passed = 0
            total_edge_cases = 0
            
            # 存在しない通知の削除
            total_edge_cases += 1
            result = self.notification_service.delete_notification("nonexistent_user", "nonexistent_id")
            if not result:  # 失敗が期待される
                edge_cases_passed += 1
            
            # 存在しないユーザーの全削除
            total_edge_cases += 1
            count = self.notification_service.delete_all_notifications("nonexistent_user")
            if count == 0:  # 0件削除が期待される
                edge_cases_passed += 1
            
            # 空文字列での通知作成
            total_edge_cases += 1
            empty_id = self.notification_service.add_notification(
                user_id="edge_test_user",
                title="",
                message="",
                datetime_str="2025-12-31 23:59"
            )
            if empty_id is None:  # 作成失敗が期待される
                edge_cases_passed += 1
            
            # 無効な日時形式
            total_edge_cases += 1
            invalid_id = self.notification_service.add_notification(
                user_id="edge_test_user",
                title="無効日時テスト",
                message="テスト",
                datetime_str="invalid-datetime"
            )
            if invalid_id is None:  # 作成失敗が期待される
                edge_cases_passed += 1
            
            success = edge_cases_passed == total_edge_cases
            
            self.record_test_result(
                "エッジケーステスト",
                success,
                f"成功: {edge_cases_passed}/{total_edge_cases}",
                {
                    "passed_cases": edge_cases_passed,
                    "total_cases": total_edge_cases,
                    "nonexistent_delete": not result,
                    "nonexistent_bulk_delete": count == 0,
                    "empty_creation_blocked": empty_id is None,
                    "invalid_datetime_blocked": invalid_id is None
                }
            )
            
        except Exception as e:
            self.record_test_result(
                "エッジケーステスト",
                False,
                f"エラー: {str(e)}"
            )
    
    def run_all_tests(self):
        """全テストの実行"""
        print("🚀 最終的な通知機能包括テスト開始")
        print("=" * 60)
        
        if not self.setup_test_environment():
            return False
        
        try:
            # 各テストの実行
            self.test_id_generation_uniqueness()
            self.test_individual_deletion_verification()
            self.test_bulk_deletion_verification()
            self.test_concurrent_operations()
            self.test_file_persistence_verification()
            self.test_edge_cases()
            
            # 結果の集計
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result['success'])
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            print("\n" + "=" * 60)
            print("📊 最終テスト結果サマリー")
            print("=" * 60)
            print(f"総テスト数: {total_tests}")
            print(f"成功: {passed_tests}")
            print(f"失敗: {total_tests - passed_tests}")
            print(f"成功率: {success_rate:.1f}%")
            
            if success_rate == 100:
                print("🎉 全テスト成功！通知機能は正常に動作しています。")
            elif success_rate >= 80:
                print("⚠️ 一部のテストが失敗しましたが、基本機能は動作しています。")
            else:
                print("❌ 重要な問題が検出されました。修正が必要です。")
            
            # 結果をファイルに保存
            results_file = "final_notification_test_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            print(f"\n📄 詳細結果を保存: {results_file}")
            
            return success_rate == 100
            
        finally:
            self.cleanup_test_environment()

def main():
    """メイン実行関数"""
    test = FinalNotificationTest()
    success = test.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 