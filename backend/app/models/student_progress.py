from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import BaseModel


class StudentProgress(BaseModel):

    __tablename__ = "student_progress"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "lesson_id",
            name="uq_student_progress_user_lesson",
        ),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    lesson_id: Mapped[str] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    video_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    grammar_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    vocabulary_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    vocabulary_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    reading_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    listening_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    writing_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    speaking_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    quiz_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    total_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    lesson_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    user = relationship("User")

    lesson = relationship("Lesson")
    module_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    course_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    unlocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    experience: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    study_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    streak_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )