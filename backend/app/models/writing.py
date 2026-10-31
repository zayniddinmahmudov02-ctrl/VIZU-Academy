from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
)

from datetime import datetime

from sqlalchemy import DateTime, or_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import BaseModel

# The competency a written task belongs to (migration d7e2b4f8a1c6). NULL =
# SCHREIBEN, so every task that existed before stays a Schreiben task. A
# Wortschatz worksheet, a Grammatik written exercise or the open questions on a
# Lesen text are answered in writing too, but they belong to — and are shown,
# counted and evaluated in — their own competency, never in Schreiben.
WRITING_COMPETENCY_SCHREIBEN = "SCHREIBEN"
WRITING_COMPETENCIES = ("SCHREIBEN", "GRAMMATIK", "WORTSCHATZ", "LESEN")


class Writing(BaseModel):

    __tablename__ = "writings"
    __table_args__ = (
        CheckConstraint("competency IS NULL OR competency IN ('SCHREIBEN', 'GRAMMATIK', 'WORTSCHATZ', 'LESEN')", name="ck_writings_competency"),
    )

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

    # NULL = no word limit (e.g. a book task that states none): nothing is
    # shown or enforced for that bound (migration a7c2e9f4b1d6). No column
    # default — it would silently turn an intended NULL into a limit; the
    # admin form's defaults (30 / 150) live in WritingBase.
    min_words: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    max_words: Mapped[int | None] = mapped_column(
        Integer,
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
    # A1-C1 task metadata: message / email / letter / description / opinion / essay / other
    text_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # audience or communicative situation ("an einen Freund", "an die Hausverwaltung")
    audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)  # recommended time
    # stable id of imported (Claude JSON) content — duplicate detection
    content_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    competency: Mapped[str | None] = mapped_column(String(20), nullable=True)

    @property
    def competency_kind(self) -> str:
        return self.competency or WRITING_COMPETENCY_SCHREIBEN

    lesson = relationship(
        "Lesson",
        back_populates="writings",
    )


def writing_competency_filter(competency: str):
    """SQL condition: the written tasks of one competency (NULL = Schreiben)."""
    if competency == WRITING_COMPETENCY_SCHREIBEN:
        return or_(Writing.competency.is_(None), Writing.competency == WRITING_COMPETENCY_SCHREIBEN)
    return Writing.competency == competency