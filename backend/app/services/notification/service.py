from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.repositories.notification import NotificationRepository


def create_notification(
    db: Session,
    user_id: str,
    title: str,
    message: str,
    type: str,
    audio_url: str | None = None,
) -> Notification:
    """Plain internal helper — not an HTTP call. Writing/Speaking grading
    completion calls this directly so a notification is created in the
    same transaction as the grading write, rather than round-tripping
    through this router."""

    return NotificationRepository(db).create(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        audio_url=audio_url,
    )


class NotificationService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = NotificationRepository(db)

    def get_for_user(self, user_id: str):
        return self.repository.get_for_user(user_id)

    def create_for_user(self, user_id: str, title: str, message: str, type: str) -> Notification:
        return create_notification(self.db, user_id=user_id, title=title, message=message, type=type)

    def mark_read(self, user_id: str, notification_id: str) -> Notification | None:
        item = self.repository.get_for_user_by_id(user_id, notification_id)

        if not item:
            return None

        return self.repository.mark_read(item)

    def mark_all_read(self, user_id: str) -> None:
        self.repository.mark_all_read(user_id)
