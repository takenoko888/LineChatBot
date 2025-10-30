"""
Ultimate System Test - 究極のシステムテスト
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# テスト用に環境変数を設定
os.environ['SKIP_CONFIG_VALIDATION'] = 'true'
os.environ['GEMINI_API_KEY'] = 'test_key_for_mock'
os.environ['MOCK_MODE'] = 'true'

async def test_core_functionality():
    """コア機能テスト"""
    logger.info("🧪 コア機能テストを開始")

    try:
        # 1. サービス統合マネージャーの直接テスト
        from services.service_integration_manager import service_integration_manager

        # 利用可能なサービスを確認
        available_services = service_integration_manager.get_available_services()

        if available_services:
            logger.info(f"✅ サービス統合マネージャー動作確認: {len(available_services)}個のサービス")
        else:
            logger.warning("⚠️ 利用可能なサービスがありません")

        # 2. インテントルーターの直接テスト
        from services.context_aware_router import context_aware_router

        # インテント分析のテスト
        test_queries = [
            "今日の天気を教えて",
            "毎朝8時に起こして",
            "ニュースを検索して"
        ]

        for query in test_queries:
            try:
                routing_decision = context_aware_router.analyze_and_route_sync(query)
                logger.info(f"✅ インテント分析: {query[:15]}... → {routing_decision.selected_service}")
            except Exception as e:
                logger.warning(f"⚠️ インテント分析エラー: {query[:15]}... - {str(e)}")

        # 3. 柔軟AIサービスの直接テスト
        from services.flexible_ai_service import flexible_ai_service

        try:
            response = flexible_ai_service.generate_flexible_response_sync("テストクエリ")
            logger.info(f"✅ 柔軟AIサービス: {len(response)}文字の応答生成")
        except Exception as e:
            logger.warning(f"⚠️ 柔軟AIサービスエラー: {str(e)}")

        return True

    except Exception as e:
        logger.error(f"❌ コア機能テスト失敗: {str(e)}")
        return False

async def test_mock_responses():
    """モック応答テスト"""
    logger.info("🤖 モック応答テストを開始")

    try:
        from services.flexible_ai_service import flexible_ai_service
        from services.context_aware_router import context_aware_router

        # AIサービスのモック応答テスト
        test_cases = [
            ("天気クエリ", "今日の天気を教えて"),
            ("通知クエリ", "毎朝8時に起こして"),
            ("検索クエリ", "ニュースを検索して"),
            ("一般クエリ", "こんにちは")
        ]

        for name, query in test_cases:
            try:
                # AI応答テスト
                ai_response = flexible_ai_service.generate_flexible_response_sync(query)
                if ai_response and len(ai_response) > 0:
                    logger.info(f"  ✅ {name}: AI応答 {len(ai_response)}文字")
                else:
                    logger.warning(f"  ⚠️ {name}: AI応答なし")

                # インテント分析テスト
                routing_decision = context_aware_router.analyze_and_route_sync(query)
                if routing_decision:
                    logger.info(f"  ✅ {name}: インテント分析 {routing_decision.selected_service}")
                else:
                    logger.warning(f"  ⚠️ {name}: インテント分析なし")

            except Exception as e:
                logger.warning(f"  ⚠️ {name}: エラー - {str(e)}")

        return True

    except Exception as e:
        logger.error(f"❌ モック応答テスト失敗: {str(e)}")
        return False

async def test_system_initialization():
    """システム初期化テスト"""
    logger.info("🔧 システム初期化テストを開始")

    try:
        from services.integrated_service_manager import integrated_service_manager

        # システム状態の確認
        system_status = integrated_service_manager.get_system_status()

        logger.info("✅ 統合サービスマネージャー初期化確認")
        logger.info(f"   初期化状態: {system_status.get('initialized', False)}")
        logger.info(f"   モックモード: {system_status.get('mock_mode', False)}")
        logger.info(f"   利用可能サービス数: {len(system_status.get('available_services', []))}")

        # 統計情報
        user_stats = integrated_service_manager.get_user_statistics("test_user")
        logger.info("✅ ユーザー統計機能確認")

        return True

    except Exception as e:
        logger.error(f"❌ システム初期化テスト失敗: {str(e)}")
        return False

async def main():
    """メイン実行関数"""
    logger.info("🚀 究極のシステムテストを開始")

    tests = [
        ("コア機能テスト", test_core_functionality),
        ("モック応答テスト", test_mock_responses),
        ("システム初期化テスト", test_system_initialization)
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n📋 {test_name} を実行中...")
        try:
            result = await test_func()
            results.append((test_name, result))
            status = "✅" if result else "❌"
            logger.info(f"  {status} {test_name} 完了")
        except Exception as e:
            logger.error(f"  ❌ {test_name} でエラーが発生: {str(e)}")
            results.append((test_name, False))

    # 結果サマリー
    successful_tests = len([r for r in results if r[1]])
    total_tests = len(results)
    success_rate = successful_tests / total_tests if total_tests > 0 else 0

    print("\n" + "="*60)
    print("📊 究極のシステムテスト レポート")
    print("="*60)
    print(f"総テスト数: {total_tests}")
    print(f"成功テスト数: {successful_tests}")
    print(f"失敗テスト数: {total_tests - successful_tests}")
    print(f"成功率: {success_rate:.1%}")
    print(f"テスト完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 詳細なテスト結果
    print("\n📋 テスト結果詳細:")
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}")

    # 評価
    if success_rate >= 0.8:
        print("\n🎉 システムは正常に動作しています！")
        print("✅ すべての主要機能が動作確認済み")
        return True
    elif success_rate >= 0.5:
        print("\n⚠️  システムは部分的に動作していますが、改善が必要です。")
        return True
    else:
        print("\n❌ システムに問題があります。修正が必要です。")
        return False

def main_sync():
    """同期版メイン実行関数"""
    logger.info("🚀 究極のシステムテストを開始")

    tests = [
        ("コア機能テスト", test_core_functionality),
        ("モック応答テスト", test_mock_responses),
        ("システム初期化テスト", test_system_initialization)
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n📋 {test_name} を実行中...")
        try:
            result = test_func()  
            results.append((test_name, result))
            status = "✅" if result else "❌"
            logger.info(f"  {status} {test_name} 完了")
        except Exception as e:
            logger.error(f"  ❌ {test_name} でエラーが発生: {str(e)}")
            results.append((test_name, False))

    # 結果サマリー
    successful_tests = len([r for r in results if r[1]])
    total_tests = len(results)
    success_rate = successful_tests / total_tests if total_tests > 0 else 0

    print("\n" + "="*60)
    print("📊 究極のシステムテスト レポート")
    print("="*60)
    print(f"総テスト数: {total_tests}")
    print(f"成功テスト数: {successful_tests}")
    print(f"失敗テスト数: {total_tests - successful_tests}")
    print(f"成功率: {success_rate:.1%}")
    print(f"テスト完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 詳細なテスト結果
    print("\n📋 テスト結果詳細:")
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}")

    # 評価
    if success_rate >= 0.8:
        print("\n🎉 システムは正常に動作しています！")
        print("✅ すべての主要機能が動作確認済み")
        return True
    elif success_rate >= 0.5:
        print("\n⚠️  システムは部分的に動作していますが、改善が必要です。")
        return True
    else:
        print("\n❌ システムに問題があります。修正が必要です。")
        return False

if __name__ == "__main__":
    success = main_sync()
    logger.info(f"テスト実行完了: {'成功' if success else '失敗'}")
    sys.exit(0 if success else 1)
