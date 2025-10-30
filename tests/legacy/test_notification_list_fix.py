#!/usr/bin/env python3
"""
通知一覧機能修正とGemini安全性フィルター対策テストスクリプト
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
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_notification_list():
    """通知一覧機能のテスト"""
    try:
        from services.notification_service import NotificationService
        from services.gemini_service import GeminiService
        
        print("📍 通知一覧機能テスト")
        
        # Geminiサービス初期化
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEYが設定されていません")
            return False
            
        gemini_service = GeminiService(api_key)
        notification_service = NotificationService(gemini_service=gemini_service)
        
        test_user = "test_user_123"
        
        # テスト通知を作成
        print("📝 テスト通知を作成中...")
        
        # 未来の通知
        success1, msg1 = notification_service.add_notification_from_text(
            test_user, "明日の10時に会議"
        )
        print(f"未来の通知作成: {success1} - {msg1}")
        
        # 今日の通知
        success2, msg2 = notification_service.add_notification_from_text(
            test_user, "今日の23時に寝る"
        )
        print(f"今日の通知作成: {success2} - {msg2}")
        
        # 通知一覧の取得と表示をテスト
        print("\n📋 通知一覧取得テスト")
        notifications = notification_service.get_notifications(test_user)
        print(f"取得した通知数: {len(notifications)}")
        
        # past_only=False での表示テスト
        formatted_list = notification_service.format_notification_list(
            notifications, format_type='detailed', past_only=False
        )
        print("\n🔍 通知一覧（全て表示）:")
        print(formatted_list)
        print(f"表示文字数: {len(formatted_list)}")
        
        # past_only=True での表示テスト
        formatted_past = notification_service.format_notification_list(
            notifications, format_type='detailed', past_only=True
        )
        print("\n🔍 通知一覧（過去のみ）:")
        print(formatted_past)
        print(f"表示文字数: {len(formatted_past)}")
        
        # クリーンアップ
        deleted_count = notification_service.delete_all_notifications(test_user)
        print(f"\n🧹 テスト通知削除: {deleted_count}件")
        
        return True
        
    except Exception as e:
        print(f"❌ 通知一覧テストエラー: {str(e)}")
        return False

def test_gemini_safety_filter():
    """Gemini安全性フィルター対策テスト"""
    try:
        from services.gemini_service import GeminiService
        
        print("\n📍 Gemini安全性フィルター対策テスト")
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEYが設定されていません")
            return False
            
        gemini_service = GeminiService(api_key)
        
        # 検索意図のテスト
        test_cases = [
            "新潟大学について検索して",
            "Python プログラミングを調べて",
            "最新のAI技術について",
            "料理のレシピを検索"
        ]
        
        for test_text in test_cases:
            print(f"\n🔍 テスト: '{test_text}'")
            
            # フォールバック応答のテスト
            fallback_result = gemini_service._generate_safe_fallback_response(test_text)
            print(f"フォールバック応答: {fallback_result}")
            
            # 検索意図判定のテスト
            is_search = gemini_service._is_search_intent(test_text)
            print(f"検索意図判定: {is_search}")
        
        return True
        
    except Exception as e:
        print(f"❌ 安全性フィルターテストエラー: {str(e)}")
        return False

def main():
    """メインテスト関数"""
    setup_logging()
    
    print("🚀 通知一覧機能とGemini安全性フィルター対策テスト開始")
    print("=" * 60)
    
    # テスト実行
    test1_result = test_notification_list()
    test2_result = test_gemini_safety_filter()
    
    print("\n" + "=" * 60)
    print("📊 テスト結果")
    print(f"通知一覧機能: {'✅ 成功' if test1_result else '❌ 失敗'}")
    print(f"安全性フィルター対策: {'✅ 成功' if test2_result else '❌ 失敗'}")
    
    if test1_result and test2_result:
        print("🎉 全てのテストが成功しました！")
        return True
    else:
        print("⚠️ 一部のテストが失敗しました。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 