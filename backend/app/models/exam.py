from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import BaseModel


class Exam(BaseModel):

    __tablename__ = "exams"

    provider_id: Mapped[str] = mapped_column(
        ForeignKey("exam_providers.id"),
        nullable=False,
    )

    level: Mapped[str] = mapped_column(
        String(20),
    )

    title: Mapped[str] = mapped_column(
        String(255),
    )

    duration: Mapped[int] = mapped_column(
        Integer,
        default=180,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    provider = relationship("ExamProvider")

    parts = relationship(
        "ExamPart",
        back_populates="exam",
        cascade="all, delete-orphan",
    )