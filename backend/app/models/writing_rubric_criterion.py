from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class WritingRubricCriterion(BaseModel):
    """One admin-defined scoring criterion for a WRITING task (e.g.
    "Inhalt" = 5 points). Never hardcoded — a task's rubric is exactly
    whatever criteria its admin created here, and AssessmentTask.max_points
    is kept in sync as their sum (mirrors how max_points already tracks
    SUM(TaskQuestion.points) for the objective task types)."""

    __tablename__ = "writing_rubric_criteria"

    task_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    max_score: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    task = relationship("AssessmentTask", back_populates="rubric_criteria")
