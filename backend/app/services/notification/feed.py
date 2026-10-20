"""Student notification feed = personal notifications (notifications table:
grading feedback, support replies ...) + admin broadcasts
(broadcast_notifications), merged newest first.

Broadcasts are never copied per student: visibility is a WHERE clause on
the audience (all / level / interface language / one student) evaluated at
read time, read state is one row per (broadcast, student). So publishing to
every student is one INSERT, and a "scheduled" broadcast needs no scheduler
— it is PUBLISHED with a future publish_at and appears once that time passed.

Paging is a cursor (`before`, an ISO time) with a small limit; the badge is
two COUNT queries.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import and_, exists, false, func, or_, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.broadcast_notification import (
    AUD_ALL,
    AUD_LANGUAGE,
    AUD_LEVEL,
    AUD_USER,
    LINK_EXTERNAL,
    LINK_INTERNAL,
    ST_PUBLISHED,
    BroadcastNotification as B,
    BroadcastNotificationRead as R,
)
from app.models.notification import Notification as P
from app.models.user import User

MAX_LIMIT = 50
DEFAULT_LIMIT = 20


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def user_levels(db: Session, user: User) -> set[str]:
    """Levels a student belongs to: any lesson progress in the level, or a
    purchased (APPROVED) level."""
    from app.services.vizu_pay.access import owned_levels

    rows = db.execute(text("""
        SELECT DISTINCT c.level FROM student_progress sp
        JOIN lessons l ON l.id = sp.lesson_id JOIN modules m ON m.id = l.module_id JOIN courses c ON c.id = m.course_id
        WHERE sp.user_id = :u"""), {"u": user.id}).scalars().all()
    return {r for r in rows if r} | owned_levels(user)


def audience_clause(db: Session, user: User):
    levels = sorted(user_levels(db, user))
    return or_(
        B.audience_type == AUD_ALL,
        and_(B.audience_type == AUD_USER, B.audience_value == str(user.id)),
        and_(B.audience_type == AUD_LEVEL, B.audience_value.in_(levels)) if levels else false(),
        and_(B.audience_type == AUD_LANGUAGE, B.audience_value == (user.preferred_language or "de")),
    )


def visible_clause(db: Session, user: User, now: datetime | None = None):
    return and_(B.status == ST_PUBLISHED, B.publish_at.isnot(None), B.publish_at <= (now or _now()), audience_clause(db, user))


def _broadcast_link(b: B) -> dict | None:
    if b.link_type == LINK_EXTERNAL and b.external_url:
        return {"type": "EXTERNAL", "url": b.external_url}
    if b.link_type == LINK_INTERNAL:
        from app.services import student_routes

        path, _ = student_routes.resolve(b.internal_route, b.internal_params)
        return {"type": "INTERNAL", "path": path}
    return None


def _personal_link(p: P) -> dict | None:
    path = p.link_path or ""
    return {"type": "INTERNAL", "path": path} if path.startswith("/") and not path.startswith("//") else None


def _broadcast_item(b: B, read: bool) -> dict:
    return {"id": f"b:{b.id}", "kind": "broadcast", "type": b.type, "title": None, "message": None,
            "title_de": b.title_de, "title_uz": b.title_uz, "message_de": b.message_de, "message_uz": b.message_uz,
            "created_at": _aware(b.publish_at), "is_read": read, "is_important": b.is_important, "link": _broadcast_link(b), "audio_url": None}


def _personal_item(p: P) -> dict:
    return {"id": f"p:{p.id}", "kind": "personal", "type": p.type, "title": p.title, "message": p.message,
            "title_de": None, "title_uz": None, "message_de": None, "message_uz": None,
            "created_at": _aware(p.created_at), "is_read": p.is_read, "is_important": False, "link": _personal_link(p), "audio_url": p.audio_url}


def feed(db: Session, user: User, before: datetime | None = None, limit: int = DEFAULT_LIMIT) -> dict:
    limit = max(1, min(int(limit or DEFAULT_LIMIT), MAX_LIMIT))
    before = _aware(before)
    pq = select(P).where(P.user_id == user.id).order_by(P.created_at.desc()).limit(limit)
    bq = select(B, exists().where(R.notification_id == B.id, R.user_id == user.id)).where(visible_clause(db, user)).order_by(B.publish_at.desc()).limit(limit)
    if before is not None:
        pq = pq.where(P.created_at < before)
        bq = bq.where(B.publish_at < before)
    items = [_personal_item(p) for p in db.scalars(pq)] + [_broadcast_item(b, bool(read)) for b, read in db.execute(bq)]
    items.sort(key=lambda i: i["created_at"], reverse=True)
    page = items[:limit]
    more = len(items) > limit or len(page) == limit
    return {"items": page, "next_before": page[-1]["created_at"] if page and more else None}


def unread_count(db: Session, user: User) -> int:
    personal = db.scalar(select(func.count()).select_from(P).where(P.user_id == user.id, P.is_read.is_(False))) or 0
    broadcast = db.scalar(select(func.count()).select_from(B).where(
        visible_clause(db, user), ~exists().where(R.notification_id == B.id, R.user_id == user.id))) or 0
    return int(personal) + int(broadcast)


def _parse_id(item_id: str) -> tuple[str, UUID] | None:
    kind, _, raw = (item_id or "").partition(":")
    try:
        return (kind, UUID(raw)) if kind in ("p", "b") else None
    except ValueError:
        return None


def mark_read(db: Session, user: User, item_id: str) -> bool:
    """Idempotent. Only the caller's own personal rows / broadcasts the caller can see."""
    parsed = _parse_id(item_id)
    if parsed is None:
        return False
    kind, uid = parsed
    if kind == "p":
        row = db.scalar(select(P).where(P.id == uid, P.user_id == user.id))
        if row is None:
            return False
        row.is_read = True
        db.commit()
        return True
    if db.scalar(select(B.id).where(B.id == uid, visible_clause(db, user))) is None:
        return False
    db.execute(insert(R).values(id=uuid4(), notification_id=uid, user_id=user.id, read_at=_now())
               .on_conflict_do_nothing(constraint="uq_broadcast_notification_read"))
    db.commit()
    return True


