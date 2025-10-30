import types

from handlers.message_handler import MessageHandler
import handlers.message_handler as mh


class DummyMessage:
    def __init__(self, text: str):
        self.text = text
        self.id = "msg-1"


class DummySource:
    def __init__(self, user_id: str):
        self.user_id = user_id


class DummyEvent:
    def __init__(self, text: str, user_id: str = "U1", reply_token: str = "rtok"):
        self.message = DummyMessage(text)
        self.source = DummySource(user_id)
        self.reply_token = reply_token


class FakeGemini:
    def analyze_text(self, text: str, user_id: str = "default"):
        # 解析結果は使わないが最低限返す
        return {"intent": "chat", "confidence": 0.9}


class FakeNotification:
    pass


class DummyIntegratedResponse:
    def __init__(self, response: str):
        self.response = response


def test_composite_text_prefers_integrated_service(monkeypatch):
    # Patch integrated_service_manager.process_integrated_request_sync
    def fake_process_sync(_req):
        return DummyIntegratedResponse("INTEGRATED_OK")

    monkeypatch.setattr(
        mh.integrated_service_manager,
        "process_integrated_request_sync",
        fake_process_sync,
        raising=True,
    )

    handler = MessageHandler()
    event = DummyEvent("毎日6時に天気とニュースを確認して通知して")

    msg, qr = handler.handle_message(
        event=event,
        gemini_service=FakeGemini(),
        notification_service=FakeNotification(),
        weather_service=None,
        search_service=None,
        auto_task_service=None,
    )

    assert msg == "INTEGRATED_OK"

