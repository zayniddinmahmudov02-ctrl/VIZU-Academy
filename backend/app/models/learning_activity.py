from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

SOURCE_VIDEO = "VIDEO"  # playback position really advanced (server-validated deltas)
SOURCE_SKILL_ATTEMPT = "SKILL_ATTEMPT"  # submitted Lesen / Hören / Übungen attempt


class LearningActivity(BaseModel):
    """Server-confirmed learning time ("Lernserie"): seconds credited to one
    student from one source in one UTC hour bucket. Never written from a
    client-reported duration — see app.services.learning_activity.

    The unique key (user, source, source_ref, bucket_start) makes every
    credit idempotent: an attempt is credited once, video seconds of the same
    video and hour accumulate in one row."""

    __tablename__ = "learning_activity"
    __table_args__ = (
        UniqueConstraint("user_id", "source", "source_ref", "bucket_start", name="uq_learning_activity_bucket"),
    )

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    source_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    lesson_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
    # start of the UTC hour the activity happened in (local days are derived at read time)
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
