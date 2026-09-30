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

# Which of the lesson's quizzes this is. GRAMMAR is the mid-lesson
# check tied to the Grammatik section — its score counts for 10 of the
# lesson's 100 points. LESSON is the end-of-lesson diagnostic — shown to
# the student separately and never added to the 100-point score (see
# app/services/lesson_scoring/service.py). VOCABULARY is the A1-only,
# auto-generated 20-question Wortschatz test (see
# app/services/vocabulary/test_sync_service.py) — its score is never
# read back from this Quiz/StudentQuiz machinery; it feeds
# StudentProgress.vocabulary_score directly instead, so it's excluded
# from lesson_scoring/service.py's quiz-type lookups on purpose.
QUIZ_TYPE_GRAMMAR = "GRAMMAR"
QUIZ_TYPE_LESSON = "LESSON"
QUIZ_TYPE_VOCABULARY = "VOCABULARY"
ALL_QUIZ_TYPES = {QUIZ_TYPE_GRAMMAR, QUIZ_TYPE_LESSON, QUIZ_TYPE_VOCABULARY}


class Quiz(BaseModel):

    __tablename__ = "quizzes"

    lesson_id: Mapped[str] = mapped_column(
        ForeignKey(
            "lessons.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    quiz_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=QUIZ_TYPE_GRAMMAR,
        server_default=QUIZ_TYPE_GRAMMAR,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    passing_score: Mapped[int] = mapped_column(
        Integer,
        default=70,
    )

    order_index: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    lesson = relationship(
        "Lesson",
    )

    questions = relationship(
        "QuizQuestion",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )