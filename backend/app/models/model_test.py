from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

STATUS_DRAFT = "DRAFT"
STATUS_PUBLISHED = "PUBLISHED"
STATUS_ARCHIVED = "ARCHIVED"


class ModelTest(BaseModel):
    """A single mock exam ("Modelltest 1") within a MockExamLevel."""

    __tablename__ = "model_tests"

    level_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mock_exam_levels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=STATUS_DRAFT,
        server_default=STATUS_DRAFT,
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    level = relationship("MockExamLevel", back_populates="model_tests")
    kompetenzen = relationship(
        "Kompetenz",
        back_populates="model_test",
        cascade="all, delete-orphan",
        order_by="Kompetenz.sort_order",
    )
