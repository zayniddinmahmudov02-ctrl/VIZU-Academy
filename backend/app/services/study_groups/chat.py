"""Group chat and announcements.

Messages are plain text (the frontend renders them as text, never as HTML);
control characters are stripped and the length is capped. Clients poll for
new messages with ?after=<last created_at>; history pages with ?before=.
A moderated message keeps its row (body hidden, who/when recorded, audit log
entry). Sending is rate limited per user."""

import re
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.auth_rate_limit_event import AuthRateLimitEvent
from app.models.study_group import (
    CHAT_CLOSED,
    CHAT_MODES,
    CHAT_OPEN,
    GROUP_ACTIVE,
    MESSAGE_TEXT,
    StudyGroup,
    StudyGroupAnnouncement,
    StudyGroupMember,
    StudyGroupMessage,
)
from app.models.user import User
from app.services.auth.rate_limit import RateLimited, _check
from app.services.study_groups import notify
from app.services.study_groups.access import audit, display_name, is_manager, now, require_manage
from app.services.study_groups.codes import user_key

MAX_MESSAGE = 2000
MAX_ANNOUNCEMENT = 5000
PAGE = 50
ACTION_MESSAGE = "group_message"
MESSAGE_WINDOW = timedelta(minutes=1)
MAX_MESSAGES_PER_MINUTE = 20
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(text: str, limit: int) -> str:
    text = _CONTROL.sub("", (text or "").replace("\r\n", "\n")).strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="empty")
    if len(text) > limit:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="too_long")
    return text


def _message(m: StudyGroupMessage, viewer: User, manager: bool, teacher_id) -> dict:
    deleted = m.deleted_at is not None
    return {"id": m.id, "kind": m.kind, "body": None if deleted else m.body, "deleted": deleted, "is_pinned": m.is_pinned,
            "created_at": m.created_at,
            "sender": None if m.sender_id is None else {"id": m.sender_id, "name": display_name(m.sender),
                                                       "is_teacher": m.sender_id == teacher_id},
            "mine": m.sender_id == viewer.id, "can_moderate": manager and not deleted}


def unread_count(db: Session, group_id, user_id, last_read_at: datetime | None) -> int:
    stmt = select(func.count()).select_from(StudyGroupMessage).where(
        StudyGroupMessage.group_id == group_id, StudyGroupMessage.deleted_at.is_(None),
        (StudyGroupMessage.sender_id != user_id) | StudyGroupMessage.sender_id.is_(None))
    if last_read_at is not None:
        stmt = stmt.where(StudyGroupMessage.created_at > last_read_at)
    return db.scalar(stmt) or 0


def last_message(db: Session, group_id) -> dict | None:
    m = db.scalar(select(StudyGroupMessage).where(StudyGroupMessage.group_id == group_id, StudyGroupMessage.deleted_at.is_(None))
                  .order_by(StudyGroupMessage.created_at.desc()).limit(1))
    if m is None:
        return None
    return {"body": m.body[:120], "created_at": m.created_at, "sender": display_name(m.sender) if m.sender_id else None}


def can_post(group: StudyGroup, viewer: User, member: StudyGroupMember | None) -> bool:
    if group.status != GROUP_ACTIVE or group.chat_mode == CHAT_CLOSED:
        return False
    if is_manager(viewer, group):
        return True
    return group.chat_mode == CHAT_OPEN and member is not None and member.can_post


def list_messages(db: Session, viewer: User, group: StudyGroup, member: StudyGroupMember | None,
                  before: datetime | None = None, after: datetime | None = None, limit: int = PAGE) -> dict:
    limit = min(max(limit, 1), 100)
    manager = is_manager(viewer, group)
    stmt = select(StudyGroupMessage).where(StudyGroupMessage.group_id == group.id)
    if after is not None:
        rows = list(db.scalars(stmt.where(StudyGroupMessage.created_at > after).order_by(StudyGroupMessage.created_at).limit(limit)).unique())
        has_more = False
    else:
        if before is not None:
            stmt = stmt.where(StudyGroupMessage.created_at < before)
        rows = list(db.scalars(stmt.order_by(StudyGroupMessage.created_at.desc()).limit(limit + 1)).unique())
        has_more = len(rows) > limit
        rows = list(reversed(rows[:limit]))
    pinned = list(db.scalars(select(StudyGroupMessage).where(StudyGroupMessage.group_id == group.id, StudyGroupMessage.is_pinned.is_(True),
                                                             StudyGroupMessage.deleted_at.is_(None))
                             .order_by(StudyGroupMessage.created_at.desc()).limit(5)).unique())
    return {"items": [_message(m, viewer, manager, group.teacher_id) for m in rows], "has_more": has_more,
            "pinned": [_message(m, viewer, manager, group.teacher_id) for m in pinned],
            "can_post": can_post(group, viewer, member), "chat_mode": group.chat_mode,
            "unread": unread_count(db, group.id, viewer.id, member.last_read_at) if member else 0}


