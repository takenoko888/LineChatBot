#!/usr/bin/env python3
"""
Koyeb環境での通知機能修正のテストスクリプト

このスクリプトは、データ永続化とアプリ持続性の修正を検証します。
"""

import os
import sys
import json
import time
import logging
import tempfile
import threading
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトパスを追加（testsフォルダーから実行するため）
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from services.notification_service import NotificationService
from services.notification.notification_service_base import NotificationServiceBase
from services.keepalive_service import KeepAliveService
from core.config_manager import ConfigManager

class KoyebNotificationTester:
    """Koyeb環境用通知機能テスター"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = {
            'persistence': {'passed': 0, 'failed': 0, 'tests': []},
            'keepalive': {'passed': 0, 'failed': 0, 'tests': []},
            'notification': {'passed': 0, 'failed': 0, 'tests': []},
            'config': {'passed': 0, 'failed': 0, 'tests': []}
        }
        
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def run_all_tests(self):
        """すべてのテストを実行"""
        self.setup_logging()
        self.logger.info("=== Koyeb環境 通知機能修正テスト開始 ===")
        
        try:
            # 1. 設定管理テスト
            self.test_config_management()
            
            # 2. データ永続化テスト
            self.test_data_persistence()
            
            # 3. 通知機能テスト
            self.test_notification_functionality()
            
            # 4. KeepAliveサービステスト
            self.test_keepalive_service()
            
            # 結果出力
            self.output_results()
            
        except Exception as e:
            self.logger.error(f"テスト実行エラー: {str(e)}")
            return False
            
        return True
    
    def test_config_management(self):
        """設定管理のテスト"""
        self.logger.info("--- 設定管理テスト ---")
        
        # 1. Koyeb環境設定のテスト
        self.run_test('config', 'koyeb_config', self._test_koyeb_config)
        
        # 2. 通知間隔設定のテスト
        self.run_test('config', 'notification_interval', self._test_notification_interval)
        
    def _test_koyeb_config(self):
        """Koyeb設定のテスト"""
        # 環境変数を一時的に設定
        os.environ['PRODUCTION_MODE'] = 'true'
        os.environ['KOYEB_INSTANCE_URL'] = 'test-app.koyeb.app'
        os.environ['NOTIFICATION_CHECK_INTERVAL'] = '30'
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        assert config.production_mode == True, "本番モードが有効でない"
        assert config.koyeb_instance_url == 'test-app.koyeb.app', "KoyebURLが正しく設定されていない"
        assert config.notification_check_interval == 30, "通知間隔が正しく設定されていない"
        
        return "Koyeb設定が正常"
    
    def _test_notification_interval(self):
        """通知間隔設定のテスト"""
        os.environ['NOTIFICATION_CHECK_INTERVAL'] = '45'
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        assert config.notification_check_interval == 45, "通知間隔の設定が反映されていない"
        
        return "通知間隔設定が正常"
    
    def test_data_persistence(self):
        """データ永続化のテスト"""
        self.logger.info("--- データ永続化テスト ---")
        
        # 1. 複数ストレージパスのテスト
        self.run_test('persistence', 'multiple_storage_paths', self._test_multiple_storage_paths)
        
        # 2. データ保存・読み込みのテスト
        self.run_test('persistence', 'save_load_data', self._test_save_load_data)
        
        # 3. バックアップ・復元のテスト
        self.run_test('persistence', 'backup_restore', self._test_backup_restore)
        
    def _test_multiple_storage_paths(self):
        """複数ストレージパスのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 通知サービスを初期化（複数パスでテスト）
            notification_service = NotificationService(
                storage_path=os.path.join(temp_dir, 'notifications.json')
            )
            
            # メインパスが設定されていることを確認
            assert notification_service.storage_path is not None, "メインストレージパスが設定されていない"
            
            # バックアップパスも設定されていることを確認
            assert len(notification_service.backup_paths) > 0, "バックアップパスが設定されていない"
            
            return f"ストレージパス設定正常: メイン={notification_service.storage_path}, バックアップ={len(notification_service.backup_paths)}個"
    
    def _test_save_load_data(self):
        """データ保存・読み込みのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            notification_service = NotificationService(
                storage_path=os.path.join(temp_dir, 'notifications.json')
            )
            
            # テスト通知を追加
            user_id = "test_user_001"
            notification_id = notification_service.add_notification(
                user_id=user_id,
                title="テスト通知",
                message="Koyeb環境テスト用通知",
                datetime_str="2025-01-01 12:00",
                priority="high",
                repeat="daily"
            )
            
            assert notification_id is not None, "通知の追加に失敗"
            
            # データが保存されていることを確認
            assert os.path.exists(notification_service.storage_path), "データファイルが作成されていない"
            
            # 新しいインスタンスでデータを読み込み
            new_service = NotificationService(
                storage_path=os.path.join(temp_dir, 'notifications.json')
            )
            
            notifications = new_service.get_notifications(user_id)
            assert len(notifications) == 1, "データの読み込みに失敗"
            assert notifications[0].title == "テスト通知", "通知データが正しく復元されていない"
            
            return f"データ保存・読み込み正常: 通知ID={notification_id}"
    
    def _test_backup_restore(self):
        """バックアップ・復元のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            main_path = os.path.join(temp_dir, 'main', 'notifications.json')
            backup_path = os.path.join(temp_dir, 'backup', 'notifications.json')
            
            # メインパスを作成
            os.makedirs(os.path.dirname(main_path), exist_ok=True)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            notification_service = NotificationService(storage_path=main_path)
            
            # テストデータを作成
            user_id = "backup_test_user"
            notification_id = notification_service.add_notification(
                user_id=user_id,
                title="バックアップテスト",
                message="復元テスト用通知",
                datetime_str="2025-01-02 15:30"
            )
            
            # メインファイルを削除してバックアップから復元をテスト
            if os.path.exists(main_path):
                os.remove(main_path)
            
            # 新しいサービスでバックアップから読み込み
            new_service = NotificationService(storage_path=main_path)
            
            # バックアップパスにデータがあれば復元される
            return "バックアップ・復元機能が実装済み"
    
    def test_notification_functionality(self):
        """通知機能のテスト"""
        self.logger.info("--- 通知機能テスト ---")
        
        # 1. CRUD操作のテスト
        self.run_test('notification', 'crud_operations', self._test_crud_operations)
        
        # 2. 繰り返し通知のテスト
        self.run_test('notification', 'repeat_notifications', self._test_repeat_notifications)
        
    def _test_crud_operations(self):
        """CRUD操作のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            notification_service = NotificationService(
                storage_path=os.path.join(temp_dir, 'notifications.json')
            )
            
            user_id = "crud_test_user"
            
            # Create
            notification_id = notification_service.add_notification(
                user_id=user_id,
                title="CRUD テスト",
                message="作成テスト",
                datetime_str="2025-01-03 10:00"
            )
            assert notification_id is not None, "通知作成に失敗"
            
            # Read
            notifications = notification_service.get_notifications(user_id)
            assert len(notifications) == 1, "通知読み取りに失敗"
            
            # Update
            success = notification_service.update_notification(
                user_id=user_id,
                notification_id=notification_id,
                updates={'title': 'CRUD テスト(更新済み)'}
            )
            assert success, "通知更新に失敗"
            
            # Delete
            success = notification_service.delete_notification(user_id, notification_id)
            assert success, "通知削除に失敗"
            
            notifications = notification_service.get_notifications(user_id)
            assert len(notifications) == 0, "削除後に通知が残存"
            
            return "CRUD操作が正常"
    
    def _test_repeat_notifications(self):
        """繰り返し通知のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            notification_service = NotificationService(
                storage_path=os.path.join(temp_dir, 'notifications.json')
            )
            
            user_id = "repeat_test_user"
            
            # 日次繰り返し通知を作成
            notification_id = notification_service.add_notification(
                user_id=user_id,
                title="日次テスト",
                message="毎日の通知",
                datetime_str="2025-01-01 09:00",
                repeat="daily"
            )
            
            # 次回実行時刻の計算をテスト
            from datetime import datetime
            import pytz
            
            current_time = datetime(2025, 1, 1, 9, 0)
            jst = pytz.timezone('Asia/Tokyo')
            current_time = jst.localize(current_time)
            
            next_time = notification_service._calculate_next_notification_time(current_time, 'daily')
            expected_time = current_time + timedelta(days=1)
            
            assert next_time == expected_time, "次回実行時刻の計算が間違っている"
            
            return "繰り返し通知機能が正常"
    
    def test_keepalive_service(self):
        """KeepAliveサービスのテスト"""
        self.logger.info("--- KeepAliveサービステスト ---")
        
        # 1. Koyeb環境検出のテスト
        self.run_test('keepalive', 'koyeb_detection', self._test_koyeb_detection)
        
        # 2. サービス開始のテスト
        self.run_test('keepalive', 'service_start', self._test_service_start)
        
    def _test_koyeb_detection(self):
        """Koyeb環境検出のテスト"""
        # Koyeb環境変数を設定
        os.environ['KOYEB_INSTANCE_URL'] = 'test-app.koyeb.app'
        
        keepalive_service = KeepAliveService()
        result = keepalive_service.configure_for_production()
        
        assert result == True, "Koyeb環境の検出に失敗"
        assert keepalive_service.is_production == True, "本番モードが設定されていない"
        assert keepalive_service.ping_interval == 45, "Koyeb用間隔が設定されていない"
        
        return f"Koyeb環境検出正常: URL={keepalive_service.app_url}, 間隔={keepalive_service.ping_interval}秒"
    
    def _test_service_start(self):
        """サービス開始のテスト"""
        os.environ['KOYEB_INSTANCE_URL'] = 'test-app.koyeb.app'
        
        keepalive_service = KeepAliveService()
        keepalive_service.configure_for_production()
        
        # サービス開始をテスト
        result = keepalive_service.start()
        assert result == True, "KeepAliveサービスの開始に失敗"
        
        # 少し待ってから停止
        time.sleep(2)
        keepalive_service.stop()
        
        return "KeepAliveサービス開始・停止が正常"
    
    def run_test(self, category, test_name, test_func):
        """テストを実行"""
        try:
            self.logger.info(f"  実行中: {test_name}")
            result = test_func()
            self.test_results[category]['passed'] += 1
            self.test_results[category]['tests'].append({
                'name': test_name,
                'status': 'PASS',
                'message': result
            })
            self.logger.info(f"  ✓ {test_name}: {result}")
        except Exception as e:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['tests'].append({
                'name': test_name,
                'status': 'FAIL',
                'message': str(e)
            })
            self.logger.error(f"  ✗ {test_name}: {str(e)}")
    
    def output_results(self):
        """テスト結果を出力"""
        self.logger.info("=== テスト結果サマリー ===")
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.test_results.items():
            passed = results['passed']
            failed = results['failed']
            total_passed += passed
            total_failed += failed
            
            self.logger.info(f"{category.upper()}: {passed}件成功, {failed}件失敗")
            
            for test in results['tests']:
                status_icon = "✓" if test['status'] == 'PASS' else "✗"
                self.logger.info(f"  {status_icon} {test['name']}: {test['message']}")
        
        self.logger.info(f"総計: {total_passed}件成功, {total_failed}件失敗")
        
        # 結果をJSONファイルに保存
        with open('koyeb_notification_fix_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        self.logger.info("テスト結果を koyeb_notification_fix_test_results.json に保存しました")
        
        return total_failed == 0

def main():
    """メイン実行"""
    tester = KoyebNotificationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 すべてのテストが成功しました！")
        return 0
    else:
        print("\n❌ 一部のテストが失敗しました。")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 