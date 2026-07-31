from sqlalchemy import Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class VideoProgress(BaseModel):
    __tablename__ = "video_progress"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "video_id",
            name="uq_video_progress_user_video",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    video_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Denormalized from video.lesson_id — cheap "does this user still
    # need to watch lesson X's video" lookups without a join.
    lesson_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    last_position: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    watch_percent: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
