from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# Assessment type — which surface owns this assessment. One universal
# engine (Assessment -> Section -> Task -> Question -> Option) serves all
# three; COURSE assessments hang off a Lesson, PREPARATION/MOCK_TEST ones
# stand alone (lesson_id is NULL).
TYPE_COURSE = "COURSE"
TYPE_PREPARATION = "PREPARATION"
TYPE_MOCK_TEST = "MOCK_TEST"
ALL_ASSESSMENT_TYPES = {TYPE_COURSE, TYPE_PREPARATION, TYPE_MOCK_TEST}

STATUS_DRAFT = "DRAFT"
STATUS_PUBLISHED = "PUBLISHED"
STATUS_ARCHIVED = "ARCHIVED"
ALL_STATUSES = {STATUS_DRAFT, STATUS_PUBLISHED, STATUS_ARCHIVED}


class Assessment(BaseModel):
    """Root of the universal assessment engine. A COURSE assessment
    belongs to exactly one Lesson (its Lesen/Hören/... panel); a MOCK_TEST
    assessment belongs to exactly one Vorbereitung ModelTest (its
    Lesen/Hören/... panel) via model_test_id; a standalone PREPARATION
    assessment sets neither, optionally scoped to a language/level. The
    existing Mock Exam System (CertificationProvider/MockExamLevel/
    ModelTest) is untouched — ModelTest itself, its own admin CRUD, and its
    legacy Kompetenz/Teil/*Content tables all keep working exactly as
    before; this FK is the opt-in bridge new work can use to attach a
    ModelTest's competency content to this shared engine instead of the
    legacy one."""

    __tablename__ = "assessments"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessment_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), default=STATUS_DRAFT, server_default=STATUS_DRAFT, nullable=False, index=True
    )

    lesson_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # The connection this module's own docstring anticipated: a MOCK_TEST
    # assessment anchors to a Vorbereitung ModelTest instead of a Lesson.
    # Exactly one of lesson_id/model_test_id is set — enforced in
    # crud_service, same pattern as Teil's one-of-four content relationships.
    model_test_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("model_tests.id", ondelete="CASCADE"), nullable=True, index=True
    )
    language_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("languages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    level: Mapped[str | None] = mapped_column(String(20), nullable=True)

    created_by_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Attempt policy — enforced by the attempt service, not the DB.
    attempt_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    allow_retry: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    allow_edit: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    allow_resubmit: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    show_correct_answers: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    show_score: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    show_feedback: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    lesson = relationship("Lesson")
    model_test = relationship("ModelTest")
    language = relationship("Language")
    created_by = relationship("User")

    sections = relationship(
        "AssessmentSection",
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="AssessmentSection.sort_order",
    )
