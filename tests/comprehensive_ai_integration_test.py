"""
AI機能統合テスト - AIがすべての既存機能に完璧に対応できるかを検証
"""
import os
import sys
import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import asyncio

# パス/環境変数設定
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 環境変数設定
os.environ['MOCK_MODE'] = 'true'
os.environ['SKIP_CONFIG_VALIDATION'] = 'true'
os.environ.setdefault('GEMINI_MOCK', 'true')

# テスト用のモックデータ
MOCK_WEATHER_RESPONSE = {
    "weather": {
        "location": "東京",
        "temperature": "22°C",
        "condition": "晴れ",
        "note": "テスト用モックデータ"
    }
}

MOCK_SEARCH_RESPONSE = {
    "search": {
        "query": "テストクエリ",
        "results": ["検索結果1", "検索結果2", "検索結果3"],
        "note": "テスト用モックデータ"
    }
}

MOCK_NOTIFICATION_RESPONSE = {
    "notification": {
        "message": "テスト通知",
        "status": "created",
        "id": "test_notif_001"
    }
}

class TestAIFunctionIntegration(unittest.TestCase):
    """AI機能統合テスト"""

    def setUp(self):
        """テスト前の準備"""
        try:
            # 必要なサービスをインポート
            from services.flexible_ai_service import flexible_ai_service
            from services.context_aware_router import context_aware_router
            from services.service_integration_manager import service_integration_manager
            from services.integrated_service_manager import integrated_service_manager
            from services.ai_function_plugin import ai_function_registry

            self.ai_service = flexible_ai_service
            self.router = context_aware_router
            self.service_manager = service_integration_manager
            self.integrated_manager = integrated_service_manager
            self.function_registry = ai_function_registry

            # 利用可能な機能を取得
            self.available_functions = self.ai_service._get_available_ai_functions()

            print(f"✅ セットアップ完了 - AI機能数: {len(self.available_functions)}")

        except Exception as e:
            self.fail(f"セットアップエラー: {e}")

    def test_01_available_functions(self):
        """利用可能なAI機能の確認"""
        print("\n🧪 テスト1: 利用可能なAI機能の確認")

        # 最低限必要な機能が存在することを確認
        function_names = [func['name'] for func in self.available_functions]

        required_functions = [
            'notification_handler',
            'weather_handler',
            'search_handler',
            'auto_task_handler',
            'math_calculator',
            'translator',
            'daily_fortune',
            'code_executor'
        ]

        for func_name in required_functions:
            self.assertIn(func_name, function_names,
                         f"必須機能 '{func_name}' が見つかりません")

        print(f"✅ 必須機能 {len(required_functions)} 個すべて存在")
        print(f"   利用可能な機能: {function_names}")

    def test_02_notification_functions(self):
        """通知機能のテスト"""
        print("\n🧪 テスト2: 通知機能のテスト")

        test_cases = [
            "今日の18時にミーティングを通知して",
            "毎朝7時に天気予報を教えて",
            "今週金曜日の15時にリマインダー設定して",
            "今日の夜に買い物の通知を設定して"
        ]

        for query in test_cases:
            print(f"   クエリ: {query}")
            try:
                analysis = self.router._analyze_intent_sync(query, {})
                self.assertIn("notification", analysis.primary_service,
                             f"通知クエリが正しく解析されませんでした: {query}")

                # 複合要素を含むクエリの場合
                elements = analysis.context_info.get('detected_elements', [])
                if len(elements) > 1:
                    self.assertIn("composite_task", analysis.intent_type,
                                 f"複合クエリが正しく判定されませんでした: {query}")

                print(f"   ✅ 解析結果: {analysis.intent_type} (信頼度: {analysis.confidence:.2f})")

            except Exception as e:
                self.fail(f"通知機能テストエラー: {e}")

    def test_03_weather_functions(self):
        """天気機能のテスト"""
        print("\n🧪 テスト3: 天気機能のテスト")

        test_cases = [
            "今日の天気を教えて",
            "東京の天気予報は？",
            "明日の気温を知りたい",
            "大阪の天気はどう？"
        ]

        for query in test_cases:
            print(f"   クエリ: {query}")
            try:
                analysis = self.router._analyze_intent_sync(query, {})
                self.assertIn("weather", analysis.primary_service,
                             f"天気クエリが正しく解析されませんでした: {query}")

                print(f"   ✅ 解析結果: {analysis.intent_type} (信頼度: {analysis.confidence:.2f})")

            except Exception as e:
                self.fail(f"天気機能テストエラー: {e}")

    def test_04_search_functions(self):
        """検索機能のテスト"""
        print("\n🧪 テスト4: 検索機能のテスト")

        test_cases = [
            "Pythonの使い方を調べて",
            "最新のニュースを教えて",
            "AIについて検索して",
            "明日のイベント情報を探して"
        ]

        for query in test_cases:
            print(f"   クエリ: {query}")
            try:
                analysis = self.router._analyze_intent_sync(query, {})
                self.assertIn("search", analysis.primary_service,
                             f"検索クエリが正しく解析されませんでした: {query}")

                print(f"   ✅ 解析結果: {analysis.intent_type} (信頼度: {analysis.confidence:.2f})")

            except Exception as e:
                self.fail(f"検索機能テストエラー: {e}")

    def test_05_math_functions(self):
        """数学計算機能のテスト"""
        print("\n🧪 テスト5: 数学計算機能のテスト")

        test_cases = [
            "2 + 3 × 4 を計算して",
            "100 ÷ 5 は？",
            "√16 はいくつ？",
            "5^2 を計算して"
        ]

        for query in test_cases:
            print(f"   クエリ: {query}")
            try:
                analysis = self.router._analyze_intent_sync(query, {})
                # 数学計算はAIが直接処理するか、複合タスクとして処理される
                self.assertTrue(
                    analysis.intent_type in ["general", "composite_task"] or
                    analysis.requires_ai_assistance,
                    f"数学クエリが正しく解析されませんでした: {query}"
                )

                print(f"   ✅ 解析結果: {analysis.intent_type} (信頼度: {analysis.confidence:.2f})")

            except Exception as e:
                self.fail(f"数学機能テストエラー: {e}")

    def test_06_translation_functions(self):
        """翻訳機能のテスト"""
        print("\n🧪 テスト6: 翻訳機能のテスト")

        test_cases = [
            "Helloを日本語に翻訳して",
            "今日は英語で何て言うの？",
            "ありがとうを英語で",
            "I love you を日本語で"
        ]

        for query in test_cases:
            print(f"   クエリ: {query}")
            try:
                analysis = self.router._analyze_intent_sync(query, {})
                # 翻訳はAIが直接処理するか、複合タスクとして処理される
                self.assertTrue(
                    analysis.intent_type in ["general", "composite_task"] or
                    analysis.requires_ai_assistance,
                    f"翻訳クエリが正しく解析されませんでした: {query}"
                )

                print(f"   ✅ 解析結果: {analysis.intent_type} (信頼度: {analysis.confidence:.2f})")

            except Exception as e:
                self.fail(f"翻訳機能テストエラー: {e}")

    def test_07_composite_queries(self):
        """複合クエリのテスト"""
        print("\n🧪 テスト7: 複合クエリのテスト")

        test_cases = [
            "毎日6時に天気とニュースを確認して通知して",
            "毎朝7時に今日の運勢と天気予報を教えて",
            "今週末の天気とイベントを調べて通知設定して",
            "毎日の天気とニュースをまとめて教えて"
        ]

        for query in test_cases:
            print(f"   クエリ: {query}")
            try:
                analysis = self.router._analyze_intent_sync(query, {})

                # 複合クエリとして検出されることを確認
                elements = analysis.context_info.get('detected_elements', [])
                self.assertGreater(len(elements), 1,
                                  f"複合クエリが正しく検出されませんでした: {query}")

                self.assertIn("composite_task", analysis.intent_type,
                             f"複合クエリが正しく判定されませんでした: {query}")

                print(f"   ✅ 検出要素: {elements}")
                print(f"   ✅ 解析結果: {analysis.intent_type} (信頼度: {analysis.confidence:.2f})")

            except Exception as e:
                self.fail(f"複合クエリテストエラー: {e}")

    def test_08_error_handling(self):
        """エラーハンドリングのテスト"""
        print("\n🧪 テスト8: エラーハンドリングのテスト")

        test_cases = [
            "asdfjkl;",  # 意味不明なクエリ
            "",  # 空のクエリ
            "   ",  # 空白のみ
            "機能がないクエリ"
        ]

        for query in test_cases:
            print(f"   クエリ: '{query}'")
            try:
                analysis = self.router._analyze_intent_sync(query, {})
                # エラーハンドリングとしてフォールバックが機能することを確認
                self.assertIsNotNone(analysis,
                                   f"エラーハンドリングが機能していません: {query}")

                print(f"   ✅ フォールバック処理: {analysis.intent_type} (信頼度: {analysis.confidence:.2f})")

            except Exception as e:
                self.fail(f"エラーハンドリングテストエラー: {e}")

    def test_09_ai_response_generation(self):
        """AI応答生成のテスト"""
        print("\n🧪 テスト9: AI応答生成のテスト")

        test_cases = [
            "今日の運勢を教えて",
            "簡単な計算をして：10 + 5",
            "こんにちは",
            "ありがとう"
        ]

        for query in test_cases:
            print(f"   クエリ: {query}")
            try:
                # モックモードでの応答生成をテスト
                response = self.ai_service.generate_flexible_response_sync(
                    query, "test_user", {"test": True}
                )

                self.assertIsInstance(response, str,
                                     f"応答が文字列ではありません: {query}")
                self.assertGreater(len(response), 0,
                                  f"空の応答が返されました: {query}")

                print(f"   ✅ 応答生成成功 (文字数: {len(response)})")

            except Exception as e:
                self.fail(f"AI応答生成テストエラー: {e}")

    def test_10_function_categories(self):
        """機能カテゴリのテスト"""
        print("\n🧪 テスト10: 機能カテゴリのテスト")

        categories = {}
        for func in self.available_functions:
            category = func['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(func['name'])

        # カテゴリ別の機能数を確認
        expected_categories = {
            '通知': ['notification_handler'],
            '天気': ['weather_handler'],
            '検索': ['search_handler'],
            'タスク': ['auto_task_handler'],
            '計算': ['math_calculator'],
            '翻訳': ['translator'],
            'その他': ['daily_fortune', 'code_executor']
        }

        for category, expected_funcs in expected_categories.items():
            self.assertIn(category, categories,
                         f"カテゴリ '{category}' が見つかりません")

            actual_funcs = categories[category]
            for func in expected_funcs:
                self.assertIn(func, actual_funcs,
                             f"機能 '{func}' がカテゴリ '{category}' に含まれていません")

        print("   ✅ カテゴリ別機能確認:")
        for category, funcs in categories.items():
            print(f"     {category}: {len(funcs)} 個 - {funcs}")

def run_comprehensive_test():
    """包括的なテスト実行"""
    print("🚀 AI機能統合テスト開始")
    print("=" * 60)

    # テストスイート作成
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAIFunctionIntegration)

    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print(f"実行テスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")

    if result.failures:
        print("\n❌ 失敗したテスト:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print("\n💥 エラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"  - {test}")

    # 最終判定
    if result.wasSuccessful():
        print("\n🎉 すべてのテストが成功しました！")
        print("✅ AIがすべての既存機能に完璧に対応できています！")
        return True
    else:
        print("\n⚠️  一部のテストが失敗しました")
        print("🔧 AI対応に改善が必要な箇所があります")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
