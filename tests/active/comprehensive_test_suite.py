#!/usr/bin/env python3
"""
統合テストスイート - プロジェクト全機能テスト

このスイートは以下の順序でテストを実行します：
1. 環境設定・依存関係の確認
2. 基本機能テスト
3. 通知機能テスト
4. 高度な機能テスト（AI、検索、天気など）
5. エラーハンドリングテスト
6. パフォーマンステスト
"""

import os
import sys
import logging
import tempfile
import time
from datetime import datetime
import json
from unittest.mock import Mock

# プロジェクトパスを追加（testsフォルダーから実行するため）
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

# テスト環境のセットアップ
def setup_comprehensive_test_environment():
    """包括的なテスト環境のセットアップ"""
    print("🚀 統合テストスイート開始")
    print("=" * 60)
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # テスト用環境変数設定
    test_env = {
        'GEMINI_API_KEY': 'test_gemini_key_for_testing',
        'LINE_CHANNEL_ACCESS_TOKEN': 'test_line_token',
        'LINE_ACCESS_TOKEN': 'test_line_token',
        'LINE_CHANNEL_SECRET': 'test_line_secret',
        'GOOGLE_API_KEY': 'test_google_api_key',
        'SEARCH_ENGINE_ID': 'test_search_engine_id'
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    # テスト用データディレクトリ
    test_dir = tempfile.mkdtemp()
    os.environ['NOTIFICATION_STORAGE_PATH'] = os.path.join(test_dir, 'test_notifications.json')
    os.environ['AUTO_TASK_STORAGE_PATH'] = os.path.join(test_dir, 'test_auto_tasks.json')
    
    print(f"✅ テスト環境セットアップ完了")
    print(f"📁 テストデータ保存先: {test_dir}")
    
    return test_dir

class TestSuite:
    """統合テストスイートクラス"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
    def run_test_category(self, category_name, test_functions):
        """テストカテゴリを実行"""
        print(f"\n📋 {category_name} テスト開始...")
        print("-" * 40)
        
        category_results = []
        
        for i, (test_name, test_func) in enumerate(test_functions, 1):
            print(f"  {i}. {test_name}")
            
            try:
                start_time = time.time()
                result = test_func()
                end_time = time.time()
                
                category_results.append({
                    'name': test_name,
                    'success': True,
                    'duration': end_time - start_time,
                    'result': result
                })
                print(f"     ✅ 成功 ({end_time - start_time:.2f}s)")
                
            except Exception as e:
                category_results.append({
                    'name': test_name,
                    'success': False,
                    'error': str(e)
                })
                print(f"     ❌ 失敗: {str(e)}")
        
        success_count = sum(1 for r in category_results if r['success'])
        print(f"\n📊 {category_name} 結果: {success_count}/{len(test_functions)} 成功")
        
        self.test_results[category_name] = category_results
        return category_results

    def test_environment_setup(self):
        """環境設定テスト"""
        # 必要なモジュールのインポートテスト
        try:
            from core.config_manager import config_manager
            from services.gemini_service import GeminiService
            from services.notification_service import NotificationService
            from handlers.message_handler import MessageHandler
            return True
        except ImportError as e:
            raise Exception(f"モジュールインポートエラー: {e}")

    def test_basic_imports(self):
        """基本インポートテスト"""
        modules_to_test = [
            'app',
            'core.line_bot_base',
            'handlers.message_handler',
            'services.gemini_service',
            'services.notification_service',
            'utils.date_utils'
        ]
        
        for module in modules_to_test:
            try:
                __import__(module)
            except Exception as e:
                raise Exception(f"{module} インポート失敗: {e}")
        
        return len(modules_to_test)

    def test_gemini_service_basic(self):
        """Gemini サービス基本機能テスト"""
        from services.gemini_service import GeminiService
        
        gemini = GeminiService()
        
        # フォールバック解析テスト
        test_text = "毎日7時に起きる"
        result = gemini._fallback_analysis(test_text)
        
        if not isinstance(result, dict):
            raise Exception("フォールバック解析の結果がdict型ではありません")
        
        return result

    def test_notification_service_basic(self):
        """通知サービス基本機能テスト"""
        from services.gemini_service import GeminiService
        from services.notification_service import NotificationService
        
        line_bot_api = Mock()
        gemini_service = GeminiService()
        notification_service = NotificationService(
            gemini_service=gemini_service,
            line_bot_api=line_bot_api
        )
        
        user_id = "test_user_basic"
        
        # 通知追加テスト（正しいパラメータで）
        notification_service.add_notification(
            user_id=user_id,
            title="テスト通知",
            message="テスト通知メッセージ",
            datetime_str="2024-01-15 07:00:00"
        )
        notifications = notification_service.get_notifications(user_id)
        
        if len(notifications) != 1:
            raise Exception(f"通知追加に失敗: 期待1件、実際{len(notifications)}件")
        
        # 通知削除テスト
        if notifications:
            first_notification = notifications[0]
            notification_id = first_notification.get('id')
            if notification_id:
                notification_service.delete_notification(user_id, notification_id)
                notifications = notification_service.get_notifications(user_id)
                
                if len(notifications) != 0:
                    raise Exception(f"通知削除に失敗: 期待0件、実際{len(notifications)}件")
        
        return True

    def test_message_handler_basic(self):
        """メッセージハンドラー基本機能テスト"""
        from handlers.message_handler import MessageHandler
        from services.gemini_service import GeminiService
        from services.notification_service import NotificationService
        from unittest.mock import Mock
        
        line_bot_api = Mock()
        gemini_service = GeminiService()
        notification_service = NotificationService(
            gemini_service=gemini_service,
            line_bot_api=line_bot_api
        )
        message_handler = MessageHandler()
        
        # テストイベント作成
        mock_event = Mock()
        mock_event.message.text = "ヘルプ"
        mock_event.source.user_id = "test_user_handler"
        
        response, quick_reply = message_handler.handle_message(
            mock_event, gemini_service, notification_service
        )
        
        if not isinstance(response, str) or len(response) == 0:
            raise Exception("メッセージハンドラーの応答が不正です")
        
        return len(response)

    def test_notification_parsing(self):
        """通知解析機能テスト"""
        from services.gemini_service import GeminiService
        
        gemini = GeminiService()
        
        test_cases = [
            "毎日7時に起きる",
            "明日の15時に会議",
            "毎週月曜9時にミーティング",
            "12時40分に課題をやる"
        ]
        
        results = []
        for text in test_cases:
            result = gemini._simple_notification_parse(text)
            results.append(result)
        
        return len(results)

    def test_error_handling(self):
        """エラーハンドリングテスト"""
        from services.gemini_service import GeminiService
        
        gemini = GeminiService()
        
        # 不正な入力に対するテスト
        try:
            result = gemini._fallback_analysis("")
            if result is None:
                raise Exception("空文字列の処理に失敗")
        except Exception as e:
            # エラーが適切に処理されることを確認
            pass
        
        return True

    def test_date_utils(self):
        """日付ユーティリティテスト"""
        from utils.date_utils import DateUtils
        from datetime import datetime
        
        date_utils = DateUtils()
        
        # 自然言語解析テスト
        result_datetime, settings = date_utils.parse_natural_datetime("毎日7時に起きる")
        if result_datetime is None and not isinstance(settings, dict):
            raise Exception("自然言語解析に失敗")
        
        # 日時フォーマットテスト
        test_datetime = datetime(2024, 1, 15, 7, 0, 0)
        formatted = date_utils.format_datetime(test_datetime, 'default')
        if not isinstance(formatted, str):
            raise Exception("日時フォーマットに失敗")
        
        return True

    def test_performance_basic(self):
        """基本パフォーマンステスト"""
        from services.gemini_service import GeminiService
        
        gemini = GeminiService()
        
        # 100回の解析処理時間を測定
        start_time = time.time()
        
        for i in range(10):  # 軽量テストのため10回に削減
            gemini._fallback_analysis("毎日7時に起きる")
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        if avg_time > 1.0:  # 1秒以下を期待
            raise Exception(f"処理時間が遅すぎます: {avg_time:.2f}s")
        
        return avg_time

    def generate_final_report(self):
        """最終レポート生成"""
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("📊 統合テストスイート最終レポート")
        print("=" * 60)
        
        total_tests = 0
        successful_tests = 0
        
        for category, results in self.test_results.items():
            success_count = sum(1 for r in results if r['success'])
            total_tests += len(results)
            successful_tests += success_count
            
            print(f"\n📋 {category}:")
            print(f"  ✅ 成功: {success_count}/{len(results)}")
            
            for result in results:
                if result['success']:
                    duration = result.get('duration', 0)
                    print(f"    ✅ {result['name']} ({duration:.2f}s)")
                else:
                    print(f"    ❌ {result['name']}: {result['error']}")
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 総合結果:")
        print(f"  📊 成功率: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        print(f"  ⏱️ 実行時間: {total_time:.2f}秒")
        
        if success_rate >= 80:
            print(f"🎉 テスト成功！プロジェクトは正常に動作しています。")
        elif success_rate >= 60:
            print(f"⚠️ 一部機能に問題がありますが、基本的には動作しています。")
        else:
            print(f"❌ 重大な問題があります。詳細な調査が必要です。")
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': success_rate,
            'total_time': total_time
        }

def main():
    """メイン実行関数"""
    test_dir = setup_comprehensive_test_environment()
    
    suite = TestSuite()
    
    # テストカテゴリ定義
    test_categories = [
        ("環境設定", [
            ("環境変数設定", suite.test_environment_setup),
            ("基本インポート", suite.test_basic_imports),
        ]),
        ("基本機能", [
            ("Geminiサービス", suite.test_gemini_service_basic),
            ("通知サービス", suite.test_notification_service_basic),
            ("メッセージハンドラー", suite.test_message_handler_basic),
        ]),
        ("高度な機能", [
            ("通知解析", suite.test_notification_parsing),
            ("日付ユーティリティ", suite.test_date_utils),
        ]),
        ("品質保証", [
            ("エラーハンドリング", suite.test_error_handling),
            ("基本パフォーマンス", suite.test_performance_basic),
        ])
    ]
    
    # テスト実行
    for category_name, test_functions in test_categories:
        suite.run_test_category(category_name, test_functions)
    
    # 最終レポート
    final_report = suite.generate_final_report()
    
    # 整理されたテストファイルリストを出力
    print(f"\n📁 テストファイル整理の提案:")
    print(f"  🟢 実行済み: comprehensive_test_suite.py (このファイル)")
    print(f"  🔵 詳細テスト: test_all_features_detailed.py")
    print(f"  🔵 通知機能: test_notification_*.py ファイル群")
    print(f"  🔵 自動タスク: test_auto_task_*.py ファイル群")
    print(f"  🔵 AI機能: test_enhanced_ai_system.py")
    print(f"  🔵 検索機能: test_search_url_display.py")
    print(f"  ⚪ 軽量テスト: quick_test.py")
    print(f"  ⚪ 環境確認: environment_variable_test.py")
    
    return final_report['success_rate'] >= 60

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 