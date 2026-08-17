from sqlalchemy import (
    Boolean,
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


class QuizQuestion(BaseModel):

    __tablename__ = "quiz_questions"

    quiz_id: Mapped[str] = mapped_column(
        ForeignKey(
            "quizzes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    question_type: Mapped[str] = mapped_column(
        String(30),
        default="MULTIPLE_CHOICE",
        server_default="MULTIPLE_CHOICE",
        nullable=False,
    )

    correct_text_answer: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    points: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    order_index: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    quiz = relationship(
        "Quiz",
        back_populates="questions",
    )

    options = relationship(
        "QuizOption",
        back_populates="question",
        cascade="all, delete-orphan",
    )