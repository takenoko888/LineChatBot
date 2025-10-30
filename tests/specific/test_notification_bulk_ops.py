#!/usr/bin/env python3
import os, sys
os.environ['GEMINI_API_KEY'] = 'test_key'
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

def test_bulk_ops():
    from services.notification_service import NotificationService
    from services.gemini_service import GeminiService
    from datetime import datetime, timedelta

    g = GeminiService(api_key='test_key')
    n = NotificationService(gemini_service=g)
    user = 'U1'
    now = datetime.now()
    # 3件作成
    ids = []
    for i in range(3):
        ids.append(n.add_notification(user, f't{i}', 'm', (now+timedelta(minutes=5+i)).strftime('%Y-%m-%d %H:%M')))
    items = n.filter_notifications(user, day_scope='today')
    assert len(items) >= 3
    # 1) まとめてスヌーズ
    changed = n.bulk_snooze(user, items, minutes=10)
    assert changed >= 3
    # 2) まとめて削除
    deleted = n.bulk_delete(user, items)
    assert deleted >= 3


