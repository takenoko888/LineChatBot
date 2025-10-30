#!/usr/bin/env python3
"""
統一AI判定システムの包括的テストスクリプト
"""
import os
import sys
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.gemini_service import GeminiService
from services.notification_service import NotificationService
from handlers.message_handler import MessageHandler

class UnifiedAITestSuite:
    """統一AI判定システムのテストスイート"""
    
    def __init__(self):
        self.gemini_service = None
        self.notification_service = None
        self.message_handler = MessageHandler()
        self.test_results = []
        
    def setup(self):
        """テスト環境のセットアップ"""
        print("🔧 テスト環境をセットアップ中...")
        
        # Gemini APIキーの確認
        if not os.getenv('GEMINI_API_KEY'):
            print("❌ GEMINI_API_KEY が設定されていません")
            return False
            
        try:
            self.gemini_service = GeminiService()
            self.notification_service = NotificationService(
                storage_path="/tmp/test_unified_notifications.json",
                gemini_service=self.gemini_service
            )
            print("✅ セットアップ完了")
            return True
        except Exception as e:
            print(f"❌ セットアップ失敗: {str(e)}")
            return False
    
    def test_intent_detection(self):
        """意図判定のテスト"""
        print("\n🎯 意図判定テスト開始...")
        
        test_cases = [
            # 通知関連
            {
                "input": "毎日7時に起きる",
                "expected_intent": "notification",
                "description": "通知設定"
            },
            {
                "input": "通知一覧",
                "expected_intent": "list_notifications", 
                "description": "通知一覧表示"
            },
            {
                "input": "全通知削除",
                "expected_intent": "delete_all_notifications",
                "description": "全通知削除"
            },
            
            # 天気関連
            {
                "input": "東京の天気は？",
                "expected_intent": "weather",
                "description": "天気情報"
            },
            {
                "input": "明日の天気予報",
                "expected_intent": "weather", 
                "description": "天気予報"
            },
            
            # 検索関連
            {
                "input": "Python について検索",
                "expected_intent": "search",
                "description": "明示的検索"
            },
            {
                "input": "最新のニュースは？",
                "expected_intent": "auto_search",
                "description": "AI自動検索"
            },
            {
                "input": "話題の映画について教えて",
                "expected_intent": "auto_search",
                "description": "AI自動検索（知識要求）"
            },
            
            # その他
            {
                "input": "ヘルプ",
                "expected_intent": "help",
                "description": "ヘルプ表示"
            },
            {
                "input": "こんにちは",
                "expected_intent": "chat",
                "description": "一般的な会話"
            }
        ]
        
        passed = 0
        total = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{total}] テスト: {test_case['description']}")
            print(f"   入力: \"{test_case['input']}\"")
            
            try:
                # AI判定を実行
                analysis = self.gemini_service.analyze_text(test_case['input'])
                actual_intent = analysis.get('intent', 'unknown')
                confidence = analysis.get('confidence', 0.0)
                
                print(f"   AI判定: {actual_intent} (信頼度: {confidence:.2f})")
                print(f"   期待値: {test_case['expected_intent']}")
                
                # 結果判定
                if actual_intent == test_case['expected_intent']:
                    print("   ✅ PASS")
                    passed += 1
                    status = "PASS"
                else:
                    print("   ❌ FAIL")
                    status = "FAIL"
                    
                # 結果記録
                self.test_results.append({
                    "test": test_case['description'],
                    "input": test_case['input'],
                    "expected": test_case['expected_intent'],
                    "actual": actual_intent,
                    "confidence": confidence,
                    "status": status
                })
                
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
                self.test_results.append({
                    "test": test_case['description'],
                    "input": test_case['input'],
                    "expected": test_case['expected_intent'],
                    "actual": "ERROR",
                    "error": str(e),
                    "status": "ERROR"
                })
        
        print(f"\n🎯 意図判定テスト結果: {passed}/{total} 成功 ({passed/total*100:.1f}%)")
        return passed, total
    
    def test_parameter_extraction(self):
        """パラメータ抽出のテスト"""
        print("\n🔍 パラメータ抽出テスト開始...")
        
        test_cases = [
            {
                "input": "明日の15時に会議",
                "expected_intent": "notification",
                "check_params": ["notification"],
                "description": "通知パラメータ抽出"
            },
            {
                "input": "大阪の天気は？", 
                "expected_intent": "weather",
                "check_params": ["location"],
                "description": "地名パラメータ抽出"
            },
            {
                "input": "機械学習について検索",
                "expected_intent": "search",
                "check_params": ["query"],
                "description": "検索クエリ抽出"
            }
        ]
        
        passed = 0
        total = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{total}] テスト: {test_case['description']}")
            print(f"   入力: \"{test_case['input']}\"")
            
            try:
                analysis = self.gemini_service.analyze_text(test_case['input'])
                intent = analysis.get('intent', 'unknown')
                
                if intent == test_case['expected_intent']:
                    # パラメータの存在確認
                    params_found = all(param in analysis for param in test_case['check_params'])
                    
                    print(f"   意図: {intent} ✅")
                    print(f"   パラメータ: {test_case['check_params']} {'✅' if params_found else '❌'}")
                    
                    if params_found:
                        for param in test_case['check_params']:
                            print(f"     {param}: {analysis.get(param, 'N/A')}")
                        passed += 1
                        print("   ✅ PASS")
                    else:
                        print("   ❌ FAIL - パラメータが不足")
                else:
                    print(f"   ❌ FAIL - 意図が不正確: {intent}")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
        
        print(f"\n🔍 パラメータ抽出テスト結果: {passed}/{total} 成功 ({passed/total*100:.1f}%)")
        return passed, total
    
    def test_message_handler_integration(self):
        """メッセージハンドラー統合テスト"""
        print("\n🔗 メッセージハンドラー統合テスト開始...")
        
        # モックイベントクラス
        class MockMessage:
            def __init__(self, text):
                self.text = text
                
        class MockSource:
            def __init__(self):
                self.user_id = "test_user_123"
                
        class MockEvent:
            def __init__(self, text):
                self.message = MockMessage(text)
                self.source = MockSource()
        
        test_cases = [
            {
                "input": "ヘルプ",
                "description": "ヘルプ機能テスト"
            },
            {
                "input": "こんにちは",
                "description": "チャット機能テスト"
            },
            {
                "input": "通知一覧",
                "description": "通知一覧機能テスト"
            }
        ]
        
        passed = 0
        total = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{total}] テスト: {test_case['description']}")
            print(f"   入力: \"{test_case['input']}\"")
            
            try:
                event = MockEvent(test_case['input'])
                response, quick_reply = self.message_handler.handle_message(
                    event, 
                    self.gemini_service,
                    self.notification_service
                )
                
                if response and len(response) > 0:
                    print(f"   応答: {response[:100]}{'...' if len(response) > 100 else ''}")
                    print("   ✅ PASS")
                    passed += 1
                else:
                    print("   ❌ FAIL - 空の応答")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
        
        print(f"\n🔗 統合テスト結果: {passed}/{total} 成功 ({passed/total*100:.1f}%)")
        return passed, total
    
    def test_fallback_mechanisms(self):
        """フォールバック機能のテスト"""
        print("\n🛡️ フォールバック機能テスト開始...")
        
        # 壊れたGeminiServiceをモック
        class BrokenGeminiService:
            def analyze_text(self, text):
                raise Exception("Simulated API failure")
                
            def model(self):
                raise Exception("Model unavailable")
        
        broken_gemini = BrokenGeminiService()
        
        # モックイベント
        class MockMessage:
            def __init__(self, text):
                self.text = text
                
        class MockSource:
            def __init__(self):
                self.user_id = "test_user_123"
                
        class MockEvent:
            def __init__(self, text):
                self.message = MockMessage(text)
                self.source = MockSource()
        
        test_cases = [
            "ヘルプ",
            "通知一覧", 
            "こんにちは",
            "何らかの質問"
        ]
        
        passed = 0
        total = len(test_cases)
        
        for i, test_input in enumerate(test_cases, 1):
            print(f"\n[{i}/{total}] フォールバックテスト: \"{test_input}\"")
            
            try:
                event = MockEvent(test_input)
                response, quick_reply = self.message_handler.handle_message(
                    event,
                    broken_gemini,
                    self.notification_service
                )
                
                if response and "エラー" in response:
                    print("   ✅ PASS - エラーメッセージを適切に返却")
                    passed += 1
                elif response:
                    print("   ✅ PASS - 何らかの応答を返却")
                    passed += 1
                else:
                    print("   ❌ FAIL - 応答なし")
                    
            except Exception as e:
                print(f"   ❌ CRITICAL ERROR - 例外が発生: {str(e)}")
        
        print(f"\n🛡️ フォールバックテスト結果: {passed}/{total} 成功 ({passed/total*100:.1f}%)")
        return passed, total
    
    def generate_report(self):
        """テストレポートの生成"""
        print("\n📊 テストレポート生成中...")
        
        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "passed": len([r for r in self.test_results if r['status'] == 'PASS']),
                "failed": len([r for r in self.test_results if r['status'] == 'FAIL']),
                "errors": len([r for r in self.test_results if r['status'] == 'ERROR'])
            },
            "detailed_results": self.test_results
        }
        
        # レポートファイルに保存
        with open('unified_ai_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print("✅ レポートを unified_ai_test_report.json に保存しました")
        return report
    
    def run_all_tests(self):
        """全テストの実行"""
        print("🚀 統一AI判定システム包括テスト開始\n")
        
        if not self.setup():
            return False
        
        total_passed = 0
        total_tests = 0
        
        # 各テストの実行
        tests = [
            self.test_intent_detection,
            self.test_parameter_extraction, 
            self.test_message_handler_integration,
            self.test_fallback_mechanisms
        ]
        
        for test_func in tests:
            try:
                passed, total = test_func()
                total_passed += passed
                total_tests += total
            except Exception as e:
                print(f"❌ テスト実行エラー: {str(e)}")
        
        # 最終結果
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*50}")
        print(f"🎯 統一AI判定システム テスト結果")
        print(f"{'='*50}")
        print(f"✅ 成功: {total_passed}/{total_tests} ({success_rate:.1f}%)")
        print(f"{'✅ テスト合格' if success_rate >= 80 else '❌ 改善が必要'}")
        
        # レポート生成
        self.generate_report()
        
        return success_rate >= 80

def main():
    """メイン実行関数"""
    test_suite = UnifiedAITestSuite()
    success = test_suite.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 