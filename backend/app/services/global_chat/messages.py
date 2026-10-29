"""Global Chat messages.

Plain text only: control characters are stripped, the length is capped and
the frontend renders the body as text, never as HTML.

Clients load the newest page, older pages with ?before=<message id>, and then
poll /updates?since=<sync>: every message whose row changed after `sync`
(new, approved, pinned, unpinned, hidden). `sync` is the database clock minus
SYNC_OVERLAP, so a message committed by a slower transaction a moment later
is still picked up; the client merges by id, so the overlap costs nothing.

Visibility: users see visible messages and their own held ("pending") ones;
moderators see everything, hidden and deleted messages with their body.

Authors edit and delete their own messages (edit_own / delete_own). Only the
author — the caller comes from the token, never from the body. A message the
caller cannot see → 404, someone else's visible message → 403. Hidden
messages stay as the moderator left them (no edit, no delete); a pinned
message cannot be edited (the pinned text is what the admin chose), deleting
it unpins it. Editing is writing, so a mute / ban blocks it; deleting is
allowed. An edit runs the word filter again (a hit holds the message for
review) and the old text goes to global_chat_message_edits for moderators.
A deleted message keeps its row and text for moderators and the audit log;
for users it disappears (polling sends its id in removed_ids).

Sending (server-side, nothing trusts the client): an active ban or mute → 403,
more than MAX_PER_MINUTE messages a minute, a message within MIN_INTERVAL of
the previous one, or the same text twice within DUPLICATE_WINDOW → 429.
The checks run under a per-user advisory lock, so parallel requests cannot
slip past them.

Replies: a message may answer one Global Chat message (reply_to_id). The
client sends only the id; the target must be a message of this chat the
sender can currently see (not deleted, not someone else's held/hidden one),
otherwise 422 reply_not_found — the same answer for "does not exist", "is a
group-chat id" and "not visible", so nothing leaks. A reply is a normal
message: mute / ban, rate limit and word filter apply unchanged. The quoted
author and excerpt are built here from the target row, never taken from the
client; when the target later disappears for a viewer the preview says
"available: false" without its text."""

import re
import uuid
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select, true, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.global_chat import (
    MESSAGE_DELETED,
    MESSAGE_HIDDEN,
    MESSAGE_PENDING,
    MESSAGE_VISIBLE,
    GlobalChatMessage,
    GlobalChatMessageEdit,
    GlobalChatRead,
)
from app.models.user import User
from app.services.global_chat import restrictions, word_filter
from app.services.global_chat.access import audit, badge, display_name, is_moderator, now, require_moderator

MAX_LENGTH = 2000
PAGE = 40
MAX_PAGE = 100
MAX_PINS = 5
UNREAD_CAP = 100  # the badge shows 99+
MAX_PER_MINUTE = 10
MIN_INTERVAL = timedelta(seconds=1)
DUPLICATE_WINDOW = timedelta(seconds=60)
SYNC_OVERLAP = timedelta(seconds=15)
SYNC_MAX_AGE = timedelta(minutes=10)  # older → the client reloads the newest page
SYNC_LIMIT = 200
MAX_EDITS_PER_MINUTE = 10
REPLY_EXCERPT = 140
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(text: str) -> str:
    text = _CONTROL.sub("", (text or "").replace("\r\n", "\n")).strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="empty")
    if len(text) > MAX_LENGTH:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="too_long")
    return text


def _visible_to(viewer: User):
    if is_moderator(viewer):
        return true()
    return or_(GlobalChatMessage.status == MESSAGE_VISIBLE,
               and_(GlobalChatMessage.status == MESSAGE_PENDING, GlobalChatMessage.sender_id == viewer.id))


def _can_see(m: GlobalChatMessage, viewer: User) -> bool:
    return is_moderator(viewer) or m.status == MESSAGE_VISIBLE or (m.status == MESSAGE_PENDING and m.sender_id == viewer.id)


def _excerpt(text: str) -> str:
    line = " ".join(text.split())
    return line if len(line) <= REPLY_EXCERPT else line[:REPLY_EXCERPT - 1].rstrip() + "…"


