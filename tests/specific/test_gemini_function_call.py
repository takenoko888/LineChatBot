#!/usr/bin/env python3
"""GeminiService function-calling dispatcher test"""
import os, sys, json, logging, pytz
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from core.function_registry import register_function

# Register simple echo function
@register_function(name="echo", description="Echo text")
def echo_text(text: str) -> str:
    return f"echo:{text}"

# Mock model --------------------------------------------------------------
class MockResponse:
    def __init__(self, text):
        self.text = text

class MockModel:
    def __init__(self, response_json):
        self._resp = json.dumps(response_json)
    def generate_content(self, *args, **kwargs):
        return MockResponse(self._resp)

# Mock GeminiService ------------------------------------------------------
from services.gemini_service import GeminiService
class DummyGemini(GeminiService):
    def __init__(self):
        # bypass parent init
        self.logger = logging.getLogger(__name__)
        self.jst = pytz.timezone('Asia/Tokyo')
        self.model = MockModel({
            "function_call": {
                "name": "echo",
                "arguments": {"text": "hello"}
            }
        })
        # Disable costly services
        self._conversation_memory = False
        self._smart_suggestion = False
    def _fallback_analysis(self, text: str):
        return {"intent": "fallback"}

def test_function_call_dispatch():
    gs = DummyGemini()
    output = gs.analyze_text("任意の入力")
    assert output["intent"] == "function_result"
    assert output["result"] == "echo:hello"

if __name__ == "__main__":
    import pytest, sys
    sys.exit(pytest.main([__file__])) 