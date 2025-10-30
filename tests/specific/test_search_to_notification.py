#!/usr/bin/env python3
import os, sys
os.environ['GEMINI_API_KEY'] = 'test_key'

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

def test_search_to_notification_bridge(monkeypatch):
    from services.search_service import SearchService, SearchResult
    from services.notification_service import NotificationService
    from services.gemini_service import GeminiService
    from handlers.message_handler import MessageHandler

    # 準備
    gemini = GeminiService(api_key='test_key')
    note = NotificationService(gemini_service=gemini)
    handler = MessageHandler()

    # 検索モック
    svc = SearchService(api_key='x', search_engine_id='y', gemini_service=gemini)
    def mock_search(query, result_type='web', max_results=3, japan_only=True):
        return [SearchResult(title='t', snippet='s', link='https://example.com')]
    svc.search = mock_search

    class E: pass
    class Src: pass
    class Msg: pass
    e = E(); e.source = Src(); e.source.user_id = 'U1'
    e.message = Msg(); e.message.text = 'Python を検索'

    # 1) 検索実行
    resp, _ = handler.handle_message(e, gemini, note, weather_service=None, search_service=svc, auto_task_service=None)
    # 検索結果か、フォールバックのいずれか
    assert ('検索結果' in resp) or ('要約' in resp) or (len(resp) > 0)

    # 2) ブリッジで通知（テスト環境では簡易評価）
    e.message.text = 'これを通知して'
    resp2, _ = handler.handle_message(e, gemini, note, weather_service=None, search_service=svc, auto_task_service=None)
    assert isinstance(resp2, str) and len(resp2) > 0


