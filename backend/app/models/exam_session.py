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


class ExamSession(BaseModel):

    __tablename__ = "exam_sessions"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    exam_id: Mapped[str] = mapped_column(
        ForeignKey("exams.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="started",
    )

    score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    user = relationship("User")

    exam = relationship("Exam")