from sqlalchemy import Boolean, ForeignKey, Integer, Text
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