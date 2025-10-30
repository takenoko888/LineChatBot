#!/usr/bin/env python3
"""
簡単な通知機能テストスクリプト
"""
import os
import sys
from datetime import datetime

# プロジェクトルートを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_gemini_basic():
    """Gemini基本テスト"""
    try:
        from services.gemini_service import GeminiService
        
        print("📍 Geminiサービス初期化テスト")
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEYが設定されていません")
            return False
            
        gs = GeminiService(api_key)
        print("✅ Gemini初期化成功")
        
        # 簡単パターン判定テスト
        result = gs._check_simple_patterns("12時1分に昼を食べたいと通知して")
        print(f"✅ 簡単パターン判定: {result}")
        
        # 通知パターン判定テスト
        is_notification = gs._is_notification_pattern("12時1分に昼を食べたいと通知して")
        print(f"✅ 通知パターン判定: {is_notification}")
        
        return True
        
    except Exception as e:
        print(f"❌ Geminiテストエラー: {e}")
        return False

def test_notification_basic():
    """通知機能基本テスト"""
    try:
        from services.gemini_service import GeminiService
        from services.notification_service import NotificationService
        
        print("\n📍 通知機能テスト")
        
        # サービス初期化
        gs = GeminiService()
        ns = NotificationService(
            storage_path="test_quick_notifications.json",
            gemini_service=gs
        )
        
        # テストケース
        test_cases = [
            "12時に昼を食べると通知して",
            "12時1分に昼を食べたいと通知して"
        ]
        
        for i, text in enumerate(test_cases):
            print(f"\n--- テストケース {i+1}: '{text}' ---")
            
            # スマート時間解析
            smart_time = ns.parse_smart_time(text)
            print(f"スマート時間解析: {smart_time}")
            
            # 実際の通知設定
            success, message = ns.add_notification_from_text(f"test_user_{i}", text)
            print(f"通知設定結果: {success}")
            if success:
                print(f"応答メッセージ: {message}")
            else:
                print(f"エラー: {message}")
        
        # 通知一覧確認
        print(f"\n📍 通知一覧確認")
        all_notifications = ns.get_notifications("test_user_0")
        print(f"ユーザー test_user_0 の通知数: {len(all_notifications)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 通知機能テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メインテスト"""
    print("🔧 簡単通知機能テスト開始")
    print("=" * 50)
    
    tests = [
        ("Gemini基本テスト", test_gemini_basic),
        ("通知機能基本テスト", test_notification_basic)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        result = test_func()
        results.append((test_name, result))
        print(f"結果: {'✅ 成功' if result else '❌ 失敗'}")
    
    print(f"\n{'=' * 50}")
    print("📊 テスト結果サマリー")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n合計: {passed}/{total} 成功")
    
    # クリーンアップ
    cleanup_files = ["test_quick_notifications.json"]
    for file in cleanup_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"クリーンアップ: {file}")

if __name__ == "__main__":
    main() 