def reply_preview(m: GlobalChatMessage, viewer: User) -> dict | None:
    """What a reply shows of the message it answers — built from the target
    row for this viewer. A deleted target, or one the viewer cannot see, is
    "not available" (id only, no author or text)."""
    if m.reply_to_id is None:
        return None
    target = m.reply_to
    if target is None or target.status == MESSAGE_DELETED or not _can_see(target, viewer):
        return {"id": m.reply_to_id, "available": False, "sender": None, "excerpt": None}
    return {"id": target.id, "available": True, "excerpt": _excerpt(target.body),
            "sender": None if target.sender_id is None else {"id": target.sender_id, "name": display_name(target.sender)}}


def serialize(m: GlobalChatMessage, viewer: User, staff: bool = False) -> dict:
    mod = is_moderator(viewer)
    shown = m.status in (MESSAGE_VISIBLE, MESSAGE_PENDING) or mod
    out = {"id": m.id, "body": m.body if shown else None, "status": m.status, "created_at": m.created_at, "edited_at": m.edited_at,
           "sender": None if m.sender_id is None else {"id": m.sender_id, "name": display_name(m.sender), "badge": badge(m.sender)},
           "mine": m.sender_id == viewer.id, "is_pinned": m.pinned_at is not None, "pinned_at": m.pinned_at,
           "reply_to": reply_preview(m, viewer) if shown else None}
    if mod:
        out.update({"flagged_words": m.flagged_words or [], "hidden_reason": m.hidden_reason, "hidden_at": m.hidden_at, "deleted_at": m.deleted_at,
                    "can_restrict": m.sender is not None and m.sender_id != viewer.id and not is_moderator(m.sender)})
    if staff and m.sender is not None:
        out["sender"].update({"email": m.sender.email, "role": m.sender.role})
    return out


def _sync_token(db: Session) -> datetime:
    return db.scalar(select(func.now())) - SYNC_OVERLAP


def pinned(db: Session, viewer: User) -> list[dict]:
    rows = db.scalars(select(GlobalChatMessage).where(GlobalChatMessage.pinned_at.is_not(None), GlobalChatMessage.status == MESSAGE_VISIBLE)
                      .order_by(GlobalChatMessage.pinned_at.desc()).limit(MAX_PINS)).unique()
    return [serialize(m, viewer) for m in rows]


def _read_baseline(db: Session, viewer: User) -> datetime:
    """Messages after this count as unread. A user who never opened the chat
    starts from their registration, not from the first message ever."""
    last = db.scalar(select(GlobalChatRead.last_read_at).where(GlobalChatRead.user_id == viewer.id))
    return last or viewer.created_at


def unread_count(db: Session, viewer: User) -> int:
    inner = (select(GlobalChatMessage.id)
             .where(GlobalChatMessage.status == MESSAGE_VISIBLE, GlobalChatMessage.created_at > _read_baseline(db, viewer),
                    or_(GlobalChatMessage.sender_id != viewer.id, GlobalChatMessage.sender_id.is_(None)))
             .limit(UNREAD_CAP))
    return db.scalar(select(func.count()).select_from(inner.subquery())) or 0


def _envelope(db: Session, viewer: User) -> dict:
    return {"pinned": pinned(db, viewer), "me": restrictions.viewer_status(db, viewer), "unread": unread_count(db, viewer),
            "sync": _sync_token(db)}


def page(db: Session, viewer: User, before: UUID | None = None, limit: int = PAGE) -> dict:
    limit = min(max(limit, 1), MAX_PAGE)
    stmt = select(GlobalChatMessage).where(_visible_to(viewer))
    if before is not None:
        cursor = db.get(GlobalChatMessage, before)
        if cursor is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="cursor_not_found")
        stmt = stmt.where(tuple_(GlobalChatMessage.created_at, GlobalChatMessage.id) < tuple_(cursor.created_at, cursor.id))
    rows = list(db.scalars(stmt.order_by(GlobalChatMessage.created_at.desc(), GlobalChatMessage.id.desc()).limit(limit + 1)).unique())
    has_more = len(rows) > limit
    return {"items": [serialize(m, viewer) for m in reversed(rows[:limit])], "has_more": has_more, **_envelope(db, viewer)}


def updates(db: Session, viewer: User, since: datetime) -> dict:
    if since.tzinfo is None or since < now() - SYNC_MAX_AGE:
        return {"reset": True, "items": [], "removed_ids": [], **_envelope(db, viewer)}
    rows = list(db.scalars(select(GlobalChatMessage).where(GlobalChatMessage.updated_at > since)
                           .order_by(GlobalChatMessage.updated_at).limit(SYNC_LIMIT + 1)).unique())
    if len(rows) > SYNC_LIMIT:
        return {"reset": True, "items": [], "removed_ids": [], **_envelope(db, viewer)}
    items = [serialize(m, viewer) for m in rows if _can_see(m, viewer)]
    # hidden, deleted, or held again after an edit: gone from this viewer's window
    removed = [m.id for m in rows if not _can_see(m, viewer)]
    return {"reset": False, "items": items, "removed_ids": removed, **_envelope(db, viewer)}


