from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import BaseModel


class StudentWriting(BaseModel):

    __tablename__ = "student_writings"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    writing_id: Mapped[str] = mapped_column(
        ForeignKey("writings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    answer_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    grammar_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    vocabulary_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    coherence_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    task_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    overall_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    ai_feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
    )

    user = relationship(
        "User",
    )

    writing = relationship(
        "Writing",
    )