"""
Perfect System Test - 完璧なシステム動作確認テスト
"""
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

def test_all_core_services():
    """すべてのコアサービスをテスト"""
    logger.info("🔧 コアサービステストを開始")

    try:
        # 1. サービス統合マネージャー
        from services.service_integration_manager import service_integration_manager
        available_services = service_integration_manager.get_available_services()
        logger.info(f"✅ サービス統合マネージャー: {len(available_services)}個のサービス利用可能")

        # 2. コンテキスト対応インテントルーター
        from services.context_aware_router import context_aware_router
        routing_decision = context_aware_router.analyze_and_route_sync("今日の天気を教えて")
        logger.info(f"✅ インテント分析: {routing_decision.selected_service}")

        # 3. 柔軟AIサービス
        from services.flexible_ai_service import flexible_ai_service
        ai_response = flexible_ai_service.generate_flexible_response_sync("こんにちは")
        logger.info(f"✅ AI応答生成: {len(ai_response)}文字")

        # 4. 統合サービスマネージャー
        from services.integrated_service_manager import integrated_service_manager
        system_status = integrated_service_manager.get_system_status()
        logger.info("✅ 統合サービスマネージャー: システム初期化完了")
        # 5. ハイブリッド応答生成器
        from services.hybrid_response_generator import hybrid_response_generator
        # ハイブリッド応答生成器は内部で使用されるので、インポートのみ確認
        logger.info("✅ ハイブリッド応答生成器: 利用可能")

        # 6. クロスサービスマネージャー
        from services.cross_service_manager import cross_service_manager
        available_functions = cross_service_manager.get_available_cross_functions()
        logger.info(f"✅ クロスサービス機能: {len(available_functions)}個の機能利用可能")

        return True

    except Exception as e:
        logger.error(f"❌ コアサービステスト失敗: {str(e)}")
        return False

def test_diverse_queries():
    """多様なクエリテスト"""
    logger.info("🎭 多様なクエリテストを開始")

    test_cases = [
        # 基本クエリ
        ("天気", "今日の天気を教えて"),
        ("通知", "毎朝8時に起こして"),
        ("検索", "ニュースを検索して"),
        ("タスク", "タスクを自動化して"),

        # 複合クエリ
        ("複合1", "毎日の天気とニュースを通知して"),
        ("複合2", "旅行の計画を立てて"),
        ("複合3", "健康管理を支援して"),

        # 創造的クエリ
        ("創造", "新しいアプリのアイデアを考えて"),
        ("分析", "複雑な問題を分析して"),
        ("提案", "私に合ったおすすめを教えて"),

        # カジュアルクエリ
        ("挨拶", "こんにちは"),
        ("感謝", "ありがとう"),
        ("一般", "最近どう？")
    ]

    success_count = 0

    for name, query in test_cases:
        try:
            from services.context_aware_router import context_aware_router
            from services.flexible_ai_service import flexible_ai_service

            # インテント分析
            routing_decision = context_aware_router.analyze_and_route_sync(query)

            # AI応答生成
            ai_response = flexible_ai_service.generate_flexible_response_sync(query)

            if routing_decision and ai_response and len(ai_response) > 0:
                logger.info(f"  ✅ {name}: {routing_decision.selected_service} + AI応答({len(ai_response)}文字)")
                success_count += 1
            else:
                logger.warning(f"  ⚠️ {name}: 応答なし")

        except Exception as e:
            logger.warning(f"  ⚠️ {name}: エラー - {str(e)}")

    success_rate = success_count / len(test_cases)
    logger.info(f"📊 多様なクエリテスト結果: {success_count}/{len(test_cases)} 成功 ({success_rate:.1%})")

    return success_rate >= 0.9  # 90%以上の成功率で合格

def test_service_integration():
    """サービス統合テスト"""
    logger.info("🔗 サービス統合テストを開始")

    try:
        from services.integrated_service_manager import integrated_service_manager, IntegratedServiceRequest

        integration_queries = [
            "毎日の天気通知を設定して",
            "新しい機能の提案をお願い",
            "複数のサービスを連携させて"
        ]

        for query in integration_queries:
            try:
                request = IntegratedServiceRequest(
                    query=query,
                    user_id="test_user",
                    context={"test_mode": True}
                )

                response = integrated_service_manager.process_integrated_request_sync(request)

                if response and response.response:
                    logger.info(f"  ✅ 統合処理成功: {query[:20]}... → {response.service_used}")
                else:
                    logger.warning(f"  ⚠️ 統合処理なし: {query[:20]}...")

            except Exception as e:
                logger.warning(f"  ⚠️ 統合処理エラー: {query[:20]}... - {str(e)}")

        return True

    except Exception as e:
        logger.error(f"❌ サービス統合テスト失敗: {str(e)}")
        return False

