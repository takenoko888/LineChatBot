#!/usr/bin/env python3
"""
通知一覧Flex Message化のテスト
"""
import os
import sys
import json
from datetime import datetime

# APIキー設定（テスト用）
os.environ['GEMINI_API_KEY'] = 'test_key'

# パスを追加
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

def test_notification_flex_message_formatting():
    """通知一覧のFlex Message形式テスト"""
    print("🔔 通知一覧Flex Message化テスト")
    print("=" * 50)
    
    try:
        from services.notification_service import NotificationService
        from services.notification.notification_model import Notification
        
        # Mock NotificationService for testing
        class MockNotificationService(NotificationService):
            def __init__(self):
                # 親クラスの__init__を呼び出さないか、必要な引数を渡す
                # ここではテスト用に最小限の初期化を行う
                self.notifications = {}
                self.lock = type('Lock', (object,), {'__enter__': lambda s: None, '__exit__': lambda s, *args: None})()
                self.logger = type('Logger', (object,), {'debug': lambda s, *args: None, 'info': lambda s, *args: None, 'warning': lambda s, *args: None, 'error': lambda s, *args: None})()

            def _load_notifications(self):
                pass # テストではファイルをロードしない

            def _save_notifications(self, lock_acquired=False):
                pass # テストではファイルを保存しない

        notification_service = MockNotificationService()

        # テスト1: 通知が複数ある場合のFlex Message
        print("\n🔔 テスト1: 複数通知のFlex Message")
        print("-" * 30)
        notifications = [
            Notification(
                id="n_12345",
                user_id="user1",
                title="会議リマインダー",
                message="今日の15時から会議です。資料の準備を忘れずに。",
                datetime="2025-07-01 15:00",
                priority="high",
                repeat="none"
            ),
            Notification(
                id="n_67890",
                user_id="user1",
                title="薬の時間",
                message="毎朝8時に薬を飲んでください。",
                datetime="2025-07-02 08:00",
                priority="medium",
                repeat="daily"
            )
        ]
        flex_message = notification_service.format_notification_list(notifications, format_type='flex_message')
        
        assert isinstance(flex_message, dict)
        assert flex_message['type'] == 'carousel'
        assert len(flex_message['contents']) == 3  # 概要 + 2 通知
        
        # 概要バブル検証
        summary = flex_message['contents'][0]
        assert summary['body']['contents'][0]['text'] == "📊 通知概要"

        # 最初のバブルの検証
        bubble1 = flex_message['contents'][1]
        assert bubble1['type'] == 'bubble'
        assert bubble1['body']['contents'][0]['text'] == "会議リマインダー"
        assert "2025年07月01日 15時00分" in bubble1['body']['contents'][1]['contents'][0]['contents'][1]['text']
        assert bubble1['footer']['contents'][0]['action']['text'] == "通知編集 n_12345"
        assert bubble1['footer']['contents'][1]['action']['text'] == "通知削除 n_12345"

        # 2番目のバブルの検証
        bubble2 = flex_message['contents'][2]
        assert bubble2['body']['contents'][0]['text'] == "薬の時間"
        assert "(毎日繰り返し)" in bubble2['body']['contents'][1]['contents'][0]['contents'][1]['text']
        assert bubble2['footer']['contents'][0]['action']['text'] == "通知編集 n_67890"
        assert bubble2['footer']['contents'][1]['action']['text'] == "通知削除 n_67890"

        print("✅ 複数通知のFlex Messageの基本構造は正常です。")
        print("\n生成されたJSON:")
        print(json.dumps(flex_message, indent=2, ensure_ascii=False))

        # テスト2: 通知がない場合のFlex Message
        print("\n🔔 テスト2: 通知がない場合のFlex Message")
        print("-" * 30)
        no_notifications_flex = notification_service.format_notification_list([], format_type='flex_message')
        assert no_notifications_flex['body']['contents'][0]['text'] == "現在、設定されている通知はありません。"
        print("✅ 通知がない場合のメッセージは正常です。")
        print("\n生成されたJSON:")
        print(json.dumps(no_notifications_flex, indent=2, ensure_ascii=False))

        print("\n🎉 すべての通知一覧Flex Messageテストが完了しました！")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_notification_flex_message_formatting()
    sys.exit(0 if success else 1)
