#!/usr/bin/env python3
"""
修正内容の基本テスト
"""

import os
import sys
import tempfile
import json
from datetime import datetime

# テスト用環境変数を設定
os.environ['LINE_CHANNEL_SECRET'] = 'test_secret'
os.environ['LINE_ACCESS_TOKEN'] = 'test_token'
os.environ['GEMINI_API_KEY'] = 'test_api_key'
os.environ['PRODUCTION_MODE'] = 'true'
os.environ['KOYEB_INSTANCE_URL'] = 'test-app.koyeb.app'
os.environ['NOTIFICATION_CHECK_INTERVAL'] = '30'

def test_config_loading():
    """設定の読み込みテスト"""
    try:
        from core.config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        print("✓ 設定読み込み成功")
        print(f"  - 本番モード: {config.production_mode}")
        print(f"  - KoyebURL: {config.koyeb_instance_url}")
        print(f"  - 通知間隔: {config.notification_check_interval}秒")
        return True
    except Exception as e:
        print(f"✗ 設定読み込み失敗: {str(e)}")
        return False

def test_notification_storage():
    """通知ストレージのテスト"""
    try:
        from services.notification_service import NotificationService
        
        with tempfile.TemporaryDirectory() as temp_dir:
            notification_service = NotificationService(
                storage_path=os.path.join(temp_dir, 'notifications.json')
            )
            
            print("✓ 通知サービス初期化成功")
            print(f"  - メインストレージ: {notification_service.storage_path}")
            print(f"  - バックアップ数: {len(notification_service.backup_paths)}")
            
            # テスト通知を追加
            user_id = "test_user_001"
            notification_id = notification_service.add_notification(
                user_id=user_id,
                title="テスト通知",
                message="修正テスト用通知",
                datetime_str="2025-01-01 12:00",
                priority="high"
            )
            
            if notification_id:
                print(f"✓ 通知追加成功: {notification_id}")
                
                # データが保存されているかチェック
                if os.path.exists(notification_service.storage_path):
                    print("✓ データファイル作成成功")
                    
                    # 新しいインスタンスでデータ読み込み
                    new_service = NotificationService(
                        storage_path=os.path.join(temp_dir, 'notifications.json')
                    )
                    notifications = new_service.get_notifications(user_id)
                    
                    if len(notifications) == 1:
                        print("✓ データ永続化成功")
                        return True
                    else:
                        print("✗ データ読み込み失敗")
                        return False
                else:
                    print("✗ データファイル作成失敗")
                    return False
            else:
                print("✗ 通知追加失敗")
                return False
                
    except Exception as e:
        print(f"✗ 通知ストレージテスト失敗: {str(e)}")
        return False

def test_keepalive_service():
    """KeepAliveサービスのテスト"""
    try:
        from services.keepalive_service import KeepAliveService
        
        keepalive_service = KeepAliveService()
        result = keepalive_service.configure_for_production()
        
        if result:
            print("✓ Koyeb環境検出成功")
            print(f"  - URL: {keepalive_service.app_url}")
            print(f"  - 間隔: {keepalive_service.ping_interval}秒")
            print(f"  - 本番モード: {keepalive_service.is_production}")
            return True
        else:
            print("✗ Koyeb環境検出失敗")
            return False
            
    except Exception as e:
        print(f"✗ KeepAliveサービステスト失敗: {str(e)}")
        return False

def main():
    """メインテスト"""
    print("=== Koyeb通知機能修正テスト ===")
    
    results = []
    
    # 1. 設定読み込みテスト
    print("\n--- 設定読み込みテスト ---")
    results.append(test_config_loading())
    
    # 2. 通知ストレージテスト
    print("\n--- 通知ストレージテスト ---")
    results.append(test_notification_storage())
    
    # 3. KeepAliveサービステスト
    print("\n--- KeepAliveサービステスト ---")
    results.append(test_keepalive_service())
    
    # 結果サマリー
    print("\n=== テスト結果 ===")
    passed = sum(results)
    total = len(results)
    
    print(f"成功: {passed}/{total}")
    
    if passed == total:
        print("🎉 すべてのテストが成功しました！")
        print("\n修正内容:")
        print("- データ永続化の改善（複数ストレージパス対応）")
        print("- 通知チェック間隔の最適化（30秒間隔）")
        print("- KeepAliveサービスのKoyeb対応")
        print("- 設定管理の強化")
        return 0
    else:
        print("❌ 一部のテストが失敗しました")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 