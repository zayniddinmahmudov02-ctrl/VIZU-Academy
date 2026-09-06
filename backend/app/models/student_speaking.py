from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import BaseModel

STATUS_SUBMITTED = "SUBMITTED"
STATUS_GRADED = "GRADED"
STATUS_NEEDS_REVISION = "NEEDS_REVISION"
ALL_STUDENT_SPEAKING_STATUSES = {STATUS_SUBMITTED, STATUS_GRADED, STATUS_NEEDS_REVISION}


class StudentSpeaking(BaseModel):
    """One student's audio answer to one legacy Speaking task — exactly
    one row per (user_id, speaking_id), re-recording replaces the row's
    audio in place (same convention as the Assessment Engine's
    SpeakingSubmission). This table already existed but had NO `user_id`
    column at all — its own API router already assumed `item.user_id`
    existed (see app/api/student_speaking/router.py's
    _ensure_owner_or_admin), so it would have raised the instant it was
    ever actually called; this migration fixes that real, pre-existing
    gap rather than reversing an intentional design. `audio_url` was the
    original (NOT NULL) column for this, but nothing ever successfully
    wrote a row here (no user_id to write), so it's now nullable and
    unused — `storage_path`/`filename`/`content_type` are what a private,
    non-public-URL recording actually needs (see
    app/core/storage/protected_local.py's ProtectedLegacySpeakingStorage).
    grammar_score/vocabulary_score/pronunciation_score/fluency_score/
    task_score/overall_score/ai_feedback were an earlier, never-wired-up
    AI-grading attempt, left as-is (unused, harmless) — `score`/
    `feedback`/`reviewed_by_id`/`reviewed_at` are the real fields this
    feature's teacher grading uses."""

    __tablename__ = "student_speakings"

    user_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    speaking_id: Mapped[str] = mapped_column(
        ForeignKey("speakings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    audio_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    transcript: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    grammar_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    vocabulary_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    pronunciation_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    fluency_score: Mapped[int] = mapped_column(
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
        default=STATUS_SUBMITTED,
        server_default=STATUS_SUBMITTED,
    )

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", foreign_keys=[user_id])

    speaking = relationship(
        "Speaking",
        back_populates="student_results",
    )

    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