def _rate_limit(db: Session, viewer: User, text: str) -> None:
    db.execute(select(func.pg_advisory_xact_lock(func.hashtext(f"global_chat:{viewer.id}"))))
    at = now()
    recent = list(db.execute(select(GlobalChatMessage.created_at, GlobalChatMessage.body)
                             .where(GlobalChatMessage.sender_id == viewer.id, GlobalChatMessage.created_at > at - timedelta(minutes=1))
                             .order_by(GlobalChatMessage.created_at.desc())).all())
    if len(recent) >= MAX_PER_MINUTE:
        retry = int((recent[-1].created_at + timedelta(minutes=1) - at).total_seconds()) + 1
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="too_many_messages", headers={"Retry-After": str(max(retry, 1))})
    if recent and recent[0].created_at > at - MIN_INTERVAL:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="too_fast", headers={"Retry-After": "1"})
    if any(r.body == text and r.created_at > at - DUPLICATE_WINDOW for r in recent):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="duplicate_message")


def _reply_target(db: Session, viewer: User, reply_to_id: UUID) -> GlobalChatMessage:
    target = db.get(GlobalChatMessage, reply_to_id)
    if target is None or target.status == MESSAGE_DELETED or not _can_see(target, viewer):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="reply_not_found")
    return target


def post(db: Session, viewer: User, body: str, reply_to_id: UUID | None = None) -> dict:
    text = clean_text(body)
    me = restrictions.viewer_status(db, viewer)
    if not me["can_post"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="chat_banned" if me["restriction"]["kind"] == "ban" else "chat_muted")
    target = _reply_target(db, viewer, reply_to_id) if reply_to_id is not None else None
    _rate_limit(db, viewer, text)
    hits = [] if is_moderator(viewer) else word_filter.check(db, text)
    m = GlobalChatMessage(id=uuid.uuid4(), sender_id=viewer.id, body=text, status=MESSAGE_PENDING if hits else MESSAGE_VISIBLE,
                          flagged_words=hits or None, reply_to_id=target.id if target else None)
    db.add(m)
    db.flush()
    if hits:
        audit(db, None, "message.flag", target_user_id=viewer.id, message_id=m.id, reason="word_filter", meta={"words": hits})
    db.commit()
    db.refresh(m)
    mark_read(db, viewer, m.id)
    return serialize(m, viewer)


def mark_read(db: Session, viewer: User, until_id: UUID | None = None) -> None:
    """Moves the read marker forward (never back) to the given message, or to now."""
    until = now()
    if until_id is not None:
        m = db.get(GlobalChatMessage, until_id)
        if m is not None:
            until = min(m.created_at, until)
    stmt = insert(GlobalChatRead).values(id=uuid.uuid4(), user_id=viewer.id, last_read_at=until)
    db.execute(stmt.on_conflict_do_update(index_elements=[GlobalChatRead.user_id],
                                          set_={"last_read_at": func.greatest(GlobalChatRead.last_read_at, stmt.excluded.last_read_at),
                                                "updated_at": func.now()}))
    db.commit()


# ---------- the author's own message ----------

def _own(db: Session, viewer: User, message_id: UUID) -> GlobalChatMessage:
    m = db.scalar(select(GlobalChatMessage).where(GlobalChatMessage.id == message_id).with_for_update(of=GlobalChatMessage))
    if m is None or m.status == MESSAGE_DELETED or not _can_see(m, viewer):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if m.sender_id != viewer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not_author")
    if m.status == MESSAGE_HIDDEN:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="message_hidden")
    return m


