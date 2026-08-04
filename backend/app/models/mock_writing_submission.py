from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class MockWritingSubmission(BaseModel):
    """A student's answer to a WritingTask, plus Gemini's evaluation and
    any teacher override. Separate from the existing `student_writing`
    table, which belongs to the Lesson-based course system."""

    __tablename__ = "mock_writing_submissions"

    attempt_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mock_test_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    writing_task_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("writing_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    ai_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_grammar_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_vocabulary_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_structure_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_task_achievement_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_coherence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Set when the AI evaluation actually runs — distinct from `submitted_at`
    # (when the student answered). Needed for "checked today" dashboard
    # stats (Phase 5), which would otherwise have no accurate signal for
    # when the AI review happened.
    ai_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    teacher_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    teacher_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    attempt = relationship("MockTestAttempt", back_populates="writing_submissions")
    writing_task = relationship("WritingTask", back_populates="submissions")
