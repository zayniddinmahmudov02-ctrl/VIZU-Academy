from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import BaseModel


class Speaking(BaseModel):

    __tablename__ = "speakings"

    lesson_id: Mapped[str] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    topic: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    instruction: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    sample_answer: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    keywords: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    preparation_time: Mapped[int] = mapped_column(
        Integer,
        default=15,
    )

    speaking_time: Mapped[int] = mapped_column(
        Integer,
        default=90,
    )

    order_index: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )


    # ---- AI evaluation (per task; existing tasks keep teacher grading) ----
    ai_evaluation_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    # Extra, server-side-only instructions for the evaluator (never sent to students).
    ai_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Language of the feedback explanations ("uz", "de", ...); examples stay German.
    feedback_language: Mapped[str] = mapped_column(String(10), nullable=False, default="uz", server_default="uz")
    # Points the task is worth (the stored score itself is always 0-100).
    max_score: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    # [{"key": "...", "name": "...", "max": 25}, ...] — NULL = the A1 default rubric.
    rubric: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default="3")
    # speaking_time (seconds) is the maximum answer length; this is the minimum.
    min_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # A1-C1 task metadata
    response_type: Mapped[str] = mapped_column(String(20), nullable=False, default="MONOLOG", server_default="MONOLOG")  # MONOLOG | DIALOG
    questions: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # guiding questions shown to the student
    # expected communicative goal — used by the AI evaluation, not shown to students
    speech_goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    # stable id of imported (Claude JSON) content — duplicate detection
    content_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)

    lesson = relationship(
        "Lesson",
        back_populates="speakings",
    )

    student_results = relationship(
        "StudentSpeaking",
        back_populates="speaking",
        cascade="all, delete-orphan",
    )