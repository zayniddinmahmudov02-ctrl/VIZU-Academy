from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class MockQuestionAnswer(BaseModel):
    """A student's answer to one MockQuestion within an attempt.
    `answer_data` is JSON-encoded text — its shape depends on the parent
    question's `question_type` (selected option id(s), an ordering
    sequence of option ids, free text for FILL_BLANK, or matching pairs).
    A flexible text column here avoids needing five near-identical answer
    tables, one per question type."""

    __tablename__ = "mock_question_answers"

    attempt_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mock_test_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mock_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answer_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    points_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    attempt = relationship("MockTestAttempt", back_populates="question_answers")
    question = relationship("MockQuestion")
