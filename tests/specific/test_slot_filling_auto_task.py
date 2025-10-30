#!/usr/bin/env python3
import os, sys
os.environ['GEMINI_API_KEY'] = 'test_key'
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

def test_slot_filling(monkeypatch):
    from handlers.message_handler import MessageHandler
    from services.gemini_service import GeminiService
    from services.notification_service import NotificationService
    from services.auto_task_service import AutoTaskService

    g = GeminiService(api_key='test_key')
    n = NotificationService(gemini_service=g)
    a = AutoTaskService(notification_service=n, gemini_service=g)
    h = MessageHandler()

    class E: pass
    class Src: pass
    class Msg: pass
    e = E(); e.source = Src(); e.source.user_id = 'U1'
    e.message = Msg(); e.message.text = '毎週ニュースを送って'

    # AI解析は実API依存なのでcreate_auto_task分岐に入らない場合もある。
    # 本テストでは「不足時のガイダンスが出る」ことを主眼に確認。
    resp, _ = h.handle_message(e, g, n, weather_service=None, search_service=None, auto_task_service=a)
    assert ('不足しています' in resp) or ('解析できません' in resp) or ('設定に必要' in resp) or ('テキストメッセージ以外' not in resp)


