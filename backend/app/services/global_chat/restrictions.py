"""Global Chat mutes and bans.

Both only stop a user from WRITING in the Global Chat — reading goes on, and
the account, courses, payments and group chats are never touched (no column
of users is changed). A ban outranks a mute when both are active.

* mute: 10 min … 30 days, or a custom end up to one calendar year;
* ban:  1, 2, 3 or 5 calendar years (2025-02-28 + 1y = 2026-02-28,
        2028-02-29 + 1y = 2029-02-28), or permanent (SUPER_ADMIN only).
Years are added on the calendar in UTC, not as 365 days.

Active = not revoked and now in [starts_at, ends_at); an expired row stops
counting by itself. A new mute/ban for a user revokes their previous live one
of the same kind ("superseded"), so the partial unique index allows exactly
one live row per user and kind."""

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.global_chat import KIND_BAN, KIND_MUTE, GlobalChatModerationAction, GlobalChatRestriction
from app.models.user import User
from app.services.global_chat.access import audit, can_ban_permanently, display_name, is_moderator, now, require_moderator

MUTE_PRESETS = {
    "10m": timedelta(minutes=10),
    "1h": timedelta(hours=1),
    "24h": timedelta(hours=24),
    "3d": timedelta(days=3),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}
BAN_PRESETS = {"1y": 1, "2y": 2, "3y": 3, "5y": 5}
PERMANENT = "permanent"
CUSTOM = "custom"
DURATIONS = {KIND_MUTE: (*MUTE_PRESETS, CUSTOM), KIND_BAN: (*BAN_PRESETS, PERMANENT)}


def add_years(moment: datetime, years: int) -> datetime:
    """Calendar years; 29 February becomes 28 February in a non-leap year."""
    try:
        return moment.replace(year=moment.year + years)
    except ValueError:
        return moment.replace(year=moment.year + years, day=28)


def _bad(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


def _aware(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        raise _bad("timezone_required")
    return moment


def compute_end(kind: str, duration: str, starts_at: datetime, ends_at: datetime | None, actor: User) -> datetime | None:
    if duration not in DURATIONS.get(kind, ()):
        raise _bad("invalid_duration")
    if kind == KIND_MUTE:
        if duration != CUSTOM:
            return starts_at + MUTE_PRESETS[duration]
        if ends_at is None:
            raise _bad("ends_at_required")
        return check_mute_end(starts_at, _aware(ends_at))
    if duration == PERMANENT:
        if not can_ban_permanently(actor):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="permanent_ban_super_admin_only")
        return None
    return add_years(starts_at, BAN_PRESETS[duration])


def check_mute_end(starts_at: datetime, ends_at: datetime) -> datetime:
    if ends_at <= now():
        raise _bad("ends_at_in_past")
    if ends_at > add_years(starts_at, 1):
        raise _bad("mute_too_long")  # longer than a year: that is a ban
    return ends_at


def is_active(r: GlobalChatRestriction, at: datetime | None = None) -> bool:
    at = at or now()
    return r.revoked_at is None and r.starts_at <= at and (r.ends_at is None or r.ends_at > at)


def state(r: GlobalChatRestriction) -> str:
    if r.revoked_at is not None:
        return "revoked"
    return "active" if is_active(r) else "expired"


def _active_filter(at: datetime):
    return (GlobalChatRestriction.revoked_at.is_(None), GlobalChatRestriction.starts_at <= at,
            or_(GlobalChatRestriction.ends_at.is_(None), GlobalChatRestriction.ends_at > at))


def active_for(db: Session, user_id) -> dict[str, GlobalChatRestriction]:
    rows = db.scalars(select(GlobalChatRestriction).where(GlobalChatRestriction.user_id == user_id, *_active_filter(now()))).unique()
    return {r.kind: r for r in rows}


def viewer_status(db: Session, user: User) -> dict:
    """What the chat window needs: may this user write, and if not, why/until when."""
    active = active_for(db, user.id)
    r = active.get(KIND_BAN) or active.get(KIND_MUTE)
    if r is None:
        return {"can_post": True, "restriction": None, "is_moderator": is_moderator(user)}
    return {"can_post": False, "is_moderator": is_moderator(user),
            "restriction": {"kind": r.kind, "ends_at": r.ends_at, "permanent": r.ends_at is None, "note": r.public_note}}


def serialize(r: GlobalChatRestriction) -> dict:
    return {"id": r.id, "kind": r.kind, "state": state(r), "starts_at": r.starts_at, "ends_at": r.ends_at, "permanent": r.ends_at is None,
            "reason": r.reason, "public_note": r.public_note, "created_at": r.created_at,
            "user": {"id": r.user_id, "name": display_name(r.user), "email": r.user.email if r.user else None,
                     "role": r.user.role if r.user else None},
            "created_by": display_name(r.creator) if r.created_by else None,
            "revoked_at": r.revoked_at, "revoke_reason": r.revoke_reason}


def _target(db: Session, actor: User, user_id: UUID) -> User:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.id == actor.id:
        raise _bad("cannot_restrict_self")
    if is_moderator(target):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="cannot_restrict_moderator")
    return target


