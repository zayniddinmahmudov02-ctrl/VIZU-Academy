from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

TYPE_TRUE_FALSE = "TRUE_FALSE"
TYPE_MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
TYPE_MULTIPLE_SELECT = "MULTIPLE_SELECT"
TYPE_CLOZE_TEXT = "CLOZE_TEXT"
TYPE_HEADING_MATCHING = "HEADING_MATCHING"
TYPE_ADVERTISEMENT_MATCHING = "ADVERTISEMENT_MATCHING"
TYPE_TEXT_MATCHING = "TEXT_MATCHING"
TYPE_SENTENCE_ORDERING = "SENTENCE_ORDERING"
TYPE_SHORT_ANSWER = "SHORT_ANSWER"
TYPE_GAP_MATCHING = "GAP_MATCHING"
TYPE_DRAG_DROP = "DRAG_DROP"
TYPE_CATEGORY_SORTING = "CATEGORY_SORTING"
TYPE_IMAGE_SELECTION = "IMAGE_SELECTION"

ALL_TASK_TYPES = {
    TYPE_TRUE_FALSE,
    TYPE_MULTIPLE_CHOICE,
    TYPE_MULTIPLE_SELECT,
    TYPE_CLOZE_TEXT,
    TYPE_HEADING_MATCHING,
    TYPE_ADVERTISEMENT_MATCHING,
    TYPE_TEXT_MATCHING,
    TYPE_SENTENCE_ORDERING,
    TYPE_SHORT_ANSWER,
    TYPE_GAP_MATCHING,
    TYPE_DRAG_DROP,
    TYPE_CATEGORY_SORTING,
    TYPE_IMAGE_SELECTION,
}


class AssessmentTask(BaseModel):
    """One task ("Aufgabe") within a Section. `content` holds the rich-text
    passage/cloze-text/ad-texts body (task_type dependent); `config` holds
    any structured, task-type-specific data that doesn't fit the generic
    TaskQuestion/TaskOption shape, stored as JSON text (same
    JSON-as-text convention as MockQuestionAnswer.answer_data) rather than
    JSONB, matching this codebase's existing style."""

    __tablename__ = "assessment_tasks"

    section_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_sections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    section = relationship("AssessmentSection", back_populates="tasks")
    questions = relationship(
        "TaskQuestion",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskQuestion.sort_order",
    )
