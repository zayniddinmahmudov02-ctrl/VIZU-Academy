from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# Skill values — only LESEN is populated today; the column exists so a
# later phase can add Hören/Schreiben/Sprechen content to these same
# tables without a new migration.
SKILL_LESEN = "LESEN"
SKILL_HOEREN = "HOEREN"
SKILL_SCHREIBEN = "SCHREIBEN"
SKILL_SPRECHEN = "SPRECHEN"
ALL_SKILLS = {SKILL_LESEN, SKILL_HOEREN, SKILL_SCHREIBEN, SKILL_SPRECHEN}

QUESTION_TYPE_TRUE_FALSE = "TRUE_FALSE"
QUESTION_TYPE_MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
QUESTION_TYPE_CLOZE_TEXT = "CLOZE_TEXT"
# Reading formats. All are graded identically (exactly one correct option);
# the type only describes the task format for the admin / the student UI.
QUESTION_TYPE_HEADLINE_MATCH = "HEADLINE_MATCH"  # Überschrift zuordnen
QUESTION_TYPE_AD_MATCH = "AD_MATCH"  # Anzeige zuordnen
QUESTION_TYPE_STATEMENT_MATCH = "STATEMENT_MATCH"  # Aussage zuordnen
QUESTION_TYPE_MAIN_IDEA = "MAIN_IDEA"  # Hauptaussage finden
QUESTION_TYPE_DETAIL = "DETAIL"  # Detailinformation
QUESTION_TYPE_INFO_MATCH = "INFO_MATCH"  # passende Information finden
QUESTION_TYPE_COMPREHENSION = "COMPREHENSION"  # Textverständnis
ALL_QUESTION_TYPES = {
    QUESTION_TYPE_TRUE_FALSE,
    QUESTION_TYPE_MULTIPLE_CHOICE,
    QUESTION_TYPE_CLOZE_TEXT,
    QUESTION_TYPE_HEADLINE_MATCH,
    QUESTION_TYPE_AD_MATCH,
    QUESTION_TYPE_STATEMENT_MATCH,
    QUESTION_TYPE_MAIN_IDEA,
    QUESTION_TYPE_DETAIL,
    QUESTION_TYPE_INFO_MATCH,
    QUESTION_TYPE_COMPREHENSION,
}

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1"]


class VizuMultilevelTask(BaseModel):
    """One "Aufgabe" — a group of questions tied to one CEFR level.
    `order_index` is the task's fixed position within its skill (1-10 for
    Lesen today: 2 tasks x 5 levels), used both to render tasks in order
    and as the natural-key half of the seed script's idempotency check
    (see app/scripts/seed_vizu_multilevel_lesen.py).

    `passage_text` is nullable: some Aufgaben share one reading passage
    across both of their questions (set here), others pair each question
    with its own distinct, unrelated passage (set per-question instead,
    see VizuMultilevelQuestion.passage_text below) — the real source content
    genuinely mixes both shapes, so this isn't simplified away."""

    __tablename__ = "vizu_mock_tasks"

    skill: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    passage_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Hören only: the audio's transcript. Admin-side reference text — never
    # included in any student-facing schema (the student only hears audio).
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Unpublished Aufgaben are invisible to students and excluded from
    # grading (the admin can prepare content before releasing it).
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    questions = relationship(
        "VizuMultilevelQuestion",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="VizuMultilevelQuestion.order_index",
    )

    __table_args__ = (UniqueConstraint("skill", "order_index", name="uq_vizu_mock_task_skill_order"),)


class VizuMultilevelQuestion(BaseModel):
    """One graded question within a Task. Every question type in the
    Lesen module today (Richtig/Falsch, Multiple Choice, Lückentext) is
    graded the same way — exactly one of its Options has is_correct=True
    — so no per-type grading branch exists; a free-text question type
    would need one, but none is used here."""

    __tablename__ = "vizu_mock_questions"

    task_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vizu_mock_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # Set only when this question has its own passage distinct from its
    # task's shared one (see VizuMultilevelTask.passage_text's docstring) —
    # None means "render the task's passage_text instead".
    passage_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    # Lesen only: an inactive question is neither shown nor graded.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    # Numeric, not Integer: Hören weights points by the question's CEFR
    # level (A1=0.5 ... C1=2.5, see services/vizu_multilevel/
    # hoeren_csv_import_service.py) — Lesen's flat 5-per-question still
    # stores fine as a Numeric value (5.0), so this is a safe widening
    # shared by both skills' questions.
    points: Mapped[float] = mapped_column(
        Numeric(4, 1, asdecimal=False), default=1, server_default="1", nullable=False
    )

    task = relationship("VizuMultilevelTask", back_populates="questions")
    options = relationship(
        "VizuMultilevelOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="VizuMultilevelOption.order_index",
    )


class VizuMultilevelOption(BaseModel):
    __tablename__ = "vizu_mock_options"

    question_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vizu_mock_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    question = relationship("VizuMultilevelQuestion", back_populates="options")


class VizuMultilevelAnswer(BaseModel):
    """One student's recorded answer to one Lesen question within one
    attempt — written once, at submit time (see
    services/vizu_multilevel/lesen_service.py.submit_lesen), never before.
    The unique constraint is what makes a resubmit idempotent: a second
    submit for the same attempt is detected (rows already exist) and
    short-circuits to just re-reading the stored result instead of
    inserting again."""

    __tablename__ = "vizu_mock_answers"

    attempt_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vizu_mock_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vizu_mock_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    selected_option_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vizu_mock_options.id", ondelete="SET NULL"), nullable=True
    )
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    points_earned: Mapped[float] = mapped_column(
        Numeric(4, 1, asdecimal=False), default=0, server_default="0", nullable=False
    )

    __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_vizu_mock_answer_attempt_question"),)
