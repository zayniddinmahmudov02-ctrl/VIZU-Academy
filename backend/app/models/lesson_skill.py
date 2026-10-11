"""Lesson skill exercises (A1 Modul 1 onward) on top of the legacy lesson
tables:

* Lesen  — readings -> reading_questions -> reading_options (existing).
* Hören  — listenings (existing) -> listening_questions -> listening_options.
* LessonSkillAttempt — one graded Lesen/Hören test run (answers, score,
  duration). Correct answers live only in the *_options tables and are
  compared on the server.
* AiEvaluation — append-only history of every AI evaluation run (and every
  manual score override) of a Schreiben/Sprechen submission, so the
  original AI result is never lost when an admin corrects a score."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# Question types shared by Lesen and Hören
QUESTION_MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
QUESTION_TRUE_FALSE = "TRUE_FALSE"  # "Richtig / Falsch" — two options
# config-based types (answer key inside `config`, never sent to students):
QUESTION_MATCHING = "MATCHING"  # Zuordnung: items -> targets
QUESTION_GAP_FILL = "GAP_FILL"  # Lückentext: [[gap]] placeholders
QUESTION_SHORT_ANSWER = "SHORT_ANSWER"  # short text vs. accepted answers
OPTION_TYPES = {QUESTION_MULTIPLE_CHOICE, QUESTION_TRUE_FALSE}
CONFIG_TYPES = {QUESTION_MATCHING, QUESTION_GAP_FILL, QUESTION_SHORT_ANSWER}
QUESTION_TYPES = OPTION_TYPES | CONFIG_TYPES

SKILL_LESEN = "LESEN"
SKILL_HOEREN = "HOEREN"

ATTEMPT_IN_PROGRESS = "IN_PROGRESS"
ATTEMPT_SUBMITTED = "SUBMITTED"

EVAL_KIND_WRITING = "WRITING"
EVAL_KIND_SPEAKING = "SPEAKING"
EVAL_SOURCE_AI = "AI"
EVAL_SOURCE_OVERRIDE = "MANUAL_OVERRIDE"
EVAL_SUCCEEDED = "SUCCEEDED"
EVAL_FAILED = "FAILED"


class ListeningQuestion(BaseModel):
    __tablename__ = "listening_questions"

    listening_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("listenings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=QUESTION_MULTIPLE_CHOICE, server_default=QUESTION_MULTIPLE_CHOICE
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    # MATCHING / GAP_FILL / SHORT_ANSWER definition incl. answer key
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    options = relationship(
        "ListeningOption", cascade="all, delete-orphan", order_by="ListeningOption.order_index", lazy="selectin"
    )


class ListeningOption(BaseModel):
    __tablename__ = "listening_options"

    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("listening_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    option_text: Mapped[str] = mapped_column(String(500), nullable=False)
    # Server-side answer key — never serialised to students before grading.
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")


class LessonSkillAttempt(BaseModel):
    """One Lesen test (all of a lesson's published texts) or one Hören task
    test. `answers` = {question_id: option_id} as submitted; grading happens
    on the server against the stored answer key."""

    __tablename__ = "lesson_skill_attempts"
    __table_args__ = (Index("ix_lesson_skill_attempts_user_lesson_skill", "user_id", "lesson_id", "skill"),)

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    skill: Mapped[str] = mapped_column(String(20), nullable=False)
    # Hören: the task the test belongs to; Lesen: NULL (one test per lesson).
    listening_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("listenings.id", ondelete="CASCADE"), nullable=True, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ATTEMPT_IN_PROGRESS, server_default=ATTEMPT_IN_PROGRESS)
    answers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    correct_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    question_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[float | None] = mapped_column(Numeric(7, 2, asdecimal=False), nullable=True)
    max_points: Mapped[float | None] = mapped_column(Numeric(7, 2, asdecimal=False), nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)


class AiEvaluation(BaseModel):
    """Audit history: every AI evaluation run (succeeded or failed) and every
    manual override of a Schreiben/Sprechen submission. Never updated."""

    __tablename__ = "ai_evaluations"
    __table_args__ = (Index("ix_ai_evaluations_submission", "kind", "submission_id"),)

    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # WRITING | SPEAKING
    submission_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default=EVAL_SOURCE_AI)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    actor_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
