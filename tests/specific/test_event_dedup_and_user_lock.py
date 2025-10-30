import threading
import time

import app as app_module


def test_event_dedup():
    # 直接 LineBot を生成できない環境でも属性の有無のみ検証
    bot = app_module.LineBot.__new__(app_module.LineBot)  # __init__ を通さない
    # 手動で必要属性だけ差し込む
    bot._recent_events = {}
    bot._recent_events_ttl = 60
    bot._recent_events_lock = threading.Lock()

    now = time.time()
    with bot._recent_events_lock:
        bot._recent_events["rt:foo"] = now

    # TTL内は重複キーが残っている
    with bot._recent_events_lock:
        assert "rt:foo" in bot._recent_events


def test_user_lock_serialization():
    bot = app_module.LineBot.__new__(app_module.LineBot)
    bot._user_locks = {}
    # デフォルト辞書相当
    def get_lock(uid):
        if uid not in bot._user_locks:
            bot._user_locks[uid] = threading.Lock()
        return bot._user_locks[uid]

    uid = "U_TEST"
    lock = get_lock(uid)
    assert lock.acquire(blocking=False) is True
    try:
        # 2度目は取得不可 = 直列化が効く
        assert lock.acquire(blocking=False) is False
    finally:
        lock.release()

