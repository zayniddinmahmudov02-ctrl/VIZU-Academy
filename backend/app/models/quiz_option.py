from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import BaseModel


class QuizOption(BaseModel):

    __tablename__ = "quiz_options"

    question_id: Mapped[str] = mapped_column(
        ForeignKey(
            "quiz_questions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    option_text: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    match_value: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    order_index: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    question = relationship(
        "QuizQuestion",
        back_populates="options",
    )