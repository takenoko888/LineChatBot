#!/usr/bin/env python3
"""
デプロイ時データ永続化テスト

このテストはデプロイ後の通知データ保持を検証します。
"""

import os
import sys
import tempfile
import json
import logging
import shutil
from datetime import datetime, timedelta

# プロジェクトパスの追加
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from services.notification_service import NotificationService
from services.persistent_storage_service import PersistentStorageService
from services.gemini_service import GeminiService

class DeploymentPersistenceTest:
    """デプロイ時永続化テスト"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = []
        self.temp_dir = None
        
        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def setup_test_environment(self) -> str:
        """テスト環境のセットアップ"""
        try:
            self.temp_dir = tempfile.mkdtemp(prefix='deployment_persistence_test_')
            
            # テスト用環境変数設定
            os.environ['NOTIFICATION_STORAGE_PATH'] = os.path.join(self.temp_dir, 'notifications.json')
            os.environ['GITHUB_TOKEN'] = 'test_token'  # テスト用
            os.environ['GITHUB_REPO'] = 'test/repo'    # テスト用
            
            self.log_test_result("環境セットアップ", True, f"テストディレクトリ: {self.temp_dir}")
            return self.temp_dir
            
        except Exception as e:
            self.log_test_result("環境セットアップ", False, f"エラー: {str(e)}")
            raise
    
    def cleanup_test_environment(self):
        """テスト環境のクリーンアップ"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.logger.info(f"テストディレクトリを削除: {self.temp_dir}")
        except Exception as e:
            self.logger.warning(f"クリーンアップエラー: {str(e)}")
    
    def log_test_result(self, test_name: str, success: bool, message: str, details: dict = None):
        """テスト結果をログに記録"""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        self.logger.info(f"{status} {test_name}: {message}")
        
        if details:
            for key, value in details.items():
                self.logger.debug(f"  {key}: {value}")
    
    def test_persistent_storage_service(self) -> bool:
        """永続化ストレージサービスのテスト"""
        try:
            persistent_storage = PersistentStorageService()
            
            # テストデータの作成
            test_data = {
                'user_1': {
                    'n_001': {
                        'id': 'n_001',
                        'user_id': 'user_1',
                        'title': '永続化テスト通知',
                        'message': 'テスト用メッセージ',
                        'datetime': '2025-01-20 10:00',
                        'priority': 'high',
                        'repeat': 'daily',
                        'created_at': datetime.now().isoformat()
                    }
                }
            }
            
            # データ保存テスト
            save_success = persistent_storage.save_data(test_data)
            
            if not save_success:
                self.log_test_result("永続化ストレージ保存", False, "データ保存に失敗")
                return False
            
            # データ読み込みテスト
            loaded_data = persistent_storage.load_data()
            
            if loaded_data is None:
                self.log_test_result("永続化ストレージ読み込み", False, "データ読み込みに失敗")
                return False
            
            # データ内容の検証
            if 'user_1' in loaded_data and 'n_001' in loaded_data['user_1']:
                original_title = test_data['user_1']['n_001']['title']
                loaded_title = loaded_data['user_1']['n_001']['title']
                
                if original_title == loaded_title:
                    self.log_test_result(
                        "永続化ストレージ機能",
                        True,
                        "保存・読み込み・検証すべて成功",
                        {
                            'saved_notifications': 1,
                            'loaded_notifications': 1,
                            'data_integrity': True
                        }
                    )
                    return True
                else:
                    self.log_test_result("永続化ストレージ検証", False, f"データ不整合: {original_title} != {loaded_title}")
                    return False
            else:
                self.log_test_result("永続化ストレージ検証", False, "必要なデータが見つかりません")
                return False
                
        except Exception as e:
            self.log_test_result("永続化ストレージ機能", False, f"例外エラー: {str(e)}")
            return False
    
    def test_notification_service_persistence(self) -> bool:
        """通知サービスの永続化機能テスト"""
        try:
            # テスト用のモックGeminiサービス
            from unittest.mock import Mock
            mock_gemini = Mock()
            mock_gemini._fallback_analysis = Mock(return_value={
                'intent': 'notification',
                'datetime': '2025-01-20 15:00',
                'title': '永続化テスト通知',
                'message': 'デプロイ後も保持されるべき通知'
            })
            
            # 最初の通知サービスインスタンス（デプロイ前の状態）
            service1 = NotificationService(
                storage_path=os.path.join(self.temp_dir, 'notifications.json'),
                gemini_service=mock_gemini
            )
            
            user_id = "persistence_test_user"
            
            # 通知を追加
            notification_id = service1.add_notification(
                user_id=user_id,
                title="永続化テスト通知",
                message="デプロイ後も保持されるべき通知",
                datetime_str="2025-01-20 15:00",
                priority="high",
                repeat="daily"
            )
            
            if not notification_id:
                self.log_test_result("通知追加", False, "通知の追加に失敗")
                return False
            
            # 追加された通知の確認
            notifications_before = service1.get_notifications(user_id)
            count_before = len(notifications_before)
            
            self.log_test_result(
                "通知追加確認",
                count_before == 1,
                f"通知数: {count_before}件",
                {
                    'notification_id': notification_id,
                    'notification_count': count_before
                }
            )
            
            # 新しい通知サービスインスタンス（デプロイ後の状態をシミュレート）
            service2 = NotificationService(
                storage_path=os.path.join(self.temp_dir, 'notifications.json'),
                gemini_service=mock_gemini
            )
            
            # データが復元されているかチェック
            notifications_after = service2.get_notifications(user_id)
            count_after = len(notifications_after)
            
            # 永続化の検証
            persistence_success = (
                count_after == count_before and
                len(notifications_after) > 0 and
                notifications_after[0].title == "永続化テスト通知"
            )
            
            self.log_test_result(
                "通知データ永続化",
                persistence_success,
                f"復元後通知数: {count_after}件",
                {
                    'before_count': count_before,
                    'after_count': count_after,
                    'title_match': notifications_after[0].title if notifications_after else None,
                    'id_match': notifications_after[0].id if notifications_after else None
                }
            )
            
            return persistence_success
            
        except Exception as e:
            self.log_test_result("通知サービス永続化", False, f"例外エラー: {str(e)}")
            return False
    
    def run_all_tests(self) -> dict:
        """すべてのテストを実行"""
        self.logger.info("🚀 デプロイ時データ永続化テスト開始")
        self.logger.info("=" * 60)
        
        try:
            # 環境セットアップ
            self.setup_test_environment()
            
            # テスト実行
            tests = [
                ("永続化ストレージサービス", self.test_persistent_storage_service),
                ("通知サービス永続化", self.test_notification_service_persistence),
            ]
            
            total_tests = len(tests)
            passed_tests = 0
            
            for test_name, test_func in tests:
                self.logger.info(f"\n📋 {test_name} テスト実行中...")
                try:
                    if test_func():
                        passed_tests += 1
                    else:
                        self.logger.warning(f"{test_name} テストが失敗しました")
                except Exception as e:
                    self.logger.error(f"{test_name} テストで例外発生: {str(e)}")
            
            # 結果サマリー
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            summary = {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': success_rate,
                'overall_success': success_rate >= 75,  # 75%以上で成功とみなす
                'test_results': self.test_results
            }
            
            self.logger.info(f"\n📊 テスト結果サマリー:")
            self.logger.info(f"  総テスト数: {total_tests}")
            self.logger.info(f"  成功数: {passed_tests}")
            self.logger.info(f"  成功率: {success_rate:.1f}%")
            
            status = "✅ 合格" if summary['overall_success'] else "❌ 不合格"
            self.logger.info(f"  総合判定: {status}")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"テスト実行エラー: {str(e)}")
            return {
                'total_tests': 0,
                'passed_tests': 0,
                'success_rate': 0,
                'overall_success': False,
                'error': str(e),
                'test_results': self.test_results
            }
        finally:
            self.cleanup_test_environment()

def main():
    """メイン実行関数"""
    tester = DeploymentPersistenceTest()
    result = tester.run_all_tests()
    
    # 結果ファイルに保存
    results_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    results_file = os.path.join(results_dir, 'deployment_persistence_test_results.json')
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n結果ファイル保存: {results_file}")
    
    # 終了コード
    return 0 if result['overall_success'] else 1

if __name__ == "__main__":
    exit(main()) 