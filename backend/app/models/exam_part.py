from sqlalchemy import (
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


class ExamPart(BaseModel):

    __tablename__ = "exam_parts"

    exam_id: Mapped[str] = mapped_column(
        ForeignKey("exams.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
    )

    duration: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    max_score: Mapped[int] = mapped_column(
        Integer,
        default=100,
    )

    exam = relationship(
        "Exam",
        back_populates="parts",
    )