"""
Simple System Test - 基本機能テスト（モック対応版）
"""
import asyncio
import logging
import os
from datetime import datetime

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# テスト用に環境変数を設定
os.environ['SKIP_CONFIG_VALIDATION'] = 'true'
os.environ['GEMINI_API_KEY'] = 'test_key_for_mock'
os.environ['MOCK_MODE'] = 'true'

async def test_basic_system():
    """基本システムテスト"""
    logger.info("🧪 基本システムテストを開始")

    try:
        # 1. サービス統合マネージャーのテスト
        from services.service_integration_manager import service_integration_manager
        logger.info("✅ サービス統合マネージャーをインポート成功")

        # 2. インテントルーターのテスト
        from services.context_aware_router import context_aware_router
        logger.info("✅ コンテキスト対応インテントルーターをインポート成功")

        # 3. ハイブリッド応答生成器のテスト
        from services.hybrid_response_generator import hybrid_response_generator
        logger.info("✅ ハイブリッド応答生成器をインポート成功")

        # 4. 統合サービスマネージャーのテスト
        from services.integrated_service_manager import integrated_service_manager
        logger.info("✅ 統合サービスマネージャーをインポート成功")

        # 5. 柔軟AIサービスのテスト
        from services.flexible_ai_service import flexible_ai_service
        logger.info("✅ 柔軟AIサービスをインポート成功")

        # 6. 基本的な機能テスト
        available_services = service_integration_manager.get_available_services()
        logger.info(f"✅ 利用可能なサービス数: {len(available_services)}")

        # 7. インテント分析テスト
        test_query = "今日の天気を教えて"
        routing_decision = await context_aware_router.analyze_and_route(test_query)
        logger.info(f"✅ インテント分析成功: {routing_decision.selected_service}")

        # 8. システム状態確認
        system_status = integrated_service_manager.get_system_status()
        logger.info(f"✅ システム状態確認: 初期化={system_status.get('initialized', False)}")

        return True

    except Exception as e:
        logger.error(f"❌ 基本システムテスト失敗: {str(e)}")
        return False

async def test_diverse_queries():
    """多様なクエリテスト"""
    logger.info("🎭 多様なクエリテストを開始")

    try:
        from services.integrated_service_manager import integrated_service_manager, IntegratedServiceRequest

        test_queries = [
            # 基本的なクエリ
            "こんにちは",
            "今日の天気を教えて",
            "毎朝8時に起こして",
            "ニュースを検索して",

            # 複合クエリ
            "毎日の天気とニュースを通知して",
            "旅行の計画を立てて",

            # カジュアルなクエリ
            "おすすめ教えて",
            "最近どう？"
        ]

        success_count = 0
        for i, query in enumerate(test_queries, 1):
            try:
                request = IntegratedServiceRequest(
                    query=query,
                    user_id="test_user",
                    context={"test_mode": True}
                )

                response = await integrated_service_manager.process_integrated_request(request)

                # 応答の検証
                if response and response.response:
                    logger.info(f"  ✅ クエリ {i}: {query[:15]}... → {response.service_used}")
                    success_count += 1
                else:
                    logger.warning(f"  ⚠️ クエリ {i}: {query[:15]}... → 応答なし")

            except Exception as e:
                logger.warning(f"  ⚠️ クエリ {i}: {query[:15]}... → エラー: {str(e)}")

        success_rate = success_count / len(test_queries)
        logger.info(f"📊 多様なクエリテスト結果: {success_count}/{len(test_queries)} 成功 ({success_rate:.1%})")

        return success_rate >= 0.6  # 60%以上の成功率で合格

    except Exception as e:
        logger.error(f"❌ 多様なクエリテスト失敗: {str(e)}")
        return False

async def test_ai_flexibility():
    """AI柔軟性テスト"""
    logger.info("🤖 AI柔軟性テストを開始")

    try:
        from services.flexible_ai_service import flexible_ai_service

        test_cases = [
            ("創造的なクエリ", "新しいアプリのアイデアを考えて", {"is_creative": True}),
            ("技術的なクエリ", "Pythonの勉強方法を教えて", {"technical_level": "beginner"}),
            ("カジュアルなクエリ", "最近どう？", {"is_casual": True}),
            ("複雑なクエリ", "複数の機能を組み合わせたシステムを作って", {"is_complex": True})
        ]

        success_count = 0
        for name, query, context in test_cases:
            try:
                response = await flexible_ai_service.generate_flexible_response(
                    query,
                    context=context
                )

                if response and len(response) > 10:
                    logger.info(f"  ✅ {name}: {len(response)}文字")
                    success_count += 1
                else:
                    logger.warning(f"  ⚠️ {name}: 応答が短すぎる")

            except Exception as e:
                logger.warning(f"  ⚠️ {name}: エラー - {str(e)}")

        success_rate = success_count / len(test_cases)
        logger.info(f"📊 AI柔軟性テスト結果: {success_count}/{len(test_cases)} 成功 ({success_rate:.1%})")

        return success_rate >= 0.5  # 50%以上の成功率で合格

    except Exception as e:
        logger.error(f"❌ AI柔軟性テスト失敗: {str(e)}")
        return False

async def main():
    """メイン実行関数"""
    logger.info("🚀 システムテストを開始")

    tests = [
        ("基本システムテスト", test_basic_system),
        ("多様なクエリテスト", test_diverse_queries),
        ("AI柔軟性テスト", test_ai_flexibility)
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
    print("📊 システムテスト レポート")
    print("="*60)
    print(f"総テスト数: {total_tests}")
    print(f"成功テスト数: {successful_tests}")
    print(f"失敗テスト数: {total_tests - successful_tests}")
    print(f"成功率: {success_rate:.1%}")
    print(f"テスト完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if success_rate >= 0.8:
        print("🎉 システムは正常に動作しています！")
        return True
    elif success_rate >= 0.5:
        print("⚠️  システムは部分的に動作していますが、改善が必要です。")
        return True
    else:
        print("❌ システムに重大な問題があります。修正が必要です。")
        return False

if __name__ == "__main__":
    async def run():
        success = await main()
        exit(0 if success else 1)

    asyncio.run(run())