def create(db: Session, actor: User, data: dict) -> dict:
    require_moderator(actor)
    kind = data["kind"]
    target = _target(db, actor, data["user_id"])
    reason = (data.get("reason") or "").strip()
    if not reason:
        raise _bad("reason_required")
    starts_at = now()
    ends_at = compute_end(kind, data["duration"], starts_at, data.get("ends_at"), actor)

    previous = db.scalar(select(GlobalChatRestriction).where(GlobalChatRestriction.user_id == target.id, GlobalChatRestriction.kind == kind,
                                                             GlobalChatRestriction.revoked_at.is_(None))
                        .with_for_update(of=GlobalChatRestriction))
    if previous is not None:
        previous.revoked_at, previous.revoked_by, previous.revoke_reason = starts_at, actor.id, "superseded"
        db.flush()
    r = GlobalChatRestriction(user_id=target.id, kind=kind, starts_at=starts_at, ends_at=ends_at, reason=reason,
                              public_note=(data.get("public_note") or "").strip() or None, created_by=actor.id)
    db.add(r)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="restriction_conflict")
    audit(db, actor.id, f"{kind}.create", target_user_id=target.id, restriction_id=r.id, reason=reason,
          meta={"duration": data["duration"], "ends_at": ends_at.isoformat() if ends_at else None, "public_note": r.public_note,
                "message_id": str(data["message_id"]) if data.get("message_id") else None,
                "superseded": str(previous.id) if previous is not None else None})
    db.commit()
    db.refresh(r)
    return serialize(r)


def _editable(db: Session, actor: User, restriction_id: UUID) -> GlobalChatRestriction:
    require_moderator(actor)
    r = db.scalar(select(GlobalChatRestriction).where(GlobalChatRestriction.id == restriction_id).with_for_update(of=GlobalChatRestriction))
    if r is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restriction not found")
    if r.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="restriction_revoked")
    if r.ends_at is None and not can_ban_permanently(actor):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="permanent_ban_super_admin_only")
    return r


def update(db: Session, actor: User, restriction_id: UUID, data: dict) -> dict:
    """Extend or shorten: a new end (in the future), or permanent for a ban."""
    r = _editable(db, actor, restriction_id)
    if data.get("permanent"):
        if r.kind != KIND_BAN:
            raise _bad("mute_cannot_be_permanent")
        if not can_ban_permanently(actor):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="permanent_ban_super_admin_only")
        new_end = None
    elif data.get("ends_at") is not None:
        new_end = _aware(data["ends_at"])
        if r.kind == KIND_MUTE:
            new_end = check_mute_end(r.starts_at, new_end)
        elif new_end <= now():
            raise _bad("ends_at_in_past")
    elif data.get("ban_years") is not None:
        if r.kind != KIND_BAN:
            raise _bad("invalid_duration")
        new_end = add_years(r.starts_at, int(data["ban_years"]))
        if new_end <= now():
            raise _bad("ends_at_in_past")
    else:
        raise _bad("ends_at_required")
    old_end = r.ends_at
    r.ends_at = new_end
    if data.get("public_note") is not None:
        r.public_note = data["public_note"].strip() or None
    audit(db, actor.id, f"{r.kind}.update", target_user_id=r.user_id, restriction_id=r.id, reason=(data.get("reason") or "").strip() or None,
          meta={"from": old_end.isoformat() if old_end else None, "to": new_end.isoformat() if new_end else None})
    db.commit()
    db.refresh(r)
    return serialize(r)


def revoke(db: Session, actor: User, restriction_id: UUID, reason: str | None) -> dict:
    r = _editable(db, actor, restriction_id)
    r.revoked_at, r.revoked_by, r.revoke_reason = now(), actor.id, (reason or "").strip()[:500] or None
    audit(db, actor.id, f"{r.kind}.revoke", target_user_id=r.user_id, restriction_id=r.id, reason=r.revoke_reason,
          meta={"was_active": r.ends_at is None or r.ends_at > r.revoked_at})
    db.commit()
    db.refresh(r)
    return serialize(r)


def list_restrictions(db: Session, actor: User, state_: str = "active", kind: str | None = None, user_id: UUID | None = None,
                      q: str | None = None, page: int = 1, page_size: int = 25) -> dict:
    require_moderator(actor)
    at = now()
    stmt = select(GlobalChatRestriction).join(User, User.id == GlobalChatRestriction.user_id)
    if state_ == "active":
        stmt = stmt.where(*_active_filter(at))
    elif state_ == "expired":
        stmt = stmt.where(GlobalChatRestriction.revoked_at.is_(None), GlobalChatRestriction.ends_at.is_not(None),
                          GlobalChatRestriction.ends_at <= at)
    elif state_ == "revoked":
        stmt = stmt.where(GlobalChatRestriction.revoked_at.is_not(None))
    if kind in (KIND_MUTE, KIND_BAN):
        stmt = stmt.where(GlobalChatRestriction.kind == kind)
    if user_id is not None:
        stmt = stmt.where(GlobalChatRestriction.user_id == user_id)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(User.email.ilike(like), User.username.ilike(like), User.first_name.ilike(like), User.last_name.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.scalars(stmt.order_by(GlobalChatRestriction.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).unique()
    return {"items": [serialize(r) for r in rows], "total": total, "page": page, "page_size": page_size}


def serialize_action(a: GlobalChatModerationAction) -> dict:
    return {"id": a.id, "action": a.action, "created_at": a.created_at, "reason": a.reason, "meta": a.meta,
            "actor": display_name(a.actor) if a.actor_id else None,  # None = the word filter
            "target_user": {"id": a.target_user_id, "name": display_name(a.target_user)} if a.target_user_id else None,
            "message_id": a.message_id, "restriction_id": a.restriction_id}


def list_actions(db: Session, actor: User, user_id: UUID | None = None, action: str | None = None, page: int = 1, page_size: int = 50) -> dict:
    require_moderator(actor)
    stmt = select(GlobalChatModerationAction)
    if user_id is not None:
        stmt = stmt.where(GlobalChatModerationAction.target_user_id == user_id)
    if action:
        stmt = stmt.where(GlobalChatModerationAction.action.startswith(action))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(GlobalChatModerationAction.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).unique()
    return {"items": [serialize_action(a) for a in rows], "total": total, "page": page, "page_size": page_size}
