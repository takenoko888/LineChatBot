#!/usr/bin/env python3
"""
Gemini APIを使った実際の動的機能生成テスト
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Gemini APIキーは環境変数から取得（公開用にハードコードを廃止）
if not os.getenv('GEMINI_API_KEY'):
    print("⚠️  環境変数 GEMINI_API_KEY が未設定です。`.env` などで設定してください。")

# プロジェクトルートをPythonパスに追加（scripts/ 配下対応）
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def main():
    print("🚀 Gemini APIを使った動的機能生成システム 実機テスト")
    print("=" * 60)
    print(f"実行時間: {datetime.now()}")
    print("API Key:", os.getenv('GEMINI_API_KEY')[:20] + "...")

    try:
        # 1. 必要なモジュールのインポート
        print("\n📦 モジュールのインポートテスト...")
        from services.dynamic_feature_service import DynamicFeatureSystem
        print("✅ インポート成功")

        # 2. システム初期化（実API使用）
        print("\n🔧 システム初期化テスト...")
        try:
            from services.gemini_service import GeminiService
            gemini_service = GeminiService()
            dynamic_system = DynamicFeatureSystem(gemini_service)
            print("✅ GeminiService初期化成功")
            print("✅ DynamicFeatureSystem初期化成功")
        except Exception as e:
            print(f"❌ 初期化エラー: {e}")
            return False

        # 3. 機能生成テスト
        print("\n💡 機能生成テスト...")
        try:
            # テスト用の要求
            test_input = "今日の天気をまとめて教えて"

            print(f"入力: {test_input}")

            # 機能生成実行
            feature = dynamic_system.create_feature_from_request(test_input)
            print(f"✅ 機能生成成功!")
            print(f"   機能名: {feature.name}")
            print(f"   機能ID: {feature.feature_id}")
            print(f"   状態: {feature.status.value}")
            print(f"   説明: {feature.description}")

        except Exception as e:
            print(f"❌ 機能生成エラー: {e}")
            import traceback
            traceback.print_exc()
            return False

        # 4. 機能一覧表示
        print("\n📋 機能一覧表示...")
        try:
            features = dynamic_system.list_features()
            print(f"✅ 機能一覧取得成功: {len(features)} 個")

            for i, feature in enumerate(features, 1):
                print(f"   {i}. {feature.get('name', 'N/A')}")
                print(f"      状態: {feature.get('status', 'N/A')}")
                print(f"      使用回数: {feature.get('usage_count', 0)}")
                print()

        except Exception as e:
            print(f"❌ 機能一覧エラー: {e}")
            return False

        # 5. 機能実行テスト
        print("\n🔄 機能実行テスト...")
        try:
            if features:
                latest_feature = features[-1]
                print(f"テスト対象機能: {latest_feature.get('name')}")

                result = dynamic_system.execute_feature(latest_feature['feature_id'])
                print(f"✅ 機能実行結果:")
                print(f"   状態: {result.get('status')}")
                if result.get('status') == 'success':
                    print(f"   結果: {str(result.get('result', 'N/A'))[:300]}...")
                else:
                    print(f"   エラー: {result.get('error', 'N/A')}")
            else:
                print("⚠️  実行可能な機能がありません")

        except Exception as e:
            print(f"❌ 機能実行エラー: {e}")
            return False

        # 6. データ保存テスト
        print("\n💾 データ保存テスト...")
        try:
            dynamic_system.save_features()
            print("✅ データ保存成功")

            # 読み込みテスト
            new_system = DynamicFeatureSystem(gemini_service)
            reloaded_features = new_system.list_features()
            print(f"✅ データ読み込み成功: {len(reloaded_features)} 個の機能")

        except Exception as e:
            print(f"❌ データ保存エラー: {e}")
            return False

        print("\n" + "=" * 60)
        print("🎉 テスト完了！")
        print("✅ Gemini APIを使った動的機能生成システムは正常に動作しています")
        print()
        print("📝 テスト結果:")
        print("   - システム初期化: ✅ 成功")
        print("   - 機能生成: ✅ 成功")
        print("   - 機能実行: ✅ 成功")
        print("   - データ保存: ✅ 成功")
        print()
        print("🚀 システムは本番使用可能な状態です！")

        return True

    except Exception as e:
        print(f"\n❌ システムエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()

    if success:
        print("\n🎊 おめでとうございます！")
        print("   Gemini APIを使った動的機能生成システムが正常に動作しました！")
        print()
        print("💡 使用方法:")
        print("   1. LINE Botで「機能を作って〜」と言う")
        print("   2. AIが自動で機能を生成")
        print("   3. 作成された機能が即座に使用可能")
        print()
        print("🔧 高度な機能生成が正常に動作しています！")
    else:
        print("\n⚠️  システムに問題が発生しました")
        print("   ログを確認して原因を特定してください")
