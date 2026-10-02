from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class VizuMultilevelSpeakingTask(BaseModel):
    """One Sprechen Aufgabe variant — independent of the Course/Vorbereitung
    Speaking systems. The bank holds, for every Aufgabe number
    (`order_index` 1-5 = communicative task type), one variant per CEFR
    `level`; a student gets the ladder Aufgabe 1 @ A1 ... Aufgabe 5 @ C1
    (see sprechen_service.assigned_tasks). `level` is backend/admin-side
    data only; it is never sent to the student."""

    __tablename__ = "vizu_multilevel_speaking_tasks"
    __table_args__ = (
        UniqueConstraint("order_index", "level", name="uq_vizu_multilevel_speaking_task_slot_level"),
    )

    level: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    preparation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    prep_seconds: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    # Recommended speaking time: min_seconds (hint) .. max_seconds (recording auto-stops).
    min_seconds: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    max_seconds: Mapped[int] = mapped_column(Integer, default=120, server_default="120", nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=20, server_default="20", nullable=False)
    # "Published" — unpublished Aufgaben are hidden from students.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)


class VizuMultilevelSpeakingSubmission(BaseModel):
    """One student's recorded answer to one Sprechen Aufgabe within one
    attempt. The audio lives in protected storage (never a public URL) and
    is only served through an authenticated, ownership-checked endpoint."""

    __tablename__ = "vizu_multilevel_speaking_submissions"

    attempt_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vizu_mock_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vizu_multilevel_speaking_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    storage_path: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    teacher_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    teacher_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ---- Server-side pipeline (sprechen_evaluation_service) ----
    # PROCESSING -> TRANSCRIBED -> EVALUATING -> EVALUATED, or FAILED (retryable;
    # the audio and any transcript are kept). NULL = recorded before the AI
    # pipeline existed (teacher-graded only).
    status: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    transcript_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    stt_provider: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # What the STT agent HEARD (pronunciation / fluency / pauses) — input for
    # the pronunciation & fluency criteria, so they are not judged from text alone.
    audio_observations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_criteria: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_feedback: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    evaluation_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Claim marker so one answer is never processed by two workers at once.
    worker_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    task = relationship("VizuMultilevelSpeakingTask")

    __table_args__ = (
        UniqueConstraint("attempt_id", "task_id", name="uq_vizu_multilevel_speaking_submission_attempt_task"),
    )
