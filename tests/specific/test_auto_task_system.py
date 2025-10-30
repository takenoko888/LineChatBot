"""
自動実行・モニタリング機能テストスイート
Auto Task System Comprehensive Test Suite
"""
import os
import sys
import tempfile
import shutil
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
import json
import threading
import time

# プロジェクトのルートパスを追加（testsフォルダーから実行するため）
project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, project_root)

# テスト対象のインポート
from services.auto_task_service import AutoTaskService, AutoTask, TaskType
from services.notification_service import NotificationService
from services.gemini_service import GeminiService
from handlers.message_handler import MessageHandler

class TestAutoTaskService(unittest.TestCase):
    """AutoTaskServiceのテストクラス"""

    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリの作成
        self.temp_dir = tempfile.mkdtemp()
        
        # モックサービスの作成
        self.mock_notification_service = Mock()
        self.mock_weather_service = Mock()
        self.mock_search_service = Mock()
        self.mock_gemini_service = Mock()
        
        # AutoTaskServiceのインスタンス作成
        self.service = AutoTaskService(
            storage_path=self.temp_dir,
            notification_service=self.mock_notification_service,
            weather_service=self.mock_weather_service,
            search_service=self.mock_search_service,
            gemini_service=self.mock_gemini_service
        )
        
        print(f"✅ AutoTaskService初期化完了 (ストレージ: {self.temp_dir})")

    def tearDown(self):
        """テスト後のクリーンアップ"""
        # スケジューラーを停止
        if hasattr(self.service, 'is_running') and self.service.is_running:
            self.service.stop_scheduler()
        
        # 一時ディレクトリの削除
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        print("✅ テスト環境をクリーンアップしました")

    def test_01_service_initialization(self):
        """サービス初期化テスト"""
        print("\n🧪 テスト01: サービス初期化")
        
        # 基本的な初期化状態をチェック
        self.assertIsNotNone(self.service)
        self.assertIsInstance(self.service.tasks, dict)
        self.assertIsInstance(self.service.execution_logs, list)
        
        # 依存サービスの確認
        self.assertEqual(self.service.notification_service, self.mock_notification_service)
        self.assertEqual(self.service.weather_service, self.mock_weather_service)
        self.assertEqual(self.service.search_service, self.mock_search_service)
        self.assertEqual(self.service.gemini_service, self.mock_gemini_service)
        
        print("   ✅ サービス初期化が正常に完了")

    def test_02_create_weather_daily_task(self):
        """天気配信タスク作成テスト"""
        print("\n🧪 テスト02: 天気配信タスク作成")
        
        # 天気配信タスクを作成
        task_id = self.service.create_auto_task(
            user_id="test_user_001",
            task_type=TaskType.WEATHER_DAILY.value,
            title="毎朝の天気配信",
            description="毎日7時に東京の天気を配信",
            schedule_pattern="daily",
            schedule_time="07:00",
            parameters={"location": "東京"}
        )
        
        # 作成されたタスクを確認
        self.assertTrue(task_id)
        self.assertIn(task_id, self.service.tasks)
        
        created_task = self.service.tasks[task_id]
        self.assertEqual(created_task.user_id, "test_user_001")
        self.assertEqual(created_task.task_type, TaskType.WEATHER_DAILY.value)
        self.assertEqual(created_task.title, "毎朝の天気配信")
        self.assertEqual(created_task.schedule_pattern, "daily")
        self.assertEqual(created_task.schedule_time, "07:00")
        self.assertTrue(created_task.is_active)
        
        print(f"   ✅ 天気配信タスク作成成功: {task_id}")

    def test_03_create_news_daily_task(self):
        """ニュース配信タスク作成テスト"""
        print("\n🧪 テスト03: ニュース配信タスク作成")
        
        # ニュース配信タスクを作成
        task_id = self.service.create_auto_task(
            user_id="test_user_001",
            task_type=TaskType.NEWS_DAILY.value,
            title="毎朝のニュース配信",
            description="毎日8時にAI関連のニュースを配信",
            schedule_pattern="daily",
            schedule_time="08:00",
            parameters={"keywords": ["AI", "技術ニュース", "プログラミング"]}
        )
        
        # 作成されたタスクを確認
        self.assertTrue(task_id)
        self.assertIn(task_id, self.service.tasks)
        
        created_task = self.service.tasks[task_id]
        self.assertEqual(created_task.task_type, TaskType.NEWS_DAILY.value)
        self.assertEqual(created_task.parameters["keywords"], ["AI", "技術ニュース", "プログラミング"])
        
        print(f"   ✅ ニュース配信タスク作成成功: {task_id}")

    def test_04_create_keyword_monitor_task(self):
        """キーワードモニタリングタスク作成テスト"""
        print("\n🧪 テスト04: キーワードモニタリングタスク作成")
        
        # キーワードモニタリングタスクを作成
        task_id = self.service.create_auto_task(
            user_id="test_user_002",
            task_type=TaskType.KEYWORD_MONITOR.value,
            title="Python最新情報監視",
            description="Pythonの最新情報を監視してアラート",
            schedule_pattern="hourly",
            schedule_time="",
            parameters={
                "keywords": ["Python 3.12", "Django", "FastAPI"],
                "alert_threshold": 2
            }
        )
        
        # 作成されたタスクを確認
        self.assertTrue(task_id)
        created_task = self.service.tasks[task_id]
        self.assertEqual(created_task.task_type, TaskType.KEYWORD_MONITOR.value)
        self.assertEqual(created_task.schedule_pattern, "hourly")
        self.assertEqual(created_task.parameters["alert_threshold"], 2)
        
        print(f"   ✅ キーワードモニタリングタスク作成成功: {task_id}")

    def test_05_get_user_tasks(self):
        """ユーザータスク取得テスト"""
        print("\n🧪 テスト05: ユーザータスク取得")
        
        # 複数のタスクを作成（時間をずらして異なるIDを生成）
        task_ids = []
        for i in range(3):
            task_id = self.service.create_auto_task(
                user_id="test_user_003",
                task_type=TaskType.USAGE_REPORT.value,
                title=f"レポートタスク{i+1}",
                description=f"テスト用レポートタスク{i+1}",
                schedule_pattern="weekly",
                schedule_time="09:00",
                parameters={}
            )
            task_ids.append(task_id)
            # 少し待機してタスクIDが重複しないようにする
            time.sleep(0.01)
        
        # 他のユーザーのタスクも作成
        self.service.create_auto_task(
            user_id="other_user",
            task_type=TaskType.WEATHER_DAILY.value,
            title="他ユーザーのタスク",
            description="テスト用",
            schedule_pattern="daily",
            schedule_time="10:00",
            parameters={"location": "大阪"}
        )
        
        # ユーザー003のタスクのみ取得
        user_tasks = self.service.get_user_tasks("test_user_003")
        
        # 確認
        self.assertEqual(len(user_tasks), 3)
        for task in user_tasks:
            self.assertEqual(task.user_id, "test_user_003")
            self.assertIn(task.task_id, task_ids)
        
        print(f"   ✅ ユーザータスク取得成功: {len(user_tasks)}件")

    def test_06_delete_task(self):
        """タスク削除テスト"""
        print("\n🧪 テスト06: タスク削除")
        
        # タスクを作成
        task_id = self.service.create_auto_task(
            user_id="test_user_004",
            task_type=TaskType.WEATHER_DAILY.value,
            title="削除テスト用タスク",
            description="削除テスト",
            schedule_pattern="daily",
            schedule_time="11:00",
            parameters={"location": "京都"}
        )
        
        # タスクが存在することを確認
        self.assertIn(task_id, self.service.tasks)
        
        # タスクを削除
        result = self.service.delete_task("test_user_004", task_id)
        
        # 削除の確認
        self.assertTrue(result)
        self.assertNotIn(task_id, self.service.tasks)
        
        # 権限のないユーザーでの削除試行
        task_id2 = self.service.create_auto_task(
            user_id="test_user_005",
            task_type=TaskType.NEWS_DAILY.value,
            title="権限テスト用タスク",
            description="権限テスト",
            schedule_pattern="daily",
            schedule_time="12:00",
            parameters={"keywords": ["テスト"]}
        )
        
        # 他のユーザーが削除を試行
        result = self.service.delete_task("test_user_004", task_id2)
        self.assertFalse(result)
        self.assertIn(task_id2, self.service.tasks)
        
        print("   ✅ タスク削除および権限チェック成功")

    def test_07_toggle_task(self):
        """タスク有効/無効切り替えテスト"""
        print("\n🧪 テスト07: タスク状態切り替え")
        
        # タスクを作成
        task_id = self.service.create_auto_task(
            user_id="test_user_006",
            task_type=TaskType.USAGE_REPORT.value,
            title="切り替えテスト用タスク",
            description="状態切り替えテスト",
            schedule_pattern="weekly",
            schedule_time="13:00",
            parameters={}
        )
        
        # 初期状態は有効
        self.assertTrue(self.service.tasks[task_id].is_active)
        
        # 無効に切り替え
        result = self.service.toggle_task("test_user_006", task_id)
        self.assertTrue(result)
        self.assertFalse(self.service.tasks[task_id].is_active)
        
        # 有効に切り替え
        result = self.service.toggle_task("test_user_006", task_id)
        self.assertTrue(result)
        self.assertTrue(self.service.tasks[task_id].is_active)
        
        print("   ✅ タスク状態切り替え成功")

    def test_08_format_tasks_list(self):
        """タスク一覧フォーマットテスト"""
        print("\n🧪 テスト08: タスク一覧フォーマット")
        
        # タスクを作成
        task_id = self.service.create_auto_task(
            user_id="test_user_007",
            task_type=TaskType.WEATHER_DAILY.value,
            title="フォーマットテスト用タスク",
            description="タスク一覧フォーマットのテスト",
            schedule_pattern="daily",
            schedule_time="14:00",
            parameters={"location": "福岡"}
        )
        
        # タスク一覧を取得してフォーマット
        user_tasks = self.service.get_user_tasks("test_user_007")
        formatted_list = self.service.format_tasks_list(user_tasks)
        
        # フォーマットされた文字列の確認
        self.assertIn("自動実行タスク一覧", formatted_list)
        self.assertIn("フォーマットテスト用タスク", formatted_list)
        self.assertIn("daily 14:00", formatted_list)
        self.assertIn("✅ 有効", formatted_list)
        self.assertIn(task_id, formatted_list)
        
        # 空のタスクリストのフォーマット
        empty_formatted = self.service.format_tasks_list([])
        self.assertIn("設定されている自動実行タスクはありません", empty_formatted)
        
        print("   ✅ タスク一覧フォーマット成功")

    def test_09_data_persistence(self):
        """データ永続化テスト"""
        print("\n🧪 テスト09: データ永続化")
        
        # タスクを作成
        task_id = self.service.create_auto_task(
            user_id="test_user_008",
            task_type=TaskType.NEWS_DAILY.value,
            title="永続化テスト用タスク",
            description="データ永続化のテスト",
            schedule_pattern="daily",
            schedule_time="15:00",
            parameters={"keywords": ["永続化", "テスト"]}
        )
        
        # データファイルが作成されていることを確認
        tasks_file = os.path.join(self.temp_dir, "auto_tasks.json")
        self.assertTrue(os.path.exists(tasks_file))
        
        # ファイルの内容を確認
        with open(tasks_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertIn(task_id, saved_data)
        saved_task = saved_data[task_id]
        self.assertEqual(saved_task['title'], "永続化テスト用タスク")
        self.assertEqual(saved_task['user_id'], "test_user_008")
        
        # 新しいサービスインスタンスで読み込み
        new_service = AutoTaskService(
            storage_path=self.temp_dir,
            notification_service=self.mock_notification_service,
            weather_service=self.mock_weather_service,
            search_service=self.mock_search_service,
            gemini_service=self.mock_gemini_service
        )
        
        # データが正しく読み込まれていることを確認
        self.assertIn(task_id, new_service.tasks)
        loaded_task = new_service.tasks[task_id]
        self.assertEqual(loaded_task.title, "永続化テスト用タスク")
        self.assertEqual(loaded_task.user_id, "test_user_008")
        
        print("   ✅ データ永続化成功")

    @patch('services.auto_task_service.schedule')
    def test_10_task_execution_weather(self, mock_schedule):
        """天気タスク実行テスト"""
        print("\n🧪 テスト10: 天気タスク実行")
        
        # モックの設定
        self.mock_weather_service.get_current_weather.return_value = {
            'location': '東京',
            'temperature': 25,
            'condition': '晴れ'
        }
        self.mock_weather_service.get_weather_forecast.return_value = [
            {'day': '明日', 'temperature_high': 27, 'temperature_low': 18, 'condition': '曇り'}
        ]
        self.mock_weather_service.format_weather_message.return_value = "東京: 25°C 晴れ"
        self.mock_weather_service.format_forecast_message.return_value = "明日: 27/18°C 曇り"
        self.mock_notification_service.add_notification.return_value = "notification_123"
        
        # 天気タスクを作成
        task_id = self.service.create_auto_task(
            user_id="test_user_009",
            task_type=TaskType.WEATHER_DAILY.value,
            title="天気実行テスト",
            description="天気タスクの実行テスト",
            schedule_pattern="daily",
            schedule_time="07:00",
            parameters={"location": "東京"}
        )
        
        # タスクを手動実行
        self.service._execute_task(task_id)
        
        # 実行記録の確認
        task = self.service.tasks[task_id]
        self.assertIsNotNone(task.last_executed)
        self.assertEqual(task.execution_count, 1)
        
        # サービス呼び出しの確認
        self.mock_weather_service.get_current_weather.assert_called_with("東京")
        self.mock_weather_service.get_weather_forecast.assert_called_with("東京")
        self.mock_notification_service.add_notification.assert_called_once()
        
        print("   ✅ 天気タスク実行成功")

    @patch('services.auto_task_service.schedule')
    def test_11_task_execution_news(self, mock_schedule):
        """ニュースタスク実行テスト"""
        print("\n🧪 テスト11: ニュースタスク実行")
        
        # モックの設定
        mock_news_result = Mock()
        mock_news_result.title = "AI技術の最新動向"
        mock_news_result.snippet = "人工知能の技術が急速に進歩している..."
        mock_news_result.link = "https://example.com/ai-news"
        
        self.mock_search_service.search.return_value = [mock_news_result]
        self.mock_notification_service.add_notification.return_value = "notification_456"
        
        # ニュースタスクを作成
        task_id = self.service.create_auto_task(
            user_id="test_user_010",
            task_type=TaskType.NEWS_DAILY.value,
            title="ニュース実行テスト",
            description="ニュースタスクの実行テスト",
            schedule_pattern="daily",
            schedule_time="08:00",
            parameters={"keywords": ["AI", "技術"]}
        )
        
        # タスクを手動実行
        self.service._execute_task(task_id)
        
        # 実行記録の確認
        task = self.service.tasks[task_id]
        self.assertEqual(task.execution_count, 1)
        
        # サービス呼び出しの確認
        self.mock_search_service.search.assert_called()
        self.mock_notification_service.add_notification.assert_called_once()
        
        print("   ✅ ニュースタスク実行成功")


class TestMessageHandlerAutoTask(unittest.TestCase):
    """MessageHandler自動実行機能統合テスト"""

    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        
        # モックサービスの作成
        self.mock_gemini_service = Mock()
        self.mock_notification_service = Mock()
        self.mock_auto_task_service = Mock()
        
        # MessageHandlerのインスタンス作成
        self.handler = MessageHandler()
        
        print("✅ MessageHandler統合テスト準備完了")

    def tearDown(self):
        """テスト後のクリーンアップ"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_12_create_auto_task_intent(self):
        """自動実行タスク作成意図処理テスト"""
        print("\n🧪 テスト12: 自動実行タスク作成意図処理")
        
        # モックイベントの作成
        mock_event = Mock()
        mock_event.message = Mock()
        mock_event.message.text = "毎日7時に天気を配信して"
        mock_event.source.user_id = "test_user_011"
        
        # TextMessageタイプを正しく設定
        from linebot.models import TextMessage
        mock_event.message.__class__ = TextMessage
        
        # AI解析結果のモック
        self.mock_gemini_service.analyze_text.return_value = {
            'intent': 'create_auto_task',
            'confidence': 0.9,
            'auto_task': {
                'task_type': 'weather_daily',
                'title': '毎日の天気配信',
                'description': '毎日7時に天気を配信',
                'schedule_pattern': 'daily',
                'schedule_time': '07:00',
                'parameters': {'location': '東京'}
            }
        }
        
        # AutoTaskServiceのモック設定
        self.mock_auto_task_service.create_auto_task.return_value = "task_12345"
        
        # メッセージを処理
        response, quick_reply = self.handler.handle_message(
            event=mock_event,
            gemini_service=self.mock_gemini_service,
            notification_service=self.mock_notification_service,
            auto_task_service=self.mock_auto_task_service
        )
        
        # 応答の確認
        self.assertIn("自動実行タスクを作成しました", response)
        self.assertIn("task_12345", response)
        self.assertEqual(quick_reply, 'auto_task')
        
        # サービス呼び出しの確認
        self.mock_auto_task_service.create_auto_task.assert_called_once()
        
        print("   ✅ 自動実行タスク作成意図処理成功")

    def test_13_list_auto_tasks_intent(self):
        """自動実行タスク一覧意図処理テスト"""
        print("\n🧪 テスト13: 自動実行タスク一覧意図処理")
        
        # モックイベント
        mock_event = Mock()
        mock_event.message = Mock()
        mock_event.message.text = "自動実行一覧"
        mock_event.source.user_id = "test_user_012"
        
        # TextMessageタイプを正しく設定
        from linebot.models import TextMessage
        mock_event.message.__class__ = TextMessage
        
        # AI解析結果
        self.mock_gemini_service.analyze_text.return_value = {
            'intent': 'list_auto_tasks',
            'confidence': 0.95
        }
        
        # タスクリストのモック
        mock_tasks = [Mock()]
        mock_tasks[0].title = "テスト用タスク"
        self.mock_auto_task_service.get_user_tasks.return_value = mock_tasks
        self.mock_auto_task_service.format_tasks_list.return_value = "🤖 自動実行タスク一覧\n\n1. テスト用タスク"
        
        # メッセージを処理
        response, quick_reply = self.handler.handle_message(
            event=mock_event,
            gemini_service=self.mock_gemini_service,
            notification_service=self.mock_notification_service,
            auto_task_service=self.mock_auto_task_service
        )
        
        # 応答の確認
        self.assertIn("自動実行タスク一覧", response)
        self.assertEqual(quick_reply, 'auto_task')
        
        print("   ✅ 自動実行タスク一覧意図処理成功")


def run_comprehensive_tests():
    """包括的テストの実行"""
    print("🚀 自動実行・モニタリング機能 包括的テストスイート開始")
    print("=" * 60)
    
    # テストスイートの作成
    suite = unittest.TestSuite()
    
    # AutoTaskServiceテストを追加
    auto_task_tests = unittest.TestLoader().loadTestsFromTestCase(TestAutoTaskService)
    suite.addTests(auto_task_tests)
    
    # MessageHandler統合テストを追加
    handler_tests = unittest.TestLoader().loadTestsFromTestCase(TestMessageHandlerAutoTask)
    suite.addTests(handler_tests)
    
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📋 テスト結果サマリー")
    print(f"実行テスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失敗したテスト:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n⚠️ エラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n✅ 成功率: {success_rate:.1f}%")
    
    if result.wasSuccessful():
        print("🎉 すべてのテストが成功しました！")
    else:
        print("⚠️ 一部のテストが失敗しました。")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    try:
        success = run_comprehensive_tests()
        exit_code = 0 if success else 1
        print(f"\n🏁 テスト終了 (終了コード: {exit_code})")
        sys.exit(exit_code)
    except Exception as e:
        print(f"💥 テスト実行中に予期しないエラーが発生: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 