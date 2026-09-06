from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

STATUS_SUBMITTED = "SUBMITTED"
STATUS_GRADED = "GRADED"
STATUS_NEEDS_REVISION = "NEEDS_REVISION"
ALL_HOMEWORK_SUBMISSION_STATUSES = {STATUS_SUBMITTED, STATUS_GRADED, STATUS_NEEDS_REVISION}


class HomeworkSubmission(BaseModel):
    """One student's answer to one Homework — exactly one row per
    (student_id, homework_id), updated in place on resubmission (same
    "single row, replaced not versioned" convention as WritingSubmission/
    SpeakingSubmission — see app/models/writing_submission.py).

    There is no stored "NOT_SUBMITTED"/"in progress" state: a student who
    hasn't submitted yet simply has no row here at all (the Teacher Panel's
    homework queue is real submissions only, never a fabricated placeholder
    for work that doesn't exist), and there's no separate draft-save step
    (unlike WritingSubmission's DRAFT status) — this feature intentionally
    ships submit-only for its first pass, so a fourth "in Bearbeitung"
    status the spec asked for would have nothing real to represent.

    A NEEDS_REVISION row moves back to SUBMITTED on resubmission (see
    HomeworkSubmissionService.submit) — score/feedback from the previous
    review are left in place until the teacher grades it again, they are
    never silently cleared.
    """

    __tablename__ = "homework_submissions"
    __table_args__ = (UniqueConstraint("student_id", "homework_id", name="uq_homework_submission_student_homework"),)

    homework_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("homeworks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    text_content: Mapped[str] = mapped_column(Text, default="", nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), default=STATUS_SUBMITTED, server_default=STATUS_SUBMITTED, nullable=False, index=True
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    homework = relationship("Homework")
    student = relationship("User", foreign_keys=[student_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
