"""Activity tracking: heartbeats -> server-credited active time (student_sessions) and what it was spent on (student_activity_events).

The browser never reports a duration. The server measures the time between two heartbeats on its own clock and credits at most
MAX_CREDIT seconds for one heartbeat, so a heartbeat sent more often, a forged timestamp or a tab left open adds nothing.

* A tab sends a heartbeat every ~30 s only while the student is really active: the page is visible and there was input in the
  last 2 minutes — or a song / film is playing (then also from a hidden tab). An idle or hidden tab sends nothing, so its
  time is never counted. Closing the page sends a last heartbeat (`final`).
* Session: credit = min(now - session.last_seen_at, MAX_CREDIT). The first heartbeat of a session credits 0; a pause longer
  than SESSION_GAP starts a new session. Every tab of a student shares the one open session (partial unique index), so two
  tabs never count the same minute twice. A session never crosses a Tashkent day (a new day closes it).
* Contexts (what the time was spent on): COURSE / WORTSCHATZ / EXAM / BOOK = the visible page, MUSIC / FILM = what is playing.
  Each context is one event row, extended while heartbeats keep coming and credited the same way per row (two tabs on the same
  film count once). MUSIC / FILM are credited only when the playback position reported by the player moved since the last
  heartbeat (paused = nothing), the item exists, is published and the student may play it; BOOK only for a book the student
  may open (or read the free preview of); COURSE / WORTSCHATZ need an existing lesson. Anything else is ignored.
* Only STUDENT accounts are tracked. One advisory transaction lock per user serialises concurrent heartbeats of its tabs; the
  same tab sending again within DUPLICATE_SECONDS is dropped without a write.
"""

from datetime import date, datetime, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.security.roles import UserRole
from app.models.lesson import Lesson
from app.models.medien import KIND_BOOK, KIND_FILM, KIND_SONG, STATUS_PUBLISHED, Film, MediaBook, Song
from app.models.student_activity import (AREA_BOOK, AREA_COURSE, AREA_EXAM, AREA_FILM, AREA_MUSIC, AREA_WORTSCHATZ, AREAS,
                                         StudentActivityEvent, StudentSession)
from app.models.user import User
from app.services.medien import common as media
from app.services.medien.catalog import preview_limit

TZ = ZoneInfo("Asia/Tashkent")
MAX_CREDIT = 45  # seconds for one heartbeat (the browser sends one every ~30 s)
SESSION_GAP = 150  # seconds without a heartbeat -> the next one starts a new session / event
DUPLICATE_SECONDS = 3  # the same tab again within this time: dropped
MAX_TABS = 12
PLAYED = (AREA_MUSIC, AREA_FILM)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def local_day(at: datetime) -> date:
    return _aware(at).astimezone(TZ).date()


def credit(last: datetime | None, now: datetime) -> int:
    """Seconds one heartbeat may add after the previous one at `last` (pure): 0 for the first one, never more than MAX_CREDIT,
    nothing after a pause longer than SESSION_GAP (that heartbeat starts a new stretch)."""
    if last is None:
        return 0
    elapsed = (now - _aware(last)).total_seconds()
    if elapsed <= 0 or elapsed > SESSION_GAP:
        return 0
    return int(min(elapsed, MAX_CREDIT))


