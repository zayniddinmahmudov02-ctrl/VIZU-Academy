from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db

from app.models.user import User

from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
)

from app.services.notification import NotificationService, feed

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


# ---- feed: personal notifications + admin broadcasts (own / visible only) ----

@router.get("/feed")
def notification_feed(
    before: datetime | None = None,
    limit: int = feed.DEFAULT_LIMIT,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Newest first, `limit` (max 50) per page; `next_before` is the cursor of the next page."""
    return feed.feed(db, current_user, before, limit)


@router.get("/unread-count")
def notification_unread_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"unread": feed.unread_count(db, current_user)}


@router.post("/feed/read-all")
def notification_feed_read_all(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    feed.mark_all_read(db, current_user)
    return {"unread": 0}


@router.post("/feed/{item_id}/read")
def notification_feed_read(item_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """`item_id` = "p:<id>" (personal) or "b:<id>" (broadcast) — only the caller's own / visible ones."""
    if not feed.mark_read(db, current_user, item_id):
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"unread": feed.unread_count(db, current_user)}


@router.get(
    "",
    response_model=list[NotificationResponse],
)
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return NotificationService(db).get_for_user(str(current_user.id))


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = NotificationService(db).mark_read(str(current_user.id), str(notification_id))

    if not item:
        raise HTTPException(status_code=404, detail="Notification not found")

    return item


@router.post("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    NotificationService(db).mark_all_read(str(current_user.id))

    return {"message": "All notifications marked as read"}


@router.post(
    "",
    response_model=NotificationResponse,
)
def create_notification_for_self(
    data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return NotificationService(db).create_for_user(
        str(current_user.id),
        title=data.title,
        message=data.message,
        type=data.type,
    )