def edit_own(db: Session, viewer: User, message_id: UUID, body: str) -> dict:
    text = clean_text(body)
    m = _own(db, viewer, message_id)
    if m.pinned_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="message_pinned")
    me = restrictions.viewer_status(db, viewer)
    if not me["can_post"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="chat_banned" if me["restriction"]["kind"] == "ban" else "chat_muted")
    if text == m.body:
        return serialize(m, viewer)
    db.execute(select(func.pg_advisory_xact_lock(func.hashtext(f"global_chat:{viewer.id}"))))
    recent = db.scalar(select(func.count()).select_from(GlobalChatMessageEdit)
                       .where(GlobalChatMessageEdit.editor_id == viewer.id, GlobalChatMessageEdit.created_at > now() - timedelta(minutes=1))) or 0
    if recent >= MAX_EDITS_PER_MINUTE:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="too_many_edits", headers={"Retry-After": "60"})
    db.add(GlobalChatMessageEdit(message_id=m.id, editor_id=viewer.id, previous_body=m.body, previous_status=m.status))
    hits = [] if is_moderator(viewer) else word_filter.check(db, text)
    if hits:
        # held again for a moderator; the earlier flag (if any) is kept in the edit history
        m.status, m.flagged_words = MESSAGE_PENDING, hits
        audit(db, None, "message.flag", target_user_id=viewer.id, message_id=m.id, reason="word_filter_edit", meta={"words": hits})
    m.body, m.edited_at = text, now()
    db.commit()
    db.refresh(m)
    return serialize(m, viewer)


def delete_own(db: Session, viewer: User, message_id: UUID) -> None:
    m = _own(db, viewer, message_id)
    was_pinned, previous = m.pinned_at is not None, m.status
    m.status, m.deleted_at = MESSAGE_DELETED, now()
    m.pinned_at, m.pinned_by = None, None  # no pin may point at a deleted message
    audit(db, viewer.id, "message.delete", target_user_id=viewer.id, message_id=m.id, reason="deleted_by_author",
          meta={"previous_status": previous, "was_pinned": was_pinned, "excerpt": m.body[:200]})
    db.commit()


def edit_history(db: Session, actor: User, message_id: UUID) -> list[dict]:
    """Earlier versions of a message, oldest first — moderators only."""
    require_moderator(actor)
    if db.get(GlobalChatMessage, message_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    rows = db.scalars(select(GlobalChatMessageEdit).where(GlobalChatMessageEdit.message_id == message_id)
                      .order_by(GlobalChatMessageEdit.created_at)).all()
    return [{"id": e.id, "previous_body": e.previous_body, "previous_status": e.previous_status, "edited_at": e.created_at} for e in rows]


# ---------- moderation ----------

ACTIONS = ("pin", "unpin", "hide", "unhide", "approve")


def moderate(db: Session, actor: User, message_id: UUID, action: str, reason: str | None = None) -> dict:
    require_moderator(actor)
    m = db.scalar(select(GlobalChatMessage).where(GlobalChatMessage.id == message_id).with_for_update(of=GlobalChatMessage))
    if m is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if m.status == MESSAGE_DELETED and action != "unpin":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="message_deleted")
    reason = (reason or "").strip()[:500] or None
    at = now()
    if action == "pin":
        if m.status != MESSAGE_VISIBLE:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="message_not_visible")
        if m.pinned_at is None:
            count = db.scalar(select(func.count()).select_from(GlobalChatMessage).where(GlobalChatMessage.pinned_at.is_not(None),
                                                                                        GlobalChatMessage.status == MESSAGE_VISIBLE)) or 0
            if count >= MAX_PINS:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="too_many_pins")
            m.pinned_at, m.pinned_by = at, actor.id
    elif action == "unpin":
        m.pinned_at, m.pinned_by = None, None
    elif action == "hide":
        if m.status != MESSAGE_HIDDEN:
            m.status, m.hidden_at, m.hidden_by, m.hidden_reason = MESSAGE_HIDDEN, at, actor.id, reason
            m.pinned_at, m.pinned_by = None, None  # a hidden message is never pinned
            m.reviewed_at, m.reviewed_by = m.reviewed_at or at, m.reviewed_by or actor.id
    elif action == "unhide":
        if m.status == MESSAGE_HIDDEN:
            m.status, m.hidden_at, m.hidden_by, m.hidden_reason = MESSAGE_VISIBLE, None, None, None
    elif action == "approve":
        if m.status != MESSAGE_PENDING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="message_not_pending")
        m.status, m.reviewed_at, m.reviewed_by = MESSAGE_VISIBLE, at, actor.id
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid_action")
    audit(db, actor.id, f"message.{action}", target_user_id=m.sender_id, message_id=m.id, reason=reason,
          meta={"excerpt": m.body[:200]})
    db.commit()
    db.refresh(m)
    return serialize(m, actor, staff=True)


