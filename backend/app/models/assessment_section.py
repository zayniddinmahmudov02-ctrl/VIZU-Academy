from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# Same four skill values as the existing Kompetenz system
# (app/models/kompetenz.py) — kept consistent in naming even though this is
# a separate table for a separate (generic, Course + Mock Test) engine.
SKILL_LESEN = "LESEN"
SKILL_HOEREN = "HOEREN"
SKILL_SCHREIBEN = "SCHREIBEN"
SKILL_SPRECHEN = "SPRECHEN"
ALL_SKILLS = {SKILL_LESEN, SKILL_HOEREN, SKILL_SCHREIBEN, SKILL_SPRECHEN}


class AssessmentSection(BaseModel):
    """One skill section ("Lesen") within an Assessment."""

    __tablename__ = "assessment_sections"

    assessment_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    assessment = relationship("Assessment", back_populates="sections")
    tasks = relationship(
        "AssessmentTask",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="AssessmentTask.sort_order",
    )
