"""Background round every INTERVAL seconds (daemon thread started with the backend): special_lessons.tick and, since 2026-11-28,
vizu_pay.expiry_reminders.tick (course access "ends in 3 days" notification).

It runs under a PostgreSQL advisory lock, so with several backend processes only one round runs at a time. The lock lives on a
connection of its own held for the whole round (2026-11-28: it used to sit on the session's connection, which goes back to the pool
at every commit, so the unlock could hit another connection and leave the lock behind). Each job fails alone (rollback + log).
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


def _jobs():
    from app.services.teacher_market import special_lessons
    from app.services.vizu_pay import expiry_reminders

    # course access: "ends in 3 days" notification, once per order (owner 2026-11-25)
    return (("special lessons", special_lessons.tick), ("course access reminders", expiry_reminders.tick))


def _round() -> bool:
    """One round; False when another process holds the lock (nothing done)."""
    from app.db.database import engine
    from app.db.session import SessionLocal

    with engine.connect() as lock:  # session-level lock: keep this one connection until the unlock
        got = bool(lock.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": LOCK_KEY}).scalar())
        lock.commit()
        if not got:
            return False
        try:
            db = SessionLocal()
            try:
                for name, job in _jobs():
                    try:
                        job(db)
                    except Exception:  # noqa: BLE001 — one job failing must not stop the other
                        db.rollback()
                        log.exception("%s round failed", name)
            finally:
                db.close()
        finally:
            lock.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": LOCK_KEY})
            lock.commit()
    return True


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
