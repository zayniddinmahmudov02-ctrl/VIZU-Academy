from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class SpeakingTask(BaseModel):
    """The speaking prompt for a Sprechen Teil. 1:1 with Teil."""

    __tablename__ = "speaking_tasks"

    teil_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teile.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    task_text: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    preparation_time_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    speaking_time_seconds: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    max_recording_duration_seconds: Mapped[int] = mapped_column(Integer, default=120, nullable=False)

    teil = relationship("Teil", back_populates="speaking_task")
    submissions = relationship(
        "MockSpeakingSubmission",
        back_populates="speaking_task",
        cascade="all, delete-orphan",
    )
