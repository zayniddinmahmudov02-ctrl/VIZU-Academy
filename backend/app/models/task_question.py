from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class TaskQuestion(BaseModel):
    """One question/statement/gap/paragraph within a Task — how it's
    interpreted depends on the parent Task's task_type (same
    interpret-by-parent-type convention as the existing MockQuestion
    model). For CLOZE_TEXT, one row per gap ("Lücke"); for SHORT_ANSWER,
    a single row holding the free-text correct answer; for option-based
    types (TRUE_FALSE, MULTIPLE_CHOICE, *_MATCHING, ...), the row's
    `options` carry the actual choices/pairs."""

    __tablename__ = "task_questions"

    task_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # CLOZE_TEXT / SHORT_ANSWER only — free-text correct answer.
    correct_text_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON-encoded list of acceptable alternative spellings/answers.
    alternative_answers: Mapped[str | None] = mapped_column(Text, nullable=True)
    case_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    points: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    task = relationship("AssessmentTask", back_populates="questions")
    options = relationship(
        "TaskOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="TaskOption.sort_order",
    )
