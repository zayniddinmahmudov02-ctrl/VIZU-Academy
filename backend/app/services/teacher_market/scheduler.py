"""Background round of the special lessons every INTERVAL seconds (daemon thread started with the backend).

It runs special_lessons.tick under a PostgreSQL advisory lock, so with several backend processes only one round runs at a time.
The room time limit does not depend on it alone: every room access closes an overdue room too (video_rooms.service.expire).
Switched off by TEACHER_MARKET_SCHEDULER_ENABLED=false and always off in the test environment."""

import logging
import threading
import time

from sqlalchemy import text

from app.core.config import settings

INTERVAL = 30
LOCK_KEY = 7_302_411  # pg advisory lock id of this job
log = logging.getLogger(__name__)
_started = False
_guard = threading.Lock()


def _round() -> None:
    from app.db.session import SessionLocal
    from app.services.teacher_market import special_lessons

    db = SessionLocal()
    try:
        if not db.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": LOCK_KEY}).scalar():
            return
        try:
            special_lessons.tick(db)
        finally:
            db.rollback()
            db.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": LOCK_KEY})
            db.commit()
    finally:
        db.close()


def _loop() -> None:
    while True:
        try:
            _round()
        except Exception:  # noqa: BLE001 — the loop must survive a bad round (DB restart, LiveKit down …)
            log.exception("special lesson scheduler round failed")
        time.sleep(INTERVAL)


def on_startup() -> None:
    global _started
    if not settings.TEACHER_MARKET_SCHEDULER_ENABLED or settings.APP_ENV == "test":
        return
    with _guard:
        if _started:
            return
        _started = True
    threading.Thread(target=_loop, name="special-lessons", daemon=True).start()
