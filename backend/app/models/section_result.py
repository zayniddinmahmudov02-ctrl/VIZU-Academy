from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class SectionResult(BaseModel):
    """Per-section score subtotal for one AssessmentAttempt, computed once
    the attempt is graded."""

    __tablename__ = "section_results"

    assessment_attempt_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_sections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_section_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    assessment_attempt = relationship("AssessmentAttempt", back_populates="section_results")
    section = relationship("AssessmentSection")
