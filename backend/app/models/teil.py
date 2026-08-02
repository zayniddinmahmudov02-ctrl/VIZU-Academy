from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Teil(BaseModel):
    """One section ("Teil 1", "Teil 2", ...) within a Kompetenz. Exactly
    one of `reading_content` / `listening_content` / `writing_task` /
    `speaking_task` is populated, matching the parent Kompetenz.type —
    enforced in the service layer, not the DB, since a CHECK constraint
    spanning a nullable 1:1 relationship adds real complexity for a rule
    the admin UI already enforces structurally (each Teil is only ever
    created from within a specific Kompetenz-type's editor)."""

    __tablename__ = "teile"

    kompetenz_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kompetenzen.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    kompetenz = relationship("Kompetenz", back_populates="teile")

    reading_content = relationship(
        "ReadingContent",
        back_populates="teil",
        uselist=False,
        cascade="all, delete-orphan",
    )
    listening_content = relationship(
        "ListeningContent",
        back_populates="teil",
        uselist=False,
        cascade="all, delete-orphan",
    )
    writing_task = relationship(
        "WritingTask",
        back_populates="teil",
        uselist=False,
        cascade="all, delete-orphan",
    )
    speaking_task = relationship(
        "SpeakingTask",
        back_populates="teil",
        uselist=False,
        cascade="all, delete-orphan",
    )
