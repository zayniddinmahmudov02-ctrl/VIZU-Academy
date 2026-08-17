from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class SpeakingEvaluation(BaseModel):
    """A teacher's rubric evaluation of a SpeakingSubmission. Sprechen is
    teacher-only in this phase (no AI audio scoring is built), so unlike
    WritingEvaluation there's no evaluator_type discriminator — every row
    here is a teacher review, `reviewed_by_id` is always set."""

    __tablename__ = "speaking_evaluations"

    submission_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("speaking_submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewed_by_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # JSON text: {criterion_id: score} — same convention as WritingEvaluation.
    rubric_scores: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    feedback_audio_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    feedback_audio_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    feedback_audio_content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    submission = relationship("SpeakingSubmission", back_populates="evaluations")
    reviewed_by = relationship("User")
