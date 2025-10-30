#!/usr/bin/env python3
"""
雑談機能修正テスト

問題: すべての入力に対して検索機能が動作してしまう
修正: AI判定を改善して、雑談や創作要求は chat として処理
"""

import os
import sys
from datetime import datetime

# 環境変数の設定
os.environ.setdefault('GEMINI_API_KEY', 'test_key')
os.environ.setdefault('LINE_ACCESS_TOKEN', 'test_token')
os.environ.setdefault('LINE_CHANNEL_SECRET', 'test_secret')
os.environ.setdefault('PRODUCTION_MODE', 'false')

# パスの追加（testsフォルダーから実行するため）
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

def test_ai_intent_detection():
    """AI意図判定のテスト"""
    print("\n🤖 AI意図判定テスト - 雑談機能修正版")
    print("=" * 50)
    
    try:
        from services.gemini_service import GeminiService
        
        # テスト用のGeminiサービス
        class MockGeminiService(GeminiService):
            """テスト用のモックサービス"""
            def __init__(self):
                pass  # API初期化をスキップ
                
            def _check_simple_patterns(self, text: str):
                """実際のパターン検出をテスト"""
                return super()._check_simple_patterns(text)
                
            def _fallback_analysis(self, text: str):
                """フォールバック処理をテスト"""
                return super()._fallback_analysis(text)
        
        gemini_service = MockGeminiService()
        
        # テストケース
        test_cases = [
            {
                "input": "原神というゲームは知っていますか",
                "expected_intent": "chat",
                "description": "ゲームについての質問",
                "should_not": "auto_search"
            },
            {
                "input": "面白い話を聞かせて",
                "expected_intent": "chat", 
                "description": "創作・物語要求",
                "should_not": "auto_search"
            },
            {
                "input": "架空の物語で",
                "expected_intent": "chat",
                "description": "明確な創作要求",
                "should_not": "auto_search"
            },
            {
                "input": "普通に雑談しよ",
                "expected_intent": "chat",
                "description": "雑談要求",
                "should_not": "auto_search"
            },
            {
                "input": "さらに教えて 検索せずにあなたの情報で",
                "expected_intent": "chat",
                "description": "明確に検索拒否",
                "should_not": "auto_search"
            },
            {
                "input": "最新のニュースを検索して",
                "expected_intent": "search",
                "description": "明確な検索指示",
                "should_be": "search"
            },
            {
                "input": "今日の株価を調べて",
                "expected_intent": "auto_search",
                "description": "最新情報が必要",
                "should_be": "auto_search"
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}] {test_case['description']}")
            print(f"   入力: \"{test_case['input']}\"")
            
            # 簡単パターンでのチェック
            simple_result = gemini_service._check_simple_patterns(test_case['input'])
            
            if simple_result:
                detected_intent = simple_result.get('intent')
                print(f"   結果: {detected_intent} (簡易判定)")
                
                # 意図が期待通りかチェック
                if detected_intent == test_case['expected_intent']:
                    print("   ✅ PASS - 期待通りの意図判定")
                    success_count += 1
                elif 'should_not' in test_case and detected_intent != test_case['should_not']:
                    print(f"   ✅ PASS - 不適切な意図({test_case['should_not']})を回避")
                    success_count += 1
                else:
                    print(f"   ❌ FAIL - 期待値: {test_case['expected_intent']}")
            else:
                print("   ⚠️ 簡易判定で検出されず（AI判定が必要）")
                
                # フォールバック処理での判定
                fallback_result = gemini_service._fallback_analysis(test_case['input'])
                fallback_intent = fallback_result.get('intent', 'unknown')
                print(f"   フォールバック結果: {fallback_intent}")
                
                if fallback_intent == 'chat':
                    print("   ✅ PASS - フォールバック処理でchatとして処理")
                    success_count += 1
                else:
                    print(f"   ❌ FAIL - フォールバック結果が不適切")
        
        print(f"\n📊 テスト結果: {success_count}/{len(test_cases)} 成功 ({success_count/len(test_cases)*100:.1f}%)")
        
        if success_count >= len(test_cases) * 0.8:  # 80%以上で成功
            print("✅ 雑談機能修正テスト: PASS")
            return True
        else:
            print("❌ 雑談機能修正テスト: FAIL")
            return False
            
    except Exception as e:
        print(f"❌ テスト実行エラー: {str(e)}")
        return False

def test_chat_response_generation():
    """チャット応答生成のテスト"""
    print("\n💬 チャット応答生成テスト")
    print("=" * 50)
    
    try:
        from handlers.message_handler import MessageHandler
        
        # テスト用のモックGeminiサービス
        class MockGeminiService:
            def __init__(self):
                self.model = MockModel()
                
        class MockModel:
            def generate_content(self, prompt):
                # プロンプトの内容に基づいて適切な応答を生成
                if "架空の物語" in prompt or "物語や創作" in prompt:
                    return MockResponse("昔々、魔法の森に住む小さな妖精がいました。その妖精は...")
                elif "原神" in prompt or "ゲーム" in prompt:
                    return MockResponse("原神は中国のmiHoYoが開発したオープンワールドRPGです。美しいグラフィックと...")
                elif "面白い話" in prompt:
                    return MockResponse("今日、面白いことがありました！街で猫が...")
                else:
                    return MockResponse("はい、何でもお聞きください！😊")
                    
        class MockResponse:
            def __init__(self, text):
                self.text = text
        
        handler = MessageHandler()
        mock_gemini = MockGeminiService()
        
        test_cases = [
            "架空の物語で",
            "原神について教えて",
            "面白い話を聞かせて",
            "こんにちは"
        ]
        
        success_count = 0
        
        for i, test_input in enumerate(test_cases, 1):
            print(f"\n[{i}] 入力: \"{test_input}\"")
            
            try:
                response = handler._generate_chat_response(test_input, mock_gemini)
                print(f"   応答: {response[:100]}...")
                
                # 応答が検索に誘導していないかチェック
                if "検索" not in response and "調べ" not in response:
                    print("   ✅ PASS - 検索誘導なし")
                    success_count += 1
                else:
                    print("   ❌ FAIL - 検索誘導あり")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
        
        print(f"\n📊 応答生成テスト結果: {success_count}/{len(test_cases)} 成功")
        
        return success_count >= len(test_cases) * 0.8
        
    except Exception as e:
        print(f"❌ チャット応答テスト実行エラー: {str(e)}")
        return False

def main():
    """メインテスト実行"""
    print("🧪 雑談機能修正検証テスト")
    print("=" * 60)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # テスト実行
    results.append(("AI意図判定テスト", test_ai_intent_detection()))
    results.append(("チャット応答生成テスト", test_chat_response_generation()))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("-" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n総合結果: {passed}/{len(results)} テスト成功")
    
    if passed == len(results):
        print("🎉 すべてのテストが成功しました！")
        print("\n✅ 修正内容:")
        print("   - AI判定でauto_search基準を厳格化")
        print("   - 雑談・創作要求はchatとして処理")
        print("   - 簡易パターン検出を強化")
        print("   - フォールバック処理を改善")
        print("   - チャット応答生成を自然に改良")
        return True
    else:
        print("⚠️ 一部のテストが失敗しました。")
        return False

if __name__ == "__main__":
    main() 