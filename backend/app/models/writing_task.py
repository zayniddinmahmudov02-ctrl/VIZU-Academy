from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class WritingTask(BaseModel):
    """The writing prompt for a Schreiben Teil. 1:1 with Teil."""

    __tablename__ = "writing_tasks"

    teil_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teile.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    task_text: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_document_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    word_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    difficulty: Mapped[str | None] = mapped_column(String(20), nullable=True)
    max_points: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    evaluation_rubric: Mapped[str | None] = mapped_column(Text, nullable=True)
    passing_score: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    teil = relationship("Teil", back_populates="writing_task")
    submissions = relationship(
        "MockWritingSubmission",
        back_populates="writing_task",
        cascade="all, delete-orphan",
    )
