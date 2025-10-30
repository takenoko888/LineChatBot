#!/usr/bin/env python3
"""
自動実行機能修正テストスクリプト
- フォールバック処理のテスト
- デバッグ情報の確認
- 天気配信タスクのテスト
"""

import os
import sys
import logging
from datetime import datetime

# プロジェクトルートを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_gemini_auto_task_analysis():
    """Geminiの自動実行タスク解析テスト"""
    try:
        from services.gemini_service import GeminiService
        
        print("📍 Gemini自動実行タスク解析テスト")
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEYが設定されていません")
            return False
            
        gemini_service = GeminiService(api_key)
        
        # テストケース
        test_cases = [
            "毎日7時に新潟の天気を配信して",
            "毎日8時に東京の天気を配信して",
            "毎朝ニュースを送って",
            "毎日9時にニュース配信"
        ]
        
        for test_text in test_cases:
            print(f"\n🔍 テスト: '{test_text}'")
            
            # AI解析実行
            result = gemini_service.analyze_text(test_text, "test_user")
            print(f"意図: {result.get('intent')}")
            print(f"信頼度: {result.get('confidence')}")
            
            # auto_taskデータの確認
            if result.get('intent') == 'create_auto_task':
                auto_task_data = result.get('auto_task', {})
                print(f"自動実行タスクデータ: {auto_task_data}")
                
                # 必要なキーの確認
                required_keys = ['task_type', 'title', 'description', 'schedule_pattern', 'schedule_time']
                missing_keys = [key for key in required_keys if key not in auto_task_data]
                
                if missing_keys:
                    print(f"⚠️ 不足キー: {missing_keys}")
                else:
                    print("✅ 必要な情報がすべて揃っています")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini解析テストエラー: {str(e)}")
        return False

def test_auto_task_service():
    """自動実行サービステスト"""
    try:
        from services.auto_task_service import AutoTaskService
        from services.gemini_service import GeminiService
        from services.notification_service import NotificationService
        
        print("\n📍 自動実行サービステスト")
        
        # サービス初期化
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEYが設定されていません")
            return False
            
        gemini_service = GeminiService(api_key)
        notification_service = NotificationService(gemini_service=gemini_service)
        
        auto_task_service = AutoTaskService(
            storage_path="./test_data",
            notification_service=notification_service,
            weather_service=None,  # 天気サービスなしでテスト
            search_service=None,
            gemini_service=gemini_service
        )
        
        test_user = "test_user_123"
        
        # タスク作成テスト
        print("📝 タスク作成テスト")
        
        task_id = auto_task_service.create_auto_task(
            user_id=test_user,
            task_type="weather_daily",
            title="毎日の新潟天気配信",
            description="毎日7時に新潟の天気情報を配信",
            schedule_pattern="daily",
            schedule_time="07:00",
            parameters={"location": "新潟"}
        )
        
        print(f"作成されたタスクID: {task_id}")
        
        if task_id:
            # タスク一覧テスト
            tasks = auto_task_service.get_user_tasks(test_user)
            print(f"ユーザータスク数: {len(tasks)}")
            
            # タスク実行テスト（天気サービスなし）
            print("🔄 タスク実行テスト（天気サービスなし）")
            auto_task_service._execute_task(task_id)
            
            # クリーンアップ
            auto_task_service.delete_task(test_user, task_id)
            print("🧹 テストタスク削除完了")
        
        return True
        
    except Exception as e:
        print(f"❌ 自動実行サービステストエラー: {str(e)}")
        return False

def test_message_handler_integration():
    """メッセージハンドラー統合テスト"""
    try:
        from handlers.message_handler import MessageHandler
        from services.gemini_service import GeminiService
        from services.notification_service import NotificationService
        from services.auto_task_service import AutoTaskService
        
        print("\n📍 メッセージハンドラー統合テスト")
        
        # サービス初期化
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEYが設定されていません")
            return False
            
        gemini_service = GeminiService(api_key)
        notification_service = NotificationService(gemini_service=gemini_service)
        auto_task_service = AutoTaskService(
            storage_path="./test_data",
            notification_service=notification_service,
            weather_service=None,
            search_service=None,
            gemini_service=gemini_service
        )
        
        message_handler = MessageHandler()
        
        # テストイベントの作成
        class MockEvent:
            def __init__(self, text):
                self.message = MockMessage(text)
                self.source = MockSource()
                
        class MockMessage:
            def __init__(self, text):
                self.text = text
                
        class MockSource:
            def __init__(self):
                self.user_id = "test_user_123"
        
        # テストケース
        test_messages = [
            "毎日7時に新潟の天気を配信して",
            "毎日8時に東京の天気を配信して"
        ]
        
        for test_text in test_messages:
            print(f"\n🔍 メッセージ処理テスト: '{test_text}'")
            
            event = MockEvent(test_text)
            
            response, quick_reply_type = message_handler.handle_message(
                event=event,
                gemini_service=gemini_service,
                notification_service=notification_service,
                auto_task_service=auto_task_service
            )
            
            print(f"応答: {response}")
            print(f"クイックリプライタイプ: {quick_reply_type}")
            print(f"応答文字数: {len(response)}")
        
        return True
        
    except Exception as e:
        print(f"❌ メッセージハンドラーテストエラー: {str(e)}")
        return False

def main():
    """メインテスト関数"""
    setup_logging()
    
    print("🚀 自動実行機能修正テスト開始")
    print("=" * 60)
    
    # テスト実行
    test1_result = test_gemini_auto_task_analysis()
    test2_result = test_auto_task_service()
    test3_result = test_message_handler_integration()
    
    print("\n" + "=" * 60)
    print("📊 テスト結果")
    print(f"Gemini自動実行解析: {'✅ 成功' if test1_result else '❌ 失敗'}")
    print(f"自動実行サービス: {'✅ 成功' if test2_result else '❌ 失敗'}")
    print(f"メッセージハンドラー統合: {'✅ 成功' if test3_result else '❌ 失敗'}")
    
    if test1_result and test2_result and test3_result:
        print("🎉 全てのテストが成功しました！")
        return True
    else:
        print("⚠️ 一部のテストが失敗しました。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 