from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
)

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import BaseModel


class Writing(BaseModel):

    __tablename__ = "writings"

    lesson_id: Mapped[str] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    instruction: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    min_words: Mapped[int] = mapped_column(
        Integer,
        default=30,
    )

    max_words: Mapped[int] = mapped_column(
        Integer,
        default=150,
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
    helper_words: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    opens_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closes_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    lesson = relationship(
        "Lesson",
        back_populates="writings",
    )