def mark_all_read(db: Session, user: User) -> None:
    now = _now()
    db.query(P).filter(P.user_id == user.id, P.is_read.is_(False)).update({"is_read": True})
    unread = db.scalars(select(B.id).where(visible_clause(db, user, now), ~exists().where(R.notification_id == B.id, R.user_id == user.id))).all()
    if unread:
        db.execute(insert(R).values([{"id": uuid4(), "notification_id": nid, "user_id": user.id, "read_at": now} for nid in unread])
                   .on_conflict_do_nothing(constraint="uq_broadcast_notification_read"))
    db.commit()


# ============================================================
# Admin side
# ============================================================

def audience_size(db: Session, b: B) -> int:
    """How many students the broadcast reaches (computed, nothing stored per student)."""
    students = select(User.id).where(User.role == "STUDENT", User.is_active.is_(True))
    if b.audience_type == AUD_ALL:
        q = students
    elif b.audience_type == AUD_USER:
        q = students.where(User.id == _uuid_or_none(b.audience_value))
    elif b.audience_type == AUD_LANGUAGE:
        q = students.where(func.coalesce(User.preferred_language, "de") == b.audience_value)
    else:
        q = None
    if q is not None:
        return int(db.scalar(select(func.count()).select_from(q.subquery())) or 0)
    return int(db.execute(text("""
        SELECT count(*) FROM users u WHERE u.role = 'STUDENT' AND u.is_active AND (
          EXISTS (SELECT 1 FROM student_progress sp JOIN lessons l ON l.id = sp.lesson_id JOIN modules m ON m.id = l.module_id
                  JOIN courses c ON c.id = m.course_id WHERE sp.user_id = u.id AND c.level = :lv)
          OR EXISTS (SELECT 1 FROM subscription_orders o WHERE o.user_id = u.id AND o.status = 'APPROVED'
                     AND o.plan IN (SELECT unnest(CAST(:plans AS text[])))))"""),
        {"lv": b.audience_value, "plans": _plans_with_level(b.audience_value)}).scalar() or 0)


def _plans_with_level(level: str | None) -> list[str]:
    from app.services.vizu_pay.offers import OFFERS

    return [code for code, cfg in OFFERS.items() if level in cfg["levels"]]


def _uuid_or_none(value):
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def read_counts(db: Session, ids: list) -> dict:
    if not ids:
        return {}
    return dict(db.execute(select(R.notification_id, func.count()).where(R.notification_id.in_(ids)).group_by(R.notification_id)).all())
