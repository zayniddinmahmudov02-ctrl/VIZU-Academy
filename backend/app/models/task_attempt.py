from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_SUBMITTED = "SUBMITTED"
STATUS_GRADED = "GRADED"


class TaskAttempt(BaseModel):
    """Per-task progress/score within an AssessmentAttempt. `max_score` is
    a snapshot of the task's max_points at attempt time, so a later edit
    to the task's points doesn't retroactively change an already-graded
    attempt's denominator."""

    __tablename__ = "task_attempts"

    assessment_attempt_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=STATUS_IN_PROGRESS, server_default=STATUS_IN_PROGRESS, nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    assessment_attempt = relationship("AssessmentAttempt", back_populates="task_attempts")
    task = relationship("AssessmentTask")
    answers = relationship("Answer", back_populates="task_attempt", cascade="all, delete-orphan")