def post_message(db: Session, viewer: User, group: StudyGroup, member: StudyGroupMember | None, body: str) -> dict:
    if not can_post(group, viewer, member):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="chat_read_only")
    try:
        _check(db, ACTION_MESSAGE, AuthRateLimitEvent.email_hash, user_key(viewer.id), MAX_MESSAGES_PER_MINUTE, MESSAGE_WINDOW)
    except RateLimited as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="too_many_messages",
                            headers={"Retry-After": str(exc.retry_after)})
    text = clean_text(body, MAX_MESSAGE)
    db.add(AuthRateLimitEvent(action=ACTION_MESSAGE, email_hash=user_key(viewer.id)))
    m = StudyGroupMessage(group_id=group.id, sender_id=viewer.id, kind=MESSAGE_TEXT, body=text)
    db.add(m)
    group.last_activity_at = now()
    if member is not None:
        member.last_read_at = now()
    db.flush()
    notify.new_message(db, group, viewer.id)
    db.commit()
    db.refresh(m)
    return _message(m, viewer, is_manager(viewer, group), group.teacher_id)


def mark_read(db: Session, member: StudyGroupMember | None) -> None:
    if member is not None:
        member.last_read_at = now()
        db.commit()


def moderate_message(db: Session, actor: User, group_id: UUID, message_id: UUID, data: dict) -> dict:
    group = require_manage(db, actor, group_id)
    m = db.scalar(select(StudyGroupMessage).where(StudyGroupMessage.id == message_id, StudyGroupMessage.group_id == group.id))
    if m is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if data.get("delete") and m.deleted_at is None:
        m.deleted_at, m.deleted_by, m.is_pinned = now(), actor.id, False
        audit(db, group.id, actor.id, "message.delete", "message", m.id,
              {"sender_id": str(m.sender_id) if m.sender_id else None, "reason": (data.get("reason") or "")[:200]})
    if data.get("pinned") is not None and m.deleted_at is None:
        m.is_pinned = bool(data["pinned"])
        audit(db, group.id, actor.id, "message.pin" if m.is_pinned else "message.unpin", "message", m.id)
    db.commit()
    return _message(m, actor, True, group.teacher_id)


def set_chat_mode(db: Session, actor: User, group_id: UUID, mode: str) -> dict:
    group = require_manage(db, actor, group_id)
    if mode not in CHAT_MODES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid_chat_mode")
    if group.chat_mode != mode:
        audit(db, group.id, actor.id, "chat.mode", "group", group.id, {"from": group.chat_mode, "to": mode})
        group.chat_mode = mode
        db.commit()
    return {"chat_mode": group.chat_mode}


# ---------- announcements ----------

def _announcement(a: StudyGroupAnnouncement) -> dict:
    return {"id": a.id, "title": a.title, "body": a.body, "is_pinned": a.is_pinned, "created_at": a.created_at,
            "updated_at": a.updated_at, "author": display_name(a.author) if a.author_id else None, "archived": a.archived_at is not None}


def list_announcements(db: Session, viewer: User, group: StudyGroup, include_archived: bool = False) -> list[dict]:
    stmt = select(StudyGroupAnnouncement).where(StudyGroupAnnouncement.group_id == group.id)
    if not (include_archived and is_manager(viewer, group)):
        stmt = stmt.where(StudyGroupAnnouncement.archived_at.is_(None))
    rows = db.scalars(stmt.order_by(StudyGroupAnnouncement.is_pinned.desc(), StudyGroupAnnouncement.created_at.desc()).limit(100)).unique()
    return [_announcement(a) for a in rows]


def save_announcement(db: Session, actor: User, group_id: UUID, data: dict, announcement_id: UUID | None = None) -> dict:
    group = require_manage(db, actor, group_id)
    if announcement_id is None:
        a = StudyGroupAnnouncement(group_id=group.id, author_id=actor.id, title=clean_text(data["title"], 200),
                                   body=clean_text(data["body"], MAX_ANNOUNCEMENT), is_pinned=bool(data.get("is_pinned")))
        db.add(a)
        db.flush()
        audit(db, group.id, actor.id, "announcement.create", "announcement", a.id)
        notify.to_students(db, group, f"{group.name}: e’lon / Ankündigung", a.title, "announcements")
        group.last_activity_at = now()
    else:
        a = db.scalar(select(StudyGroupAnnouncement).where(StudyGroupAnnouncement.id == announcement_id,
                                                           StudyGroupAnnouncement.group_id == group.id))
        if a is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
        if data.get("title") is not None:
            a.title = clean_text(data["title"], 200)
        if data.get("body") is not None:
            a.body = clean_text(data["body"], MAX_ANNOUNCEMENT)
        if data.get("is_pinned") is not None:
            a.is_pinned = bool(data["is_pinned"])
        if data.get("archived") is not None:
            a.archived_at = now() if data["archived"] else None
        audit(db, group.id, actor.id, "announcement.update", "announcement", a.id,
              {k: data[k] for k in ("is_pinned", "archived") if data.get(k) is not None})
    db.commit()
    db.refresh(a)
    return _announcement(a)
