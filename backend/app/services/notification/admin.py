"""Admin broadcasts: validation, who may send to which audience, status
transitions. Texts are plain; links are a registered student page or an
http(s) URL (same validators as the Werbung-Banner)."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security.roles import UserRole
from app.models.broadcast_notification import (
    AUD_ALL,
    AUD_LANGUAGE,
    AUD_LEVEL,
    AUD_USER,
    AUDIENCES,
    BROADCAST_TYPES,
    LINK_EXTERNAL,
    LINK_INTERNAL,
    LINK_NONE,
    ST_ARCHIVED,
    ST_DRAFT,
    ST_INACTIVE,
    ST_PUBLISHED,
    BroadcastNotification,
)
from app.models.user import User

# who may send what (checked on every write)
BROADCAST_ROLES = {UserRole.SUPER_ADMIN, UserRole.ADMIN}  # every audience
SINGLE_STUDENT_ROLES = BROADCAST_ROLES | {UserRole.SUPPORT, UserRole.CONTENT_MANAGER}  # one student only
LANGUAGES = ("de", "uz")
TITLE_MAX, MESSAGE_MAX = 160, 2000


def _now() -> datetime:
    return datetime.now(timezone.utc)


def allowed_audiences(user: User) -> list[str]:
    if user.role in BROADCAST_ROLES:
        return list(AUDIENCES)
    if user.role in SINGLE_STUDENT_ROLES:
        return [AUD_USER]
    return []


def require_notification_admin(user: User) -> None:
    if not allowed_audiences(user):
        raise HTTPException(status_code=403, detail="Notification management access required")


def _text(value, name: str, max_len: int) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{name}: darf nicht leer sein")
    if len(text) > max_len:
        raise ValueError(f"{name}: max. {max_len} Zeichen")
    return text


def validate(db: Session, data: dict, actor: User, current: BroadcastNotification | None = None) -> dict:
    from app.services import student_routes
    from app.services.advertisement_validation import validate_target_url
    from app.services.lms import structure

    merged = {f: getattr(current, f) for f in ("title_de", "title_uz", "message_de", "message_uz", "type", "audience_type", "audience_value",
                                               "link_type", "internal_route", "internal_params", "external_url", "is_important")} if current else {}
    merged.update({k: v for k, v in data.items()})
    out = {
        "title_de": _text(merged.get("title_de"), "title_de", TITLE_MAX), "title_uz": _text(merged.get("title_uz"), "title_uz", TITLE_MAX),
        "message_de": _text(merged.get("message_de"), "message_de", MESSAGE_MAX), "message_uz": _text(merged.get("message_uz"), "message_uz", MESSAGE_MAX),
    }
    ntype = merged.get("type") or "INFO"
    if ntype not in BROADCAST_TYPES:
        raise ValueError(f"type: {', '.join(BROADCAST_TYPES)}")
    out["type"] = ntype

    aud, value = merged.get("audience_type") or AUD_ALL, merged.get("audience_value")
    if aud not in AUDIENCES:
        raise ValueError(f"audience_type: {', '.join(AUDIENCES)}")
    if aud not in allowed_audiences(actor):
        raise PermissionError("Deine Rolle darf nur an einzelne Studenten senden.")
    if aud == AUD_ALL:
        value = None
    elif aud == AUD_LEVEL:
        if value not in structure.LEVELS:
            raise ValueError(f"audience_value: {', '.join(structure.LEVELS)}")
    elif aud == AUD_LANGUAGE:
        if value not in LANGUAGES:
            raise ValueError("audience_value: de / uz")
    else:  # one student: by id or e-mail, resolved on the server
        student = resolve_student(db, value)
        if student is None:
            raise ValueError("audience_value: Student nicht gefunden")
        value = str(student.id)
    out["audience_type"], out["audience_value"] = aud, value

    link = merged.get("link_type") or LINK_NONE
    out.update({"link_type": link, "internal_route": None, "internal_params": None, "external_url": None})
    if link == LINK_EXTERNAL:
        out["external_url"] = validate_target_url(merged.get("external_url") or "")
    elif link == LINK_INTERNAL:
        out["internal_route"] = merged.get("internal_route")
        out["internal_params"] = student_routes.validate(merged.get("internal_route"), merged.get("internal_params"))
    elif link != LINK_NONE:
        raise ValueError("link_type: NONE / INTERNAL / EXTERNAL")
    important = merged.get("is_important", False)
    if not isinstance(important, bool):
        raise ValueError("is_important: true / false")
    out["is_important"] = important
    return out


def resolve_student(db: Session, value) -> User | None:
    if not value:
        return None
    raw = str(value).strip()
    try:
        cond = User.id == UUID(raw)
    except ValueError:
        cond = User.email == raw.lower()
    return db.scalar(select(User).where(cond, User.role == UserRole.STUDENT))


def publish(item: BroadcastNotification, publish_at: datetime | None, confirm: bool) -> None:
    if item.status == ST_ARCHIVED:
        raise HTTPException(status_code=409, detail="NOTIFICATION_ARCHIVED")
    if (item.is_important or item.audience_type != AUD_USER) and not confirm:
        # an important / mass notification is published only after the confirmation dialog
        raise HTTPException(status_code=409, detail="CONFIRMATION_REQUIRED")
    when = publish_at if publish_at is not None else _now()
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    item.status, item.publish_at = ST_PUBLISHED, when


def deactivate(item: BroadcastNotification) -> None:
    if item.status == ST_ARCHIVED:
        raise HTTPException(status_code=409, detail="NOTIFICATION_ARCHIVED")
    item.status = ST_INACTIVE


def archive(item: BroadcastNotification) -> None:
    item.status, item.archived_at = ST_ARCHIVED, _now()  # read rows are kept


def editable(item: BroadcastNotification) -> bool:
    """Texts / audience change only before students could see it: drafts,
    deactivated ones and scheduled ones (publish_at still in the future)."""
    if item.status in (ST_DRAFT, ST_INACTIVE):
        return True
    return item.status == ST_PUBLISHED and item.publish_at is not None and item.publish_at > _now()
