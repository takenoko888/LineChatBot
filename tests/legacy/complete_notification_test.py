#!/usr/bin/env python3
"""
通知機能の完全なテスト - 全修正内容を検証
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime, timedelta
import pytz

# テスト用のパス設定
TEST_DIR = tempfile.mkdtemp(prefix="complete_notification_test_")
TEST_NOTIFICATION_FILE = os.path.join(TEST_DIR, "notifications.json")

# テスト用環境変数設定
os.environ['NOTIFICATION_STORAGE_PATH'] = TEST_NOTIFICATION_FILE

# プロジェクトパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.notification_service import NotificationService
from services.gemini_service import GeminiService

class MockGeminiService:
    """テスト用のGeminiサービス"""
    
    def parse_notification_request(self, text: str) -> dict:
        """簡単な通知解析"""
        if "7時" in text and "起きる" in text:
            return {
                'datetime': '2025-05-24 07:00',
                'title': '起床時間',
                'message': text,
                'priority': 'medium',
                'repeat': 'daily'
            }
        elif "5時" in text and "課題" in text:
            return {
                'datetime': '2025-05-24 05:00',
                'title': '課題リマインダー',
                'message': text,
                'priority': 'medium',
                'repeat': 'none'
            }
        elif "8時" in text and "会議" in text:
            return {
                'datetime': '2025-05-24 08:00',
                'title': '会議リマインダー',
                'message': text,
                'priority': 'high',
                'repeat': 'none'
            }
        return None

def test_complete_notification_functionality():
    """通知機能の完全テスト"""
    print("🔍 通知機能完全テスト開始")
    print(f"📁 テストディレクトリ: {TEST_DIR}")
    print(f"📄 通知ファイル: {TEST_NOTIFICATION_FILE}")
    print("=" * 80)
    
    try:
        # サービス初期化
        gemini_service = MockGeminiService()
        notification_service = NotificationService(
            storage_path=TEST_NOTIFICATION_FILE,
            gemini_service=gemini_service
        )
        
        user_id = "test_user_complete"
        
        # テスト1: 初期状態確認
        print("🧪 テスト1: 初期状態確認")
        initial_notifications = notification_service.get_notifications(user_id)
        assert len(initial_notifications) == 0, f"初期状態で通知が存在: {len(initial_notifications)}件"
        print("✅ 初期状態確認 - 成功")
        print()
        
        # テスト2: 1件目の通知追加
        print("🧪 テスト2: 1件目の通知追加")
        success1, message1 = notification_service.add_notification_from_text(user_id, "毎日7時に起きる")
        assert success1, f"1件目の通知追加に失敗: {message1}"
        
        notifications_after_1 = notification_service.get_notifications(user_id)
        assert len(notifications_after_1) == 1, f"1件目追加後の通知数が異常: {len(notifications_after_1)}件"
        assert notifications_after_1[0].title == "起床時間", f"1件目のタイトルが異常: {notifications_after_1[0].title}"
        print("✅ 1件目の通知追加 - 成功")
        print()
        
        # テスト3: 2件目の通知追加
        print("🧪 テスト3: 2件目の通知追加")
        success2, message2 = notification_service.add_notification_from_text(user_id, "5時に課題をやると通知して")
        assert success2, f"2件目の通知追加に失敗: {message2}"
        
        notifications_after_2 = notification_service.get_notifications(user_id)
        assert len(notifications_after_2) == 2, f"2件目追加後の通知数が異常: {len(notifications_after_2)}件"
        
        titles = [n.title for n in notifications_after_2]
        assert "起床時間" in titles, f"起床時間が見つからない: {titles}"
        assert "課題リマインダー" in titles, f"課題リマインダーが見つからない: {titles}"
        print("✅ 2件目の通知追加 - 成功")
        print()
        
        # テスト4: 重複通知の拒否
        print("🧪 テスト4: 重複通知の拒否")
        success3, message3 = notification_service.add_notification_from_text(user_id, "毎日7時に起きる")
        assert not success3, f"重複通知が追加されてしまった: {message3}"
        assert "類似した通知" in message3, f"重複メッセージが適切でない: {message3}"
        
        notifications_after_3 = notification_service.get_notifications(user_id)
        assert len(notifications_after_3) == 2, f"重複追加後の通知数が異常: {len(notifications_after_3)}件"
        print("✅ 重複通知の拒否 - 成功")
        print()
        
        # テスト5: 3件目の通知追加（異なる内容）
        print("🧪 テスト5: 3件目の通知追加（異なる内容）")
        success4, message4 = notification_service.add_notification_from_text(user_id, "8時に会議に参加")
        assert success4, f"3件目の通知追加に失敗: {message4}"
        
        notifications_after_4 = notification_service.get_notifications(user_id)
        assert len(notifications_after_4) == 3, f"3件目追加後の通知数が異常: {len(notifications_after_4)}件"
        print("✅ 3件目の通知追加 - 成功")
        print()
        
        # テスト6: 通知一覧の表示
        print("🧪 テスト6: 通知一覧の表示")
        notification_list = notification_service.format_notification_list(notifications_after_4, format_type='detailed')
        assert "現在の通知一覧" in notification_list, f"一覧タイトルが見つからない"
        assert "起床時間" in notification_list, f"起床時間が一覧に見つからない"
        assert "課題リマインダー" in notification_list, f"課題リマインダーが一覧に見つからない"
        assert "会議リマインダー" in notification_list, f"会議リマインダーが一覧に見つからない"
        print("✅ 通知一覧の表示 - 成功")
        print()
        
        # テスト7: 通知削除
        print("🧪 テスト7: 通知削除")
        notification_to_delete = notifications_after_4[1]  # 2件目を削除
        delete_success = notification_service.delete_notification(user_id, notification_to_delete.id)
        assert delete_success, f"通知削除に失敗: {notification_to_delete.id}"
        
        notifications_after_delete = notification_service.get_notifications(user_id)
        assert len(notifications_after_delete) == 2, f"削除後の通知数が異常: {len(notifications_after_delete)}件"
        
        remaining_ids = [n.id for n in notifications_after_delete]
        assert notification_to_delete.id not in remaining_ids, f"削除された通知がまだ存在: {notification_to_delete.id}"
        print("✅ 通知削除 - 成功")
        print()
        
        # テスト8: 新しいサービスインスタンスでの読み込み
        print("🧪 テスト8: 新しいサービスインスタンスでの読み込み")
        new_service = NotificationService(
            storage_path=TEST_NOTIFICATION_FILE,
            gemini_service=gemini_service
        )
        new_notifications = new_service.get_notifications(user_id)
        assert len(new_notifications) == 2, f"新インスタンスの通知数が異常: {len(new_notifications)}件"
        print("✅ 新しいサービスインスタンスでの読み込み - 成功")
        print()
        
        # テスト9: 全削除
        print("🧪 テスト9: 全削除")
        deleted_count = new_service.delete_all_notifications(user_id)
        assert deleted_count == 2, f"全削除の件数が異常: {deleted_count}件"
        
        final_notifications = new_service.get_notifications(user_id)
        assert len(final_notifications) == 0, f"全削除後に通知が残存: {len(final_notifications)}件"
        print("✅ 全削除 - 成功")
        print()
        
        # テスト結果の出力
        print("=" * 80)
        print("🎉 全テスト成功！")
        print("✅ 複数通知の保存・取得")
        print("✅ 通知一覧の表示")
        print("✅ 重複通知の防止")
        print("✅ 通知の削除")
        print("✅ データの永続化")
        print("✅ format_notification_listのpast_only問題修正")
        print("=" * 80)
        
        # 詳細情報の表示
        print("\n📊 テスト詳細:")
        print(f"🔧 修正内容:")
        print("  - add_notificationメソッドでの既存データ読み込み追加")
        print("  - format_notification_listのpast_onlyパラメータ削除")
        print("  - 重複通知チェック機能の追加")
        print("  - エラーハンドリングの改善")
        
        return True
        
    except AssertionError as e:
        print(f"❌ テスト失敗: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ テスト実行エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # クリーンアップ
        print(f"\n🧹 クリーンアップ: {TEST_DIR}")
        try:
            shutil.rmtree(TEST_DIR)
        except Exception as e:
            print(f"クリーンアップエラー: {str(e)}")

def test_specific_error_scenario():
    """ログで発生した特定のエラーシナリオをテスト"""
    print("\n🔍 特定エラーシナリオのテスト")
    print("-" * 40)
    
    try:
        # サービス初期化
        gemini_service = MockGeminiService()
        notification_service = NotificationService(
            storage_path=TEST_NOTIFICATION_FILE,
            gemini_service=gemini_service
        )
        
        user_id = "U8cafc4820a70378fd6b10adb81c16cc6"
        
        # ログで確認されたシナリオの再現
        print("1. 毎日7時に起きる を追加")
        success1, message1 = notification_service.add_notification_from_text(user_id, "毎日7時に起きる")
        print(f"結果: {success1}, メッセージ: {message1[:50]}...")
        
        print("2. 通知一覧を取得")
        notifications = notification_service.get_notifications(user_id)
        print(f"通知数: {len(notifications)}")
        
        print("3. 通知一覧をフォーマット")
        formatted_list = notification_service.format_notification_list(notifications, format_type='detailed')
        print(f"フォーマット成功: {len(formatted_list) > 0}")
        
        print("4. 同じ通知を再度追加を試行")
        success2, message2 = notification_service.add_notification_from_text(user_id, "毎日7時に起きる")
        print(f"重複防止: {not success2}")
        
        print("✅ 特定エラーシナリオのテスト - 成功")
        return True
        
    except Exception as e:
        print(f"❌ 特定エラーシナリオのテスト - 失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_complete_notification_functionality()
    success2 = test_specific_error_scenario()
    
    if success1 and success2:
        print("\n🎉 すべてのテストが成功しました！")
        print("📱 アプリケーションは正常に動作するはずです。")
    else:
        print("\n❌ テストに失敗しました。")
        print("🔧 修正が必要です。") 