FILTERS = ("all", "pending", "hidden", "pinned", "flagged", "deleted", "edited")


def admin_list(db: Session, actor: User, filter_: str = "all", user_id: UUID | None = None, q: str | None = None,
               page_: int = 1, page_size: int = 30) -> dict:
    require_moderator(actor)
    stmt = select(GlobalChatMessage)
    if filter_ == "pending":
        stmt = stmt.where(GlobalChatMessage.status == MESSAGE_PENDING)
    elif filter_ == "hidden":
        stmt = stmt.where(GlobalChatMessage.status == MESSAGE_HIDDEN)
    elif filter_ == "pinned":
        stmt = stmt.where(GlobalChatMessage.pinned_at.is_not(None), GlobalChatMessage.status == MESSAGE_VISIBLE)
    elif filter_ == "flagged":
        stmt = stmt.where(GlobalChatMessage.flagged_words.is_not(None))
    elif filter_ == "deleted":
        stmt = stmt.where(GlobalChatMessage.status == MESSAGE_DELETED)
    elif filter_ == "edited":
        stmt = stmt.where(GlobalChatMessage.edited_at.is_not(None))
    if user_id is not None:
        stmt = stmt.where(GlobalChatMessage.sender_id == user_id)
    if q:
        stmt = stmt.where(GlobalChatMessage.body.ilike(f"%{q.strip()}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(GlobalChatMessage.created_at.desc()).offset((page_ - 1) * page_size).limit(page_size)).unique()
    return {"items": [serialize(m, actor, staff=True) for m in rows], "total": total, "page": page_, "page_size": page_size}


def stats(db: Session, actor: User) -> dict:
    require_moderator(actor)
    at = now()

    def count(*where) -> int:
        return db.scalar(select(func.count()).select_from(GlobalChatMessage).where(*where)) or 0

    def active(kind: str) -> int:
        return restrictions.list_restrictions(db, actor, "active", kind, page_size=1)["total"]

    return {"messages_24h": count(GlobalChatMessage.created_at > at - timedelta(hours=24)),
            "pending": count(GlobalChatMessage.status == MESSAGE_PENDING),
            "hidden_7d": count(GlobalChatMessage.status == MESSAGE_HIDDEN, GlobalChatMessage.hidden_at > at - timedelta(days=7)),
            "pinned": count(GlobalChatMessage.pinned_at.is_not(None), GlobalChatMessage.status == MESSAGE_VISIBLE),
            "active_mutes": active("mute"), "active_bans": active("ban")}


def user_history(db: Session, actor: User, user_id: UUID) -> dict:
    require_moderator(actor)
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    def count(*where) -> int:
        return db.scalar(select(func.count()).select_from(GlobalChatMessage).where(GlobalChatMessage.sender_id == user_id, *where)) or 0

    return {"user": {"id": target.id, "name": display_name(target), "email": target.email, "role": target.role,
                     "is_moderator": is_moderator(target)},
            "status": restrictions.viewer_status(db, target),
            "messages": {"total": count(), "hidden": count(GlobalChatMessage.status == MESSAGE_HIDDEN),
                         "pending": count(GlobalChatMessage.status == MESSAGE_PENDING),
                         "deleted": count(GlobalChatMessage.status == MESSAGE_DELETED),
                         "edited": count(GlobalChatMessage.edited_at.is_not(None)),
                         "flagged": count(GlobalChatMessage.flagged_words.is_not(None))},
            "restrictions": restrictions.list_restrictions(db, actor, "all", user_id=user_id, page_size=100)["items"],
            "actions": restrictions.list_actions(db, actor, user_id=user_id, page_size=100)["items"]}


def search_users(db: Session, actor: User, q: str) -> list[dict]:
    require_moderator(actor)
    q = (q or "").strip()
    if len(q) < 2:
        return []
    like = f"%{q}%"
    rows = db.scalars(select(User).where(or_(User.email.ilike(like), User.username.ilike(like), User.first_name.ilike(like),
                                             User.last_name.ilike(like), (User.first_name + " " + User.last_name).ilike(like)))
                      .order_by(User.first_name, User.username).limit(20)).all()
    return [{"id": u.id, "name": display_name(u), "email": u.email, "role": u.role, "is_moderator": is_moderator(u),
             "status": restrictions.viewer_status(db, u)} for u in rows]
