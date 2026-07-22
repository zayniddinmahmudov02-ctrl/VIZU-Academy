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


class StudentSpeaking(BaseModel):

    __tablename__ = "student_speakings"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    speaking_id: Mapped[str] = mapped_column(
        ForeignKey("speakings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    audio_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    transcript: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    grammar_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    vocabulary_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    pronunciation_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    fluency_score: Mapped[int] = mapped_column(
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

    speaking = relationship(
        "Speaking",
        back_populates="student_results",
    )