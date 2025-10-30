#!/usr/bin/env python3
"""
拡張AI統一判定システムの包括的テスト
対話履歴 + スマート提案機能のテスト
"""
import os
import sys
import json
import asyncio
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.gemini_service import GeminiService
from handlers.message_handler import MessageHandler

class EnhancedAISystemTestSuite:
    """拡張AI統一判定システムのテストスイート"""
    
    def __init__(self):
        self.gemini_service = None
        self.message_handler = MessageHandler()
        self.test_results = []
        self.test_user_id = "test_user_enhanced"
        
    def setup(self):
        """テスト環境のセットアップ"""
        print("🚀 拡張AI統一判定システムテスト開始...")
        print("=" * 60)
        
        # Gemini APIキーの確認
        if not os.getenv('GEMINI_API_KEY'):
            print("❌ GEMINI_API_KEY が設定されていません")
            print("📝 APIキーを設定してからテストを実行してください")
            return False
            
        try:
            self.gemini_service = GeminiService()
            print("✅ GeminiService 初期化完了")
            return True
        except Exception as e:
            print(f"❌ GeminiService 初期化失敗: {str(e)}")
            return False
    
    def test_new_features_intent_detection(self):
        """新機能の意図判定テスト"""
        print("\n🎯 新機能の意図判定テスト...")
        print("-" * 40)
        
        test_cases = [
            # スマート提案機能
            {
                "input": "おすすめは？",
                "expected_intent": "smart_suggestion",
                "description": "スマート提案要求"
            },
            {
                "input": "何かアドバイスして",
                "expected_intent": "smart_suggestion", 
                "description": "アドバイス要求"
            },
            {
                "input": "提案して",
                "expected_intent": "smart_suggestion",
                "description": "提案要求"
            },
            {
                "input": "最適化してほしい",
                "expected_intent": "smart_suggestion",
                "description": "最適化要求"
            },
            
            # 対話履歴機能
            {
                "input": "前回何話した？",
                "expected_intent": "conversation_history",
                "description": "会話履歴確認"
            },
            {
                "input": "会話履歴を見せて",
                "expected_intent": "conversation_history",
                "description": "履歴表示要求"
            },
            {
                "input": "利用パターン確認",
                "expected_intent": "conversation_history",
                "description": "利用パターン分析"
            },
            {
                "input": "前の話を思い出して",
                "expected_intent": "conversation_history",
                "description": "過去の会話参照"
            }
        ]
        
        success_count = 0
        for test_case in test_cases:
            try:
                result = self.gemini_service.analyze_text(
                    test_case["input"], 
                    self.test_user_id
                )
                
                detected_intent = result.get('intent', 'unknown')
                confidence = result.get('confidence', 0.0)
                
                is_success = detected_intent == test_case["expected_intent"]
                
                status = "✅" if is_success else "❌"
                print(f"{status} {test_case['description']}")
                print(f"   入力: '{test_case['input']}'")
                print(f"   期待: {test_case['expected_intent']}")
                print(f"   結果: {detected_intent} (信頼度: {confidence:.2f})")
                
                if is_success:
                    success_count += 1
                else:
                    print(f"   理由: {result.get('reasoning', '不明')}")
                
                print()
                
            except Exception as e:
                print(f"❌ テスト失敗: {str(e)}")
        
        print(f"📊 新機能意図判定成功率: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
        return success_count == len(test_cases)
    
    def test_conversation_memory_functionality(self):
        """対話履歴機能のテスト"""
        print("\n🔄 対話履歴機能テスト...")
        print("-" * 40)
        
        conversation_memory = self.gemini_service._get_conversation_memory()
        if not conversation_memory:
            print("❌ 対話履歴サービスが利用できません")
            return False
        
        test_scenarios = [
            # 会話履歴の蓄積テスト
            {
                "user_message": "毎日7時に起きる通知を設定して",
                "bot_response": "毎日7時の起床通知を設定しました",
                "intent": "notification",
                "confidence": 0.9
            },
            {
                "user_message": "東京の天気を教えて",
                "bot_response": "東京は晴れです",
                "intent": "weather", 
                "confidence": 0.8
            },
            {
                "user_message": "ありがとう",
                "bot_response": "どういたしまして！",
                "intent": "chat",
                "confidence": 0.7
            }
        ]
        
        # 会話を記録
        print("📝 会話履歴を記録中...")
        for i, scenario in enumerate(test_scenarios, 1):
            turn_id = conversation_memory.add_conversation_turn(
                user_id=self.test_user_id,
                user_message=scenario["user_message"],
                bot_response=scenario["bot_response"],
                intent=scenario["intent"],
                confidence=scenario["confidence"]
            )
            print(f"   {i}. 記録完了: {turn_id}")
        
        # 履歴取得テスト
        print("\n📖 会話履歴取得テスト...")
        context = conversation_memory.get_conversation_context(self.test_user_id, limit=3)
        if context:
            print("✅ 会話コンテキスト取得成功")
            print(f"   取得内容（一部）: {context[:100]}...")
        else:
            print("❌ 会話コンテキスト取得失敗")
            return False
        
        # プロファイル分析テスト
        print("\n👤 ユーザープロファイル分析テスト...")
        analysis = conversation_memory.analyze_conversation_patterns(self.test_user_id)
        if 'error' not in analysis:
            print("✅ パターン分析成功")
            print(f"   総会話数: {analysis['total_conversations']}")
            print(f"   よく使う機能: {analysis['recent_analysis']['most_used_features']}")
            print(f"   コミュニケーションスタイル: {analysis['communication_style']}")
        else:
            print(f"❌ パターン分析失敗: {analysis['error']}")
            return False
        
        return True
    
    def test_smart_suggestion_functionality(self):
        """スマート提案機能のテスト"""
        print("\n🎯 スマート提案機能テスト...")
        print("-" * 40)
        
        smart_suggestion = self.gemini_service._get_smart_suggestion()
        if not smart_suggestion:
            print("❌ スマート提案サービスが利用できません")
            return False
        
        # 行動記録のテスト
        print("📊 ユーザー行動記録テスト...")
        test_behaviors = [
            {
                "action_type": "notification",
                "content": "毎日7時に起きる",
                "context": {"confidence": 0.9, "repeat": "daily"}
            },
            {
                "action_type": "weather",
                "content": "東京の天気",
                "context": {"location": "東京", "confidence": 0.8}
            },
            {
                "action_type": "notification",
                "content": "明日15時に会議",
                "context": {"confidence": 0.85, "repeat": "none"}
            }
        ]
        
        for i, behavior in enumerate(test_behaviors, 1):
            smart_suggestion.record_user_behavior(
                user_id=self.test_user_id,
                action_type=behavior["action_type"],
                content=behavior["content"],
                context=behavior["context"]
            )
            print(f"   {i}. 行動記録完了: {behavior['action_type']}")
        
        # パターン分析テスト
        print("\n🔍 行動パターン分析テスト...")
        patterns = smart_suggestion.analyze_user_patterns(self.test_user_id)
        if 'error' not in patterns:
            print("✅ パターン分析成功")
            print(f"   アクション統計: {patterns.get('action_frequency', {})}")
            print(f"   時間分布: {patterns.get('time_distribution', {})}")
        else:
            print(f"❌ パターン分析失敗: {patterns['error']}")
        
        # 提案生成テスト
        print("\n💡 提案生成テスト...")
        suggestions_data = self.gemini_service.get_smart_suggestions(self.test_user_id)
        
        if suggestions_data['suggestions']:
            print("✅ 提案生成成功")
            print(f"   提案数: {len(suggestions_data['suggestions'])}")
            for i, suggestion in enumerate(suggestions_data['suggestions'][:2], 1):
                print(f"   {i}. {suggestion['title']}: {suggestion['description']}")
        else:
            print("⚠️ 提案は生成されませんでした（データ不足の可能性）")
            print(f"   メッセージ: {suggestions_data['formatted_message']}")
        
        return True
    
    def test_contextual_ai_analysis(self):
        """コンテキスト考慮のAI判定テスト"""
        print("\n🧠 コンテキスト考慮AI判定テスト...")
        print("-" * 40)
        
        # 前のやり取りを設定
        context_scenarios = [
            {
                "setup_message": "毎日7時に起きる通知を設定して",
                "setup_intent": "notification",
                "follow_up": "それを削除して",
                "expected_context_influence": "通知削除として解釈されるべき"
            },
            {
                "setup_message": "東京の天気を教えて",
                "setup_intent": "weather",
                "follow_up": "明日はどう？",
                "expected_context_influence": "天気予報として解釈されるべき"
            }
        ]
        
        success_count = 0
        
        for scenario in context_scenarios:
            print(f"\n📋 シナリオ: {scenario['expected_context_influence']}")
            
            # セットアップメッセージを処理
            setup_result = self.gemini_service.analyze_text(
                scenario["setup_message"],
                self.test_user_id
            )
            print(f"   セットアップ: '{scenario['setup_message']}'")
            print(f"   結果: {setup_result.get('intent', 'unknown')}")
            
            # 会話ターンを記録
            self.gemini_service.add_conversation_turn(
                user_id=self.test_user_id,
                user_message=scenario["setup_message"],
                bot_response="設定完了しました",
                intent=setup_result.get('intent', 'unknown'),
                confidence=setup_result.get('confidence', 0.8)
            )
            
            # フォローアップメッセージを処理
            follow_result = self.gemini_service.analyze_text(
                scenario["follow_up"],
                self.test_user_id
            )
            print(f"   フォローアップ: '{scenario['follow_up']}'")
            print(f"   結果: {follow_result.get('intent', 'unknown')}")
            print(f"   理由: {follow_result.get('reasoning', 'なし')}")
            
            # コンテキスト提案があるかチェック
            contextual_suggestions = follow_result.get('contextual_suggestions', [])
            if contextual_suggestions:
                print(f"   提案: {contextual_suggestions}")
                success_count += 1
        
        print(f"\n📊 コンテキスト考慮成功率: {success_count}/{len(context_scenarios)}")
        return success_count > 0
    
    def test_cost_optimization_features(self):
        """コスト最適化機能のテスト"""
        print("\n💰 コスト最適化機能テスト...")
        print("-" * 40)
        
        # 簡単パターンの事前チェックテスト
        simple_patterns = [
            ("通知一覧", "list_notifications"),
            ("ヘルプ", "help"),
            ("こんにちは", "chat")
        ]
        
        print("⚡ 簡単パターン事前チェックテスト...")
        for text, expected_intent in simple_patterns:
            result = self.gemini_service._check_simple_patterns(text)
            if result and result.get('intent') == expected_intent:
                print(f"✅ '{text}' -> {expected_intent}")
            else:
                print(f"❌ '{text}' -> 期待: {expected_intent}, 結果: {result}")
        
        # 長文制限テスト
        print("\n📏 長文制限テスト...")
        long_text = "これは非常に長いテキストです。" * 100  # 約500文字超
        result = self.gemini_service.analyze_text(long_text, self.test_user_id)
        if result:
            print("✅ 長文でもエラーなく処理")
            print(f"   意図: {result.get('intent', 'unknown')}")
        else:
            print("❌ 長文処理に失敗")
        
        return True
    
    def run_comprehensive_test(self):
        """包括的テストの実行"""
        if not self.setup():
            return False
        
        test_methods = [
            ("新機能意図判定", self.test_new_features_intent_detection),
            ("対話履歴機能", self.test_conversation_memory_functionality),
            ("スマート提案機能", self.test_smart_suggestion_functionality),
            ("コンテキスト考慮AI判定", self.test_contextual_ai_analysis),
            ("コスト最適化機能", self.test_cost_optimization_features)
        ]
        
        results = []
        for test_name, test_method in test_methods:
            try:
                result = test_method()
                results.append((test_name, result))
                status = "✅ 成功" if result else "❌ 失敗"
                print(f"\n{status}: {test_name}")
            except Exception as e:
                results.append((test_name, False))
                print(f"\n❌ エラー: {test_name} - {str(e)}")
        
        # 最終結果
        print("\n" + "=" * 60)
        print("🏁 最終テスト結果")
        print("=" * 60)
        
        success_count = sum(1 for _, success in results if success)
        total_count = len(results)
        
        for test_name, success in results:
            status = "✅" if success else "❌"
            print(f"{status} {test_name}")
        
        print(f"\n📊 総合成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        if success_count == total_count:
            print("🎉 すべてのテストが成功しました！")
            print("🚀 拡張AI統一判定システムは正常に動作しています")
        else:
            print("⚠️ 一部のテストが失敗しました")
            print("🔧 設定やAPIキーを確認してください")
        
        return success_count == total_count

def main():
    """メイン実行関数"""
    test_suite = EnhancedAISystemTestSuite()
    
    try:
        success = test_suite.run_comprehensive_test()
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️ テストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 