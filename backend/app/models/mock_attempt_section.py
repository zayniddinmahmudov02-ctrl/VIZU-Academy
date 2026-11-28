from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

SECTION_OPEN = "OPEN"
SECTION_SUBMITTED = "SUBMITTED"
SECTION_EXPIRED = "EXPIRED"  # closed by the server because the deadline passed

# where `score` comes from (2026-11-28): the Lesen / Hören table, the AI (Schreiben / Sprechen) or a Super Admin override
SOURCE_AUTO, SOURCE_AI, SOURCE_MANUAL = "AUTO", "AI", "MANUAL"
# AI grading of Schreiben / Sprechen (services/mock_exam/multilevel_ai.py)
AI_PENDING, AI_RUNNING, AI_DONE, AI_FAILED = "PENDING", "RUNNING", "DONE", "FAILED"
AI_NEEDS_ADMIN = "NEEDS_ADMIN"  # the raw score falls in a range the conversion table does not cover: the Super Admin decides


class MockAttemptSection(BaseModel):
    """One section (Lesen / Hören / Schreiben / Sprechen) of a timed mock-exam attempt (Multilevel exam mode,
    services/mock_exam/multilevel_exam_service.py). The server sets started_at / deadline_at; `score` is the
    0–75 section score that counts (= override_score when a Super Admin set one, else auto_score: the Lesen / Hören table or
    the AI's converted score), `level` its band. Every AI run and every override is also kept in ai_evaluations (kind ML_SECTION)."""

    __tablename__ = "mock_attempt_sections"
    __table_args__ = (
        UniqueConstraint("attempt_id", "section_type", name="uq_mock_attempt_sections_attempt_type"),
        CheckConstraint("score IS NULL OR (score >= 0 AND score <= 75)", name="ck_mock_attempt_sections_score_0_75"),
        CheckConstraint("auto_score IS NULL OR (auto_score >= 0 AND auto_score <= 75)", name="ck_mock_attempt_sections_auto_score_0_75"),
        CheckConstraint("override_score IS NULL OR (override_score >= 0 AND override_score <= 75)", name="ck_mock_attempt_sections_override_0_75"),
        Index("ix_mock_attempt_sections_ai_status", "ai_status"),
    )

    attempt_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mock_test_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kompetenz_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("kompetenzen.id", ondelete="CASCADE"), nullable=False)
    section_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=SECTION_OPEN, server_default=SECTION_OPEN, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # the section length the server granted when it was opened (Kompetenz.duration_minutes may change later); deadline_at = started_at + this
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    graded_by: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    graded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    # scoring trail (migration c7f4a1e9d3b2): rule / AI score kept even when overridden; the override wins and survives an AI re-run
    auto_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    override_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_source: Mapped[str | None] = mapped_column(String(10), nullable=True)
    ai_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_raw: Mapped[float | None] = mapped_column(Numeric(6, 2, asdecimal=False), nullable=True)
    ai_raw_max: Mapped[float | None] = mapped_column(Numeric(6, 2, asdecimal=False), nullable=True)
    ai_claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ai_runs: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    attempt = relationship("MockTestAttempt", back_populates="sections")
