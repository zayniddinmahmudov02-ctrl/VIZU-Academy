from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Answer(BaseModel):
    """A student's answer to one TaskQuestion within a TaskAttempt.
    `answer_data` is JSON-encoded text — shape depends on the parent
    question's task_type (selected option id(s), an ordering sequence,
    free text, or matching pairs) — same flexible-JSON-text convention as
    the existing MockQuestionAnswer.answer_data, avoiding a separate
    answer table per task type."""

    __tablename__ = "answers"

    task_attempt_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("task_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("task_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    answer_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    points_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    task_attempt = relationship("TaskAttempt", back_populates="answers")
    question = relationship("TaskQuestion")
