from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_for_user(self, user_id: str):
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(desc(Notification.created_at))
            .all()
        )

    def get_for_user_by_id(self, user_id: str, notification_id: str):
        return (
            self.db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .first()
        )

    def create(
        self,
        user_id: str,
        title: str,
        message: str,
        type: str,
        audio_url: str | None = None,
    ) -> Notification:
        item = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            audio_url=audio_url,
        )

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def mark_read(self, item: Notification) -> Notification:
        item.is_read = True

        self.db.commit()
        self.db.refresh(item)

        return item

    def mark_all_read(self, user_id: str) -> None:
        (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .update({"is_read": True})
        )
        self.db.commit()
