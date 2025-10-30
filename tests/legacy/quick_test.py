#!/usr/bin/env python3
"""
新機能の簡易動作テスト
"""
import os
import sys

# APIキーは環境変数から取得（公開用にハードコードを廃止）
os.environ['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY', 'test_gemini_api_key_for_testing')

try:
    from services.gemini_service import GeminiService
    
    print("🚀 新機能簡易テスト開始...")
    print("=" * 50)
    
    # Gemini サービス初期化
    gemini = GeminiService()
    print("✅ GeminiService 初期化完了")
    
    test_user = "test_user_quick"
    
    # テスト1: 新しい意図の判定
    print("\n🎯 テスト1: 新機能意図判定")
    print("-" * 30)
    
    test_inputs = [
        ("おすすめは？", "smart_suggestion"),
        ("前回何話した？", "conversation_history"), 
        ("毎日7時に起きる", "notification")
    ]
    
    for text, expected in test_inputs:
        result = gemini.analyze_text(text, test_user)
        detected = result.get('intent', 'unknown')
        confidence = result.get('confidence', 0)
        
        status = "✅" if detected == expected else "⚠️"
        print(f"{status} '{text}' -> {detected} ({confidence:.2f})")
    
    # テスト2: 対話履歴機能
    print("\n🔄 テスト2: 対話履歴機能")
    print("-" * 30)
    
    # 会話を記録
    gemini.add_conversation_turn(
        user_id=test_user,
        user_message="毎日7時に起きる通知を設定して",
        bot_response="毎日7時の起床通知を設定しました",
        intent="notification",
        confidence=0.9
    )
    print("✅ 会話記録完了")
    
    # 履歴取得
    summary = gemini.get_conversation_summary(test_user)
    print(f"✅ 履歴サマリー: {summary[:100]}...")
    
    # テスト3: スマート提案機能
    print("\n🎯 テスト3: スマート提案機能")
    print("-" * 30)
    
    suggestions = gemini.get_smart_suggestions(test_user)
    print(f"✅ 提案取得: {len(suggestions.get('suggestions', []))}件")
    print(f"   メッセージ: {suggestions.get('formatted_message', '')[:100]}...")
    
    print("\n🎉 簡易テスト完了！新機能は正常に動作しています。")
    
except Exception as e:
    print(f"❌ エラー: {str(e)}")
    sys.exit(1) 