def _media_ok(db: Session, user: User, area: str, ref: UUID | None) -> tuple[bool, int | None]:
    """(may this context be credited, the item's length in seconds if known)."""
    if ref is None:
        return area in (AREA_WORTSCHATZ, AREA_EXAM), None
    if area in (AREA_COURSE, AREA_WORTSCHATZ):
        return db.get(Lesson, ref) is not None, None
    if area == AREA_EXAM:
        return True, None
    kind, model = {AREA_MUSIC: (KIND_SONG, Song), AREA_FILM: (KIND_FILM, Film), AREA_BOOK: (KIND_BOOK, MediaBook)}[area]
    item = db.get(model, ref)
    if item is None or item.status != STATUS_PUBLISHED:
        return False, None
    if not media.can_access(db, user, kind, item):
        if area != AREA_BOOK or preview_limit(item) <= 0:  # the free preview pages of a paid book count as reading
            return False, None
    if area == AREA_MUSIC:
        return True, (item.duration_ms // 1000 + 5) if item.duration_ms else None
    if area == AREA_FILM:
        seconds = (item.video_duration_ms // 1000) if item.video_duration_ms else ((item.duration_minutes or 0) * 60 or None)
        return True, (seconds + 5) if seconds else None
    return True, None


def _open_session(db: Session, user_id, now: datetime) -> tuple[StudentSession | None, bool]:
    """The user's open session if it may continue (same Tashkent day, last heartbeat within SESSION_GAP), else a closed one is ended."""
    session = db.scalar(select(StudentSession).where(StudentSession.user_id == user_id, StudentSession.ended_at.is_(None)))
    if session is None:
        return None, False
    gap = (now - _aware(session.last_seen_at)).total_seconds()
    if session.day != local_day(now) or gap > SESSION_GAP or gap < -5:
        session.ended_at = session.last_seen_at
        db.flush()
        return None, False
    return session, True


def _event(db: Session, user_id, area: str, ref: UUID | None, now: datetime) -> StudentActivityEvent | None:
    """The stretch of this context that may continue (same day, recent), or None."""
    stmt = select(StudentActivityEvent).where(StudentActivityEvent.user_id == user_id, StudentActivityEvent.area == area,
                                              StudentActivityEvent.day == local_day(now), StudentActivityEvent.ended_at.is_(None),
                                              StudentActivityEvent.last_seen_at >= now - timedelta(seconds=SESSION_GAP))
    stmt = stmt.where(StudentActivityEvent.ref_id.is_(None) if ref is None else StudentActivityEvent.ref_id == ref)
    return db.scalar(stmt.order_by(StudentActivityEvent.last_seen_at.desc()).limit(1))


def heartbeat(db: Session, user: User, *, tab_id: str, active: bool, contexts: list[dict], final: bool = False,
              now: datetime | None = None) -> dict:
    """One heartbeat of one tab. `contexts`: [{"area", "ref_id", "position"}] (at most a few; unknown areas are ignored)."""
    if user.role != UserRole.STUDENT:
        return {"tracked": False, "credited": 0}
    now = _aware(now or now_utc())
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": f"activity:{user.id}"})

    session, continuing = _open_session(db, user.id, now)
    if continuing and not final and session.tabs.get(tab_id) and (now - datetime.fromisoformat(session.tabs[tab_id])).total_seconds() < DUPLICATE_SECONDS:
        db.rollback()
        return {"tracked": True, "credited": 0}

    playing, items = False, []
    for ctx in contexts[:4]:
        area, ref, position = ctx.get("area"), ctx.get("ref_id"), ctx.get("position")
        if area not in AREAS:
            continue
        ok, length = _media_ok(db, user, area, ref)
        if not ok:
            continue
        if area in PLAYED:
            if position is None or position < 0 or (length is not None and position > length):
                continue
        elif not active:
            continue  # a page only counts while the student is active on it
        items.append((area, ref, position))

    if session is None:
        session = StudentSession(user_id=user.id, day=local_day(now), started_at=now, last_seen_at=now, active_seconds=0, heartbeats=0, tabs={})
        db.add(session)
        db.flush()
        session_credit = 0
    else:
        session_credit = credit(session.last_seen_at, now)

    for area, ref, position in items:
        ev = _event(db, user.id, area, ref, now)
        if ev is None:
            db.add(StudentActivityEvent(user_id=user.id, session_id=session.id, day=local_day(now), area=area, ref_id=ref, started_at=now,
                                        last_seen_at=now, seconds=0, position=position, ended_at=now if final else None))
            continue
        add = credit(ev.last_seen_at, now)
        if area in PLAYED:
            moved = ev.position is not None and position != ev.position
            add = add if moved else 0
            playing = playing or moved
            ev.position = position
        ev.seconds += add
        ev.last_seen_at = now
        if final:
            ev.ended_at = now

    if active or playing:
        session.active_seconds += session_credit
    else:
        session_credit = 0
    session.last_seen_at = max(_aware(session.last_seen_at), now)
    session.heartbeats += 1
    tabs = dict(session.tabs or {})
    if final:
        tabs.pop(tab_id, None)
    else:
        tabs[tab_id] = now.isoformat()
    alive = {k: v for k, v in tabs.items() if (now - datetime.fromisoformat(v)).total_seconds() <= SESSION_GAP}
    session.tabs = dict(sorted(alive.items(), key=lambda kv: kv[1])[-MAX_TABS:])
    if final and not session.tabs:
        session.ended_at = now
    db.commit()
    return {"tracked": True, "credited": session_credit}


def close_stale(db: Session, now: datetime | None = None) -> int:
    """Ends sessions whose last heartbeat is older than SESSION_GAP (housekeeping; reads treat them as ended anyway)."""
    now = _aware(now or now_utc())
    stale = list(db.scalars(select(StudentSession).where(StudentSession.ended_at.is_(None),
                                                          StudentSession.last_seen_at < now - timedelta(seconds=SESSION_GAP))))
    for s in stale:
        s.ended_at = s.last_seen_at
    db.commit()
    return len(stale)
