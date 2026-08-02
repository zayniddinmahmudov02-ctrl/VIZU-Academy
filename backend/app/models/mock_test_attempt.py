from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_SUBMITTED = "SUBMITTED"
STATUS_GRADED = "GRADED"


class MockTestAttempt(BaseModel):
    """One student's attempt at a ModelTest. Separate from the existing
    `student_progress`/`enrollment` tables, which track Lesson-based course
    progress — this is exam-simulation history, a distinct concept."""

    __tablename__ = "mock_test_attempts"

    model_test_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("model_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=STATUS_IN_PROGRESS,
        server_default=STATUS_IN_PROGRESS,
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    model_test = relationship("ModelTest")
    user = relationship("User")
    question_answers = relationship(
        "MockQuestionAnswer",
        back_populates="attempt",
        cascade="all, delete-orphan",
    )
    writing_submissions = relationship(
        "MockWritingSubmission",
        back_populates="attempt",
        cascade="all, delete-orphan",
    )
    speaking_submissions = relationship(
        "MockSpeakingSubmission",
        back_populates="attempt",
        cascade="all, delete-orphan",
    )
