from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

SECTION_OPEN = "OPEN"
SECTION_SUBMITTED = "SUBMITTED"
SECTION_EXPIRED = "EXPIRED"  # closed by the server because the deadline passed


class MockAttemptSection(BaseModel):
    """One section (Lesen / Hören / Schreiben / Sprechen) of a timed mock-exam attempt (Multilevel exam mode,
    services/mock_exam/multilevel_exam_service.py). The server sets started_at / deadline_at; `score` is the
    0–75 section score (auto for Lesen/Hören, graded by a teacher for Schreiben/Sprechen), `level` its band."""

    __tablename__ = "mock_attempt_sections"
    __table_args__ = (
        UniqueConstraint("attempt_id", "section_type", name="uq_mock_attempt_sections_attempt_type"),
        CheckConstraint("score IS NULL OR (score >= 0 AND score <= 75)", name="ck_mock_attempt_sections_score_0_75"),
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
    raw_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    graded_by: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    graded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    attempt = relationship("MockTestAttempt", back_populates="sections")
