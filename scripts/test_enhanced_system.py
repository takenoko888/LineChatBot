#!/usr/bin/env python3
"""
拡張された動的機能生成システムのテストスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.enhanced_semantic_service import EnhancedSemanticAnalyzer, SemanticContext
from services.context_tracking_service import ContextTracker
from services.ambiguity_resolution_service import AmbiguityResolver
from services.enhanced_dynamic_feature_service import EnhancedDynamicFeatureSystem
from datetime import datetime

def test_semantic_analyzer():
    """セマンティック解析機能のテスト"""
    print("🧠 セマンティック解析機能のテスト")
    print("=" * 50)

    analyzer = EnhancedSemanticAnalyzer()

    # テストケース
    test_cases = [
        "毎日の天気予報を自動で通知する機能を作って",
        "なんか天気みたいな機能が欲しい",
        "通知機能を作って",
        "あれと同じような機能が欲しい",
        "リマインダーみたいなの作って",
        "なんか便利な機能を作って",
    ]

    for user_input in test_cases:
        print(f"入力: {user_input}")

        # セマンティックコンテキストの作成
        context = SemanticContext(
            user_id="test_user",
            session_id="test_session",
            timestamp=datetime.now(),
            conversation_history=[],
            user_preferences={},
            recent_topics=[],
            intent_confidence=0.5,
            extracted_entities={}
        )

        # 解析実行
        intent_analysis, entity_extraction, ambiguity_info = analyzer.analyze_semantic_context(user_input, context)

        print(f"  意図: {intent_analysis.primary_intent}")
        print(f"  信頼度: {intent_analysis.confidence_score:.2f}")
        print(f"  緊急度: {intent_analysis.urgency_level}")
        print(f"  機能: {entity_extraction.functions}")
        print(f"  オブジェクト: {entity_extraction.objects}")
        print(f"  曖昧さ: {ambiguity_info.is_ambiguous}")
        if ambiguity_info.ambiguous_terms:
            print(f"  曖昧な用語: {ambiguity_info.ambiguous_terms}")
        print()

def test_context_tracker():
    """コンテキスト追跡機能のテスト"""
    print("📊 コンテキスト追跡機能のテスト")
    print("=" * 50)

    tracker = ContextTracker()

    user_id = "test_user"
    test_inputs = [
        "毎日の天気予報を自動で通知する機能を作って",
        "東京の天気を知らせて",
        "明日の天気も教えて",
        "週間天気予報が欲しい",
    ]

    for user_input in test_inputs:
        print(f"入力: {user_input}")

        # コンテキスト追跡
        semantic_analysis = {
            'primary_intent': 'create_function',
            'confidence_score': 0.8,
            'entities': {
                'functions': ['weather_notification'],
                'locations': ['tokyo']
            }
        }

        context_window = tracker.track_context(user_id, user_input, semantic_analysis, "OK")

        print(f"  コンテキストスコア: {context_window.context_score:.2f}")
        print(f"  現在のトピック: {context_window.current_topics}")
        print(f"  アクティブ機能: {context_window.active_features}")
        print()

    # ユーザー行動パターンの確認
    user_patterns = tracker.get_user_patterns(user_id)
    if user_patterns:
        print("📈 ユーザー行動パターン:")
        print(f"  よく使う意図: {dict(user_patterns.frequent_intents)}")
        print(f"  好みの機能: {user_patterns.preferred_functions}")
        print(f"  好みの時間帯: {user_patterns.preferred_times}")

def test_ambiguity_resolver():
    """曖昧さ解消機能のテスト"""
    print("🤔 曖昧さ解消機能のテスト")
    print("=" * 50)

    resolver = AmbiguityResolver()
    tracker = ContextTracker()

    user_id = "test_user"
    test_inputs = [
        "なんか天気みたいな機能が欲しい",
        "あれと同じような機能を作って",
        "便利な機能を作って",
        "なんか通知みたいなの",
    ]

    for user_input in test_inputs:
        print(f"入力: {user_input}")

        # セマンティック解析（簡易版）
        semantic_analysis = {
            'primary_intent': 'create_function',
            'confidence_score': 0.3,
            'entities': {
                'functions': [],
                'objects': []
            },
            'is_ambiguous': True
        }

        # 曖昧さ解消
        resolution, clarification_requests = resolver.resolve_ambiguity(
            user_input, semantic_analysis, tracker, user_id
        )

        print(f"  解消意図: {resolution.resolved_intent}")
        print(f"  解消信頼度: {resolution.confidence_score:.2f}")
        print(f"  追加情報必要: {resolution.additional_info_needed}")

        if clarification_requests:
            print("  明確化質問:")
            for req in clarification_requests:
                for question in req.questions:
                    print(f"    • {question}")

        print()

def test_enhanced_system():
    """拡張システム全体のテスト"""
    print("🚀 拡張システム全体のテスト")
    print("=" * 50)

    # モックGeminiサービス
    class MockGeminiService:
        def generate_content(self, prompt):
            if "機能名" in prompt:
                return '''
                {
                    "functionality": "天気情報提供",
                    "function_name": "weather_info_enhanced",
                    "description": "拡張された天気情報提供機能",
                    "parameters": [
                        {
                            "name": "location",
                            "type": "string",
                            "required": true,
                            "description": "場所の名前"
                        }
                    ],
                    "trigger_conditions": ["天気", "weather"],
                    "return_type": "text",
                    "dependencies": ["requests"],
                    "priority": 3
                }
                '''
            elif "コードを生成" in prompt:
                return '''
import requests
from typing import Dict, Any

def weather_info_enhanced(parameters: Dict[str, Any]) -> str:
    """拡張された天気情報提供機能"""
    try:
        location = parameters.get('location', '東京')
        return f"🌤️ {location}の天気情報:\\n現在は晴れで、気温は22℃です。\\n（拡張版テストデータ）"
    except Exception as e:
        return f"天気情報の取得に失敗しました: {str(e)}"
'''
            else:
                return '{"functionality": "デフォルト機能", "function_name": "default_enhanced"}'

    try:
        system = EnhancedDynamicFeatureSystem(MockGeminiService())

        test_input = "毎日の天気予報を自動で通知する機能を作って"
        user_id = "test_user"

        print(f"機能生成テスト: {test_input}")

        # 機能生成
        feature = system.create_feature_from_request(test_input, user_id)

        print("✅ 機能生成成功!")
        print(f"  機能名: {feature.name}")
        print(f"  説明: {feature.description}")
        print(f"  セマンティック信頼度: {feature.code.semantic_confidence}")
        print(f"  コンテキスト関連度: {feature.code.context_relevance}")

        # 機能実行テスト
        print("\n🔧 機能実行テスト:")
        result = system.execute_feature(feature.feature_id, {'location': '大阪'})
        print(f"  実行結果: {result.get('result', '実行失敗')}")

        # 機能一覧テスト
        print("\n📋 機能一覧テスト:")
        features = system.list_features(user_id)
        print(f"  登録機能数: {len(features)}")
        for f in features:
            print(f"  - {f['name']}: {f.get('semantic_confidence', 'N/A')}")

    except Exception as e:
        print(f"❌ システムテスト失敗: {str(e)}")

def main():
    """メイン実行関数"""
    print("🧪 拡張された動的機能生成システムのテスト")
    print("=" * 60)

    try:
        # 各コンポーネントのテスト
        test_semantic_analyzer()
        test_context_tracker()
        test_ambiguity_resolver()
        test_enhanced_system()

        print("\n🎉 すべてのテストが完了しました！")
        print("\nシステムの特徴:")
        print("✅ セマンティック解析の強化")
        print("✅ コンテキスト追跡機能")
        print("✅ 曖昧さ解消機能")
        print("✅ 既存システムとの統合")
        print("✅ 詳細な解析情報提供")

    except Exception as e:
        print(f"❌ テスト実行エラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
