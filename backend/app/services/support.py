"""Hilfe benötigt / Support tickets.

Rules (all enforced here, on the server):
* the student is the logged-in user — never an id from the request;
* a student only ever sees / writes his own tickets (others: 404);
* a repeated submit (same client request id, or the same subject + text
  within DUPLICATE_WINDOW) returns the existing ticket / message;
* "Beantwortet" / "Warten auf Antwort" only after a staff reply that is
  newer than the student's last message;
* a student message on an answered / waiting / closed ticket reopens it
  (In Bearbeitung when someone is assigned, otherwise Neu);
* closing never deletes the conversation; every message keeps author, role
  and time; staff replies notify the student, new tickets / student replies
  notify the support staff.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security.roles import UserRole
from app.models.support import (
    AUTHOR_STAFF,
    AUTHOR_STUDENT,
    CATEGORIES,
    S_ANSWERED,
    S_CLOSED,
    S_IN_PROGRESS,
    S_NEW,
    S_WAITING,
    STATUSES,
    SupportMessage,
    SupportTicket,
)
from app.models.user import User

SUPPORT_ROLES = {UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.SUPPORT}
SUBJECT_MIN, SUBJECT_MAX = 3, 160
BODY_MIN, BODY_MAX = 10, 5000
DUPLICATE_WINDOW = timedelta(minutes=2)
STAFF_ANSWER_STATUSES = (S_ANSWERED, S_WAITING)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _clean(value, name: str, low: int, high: int) -> str:
    text = str(value or "").strip()
    if len(text) < low:
        raise HTTPException(status_code=422, detail=f"{name.upper()}_TOO_SHORT")
    if len(text) > high:
        raise HTTPException(status_code=422, detail=f"{name.upper()}_TOO_LONG")
    return text


def _request_id(value) -> str | None:
    text = str(value or "").strip()
    return text[:64] if text else None


def display_number(ticket: SupportTicket) -> str:
    return f"#{ticket.number}"


def _name(u: User | None) -> str | None:
    if u is None:
        return None
    return " ".join(x for x in (u.first_name, u.last_name) if x) or u.username


def ticket_summary(t: SupportTicket, *, staff_view: bool = False) -> dict:
    out = {"id": str(t.id), "number": t.number, "display_number": display_number(t), "subject": t.subject, "category": t.category,
           "status": t.status, "created_at": t.created_at, "updated_at": t.updated_at, "last_message_at": t.last_message_at}
    if staff_view:
        out["student"] = {"id": str(t.user_id), "email": t.user.email if t.user else None, "name": _name(t.user)}
        out["assigned_to"] = {"id": str(t.assigned_to_id), "name": _name(t.assigned_to)} if t.assigned_to_id else None
    return out


def messages_of(db: Session, t: SupportTicket, *, staff_view: bool) -> list[dict]:
    rows = db.scalars(select(SupportMessage).where(SupportMessage.ticket_id == t.id).order_by(SupportMessage.created_at, SupportMessage.id)).all()
    return [{"id": str(m.id), "author_role": m.author_role, "body": m.body, "created_at": m.created_at,
             # students see "VIZU Support" for staff, staff see who wrote it
             "author_name": (_name(m.author) if staff_view or m.author_role == AUTHOR_STUDENT else None)} for m in rows]


def detail(db: Session, t: SupportTicket, *, staff_view: bool) -> dict:
    return {**ticket_summary(t, staff_view=staff_view), "messages": messages_of(db, t, staff_view=staff_view)}


# ---- notifications ----

def _notify_student(db: Session, t: SupportTicket) -> None:
    from app.services.notification.service import create_notification

    create_notification(db, str(t.user_id), title=f"Support {display_number(t)}: neue Antwort / yangi javob",
                        message=t.subject[:200], type="system", link_path=f"/support/{t.id}")


def _notify_staff(db: Session, t: SupportTicket, what: str) -> None:
    from app.services.notification.service import create_notification

    staff = db.scalars(select(User.id).where(User.role.in_(SUPPORT_ROLES), User.is_active.is_(True))).all()
    for uid in staff:
        create_notification(db, str(uid), title=f"Support {display_number(t)}: {what}", message=t.subject[:200], type="system",
                            link_path=f"/admin/support?ticket={t.id}")


# ---- student ----

def own_ticket(db: Session, user: User, ticket_id: UUID) -> SupportTicket:
    t = db.scalar(select(SupportTicket).where(SupportTicket.id == ticket_id, SupportTicket.user_id == user.id))
    if t is None:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return t


def create_ticket(db: Session, user: User, subject, category, body, request_id) -> tuple[SupportTicket, bool]:
    """(ticket, created). Idempotent for the same request id and for an
    identical subject + text sent again within DUPLICATE_WINDOW."""
    subject = _clean(subject, "subject", SUBJECT_MIN, SUBJECT_MAX)
    body = _clean(body, "message", BODY_MIN, BODY_MAX)
    if category not in CATEGORIES:
        raise HTTPException(status_code=422, detail="INVALID_CATEGORY")
    rid = _request_id(request_id)
    # serialize this student's submits (row lock) so parallel double clicks see each other
    db.query(User.id).filter(User.id == user.id).with_for_update().first()
    if rid:
        existing = db.scalar(select(SupportTicket).where(SupportTicket.user_id == user.id, SupportTicket.client_request_id == rid))
        if existing:
            db.commit()
            return existing, False
    recent = db.scalar(
        select(SupportTicket).join(SupportMessage, SupportMessage.ticket_id == SupportTicket.id)
        .where(SupportTicket.user_id == user.id, SupportTicket.subject == subject, SupportMessage.body == body,
               SupportTicket.created_at > _now() - DUPLICATE_WINDOW).limit(1))
    if recent:
        db.commit()
        return recent, False
    now = _now()
    t = SupportTicket(user_id=user.id, subject=subject, category=category, status=S_NEW, last_message_at=now, status_changed_at=now,
                      client_request_id=rid)
    db.add(t)
    db.flush()
    db.add(SupportMessage(ticket_id=t.id, author_id=user.id, author_role=AUTHOR_STUDENT, body=body))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(SupportTicket).where(SupportTicket.user_id == user.id, SupportTicket.client_request_id == rid))
        if existing:
            return existing, False
        raise
    db.refresh(t)
    _notify_staff(db, t, "neue Anfrage")
    return t, True


def add_student_message(db: Session, user: User, ticket_id: UUID, body, request_id) -> SupportTicket:
    t = own_ticket(db, user, ticket_id)
    body = _clean(body, "message", 1, BODY_MAX)
    rid = _request_id(request_id)
    db.query(SupportTicket.id).filter(SupportTicket.id == t.id).with_for_update().first()
    if rid and db.scalar(select(SupportMessage.id).where(SupportMessage.ticket_id == t.id, SupportMessage.client_request_id == rid)):
        db.commit()
        return t
    now = _now()
    db.add(SupportMessage(ticket_id=t.id, author_id=user.id, author_role=AUTHOR_STUDENT, body=body, client_request_id=rid))
    if t.status in (S_ANSWERED, S_WAITING, S_CLOSED):
        t.status, t.status_changed_at = (S_IN_PROGRESS if t.assigned_to_id else S_NEW), now
    t.last_message_at = now
    db.commit()
    db.refresh(t)
    _notify_staff(db, t, "neue Nachricht des Studenten")
    return t


def list_own(db: Session, user: User, page: int, page_size: int) -> dict:
    page, page_size = max(1, page), max(1, min(page_size, 50))
    q = select(SupportTicket).where(SupportTicket.user_id == user.id)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(q.order_by(SupportTicket.last_message_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [ticket_summary(t) for t in rows], "total": total, "page": page, "page_size": page_size}


# ---- staff ----

def require_support_staff(user: User) -> None:
    if user.role not in SUPPORT_ROLES:
        raise HTTPException(status_code=403, detail="Support access required")


def staff_ticket(db: Session, ticket_id: UUID) -> SupportTicket:
    t = db.get(SupportTicket, ticket_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return t


def _last_author(db: Session, t: SupportTicket) -> str | None:
    return db.scalar(select(SupportMessage.author_role).where(SupportMessage.ticket_id == t.id)
                     .order_by(SupportMessage.created_at.desc(), SupportMessage.id.desc()).limit(1))


def staff_reply(db: Session, staff: User, ticket_id: UUID, body, status: str | None, request_id) -> SupportTicket:
    t = staff_ticket(db, ticket_id)
    body = _clean(body, "message", 1, BODY_MAX)
    new_status = status or S_ANSWERED
    if new_status not in STATUSES:
        raise HTTPException(status_code=422, detail="INVALID_STATUS")
    rid = _request_id(request_id)
    db.query(SupportTicket.id).filter(SupportTicket.id == t.id).with_for_update().first()
    if rid and db.scalar(select(SupportMessage.id).where(SupportMessage.ticket_id == t.id, SupportMessage.client_request_id == rid)):
        db.commit()
        return t
    now = _now()
    db.add(SupportMessage(ticket_id=t.id, author_id=staff.id, author_role=AUTHOR_STAFF, body=body, client_request_id=rid))
    if t.assigned_to_id is None:
        t.assigned_to_id = staff.id
    if t.status != new_status:
        t.status, t.status_changed_at = new_status, now
    t.last_message_at = now
    db.commit()
    db.refresh(t)
    _notify_student(db, t)
    return t


def set_status(db: Session, ticket_id: UUID, status: str) -> SupportTicket:
    t = staff_ticket(db, ticket_id)
    if status not in STATUSES:
        raise HTTPException(status_code=422, detail="INVALID_STATUS")
    if status in STAFF_ANSWER_STATUSES and _last_author(db, t) != AUTHOR_STAFF:
        # "Beantwortet" / "Warten auf Antwort" only after a real staff answer
        raise HTTPException(status_code=422, detail="REPLY_REQUIRED: erst antworten, dann diesen Status setzen")
    if t.status != status:
        t.status, t.status_changed_at = status, _now()
    db.commit()
    db.refresh(t)
    return t


def assign(db: Session, ticket_id: UUID, assignee_id: UUID | None) -> SupportTicket:
    t = staff_ticket(db, ticket_id)
    if assignee_id is not None:
        staff = db.get(User, assignee_id)
        if staff is None or staff.role not in SUPPORT_ROLES or not staff.is_active:
            raise HTTPException(status_code=422, detail="INVALID_ASSIGNEE")
    t.assigned_to_id = assignee_id
    db.commit()
    db.refresh(t)
    return t


def staff_list(db: Session, *, status=None, category=None, q=None, date_from=None, date_to=None, assigned=None, me: User,
               page: int = 1, page_size: int = 25) -> dict:
    page, page_size = max(1, page), max(1, min(page_size, 100))
    query = select(SupportTicket).join(User, User.id == SupportTicket.user_id)
    if status in STATUSES:
        query = query.where(SupportTicket.status == status)
    if category in CATEGORIES:
        query = query.where(SupportTicket.category == category)
    if q:
        needle = f"%{q.strip().lstrip('#')}%"
        conds = [SupportTicket.subject.ilike(needle), User.email.ilike(needle), User.first_name.ilike(needle), User.last_name.ilike(needle)]
        if q.strip().lstrip("#").isdigit():
            conds.append(SupportTicket.number == int(q.strip().lstrip("#")))
        query = query.where(or_(*conds))
    if date_from:
        query = query.where(SupportTicket.created_at >= date_from)
    if date_to:
        query = query.where(SupportTicket.created_at < date_to)
    if assigned == "me":
        query = query.where(SupportTicket.assigned_to_id == me.id)
    elif assigned == "none":
        query = query.where(SupportTicket.assigned_to_id.is_(None))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(SupportTicket.last_message_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    counts = dict(db.execute(select(SupportTicket.status, func.count()).group_by(SupportTicket.status)).all())
    return {"items": [ticket_summary(t, staff_view=True) for t in rows], "total": total, "page": page, "page_size": page_size,
            "counts": {s: counts.get(s, 0) for s in STATUSES}}
