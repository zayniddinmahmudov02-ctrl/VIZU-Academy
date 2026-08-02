from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class MockExamLevel(BaseModel):
    """A1-C2 within a CertificationProvider. Named `MockExamLevel` (not
    `Level`) to avoid colliding with the existing student-course `Course`
    model, which the admin CMS already labels "Levels" for an unrelated
    hierarchy (Language -> Course -> Module -> Lesson)."""

    __tablename__ = "mock_exam_levels"

    provider_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("certification_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    provider = relationship("CertificationProvider", back_populates="levels")
    model_tests = relationship(
        "ModelTest",
        back_populates="level",
        cascade="all, delete-orphan",
        order_by="ModelTest.sort_order",
    )
