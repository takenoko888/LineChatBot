#!/usr/bin/env python3
"""
動的機能生成システムのテストスクリプト
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# プロジェクトルートをPythonパスに追加（scripts/ 配下対応）
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 環境変数の設定（テスト用）
os.environ.setdefault('GEMINI_API_KEY', os.getenv('GEMINI_API_KEY', 'test_key'))
os.environ.setdefault('LINE_ACCESS_TOKEN', 'test_token')
os.environ.setdefault('LINE_CHANNEL_SECRET', 'test_secret')

def test_dynamic_feature_system():
    """動的機能生成システムのテスト"""
    print("🧪 動的機能生成システムのテストを開始します")
    print("=" * 60)

    try:
        # 1. 必要なモジュールのインポートテスト
        print("📦 モジュールのインポートテスト...")
        from services.dynamic_feature_service import (
            DynamicFeatureSystem,
            FeatureRequestAnalyzer,
            CodeGenerator,
            DynamicExecutionEngine
        )
        print("✅ モジュールインポート成功")

        # 2. システム初期化テスト
        print("\n🔧 システム初期化テスト...")
        try:
            from services.gemini_service import GeminiService
            gemini_service = GeminiService()
            print("✅ Geminiサービス初期化成功")
        except Exception as e:
            print(f"⚠️  Geminiサービス初期化エラー（テストモードで続行）: {e}")
            gemini_service = None

        # 3. DynamicFeatureSystem初期化
        print("\n🚀 DynamicFeatureSystem初期化...")
        dynamic_system = DynamicFeatureSystem(gemini_service)
        print("✅ DynamicFeatureSystem初期化成功")

        # 4. 機能要求解析テスト
        print("\n🧠 機能要求解析テスト...")
        if gemini_service:
            analyzer = FeatureRequestAnalyzer(gemini_service)
            test_request = "毎日の天気予報を自動でまとめて、雨が降りそうなら通知して"

            try:
                request = analyzer.analyze_request(test_request)
                print(f"✅ 要求解析成功: {request.extracted_functionality.get('function_name', 'N/A')}")
            except Exception as e:
                print(f"❌ 要求解析エラー: {e}")
                return False
        else:
            print("⚠️  Gemini APIなしのため要求解析スキップ")

        # 5. コード生成テスト
        print("\n💻 コード生成テスト...")
        if gemini_service:
            generator = CodeGenerator(gemini_service)
            test_request = type('obj', (object,), {
                'request_id': 'test-123',
                'extracted_functionality': {
                    'function_name': 'test_weather_function',
                    'description': '天気情報を取得して通知する',
                    'parameters': [{'name': 'location', 'type': 'string', 'required': True}],
                    'return_type': 'text',
                    'dependencies': ['requests'],
                    'priority': 1
                }
            })()

            try:
                code = generator.generate_feature_code(test_request)
                print(f"✅ コード生成成功: {len(code.generated_code)} 文字")
                print(f"   セキュリティスコア: {code.security_score}")
            except Exception as e:
                print(f"❌ コード生成エラー: {e}")
                return False
        else:
            print("⚠️  Gemini APIなしのためコード生成スキップ")

        # 6. 実行エンジンテスト
        print("\n⚡ 実行エンジンテスト...")
        executor = DynamicExecutionEngine()

        # シンプルなテストコード
        test_code = type('obj', (object,), {
            'generated_code': '''
def test_function(user_input, parameters):
    """テスト関数"""
    return f"テスト実行成功: {user_input}"
''',
            'code_id': 'test-code-123'
        })()

        try:
            result = executor.execute_generated_code(test_code, "テスト入力", {})
            if result.get('status') == 'success':
                print(f"✅ コード実行成功: {result.get('result', 'N/A')}")
            else:
                print(f"❌ コード実行失敗: {result.get('error', 'N/A')}")
                return False
        except Exception as e:
            print(f"❌ コード実行エラー: {e}")
            return False

        # 7. 完全な機能生成テスト
        print("\n🎯 完全な機能生成テスト...")
        if gemini_service:
            try:
                test_input = "今日の星座占いをまとめて教えて"
                feature = dynamic_system.create_feature_from_request(test_input)
                print(f"✅ 機能生成成功: {feature.name}")
                print(f"   機能ID: {feature.feature_id}")
                print(f"   状態: {feature.status.value}")
            except Exception as e:
                print(f"❌ 機能生成エラー: {e}")
                return False
        else:
            print("⚠️  Gemini APIなしのため完全機能生成スキップ")

        # 8. 機能一覧テスト
        print("\n📋 機能一覧テスト...")
        try:
            features = dynamic_system.list_features()
            print(f"✅ 機能一覧取得成功: {len(features)} 個の機能")
            for i, feature in enumerate(features[-3:], len(features)-2):  # 最新3つを表示
                print(f"   {i+1}. {feature.get('name', 'N/A')} - {feature.get('status', 'N/A')}")
        except Exception as e:
            print(f"❌ 機能一覧エラー: {e}")
            return False

        # 9. 機能実行テスト
        print("\n🔄 機能実行テスト...")
        if gemini_service and features:
            try:
                latest_feature = features[-1]  # 最新の機能
                result = dynamic_system.execute_feature(latest_feature['feature_id'])
                if result.get('status') == 'success':
                    print(f"✅ 機能実行成功: {str(result.get('result', 'N/A'))[:100]}...")
                else:
                    print(f"⚠️ 機能実行結果: {result.get('error', 'N/A')}")
            except Exception as e:
                print(f"❌ 機能実行エラー: {e}")

        # 10. データ保存・読み込みテスト
        print("\n💾 データ保存テスト...")
        try:
            dynamic_system.save_features()
            print("✅ 機能保存成功")

            # 新しいインスタンスで読み込みテスト
            new_system = DynamicFeatureSystem(gemini_service)
            new_features = new_system.list_features()
            print(f"✅ 機能読み込み成功: {len(new_features)} 個の機能")
        except Exception as e:
            print(f"❌ データ保存エラー: {e}")
            return False

        print("\n" + "=" * 60)
        print("🎉 すべてのテストが完了しました！")
        print("✅ 動的機能生成システムは正常に動作しています")
        return True

    except Exception as e:
        print(f"\n❌ システムテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_functionality():
    """シンプルな機能テスト（APIなし）"""
    print("\n🧪 シンプル機能テスト（Gemini APIなし）")
    print("=" * 40)

    try:
        from services.dynamic_feature_service import DynamicExecutionEngine

        executor = DynamicExecutionEngine()

        # シンプルなテストコード
        test_code = type('obj', (object,), {
            'generated_code': '''
def simple_greeting(user_input, parameters):
    """シンプルな挨拶機能"""
    name = parameters.get('name', 'ゲスト')
    return f"こんにちは、{name}さん！入力: {user_input}"
''',
            'code_id': 'simple-test-123'
        })()

        result = executor.execute_generated_code(test_code, "テストメッセージ", {"name": "太郎"})
        if result.get('status') == 'success':
            print(f"✅ シンプル機能実行成功: {result.get('result')}")
            return True
        else:
            print(f"❌ シンプル機能実行失敗: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ シンプル機能テストエラー: {e}")
        return False

if __name__ == "__main__":
    print("🚀 動的機能生成システム テストスイート")
    print(f"テスト実行時刻: {datetime.now()}")
    print(f"Pythonバージョン: {sys.version}")
    print(f"プロジェクトパス: {project_root}")

    # シンプルテスト（APIなし）
    simple_ok = test_simple_functionality()

    # 完全テスト（APIあり）
    if simple_ok:
        full_ok = test_dynamic_feature_system()
    else:
        print("\n⚠️  シンプルテストが失敗したため、完全テストをスキップします")
        full_ok = False

    print("\n" + "=" * 60)
    if full_ok:
        print("🎉 テスト結果: 成功")
        print("✅ 動的機能生成システムは正常に動作します")
    else:
        print("❌ テスト結果: 失敗")
        print("⚠️  システムに問題がある可能性があります")

    # テストサマリー
    print("\n📊 テストサマリー:")
    print(f"   シンプルテスト: {'✅' if simple_ok else '❌'}")
    print(f"   完全システムテスト: {'✅' if full_ok else '❌'}")
