from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

EVALUATOR_AI = "AI"
EVALUATOR_TEACHER = "TEACHER"
ALL_EVALUATOR_TYPES = {EVALUATOR_AI, EVALUATOR_TEACHER}


class WritingEvaluation(BaseModel):
    """One evaluation pass over a WritingSubmission — AI produces one row
    on submit (for AI_ONLY / AI_AND_TEACHER), a teacher produces another
    (for TEACHER_ONLY / to finalize AI_AND_TEACHER). Multiple rows can
    exist per submission; WritingSubmission.final_score/status always
    reflect whichever evaluation is currently authoritative."""

    __tablename__ = "writing_evaluations"

    submission_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("writing_submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evaluator_type: Mapped[str] = mapped_column(String(10), nullable=False)
    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # JSON text: {criterion_id: score} — same JSON-as-text convention used
    # throughout this engine (Answer.answer_data, TaskAudio, ...).
    rubric_scores: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)

    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON list of grammar/vocabulary/structure/task-completion issues.
    errors: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggestions: Mapped[str | None] = mapped_column(Text, nullable=True)

    submission = relationship("WritingSubmission", back_populates="evaluations")
    reviewed_by = relationship("User")
