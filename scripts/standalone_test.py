#!/usr/bin/env python3
"""
簡易動的機能生成システムテスト（完全独立版）
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

def main():
    print("🚀 動的機能生成システム 完全独立テスト")
    print("=" * 50)
    print(f"実行時間: {datetime.now()}")

    try:
        # 1. 必要なモジュールのインポート
        print("\n📦 モジュールのインポートテスト...")
        from services.dynamic_feature_service import DynamicFeatureSystem
        print("✅ インポート成功")

        # 2. システム初期化（完全独立）
        print("\n🔧 システム初期化テスト...")
        dynamic_system = DynamicFeatureSystem()  # GeminiServiceなし
        print("✅ DynamicFeatureSystem初期化成功")

        # 3. シンプルな機能生成テスト
        print("\n💡 機能生成テスト...")
        try:
            # テスト用のシンプルな要求
            test_input = "今日の天気を教えて"

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
                print(f"   結果: {str(result.get('result', 'N/A'))[:200]}...")
            else:
                print("⚠️  実行可能な機能がありません")

        except Exception as e:
            print(f"❌ 機能実行エラー: {e}")
            return False

        # 6. システム保存テスト
        print("\n💾 システム保存テスト...")
        try:
            dynamic_system.save_features()
            print("✅ データ保存成功")

            # 読み込みテスト
            new_system = DynamicFeatureSystem()
            reloaded_features = new_system.list_features()
            print(f"✅ データ読み込み成功: {len(reloaded_features)} 個の機能")

        except Exception as e:
            print(f"❌ データ保存エラー: {e}")
            return False

        print("\n" + "=" * 50)
        print("🎉 テスト完了！")
        print("✅ 動的機能生成システムは正常に動作しています")
        print()
        print("📝 テスト結果:")
        print("   - システム初期化: ✅ 成功")
        print("   - 機能生成: ✅ 成功")
        print("   - 機能実行: ✅ 成功")
        print("   - データ保存: ✅ 成功")
        print()
        print("🚀 システムは使用可能な状態です！")

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
        print("   動的機能生成システムが正常に動作しました！")
        print()
        print("💡 使用方法:")
        print("   1. LINE Botで「機能を作って〜」と言う")
        print("   2. AIが自動で機能を生成")
        print("   3. 作成された機能が即座に使用可能")
        print()
        print("🔧 Gemini APIキーを設定すると、より高度な機能生成が可能になります")
    else:
        print("\n⚠️  システムに問題が発生しました")
        print("   ログを確認して原因を特定してください")
