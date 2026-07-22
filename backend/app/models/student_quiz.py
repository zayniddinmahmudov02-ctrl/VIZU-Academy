from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import BaseModel


class StudentQuiz(BaseModel):

    __tablename__ = "student_quizzes"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    quiz_id: Mapped[str] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    correct_answers: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    wrong_answers: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    skipped_answers: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    passed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    user = relationship(
        "User",
    )

    quiz = relationship(
        "Quiz",
    )