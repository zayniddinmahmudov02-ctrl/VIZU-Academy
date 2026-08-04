from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class MockSpeakingSubmission(BaseModel):
    """A student's recorded answer to a SpeakingTask, plus Gemini's
    speech-to-text transcript + evaluation. Separate from the existing
    `student_speaking` table (Lesson-based course system)."""

    __tablename__ = "mock_speaking_submissions"

    attempt_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mock_test_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    speaking_task_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("speaking_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    audio_url: Mapped[str] = mapped_column(Text, nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)

    ai_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    # See MockWritingSubmission.ai_evaluated_at for why this is separate
    # from submitted_at.
    ai_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    teacher_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    teacher_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    attempt = relationship("MockTestAttempt", back_populates="speaking_submissions")
    speaking_task = relationship("SpeakingTask", back_populates="submissions")
