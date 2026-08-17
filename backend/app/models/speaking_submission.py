from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

STATUS_PENDING_REVIEW = "PENDING_REVIEW"
STATUS_REVIEWED = "REVIEWED"
STATUS_FINAL = "FINAL"
ALL_SPEAKING_SUBMISSION_STATUSES = {STATUS_PENDING_REVIEW, STATUS_REVIEWED, STATUS_FINAL}


class SpeakingSubmission(BaseModel):
    """One user's audio answer to one SPEAKING task within one attempt —
    exactly one row per (attempt_id, task_id); a re-record replaces the
    row's audio file and metadata in place (same replace semantics as
    TaskAudio.upload_audio), it doesn't create a second row. Named/shaped
    to mirror WritingSubmission (this engine's other submission-based skill),
    with audio metadata instead of text content — same fields TaskAudio
    already carries (storage_path/filename/format/duration/size)."""

    __tablename__ = "speaking_submissions"
    __table_args__ = (UniqueConstraint("attempt_id", "task_id", name="uq_speaking_submission_attempt_task"),)

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

    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), default=STATUS_PENDING_REVIEW, server_default=STATUS_PENDING_REVIEW, nullable=False, index=True
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    final_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    user = relationship("User")
    assessment = relationship("Assessment")
    task = relationship("AssessmentTask")
    attempt = relationship("AssessmentAttempt")
    evaluations = relationship(
        "SpeakingEvaluation",
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="SpeakingEvaluation.created_at",
    )
