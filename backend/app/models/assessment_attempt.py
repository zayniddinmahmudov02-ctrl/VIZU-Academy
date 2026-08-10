from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_SUBMITTED = "SUBMITTED"
STATUS_GRADED = "GRADED"
ALL_ATTEMPT_STATUSES = {STATUS_IN_PROGRESS, STATUS_SUBMITTED, STATUS_GRADED}


class AssessmentAttempt(BaseModel):
    """One user's attempt at an Assessment — the top-level attempt session,
    same shape/purpose as the existing MockTestAttempt but generic (works
    for COURSE, PREPARATION and MOCK_TEST assessments alike) and policy-
    aware (`locked` is set on submit when the assessment doesn't
    allow_edit/allow_resubmit, per the attempt policy on Assessment)."""

    __tablename__ = "assessment_attempts"

    assessment_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=STATUS_IN_PROGRESS, server_default=STATUS_IN_PROGRESS, nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    locked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assessment = relationship("Assessment")
    user = relationship("User")

    task_attempts = relationship(
        "TaskAttempt", back_populates="assessment_attempt", cascade="all, delete-orphan"
    )
    section_results = relationship(
        "SectionResult", back_populates="assessment_attempt", cascade="all, delete-orphan"
    )
    result = relationship(
        "AssessmentResult",
        back_populates="assessment_attempt",
        uselist=False,
        cascade="all, delete-orphan",
    )
