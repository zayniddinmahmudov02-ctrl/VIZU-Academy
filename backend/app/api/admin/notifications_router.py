"""Admin -> Notifications (broadcasts). Every write checks the caller's role
and the audience it may address (app.services.notification.admin)."""

import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.audit import write_audit
from app.db.session import get_db
from app.models.broadcast_notification import AUD_USER, STATUSES, BroadcastNotification as B
from app.models.user import User
from app.services.notification import admin as service
from app.services.notification import feed

router = APIRouter(prefix="/admin/notifications", tags=["Admin - Notifications"])


def notification_admin(current_user: User = Depends(get_current_user)) -> User:
    service.require_notification_admin(current_user)
    return current_user


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _item(db: Session, b: B, reads: int | None = None, with_size: bool = True) -> dict:
    student = None
    if b.audience_type == AUD_USER and b.audience_value:
        u = db.scalar(select(User).where(User.id == feed._uuid_or_none(b.audience_value)))
        student = {"id": str(u.id), "email": u.email, "name": " ".join(x for x in (u.first_name, u.last_name) if x) or u.username} if u else None
    now = datetime.now(timezone.utc)
    state = b.status
    if b.status == "PUBLISHED" and b.publish_at and b.publish_at > now:
        state = "SCHEDULED"
    return {
        "id": str(b.id), "title_de": b.title_de, "title_uz": b.title_uz, "message_de": b.message_de, "message_uz": b.message_uz,
        "type": b.type, "audience_type": b.audience_type, "audience_value": b.audience_value, "audience_student": student,
        "link_type": b.link_type, "internal_route": b.internal_route, "internal_params": b.internal_params, "external_url": b.external_url,
        "link": feed._broadcast_link(b), "is_important": b.is_important, "status": b.status, "state": state,
        "publish_at": b.publish_at, "archived_at": b.archived_at, "created_at": b.created_at, "updated_at": b.updated_at,
        "editable": service.editable(b), "recipients": feed.audience_size(db, b) if with_size else None,
        "reads": reads if reads is not None else feed.read_counts(db, [b.id]).get(b.id, 0),
    }


@router.get("/meta")
def meta(user: User = Depends(notification_admin)):
    from app.services import student_routes
    from app.services.lms import structure

    return {"audiences": service.allowed_audiences(user), "types": ["INFO", "SUCCESS", "WARNING", "ANNOUNCEMENT"],
            "levels": list(structure.LEVELS), "languages": list(service.LANGUAGES), "internal_routes": student_routes.catalogue()}


@router.get("")
def list_notifications(status: str | None = None, page: int = 1, page_size: int = 20, db: Session = Depends(get_db), user: User = Depends(notification_admin)):
    page, page_size = max(1, page), max(1, min(page_size, 50))
    q = select(B)
    if status in STATUSES:
        q = q.where(B.status == status)
    if user.role not in service.BROADCAST_ROLES:
        q = q.where(B.audience_type == AUD_USER)  # single-student roles only see that kind
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(q.order_by(B.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    reads = feed.read_counts(db, [b.id for b in rows])
    return {"items": [_item(db, b, reads.get(b.id, 0)) for b in rows], "total": total, "page": page, "page_size": page_size}


def _get(db: Session, user: User, item_id: UUID) -> B:
    b = db.get(B, item_id)
    if b is None or (user.role not in service.BROADCAST_ROLES and b.audience_type != AUD_USER):
        raise HTTPException(status_code=404, detail="Notification not found.")
    return b


def _validated(db: Session, payload: dict, user: User, current: B | None = None) -> dict:
    try:
        return service.validate(db, payload, user, current)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"INVALID_NOTIFICATION: {exc}") from None


@router.post("", status_code=201)
def create(payload: dict, request: Request, db: Session = Depends(get_db), user: User = Depends(notification_admin)):
    b = B(**_validated(db, payload, user), status="DRAFT", created_by_id=user.id)
    db.add(b)
    db.commit()
    db.refresh(b)
    write_audit(db, str(user.id), "notification_created", details=f"{b.id} {b.audience_type}:{b.audience_value or ''} {b.title_de[:80]}", ip_address=_ip(request))
    return _item(db, b)


@router.put("/{item_id}")
def update(item_id: UUID, payload: dict, request: Request, db: Session = Depends(get_db), user: User = Depends(notification_admin)):
    b = _get(db, user, item_id)
    if not service.editable(b):
        raise HTTPException(status_code=409, detail="NOTIFICATION_NOT_EDITABLE: bereits veröffentlicht — archivieren und neu anlegen")
    before = {k: getattr(b, k) for k in ("title_de", "title_uz", "audience_type", "audience_value")}
    for field, value in _validated(db, payload, user, b).items():
        setattr(b, field, value)
    db.commit()
    write_audit(db, str(user.id), "notification_updated", details=json.dumps({"id": str(b.id), "before": before}, default=str)[:2000], ip_address=_ip(request))
    return _item(db, b)


class PublishIn(BaseModel):
    publish_at: datetime | None = None
    confirm: bool = False


@router.post("/{item_id}/publish")
def publish(item_id: UUID, data: PublishIn, request: Request, db: Session = Depends(get_db), user: User = Depends(notification_admin)):
    b = _get(db, user, item_id)
    _validated(db, {}, user, b)  # the audience must still be allowed for this role
    service.publish(b, data.publish_at, data.confirm)
    db.commit()
    write_audit(db, str(user.id), "notification_published", details=f"{b.id} at {b.publish_at.isoformat()} {b.audience_type}:{b.audience_value or ''}",
                ip_address=_ip(request))
    return _item(db, b)


@router.post("/{item_id}/deactivate")
def deactivate(item_id: UUID, request: Request, db: Session = Depends(get_db), user: User = Depends(notification_admin)):
    b = _get(db, user, item_id)
    service.deactivate(b)
    db.commit()
    write_audit(db, str(user.id), "notification_deactivated", details=str(b.id), ip_address=_ip(request))
    return _item(db, b)


@router.post("/{item_id}/archive")
def archive(item_id: UUID, request: Request, db: Session = Depends(get_db), user: User = Depends(notification_admin)):
    b = _get(db, user, item_id)
    service.archive(b)
    db.commit()
    write_audit(db, str(user.id), "notification_archived", details=str(b.id), ip_address=_ip(request))
    return _item(db, b)


@router.get("/resolve-student")
def resolve_student(q: str, db: Session = Depends(get_db), _: User = Depends(notification_admin)):
    """E-mail or id -> the student (for the "one student" audience)."""
    u = service.resolve_student(db, q)
    if u is None:
        raise HTTPException(status_code=404, detail="Student nicht gefunden")
    return {"id": str(u.id), "email": u.email, "name": " ".join(x for x in (u.first_name, u.last_name) if x) or u.username}
