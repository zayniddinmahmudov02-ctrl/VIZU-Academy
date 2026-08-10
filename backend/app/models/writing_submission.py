from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

STATUS_DRAFT = "DRAFT"
STATUS_SUBMITTED = "SUBMITTED"
STATUS_PENDING_REVIEW = "PENDING_REVIEW"
STATUS_GRADED = "GRADED"
ALL_SUBMISSION_STATUSES = {STATUS_DRAFT, STATUS_SUBMITTED, STATUS_PENDING_REVIEW, STATUS_GRADED}


class WritingSubmission(BaseModel):
    """One user's answer to one WRITING task within one attempt — exactly
    one row per (attempt_id, task_id), updated in place across
    Speichern (DRAFT) -> Abgeben (SUBMITTED) -> evaluated (PENDING_REVIEW /
    GRADED), rather than versioned as separate rows."""

    __tablename__ = "writing_submissions"
    __table_args__ = (UniqueConstraint("attempt_id", "task_id", name="uq_writing_submission_attempt_task"),)

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_sections.id", ondelete="CASCADE"), nullable=False
    )
    task_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    character_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=STATUS_DRAFT, server_default=STATUS_DRAFT, nullable=False, index=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    final_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user = relationship("User")
    assessment = relationship("Assessment")
    task = relationship("AssessmentTask")
    attempt = relationship("AssessmentAttempt")
    evaluations = relationship(
        "WritingEvaluation",
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="WritingEvaluation.created_at",
    )
