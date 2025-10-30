#!/usr/bin/env python3
"""
削除機能修正の動作確認テスト
"""
import os
import sys
import tempfile
import shutil
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.notification_service import NotificationService

def test_deletion_fix():
    """削除機能の修正確認テスト"""
    print("🔧 削除機能修正テストを開始します...")
    
    # 一時ディレクトリでテスト
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = os.path.join(temp_dir, "test_notifications.json")
        
        # サービス初期化
        service = NotificationService(
            storage_path=storage_path,
            gemini_service=None,
            line_bot_api=None
        )
        
        test_user = "test_user_12345"
        
        # 1. 通知作成
        print("📝 通知を作成中...")
        notification_id1 = service.add_notification(
            user_id=test_user,
            title="テスト通知1",
            message="テストメッセージ1",
            datetime_str="2025-12-31 23:59",
            priority="high"
        )
        
        notification_id2 = service.add_notification(
            user_id=test_user,
            title="テスト通知2", 
            message="テストメッセージ2",
            datetime_str="2025-12-31 23:58",
            priority="medium"
        )
        
        if not notification_id1 or not notification_id2:
            print("❌ 通知作成に失敗")
            return False
        
        print(f"✅ 通知作成成功: {notification_id1}, {notification_id2}")
        
        # 2. 通知一覧確認
        notifications = service.get_notifications(test_user)
        print(f"📋 作成後通知数: {len(notifications)}件")
        
        # 3. 個別削除テスト
        print(f"🗑️ 個別削除テスト: {notification_id1}")
        delete_result = service.delete_notification(test_user, notification_id1)
        print(f"削除結果: {delete_result}")
        
        # 4. 削除後確認
        notifications_after_single = service.get_notifications(test_user)
        print(f"📋 個別削除後通知数: {len(notifications_after_single)}件")
        
        # 5. 全削除テスト
        print("🗑️ 全削除テスト")
        deleted_count = service.delete_all_notifications(test_user)
        print(f"削除数: {deleted_count}")
        
        # 6. 全削除後確認
        notifications_after_all = service.get_notifications(test_user)
        print(f"📋 全削除後通知数: {len(notifications_after_all)}件")
        
        # 結果判定
        success = (
            len(notifications) == 2 and
            delete_result == True and 
            len(notifications_after_single) == 1 and
            deleted_count == 1 and
            len(notifications_after_all) == 0
        )
        
        if success:
            print("🎉 削除機能修正テスト: 完全成功！")
        else:
            print("❌ 削除機能修正テスト: 失敗")
            print(f"   期待値: 作成2件→個別削除1件→全削除0件")
            print(f"   実際値: 作成{len(notifications)}件→個別削除{len(notifications_after_single)}件→全削除{len(notifications_after_all)}件")
        
        return success

if __name__ == "__main__":
    success = test_deletion_fix()
    exit(0 if success else 1) 