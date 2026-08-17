from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

TYPE_INFORMATION = "information"
TYPE_UPDATE = "update"
TYPE_EXAM = "exam"
TYPE_COURSE = "course"
TYPE_SYSTEM = "system"
ALL_NOTIFICATION_TYPES = {
    TYPE_INFORMATION,
    TYPE_UPDATE,
    TYPE_EXAM,
    TYPE_COURSE,
    TYPE_SYSTEM,
}


class Notification(BaseModel):

    __tablename__ = "notifications"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(
        String(20), default=TYPE_INFORMATION, server_default=TYPE_INFORMATION, nullable=False
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user = relationship("User")
