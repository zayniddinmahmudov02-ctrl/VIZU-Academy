from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import BaseModel

STATUS_DRAFT = "DRAFT"
STATUS_SUBMITTED = "SUBMITTED"
STATUS_GRADED = "GRADED"
STATUS_NEEDS_REVISION = "NEEDS_REVISION"
# AI-evaluated tasks: SUBMITTED = pending_evaluation, then EVALUATING (a worker
# holds it), GRADED (AI or teacher) or EVALUATION_FAILED (retry possible).
STATUS_EVALUATING = "EVALUATING"
STATUS_EVALUATION_FAILED = "EVALUATION_FAILED"
ALL_STUDENT_WRITING_STATUSES = {
    STATUS_DRAFT,
    STATUS_SUBMITTED,
    STATUS_GRADED,
    STATUS_NEEDS_REVISION,
    STATUS_EVALUATING,
    STATUS_EVALUATION_FAILED,
}


class StudentWriting(BaseModel):
    """One student's answer to one legacy Writing task — exactly one row
    per (user_id, writing_id), updated in place across Entwurf speichern
    (DRAFT) -> Aufgabe abgeben (SUBMITTED) -> teacher review (GRADED /
    NEEDS_REVISION), same "single row, replaced not versioned" convention
    as the Assessment Engine's WritingSubmission. This table already
    existed (unused until now) — extended here rather than creating a
    second Writing-submission table; grammar_score/vocabulary_score/
    coherence_score/task_score/overall_score/ai_feedback were an earlier,
    never-wired-up AI-grading attempt and are left as-is (unused, but
    harmless) — `score`/`feedback`/`reviewed_by_id`/`reviewed_at` are the
    real, teacher-driven grading fields this feature actually uses."""

    __tablename__ = "student_writings"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    writing_id: Mapped[str] = mapped_column(
        ForeignKey("writings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    answer_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    grammar_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    vocabulary_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    coherence_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    task_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    overall_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    ai_feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default=STATUS_DRAFT,
        server_default=STATUS_DRAFT,
    )

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ---- AI evaluation (tasks with ai_evaluation_enabled) ----
    # Latest successful AI result (criteria, strengths, errors, ...); every
    # run, failed ones and manual overrides included, is in ai_evaluations.
    ai_evaluation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evaluation_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evaluation_runs: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # Final submissions so far (re-submission allowed up to the task's max_attempts).
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    user = relationship(
        "User",
        foreign_keys=[user_id],
    )

    writing = relationship(
        "Writing",
    )

    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
