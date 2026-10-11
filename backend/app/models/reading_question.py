from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ReadingQuestion(BaseModel):
    __tablename__ = "reading_questions"

    reading_id: Mapped[str] = mapped_column(
        ForeignKey(
            "readings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # MULTIPLE_CHOICE (A/B/C) or TRUE_FALSE (Richtig / Falsch) — see
    # app/models/lesson_skill.py. All options live in reading_options.
    question_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MULTIPLE_CHOICE",
        server_default="MULTIPLE_CHOICE",
    )

    points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    order_index: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    reading = relationship(
        "Reading",
        back_populates="questions",
    )

    options = relationship(
        "ReadingOption",
        back_populates="question",
        cascade="all, delete-orphan",
    )