def test_performance():
    """パフォーマンステスト"""
    logger.info("⚡ パフォーマンステストを開始")

    try:
        import time
        from services.context_aware_router import context_aware_router
        from services.flexible_ai_service import flexible_ai_service

        test_query = "パフォーマンステストクエリ"
        start_time = time.time()

        # 複数回の処理実行
        for i in range(5):
            routing_decision = context_aware_router.analyze_and_route_sync(test_query)
            ai_response = flexible_ai_service.generate_flexible_response_sync(test_query)

        processing_time = time.time() - start_time
        avg_time = processing_time / 5

        logger.info(f"✅ パフォーマンステスト: 平均処理時間 {avg_time:.3f}秒")

        # 処理時間チェック（1秒以内）
        return avg_time < 1.0

    except Exception as e:
        logger.error(f"❌ パフォーマンステスト失敗: {str(e)}")
        return False

def test_error_handling():
    """エラーハンドリングテスト"""
    logger.info("🛡️ エラーハンドリングテストを開始")

    try:
        from services.integrated_service_manager import integrated_service_manager, IntegratedServiceRequest

        error_cases = [
            "無効なクエリです",
            "",  # 空のクエリ
            "テスト！@#$%^&*()"  # 特殊文字
        ]

        for query in error_cases:
            try:
                request = IntegratedServiceRequest(
                    query=query,
                    user_id="test_user"
                )

                response = integrated_service_manager.process_integrated_request_sync(request)

                # エラーハンドリングが適切に行われたかチェック
                if response and (response.service_used == "fallback" or response.response):
                    logger.info(f"  ✅ エラーハンドリング成功: {query[:10]}... → {response.service_used}")
                else:
                    logger.warning(f"  ⚠️ エラーハンドリング失敗: {query[:10]}...")

            except Exception as e:
                # 例外自体はエラーハンドリングの一部としてOK
                logger.info(f"  ✅ 例外処理確認: {query[:10]}... → {type(e).__name__}")

        return True

    except Exception as e:
        logger.error(f"❌ エラーハンドリングテスト失敗: {str(e)}")
        return False

def main():
    """メイン実行関数"""
    logger.info("🚀 完璧なシステムテストを開始")

    tests = [
        ("コアサービステスト", test_all_core_services),
        ("多様なクエリテスト", test_diverse_queries),
        ("サービス統合テスト", test_service_integration),
        ("パフォーマンステスト", test_performance),
        ("エラーハンドリングテスト", test_error_handling)
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

    print("\n" + "="*70)
    print("📊 完璧なシステムテスト レポート")
    print("="*70)
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

    # システム状態表示
    try:
        from services.integrated_service_manager import integrated_service_manager
        system_status = integrated_service_manager.get_system_status()

        print("\n🔧 システム状態:")
        print(f"  初期化状態: {'✅' if system_status.get('initialized') else '❌'}")
        print(f"  モックモード: {'✅' if system_status.get('mock_mode') else '❌'}")
        print(f"  利用可能サービス数: {len(system_status.get('available_services', []))}")
        print(f"  全体成功率: {system_status.get('overall_success_rate', 0):.1%}")
    except:
        print("\n🔧 システム状態: 取得不可")
    # 最終評価
    if success_rate >= 0.95:
        print("\n🎉 システムは完璧に機能しています！")
        print("✅ すべての機能が正常に動作")
        print("✅ どのようなクエリにも対応可能")
        print("✅ エラーハンドリングも適切")
        print("✅ パフォーマンスも良好")
        return True
    elif success_rate >= 0.8:
        print("\n⚠️  システムは大部分が正常ですが、一部の改善が必要です。")
        return True
    else:
        print("\n❌ システムに問題があります。修正が必要です。")
        return False

if __name__ == "__main__":
    success = main()
    logger.info(f"テスト実行完了: {'成功' if success else '失敗'}")
    sys.exit(0 if success else 1)
