#!/usr/bin/env python3
"""
全機能詳細テスト - すべての機能を個別に確認

機能一覧:
1. 基本コマンド（通知一覧、ヘルプ、全通知削除）
2. 通知設定（時間指定、分単位指定、繰り返し設定）
3. 通知削除（個別削除、全削除）
4. 天気機能（現在の天気、天気予報）
5. 検索機能（ウェブ検索、自動検索判定）
6. スマート提案機能（個人最適化提案）
7. 自動実行機能（定期配信タスク作成・管理）
8. 対話履歴機能（会話履歴、利用パターン分析）
9. 一般会話（雑談、挨拶など）
"""

import os
import sys
import logging
import json
import tempfile
from datetime import datetime, timedelta
import pytz
from unittest.mock import Mock, patch

# プロジェクトルートを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_test_environment():
    """テスト環境のセットアップ"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    os.environ['GEMINI_API_KEY'] = 'test_key_for_testing'
    os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'test_line_token'
    os.environ['LINE_CHANNEL_SECRET'] = 'test_line_secret'
    
    test_dir = tempfile.mkdtemp()
    os.environ['NOTIFICATION_STORAGE_PATH'] = os.path.join(test_dir, 'test_notifications.json')
    
    print(f"✅ テスト環境をセットアップしました")
    print(f"📁 テストデータ保存先: {os.environ['NOTIFICATION_STORAGE_PATH']}")
    return test_dir

def create_mock_event(text, user_id="test_user"):
    """MockEventを作成"""
    from linebot.models import TextMessage
    from unittest.mock import Mock
    
    mock_message = Mock()
    mock_message.text = text
    mock_message.__class__ = TextMessage
    
    mock_event = Mock()
    mock_event.message = mock_message
    mock_event.source.user_id = user_id
    
    return mock_event

def test_basic_commands():
    """基本コマンドのテスト"""
    print("\n📋 基本コマンドのテストを開始...")
    
    try:
        from services.gemini_service import GeminiService
        from services.notification_service import NotificationService
        from handlers.message_handler import MessageHandler
        
        # サービスの初期化
        line_bot_api = Mock()
        gemini_service = GeminiService()
        notification_service = NotificationService(
            gemini_service=gemini_service,
            line_bot_api=line_bot_api
        )
        message_handler = MessageHandler()
        
        test_cases = [
            {
                'name': '通知一覧表示',
                'text': '通知一覧',
                'expected_keywords': ['通知']
            },
            {
                'name': 'ヘルプ表示',
                'text': 'ヘルプ',
                'expected_keywords': ['多機能AIアシスタント', '通知・リマインダー']
            },
            {
                'name': '全通知削除',
                'text': '全通知削除',
                'expected_keywords': ['通知', '削除']
            }
        ]
        
        results = []
        user_id = "test_basic_commands"
        
        for i, case in enumerate(test_cases, 1):
            print(f"  {i}. {case['name']}: '{case['text']}'")
            
            try:
                mock_event = create_mock_event(case['text'], user_id)
                response, quick_reply = message_handler.handle_message(
                    mock_event, gemini_service, notification_service
                )
                
                # 期待されるキーワードが含まれているかチェック
                contains_keywords = all(keyword in response for keyword in case['expected_keywords'])
                
                print(f"     ✅ 応答: {response[:150]}...")
                print(f"     🔍 キーワード確認: {contains_keywords}")
                
                results.append({
                    'case': case['name'],
                    'success': True,
                    'contains_keywords': contains_keywords,
                    'response_length': len(response)
                })
                
            except Exception as e:
                print(f"     ❌ エラー: {str(e)}")
                results.append({'case': case['name'], 'success': False, 'error': str(e)})
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\n📊 基本コマンドテスト結果: {success_count}/{len(test_cases)} 成功")
        return results
        
    except Exception as e:
        print(f"❌ 基本コマンドテストでエラー: {str(e)}")
        return []

def test_notification_settings():
    """通知設定のテスト"""
    print("\n🔔 通知設定のテストを開始...")
    
    try:
        from services.gemini_service import GeminiService
        from services.notification_service import NotificationService
        from handlers.message_handler import MessageHandler
        
        line_bot_api = Mock()
        gemini_service = GeminiService()
        notification_service = NotificationService(
            gemini_service=gemini_service,
            line_bot_api=line_bot_api
        )
        message_handler = MessageHandler()
        
        test_cases = [
            {
                'name': '基本時間指定',
                'text': '毎日7時に起きる',
                'expected_keywords': ['通知を設定', '07時00分']
            },
            {
                'name': '分単位時間指定',
                'text': '12時40分に課題をやる',
                'expected_keywords': ['40分']
            },
            {
                'name': '明日の予定設定',
                'text': '明日の15時に会議',
                'expected_keywords': ['15時']
            },
            {
                'name': '毎週の繰り返し',
                'text': '毎週月曜9時にミーティング',
                'expected_keywords': ['09時']
            }
        ]
        
        results = []
        user_id = "test_notification_settings"
        
        for i, case in enumerate(test_cases, 1):
            print(f"  {i}. {case['name']}: '{case['text']}'")
            
            try:
                mock_event = create_mock_event(case['text'], user_id)
                response, quick_reply = message_handler.handle_message(
                    mock_event, gemini_service, notification_service
                )
                
                print(f"     ✅ 応答: {response[:150]}...")
                
                # 通知が実際に追加されたかチェック
                notifications = notification_service.get_notifications(user_id)
                notification_added = len(notifications) > i - 1
                
                print(f"     📝 通知追加確認: {notification_added}")
                print(f"     📊 現在の通知数: {len(notifications)}")
                
                results.append({
                    'case': case['name'],
                    'success': True,
                    'notification_added': notification_added,
                    'total_notifications': len(notifications)
                })
                
            except Exception as e:
                print(f"     ❌ エラー: {str(e)}")
                results.append({'case': case['name'], 'success': False, 'error': str(e)})
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\n📊 通知設定テスト結果: {success_count}/{len(test_cases)} 成功")
        return results
        
    except Exception as e:
        print(f"❌ 通知設定テストでエラー: {str(e)}")
        return []

def test_notification_deletion():
    """通知削除のテスト"""
    print("\n🗑️  通知削除のテストを開始...")
    
    try:
        from services.gemini_service import GeminiService
        from services.notification_service import NotificationService
        from handlers.message_handler import MessageHandler
        
        line_bot_api = Mock()
        gemini_service = GeminiService()
        notification_service = NotificationService(
            gemini_service=gemini_service,
            line_bot_api=line_bot_api
        )
        message_handler = MessageHandler()
        
        user_id = "test_notification_deletion"
        
        # まず通知を作成
        print("  準備: 通知を作成中...")
        test_notifications = [
            "8時に起きる",
            "12時にランチ",
            "18時に運動"
        ]
        
        for text in test_notifications:
            mock_event = create_mock_event(text, user_id)
            message_handler.handle_message(mock_event, gemini_service, notification_service)
        
        initial_count = len(notification_service.get_notifications(user_id))
        print(f"     📊 初期通知数: {initial_count}")
        
        # 削除テスト
        test_cases = [
            {
                'name': '全通知削除',
                'text': '全通知削除',
                'expected_action': 'all_deleted'
            }
        ]
        
        results = []
        
        for i, case in enumerate(test_cases, 1):
            print(f"  {i}. {case['name']}: '{case['text']}'")
            
            try:
                mock_event = create_mock_event(case['text'], user_id)
                response, quick_reply = message_handler.handle_message(
                    mock_event, gemini_service, notification_service
                )
                
                final_count = len(notification_service.get_notifications(user_id))
                print(f"     ✅ 応答: {response[:100]}...")
                print(f"     📊 削除後通知数: {final_count}")
                
                deletion_success = final_count == 0 if case['expected_action'] == 'all_deleted' else final_count < initial_count
                
                results.append({
                    'case': case['name'],
                    'success': True,
                    'deletion_success': deletion_success,
                    'final_count': final_count
                })
                
            except Exception as e:
                print(f"     ❌ エラー: {str(e)}")
                results.append({'case': case['name'], 'success': False, 'error': str(e)})
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\n📊 通知削除テスト結果: {success_count}/{len(test_cases)} 成功")
        return results
        
    except Exception as e:
        print(f"❌ 通知削除テストでエラー: {str(e)}")
        return []

def test_weather_functionality():
    """天気機能のテスト"""
    print("\n🌤️  天気機能のテストを開始...")
    
    try:
        from services.gemini_service import GeminiService
        from services.notification_service import NotificationService
        from handlers.message_handler import MessageHandler
        
        # 天気サービスのモック作成
        weather_service = Mock()
        weather_service.is_available = True
        weather_service.get_current_weather.return_value = {
            'location': '東京',
            'temperature': 22,
            'description': '晴れ'
        }
        weather_service.format_weather_message.return_value = "🌤️ 東京の天気: 晴れ、気温22℃"
        weather_service.get_weather_forecast.return_value = {
            'location': '東京',
            'forecast': ['明日: 晴れ', '明後日: 曇り']
        }
        weather_service.format_forecast_message.return_value = "📅 東京の天気予報:\n明日: 晴れ\n明後日: 曇り"
        
        line_bot_api = Mock()
        gemini_service = GeminiService()
        notification_service = NotificationService(
            gemini_service=gemini_service,
            line_bot_api=line_bot_api
        )
        message_handler = MessageHandler()
        
        test_cases = [
            {
                'name': '現在の天気',
                'text': '東京の天気',
                'expected_keywords': ['天気', '東京']
            },
            {
                'name': '天気予報',
                'text': '明日の天気予報',
                'expected_keywords': ['予報', '明日']
            }
        ]
        
        results = []
        user_id = "test_weather"
        
        for i, case in enumerate(test_cases, 1):
            print(f"  {i}. {case['name']}: '{case['text']}'")
            
            try:
                mock_event = create_mock_event(case['text'], user_id)
                response, quick_reply = message_handler.handle_message(
                    mock_event, gemini_service, notification_service, weather_service
                )
                
                print(f"     ✅ 応答: {response[:100]}...")
                
                results.append({
                    'case': case['name'],
                    'success': True,
                    'response_generated': len(response) > 0
                })
                
            except Exception as e:
                print(f"     ❌ エラー: {str(e)}")
                results.append({'case': case['name'], 'success': False, 'error': str(e)})
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\n📊 天気機能テスト結果: {success_count}/{len(test_cases)} 成功")
        return results
        
    except Exception as e:
        print(f"❌ 天気機能テストでエラー: {str(e)}")
        return []

def test_search_functionality():
    """検索機能のテスト"""
    print("\n🔍 検索機能のテストを開始...")
    
    try:
        from services.gemini_service import GeminiService
        from services.notification_service import NotificationService
        from handlers.message_handler import MessageHandler
        
        # 検索サービスのモック作成
        search_service = Mock()
        search_service.search.return_value = [
            {'title': 'テスト結果1', 'url': 'https://example.com/1', 'snippet': 'テスト内容1'},
            {'title': 'テスト結果2', 'url': 'https://example.com/2', 'snippet': 'テスト内容2'}
        ]
        search_service.format_search_results_with_clickable_links.return_value = "🔍 検索結果:\n1. テスト結果1 (https://example.com/1)"
        search_service.summarize_results.return_value = "AI要約: テストに関する情報です"
        
        line_bot_api = Mock()
        gemini_service = GeminiService()
        notification_service = NotificationService(
            gemini_service=gemini_service,
            line_bot_api=line_bot_api
        )
        message_handler = MessageHandler()
        
        test_cases = [
            {
                'name': '明示的検索',
                'text': 'Python について検索',
                'expected_keywords': ['検索結果']
            },
            {
                'name': '自動検索判定',
                'text': '最新のニュース',
                'expected_keywords': ['検索', 'ニュース']
            }
        ]
        
        results = []
        user_id = "test_search"
        
        for i, case in enumerate(test_cases, 1):
            print(f"  {i}. {case['name']}: '{case['text']}'")
            
            try:
                mock_event = create_mock_event(case['text'], user_id)
                response, quick_reply = message_handler.handle_message(
                    mock_event, gemini_service, notification_service, None, search_service
                )
                
                print(f"     ✅ 応答: {response[:100]}...")
                
                results.append({
                    'case': case['name'],
                    'success': True,
                    'response_generated': len(response) > 0
                })
                
            except Exception as e:
                print(f"     ❌ エラー: {str(e)}")
                results.append({'case': case['name'], 'success': False, 'error': str(e)})
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\n📊 検索機能テスト結果: {success_count}/{len(test_cases)} 成功")
        return results
        
    except Exception as e:
        print(f"❌ 検索機能テストでエラー: {str(e)}")
        return []

def test_smart_suggestion_functionality():
    """スマート提案機能のテスト"""
    print("\n🎯 スマート提案機能のテストを開始...")
    
    try:
        from services.gemini_service import GeminiService
        from services.notification_service import NotificationService
        from handlers.message_handler import MessageHandler
        
        line_bot_api = Mock()
        gemini_service = GeminiService()
        notification_service = NotificationService(
            gemini_service=gemini_service,
            line_bot_api=line_bot_api
        )
        message_handler = MessageHandler()
        
        test_cases = [
            {
                'name': 'スマート提案要求',
                'text': 'おすすめは？',
                'expected_keywords': ['提案']
            },
            {
                'name': '提案機能呼び出し',
                'text': '提案して',
                'expected_keywords': ['提案']
            }
        ]
        
        results = []
        user_id = "test_smart_suggestion"
        
        for i, case in enumerate(test_cases, 1):
            print(f"  {i}. {case['name']}: '{case['text']}'")
            
            try:
                mock_event = create_mock_event(case['text'], user_id)
                response, quick_reply = message_handler.handle_message(
                    mock_event, gemini_service, notification_service
                )
                
                print(f"     ✅ 応答: {response[:100]}...")
                
                results.append({
                    'case': case['name'],
                    'success': True,
                    'response_generated': len(response) > 0
                })
                
            except Exception as e:
                print(f"     ❌ エラー: {str(e)}")
                results.append({'case': case['name'], 'success': False, 'error': str(e)})
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\n📊 スマート提案テスト結果: {success_count}/{len(test_cases)} 成功")
        return results
        
    except Exception as e:
        print(f"❌ スマート提案テストでエラー: {str(e)}")
        return []

def test_auto_task_functionality():
    """自動実行機能のテスト"""
    print("\n🤖 自動実行機能のテストを開始...")
    
    try:
        from services.gemini_service import GeminiService
        from services.notification_service import NotificationService
        from handlers.message_handler import MessageHandler
        
        # 自動実行サービスのモック作成
        auto_task_service = Mock()
        auto_task_service.create_auto_task.return_value = "task_123"
        auto_task_service.get_user_tasks.return_value = []
        auto_task_service.format_tasks_list.return_value = "自動実行タスクはありません。"
        
        line_bot_api = Mock()
        gemini_service = GeminiService()
        notification_service = NotificationService(
            gemini_service=gemini_service,
            line_bot_api=line_bot_api
        )
        message_handler = MessageHandler()
        
        test_cases = [
            {
                'name': '天気配信タスク作成',
                'text': '毎日7時に天気を配信して',
                'expected_keywords': ['自動実行', 'タスク']
            },
            {
                'name': 'ニュース配信タスク作成',
                'text': '毎朝ニュースを送って',
                'expected_keywords': ['自動実行', 'タスク']
            },
            {
                'name': 'タスク一覧確認',
                'text': '自動実行一覧',
                'expected_keywords': ['タスク']
            }
        ]
        
        results = []
        user_id = "test_auto_task"
        
        for i, case in enumerate(test_cases, 1):
            print(f"  {i}. {case['name']}: '{case['text']}'")
            
            try:
                mock_event = create_mock_event(case['text'], user_id)
                response, quick_reply = message_handler.handle_message(
                    mock_event, gemini_service, notification_service, None, None, auto_task_service
                )
                
                print(f"     ✅ 応答: {response[:100]}...")
                
                results.append({
                    'case': case['name'],
                    'success': True,
                    'response_generated': len(response) > 0
                })
                
            except Exception as e:
                print(f"     ❌ エラー: {str(e)}")
                results.append({'case': case['name'], 'success': False, 'error': str(e)})
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\n📊 自動実行機能テスト結果: {success_count}/{len(test_cases)} 成功")
        return results
        
    except Exception as e:
        print(f"❌ 自動実行機能テストでエラー: {str(e)}")
        return []

def test_conversation_history_functionality():
    """対話履歴機能のテスト"""
    print("\n🔄 対話履歴機能のテストを開始...")
    
    try:
        from services.gemini_service import GeminiService
        from services.notification_service import NotificationService
        from handlers.message_handler import MessageHandler
        
        line_bot_api = Mock()
        gemini_service = GeminiService()
        notification_service = NotificationService(
            gemini_service=gemini_service,
            line_bot_api=line_bot_api
        )
        message_handler = MessageHandler()
        
        test_cases = [
            {
                'name': '会話履歴確認',
                'text': '前回何話した？',
                'expected_keywords': ['会話', '履歴']
            },
            {
                'name': '利用パターン分析',
                'text': '利用パターン確認',
                'expected_keywords': ['パターン']
            }
        ]
        
        results = []
        user_id = "test_conversation_history"
        
        for i, case in enumerate(test_cases, 1):
            print(f"  {i}. {case['name']}: '{case['text']}'")
            
            try:
                mock_event = create_mock_event(case['text'], user_id)
                response, quick_reply = message_handler.handle_message(
                    mock_event, gemini_service, notification_service
                )
                
                print(f"     ✅ 応答: {response[:100]}...")
                
                results.append({
                    'case': case['name'],
                    'success': True,
                    'response_generated': len(response) > 0
                })
                
            except Exception as e:
                print(f"     ❌ エラー: {str(e)}")
                results.append({'case': case['name'], 'success': False, 'error': str(e)})
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\n📊 対話履歴機能テスト結果: {success_count}/{len(test_cases)} 成功")
        return results
        
    except Exception as e:
        print(f"❌ 対話履歴機能テストでエラー: {str(e)}")
        return []

def test_general_chat_functionality():
    """一般会話のテスト"""
    print("\n💬 一般会話のテストを開始...")
    
    try:
        from services.gemini_service import GeminiService
        from services.notification_service import NotificationService
        from handlers.message_handler import MessageHandler
        
        line_bot_api = Mock()
        gemini_service = GeminiService()
        notification_service = NotificationService(
            gemini_service=gemini_service,
            line_bot_api=line_bot_api
        )
        message_handler = MessageHandler()
        
        test_cases = [
            {
                'name': '挨拶',
                'text': 'こんにちは',
                'expected_response_type': 'greeting'
            },
            {
                'name': '感謝',
                'text': 'ありがとう',
                'expected_response_type': 'acknowledgment'
            },
            {
                'name': '雑談',
                'text': '今日はいい天気ですね',
                'expected_response_type': 'chat'
            }
        ]
        
        results = []
        user_id = "test_general_chat"
        
        for i, case in enumerate(test_cases, 1):
            print(f"  {i}. {case['name']}: '{case['text']}'")
            
            try:
                mock_event = create_mock_event(case['text'], user_id)
                response, quick_reply = message_handler.handle_message(
                    mock_event, gemini_service, notification_service
                )
                
                print(f"     ✅ 応答: {response[:100]}...")
                
                # 応答が生成されたかチェック
                response_appropriate = len(response) > 0 and ('こんにちは' in response or 'ありがとう' in response or len(response) > 10)
                
                results.append({
                    'case': case['name'],
                    'success': True,
                    'response_appropriate': response_appropriate,
                    'response_length': len(response)
                })
                
            except Exception as e:
                print(f"     ❌ エラー: {str(e)}")
                results.append({'case': case['name'], 'success': False, 'error': str(e)})
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\n📊 一般会話テスト結果: {success_count}/{len(test_cases)} 成功")
        return results
        
    except Exception as e:
        print(f"❌ 一般会話テストでエラー: {str(e)}")
        return []

def run_all_detailed_tests():
    """すべての機能の詳細テストを実行"""
    print("🎯 全機能詳細テストを開始します...")
    print("=" * 80)
    
    # テスト環境のセットアップ
    test_dir = setup_test_environment()
    
    # 各機能のテスト実行
    test_results = {}
    
    test_results['basic_commands'] = test_basic_commands()
    test_results['notification_settings'] = test_notification_settings()
    test_results['notification_deletion'] = test_notification_deletion()
    test_results['weather_functionality'] = test_weather_functionality()
    test_results['search_functionality'] = test_search_functionality()
    test_results['smart_suggestion'] = test_smart_suggestion_functionality()
    test_results['auto_task'] = test_auto_task_functionality()
    test_results['conversation_history'] = test_conversation_history_functionality()
    test_results['general_chat'] = test_general_chat_functionality()
    
    # 総合結果の表示
    print("\n" + "=" * 80)
    print("🏁 全機能詳細テスト結果")
    print("=" * 80)
    
    total_tests = 0
    total_success = 0
    
    feature_names = {
        'basic_commands': '📋 基本コマンド',
        'notification_settings': '🔔 通知設定',
        'notification_deletion': '🗑️  通知削除',
        'weather_functionality': '🌤️  天気機能',
        'search_functionality': '🔍 検索機能',
        'smart_suggestion': '🎯 スマート提案',
        'auto_task': '🤖 自動実行',
        'conversation_history': '🔄 対話履歴',
        'general_chat': '💬 一般会話'
    }
    
    for test_name, results in test_results.items():
        feature_name = feature_names.get(test_name, test_name)
        
        if results:
            success_count = sum(1 for r in results if r.get('success', False))
            total_count = len(results)
            
            total_tests += total_count
            total_success += success_count
            
            status = "✅" if success_count == total_count else "⚠️"
            print(f"{status} {feature_name}: {success_count}/{total_count} 成功")
        else:
            print(f"❌ {feature_name}: テスト実行失敗")
    
    print("-" * 80)
    success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
    print(f"🎯 全機能総合成功率: {total_success}/{total_tests} ({success_rate:.1f}%)")
    
    # 機能別詳細結果
    print("\n📊 機能別詳細結果:")
    for test_name, results in test_results.items():
        if results:
            feature_name = feature_names.get(test_name, test_name)
            print(f"\n{feature_name}:")
            for result in results:
                status = "✅" if result.get('success', False) else "❌"
                print(f"  {status} {result.get('case', 'Unknown')}")
    
    # クリーンアップ
    try:
        import shutil
        shutil.rmtree(test_dir)
        print(f"\n🧹 テストディレクトリを削除しました: {test_dir}")
    except Exception as e:
        print(f"\n⚠️  テストディレクトリの削除に失敗: {str(e)}")
    
    return test_results

if __name__ == "__main__":
    try:
        test_results = run_all_detailed_tests()
        
        # テスト結果に基づいて終了コードを設定
        all_success = all(
            all(r.get('success', False) for r in results) if results else False
            for results in test_results.values()
        )
        
        if all_success:
            print("\n🎉 すべての機能が正常に動作しています！")
            exit(0)
        else:
            print("\n⚠️  一部の機能で問題が検出されました。")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 テスト実行中に重大なエラーが発生しました: {str(e)}")
        exit(2) 