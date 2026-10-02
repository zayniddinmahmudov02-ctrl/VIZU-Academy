from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

STATUS_DRAFT = "DRAFT"
STATUS_SUBMITTED = "SUBMITTED"
ALL_WRITING_SUBMISSION_STATUSES = {STATUS_DRAFT, STATUS_SUBMITTED}


class VizuMultilevelWritingTask(BaseModel):
    """One Schreiben Aufgabe (topic) — independent of the Course/
    Vorbereitung Writing systems by design (see VizuMultilevelAudio's own
    docstring for the same rationale). Unlike Lesen/Hören's VizuMultilevelTask
    (auto-graded MC/TF/Cloze), Schreiben is free-text and teacher-graded,
    so it needs its own shape: instruction + word limits + an optional
    topic image + a rubric (see VizuMultilevelWritingRubricCriterion) instead
    of questions/options.

    Content is seeded once (see scripts/seed_vizu_multilevel_schreiben.py) but,
    unlike Lesen/Hören, IS meant to be edited afterward from the admin
    panel (title/instruction/word limits/image/points/rubric/order/
    is_active) — this module explicitly asked for a real admin editor,
    not just a read-only content preview."""

    __tablename__ = "vizu_mock_writing_tasks"

    level: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    min_words: Mapped[int] = mapped_column(Integer, nullable=False)
    max_words: Mapped[int] = mapped_column(Integer, nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=20, server_default="20", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    rubric_criteria = relationship(
        "VizuMultilevelWritingRubricCriterion",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="VizuMultilevelWritingRubricCriterion.order_index",
    )


class VizuMultilevelWritingRubricCriterion(BaseModel):
    """One scoring criterion within a Schreiben Aufgabe's rubric (e.g.
    "Aufgaben erfüllt", 0-8) — same shape as the Assessment Engine's
    WritingRubricCriterion, kept as an independent, VIZU-Multilevel-owned copy
    rather than a shared/imported table (see VizuMultilevelAudio's docstring)."""

    __tablename__ = "vizu_mock_writing_rubric_criteria"

    task_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vizu_mock_writing_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    max_score: Mapped[int] = mapped_column(Integer, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)

    task = relationship("VizuMultilevelWritingTask", back_populates="rubric_criteria")


class VizuMultilevelWritingSubmission(BaseModel):
    """One student's answer to one Schreiben Aufgabe within one attempt —
    a single row per (attempt, task), updated in place while status is
    DRAFT (every "Speichern" click), then frozen once the whole Schreiben
    module is submitted (attempt.schreiben_submitted_at gets set) — no
    further edits are accepted after that (enforced in
    services/vizu_multilevel/schreiben_service.py, not just the UI)."""

    __tablename__ = "vizu_mock_writing_submissions"

    attempt_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vizu_mock_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vizu_mock_writing_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, default="", server_default="", nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=STATUS_DRAFT, server_default=STATUS_DRAFT, nullable=False)
    saved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Teacher grading — a single denormalized total (sum of this
    # submission's VizuMultilevelWritingCriterionScore rows) kept in sync by
    # the grading service, same convention as MockWritingSubmission
    # .teacher_score / WritingSubmission.final_score.
    teacher_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    teacher_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    task = relationship("VizuMultilevelWritingTask")
    reviewed_by = relationship("User")
    criterion_scores = relationship(
        "VizuMultilevelWritingCriterionScore", back_populates="submission", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("attempt_id", "task_id", name="uq_vizu_mock_writing_submission_attempt_task"),)


class VizuMultilevelWritingCriterionScore(BaseModel):
    """One rubric criterion's score within a graded submission — e.g.
    "Grammatik: 3/4". Summed into VizuMultilevelWritingSubmission.teacher_score
    by the grading service whenever a criterion score is upserted."""

    __tablename__ = "vizu_mock_writing_criterion_scores"

    submission_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vizu_mock_writing_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    criterion_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vizu_mock_writing_rubric_criteria.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)

    submission = relationship("VizuMultilevelWritingSubmission", back_populates="criterion_scores")
    criterion = relationship("VizuMultilevelWritingRubricCriterion")

    __table_args__ = (
        UniqueConstraint("submission_id", "criterion_id", name="uq_vizu_mock_writing_score_submission_criterion"),
    )
