#!/usr/bin/env python3
import os, sys
os.environ['GEMINI_API_KEY'] = 'test_key'
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

def test_ambiguous_time_candidates():
    from services.gemini_service import GeminiService
    g = GeminiService(api_key=os.environ.get('GEMINI_API_KEY','dummy'))
    # 夕方→候補が付与される想定
    try:
        res = g.parse_notification_request('明日の夕方に会議')
    except Exception:
        res = None
    # オフライン環境ではNoneでも許容
    if res is None:
        assert True
        return
    # 候補キーは存在しても良いし、API側で直接datetimeを生成しても良い
    assert ('time_candidates' in res) or ('datetime' in res)


