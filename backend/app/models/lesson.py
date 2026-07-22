from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Lesson(BaseModel):
    __tablename__ = "lessons"

    module_id: Mapped[str] = mapped_column(
        ForeignKey("modules.id"),
        nullable=False,
        index=True,
    )

    number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    video_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    duration: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    is_free: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    module = relationship(
        "Module",
        back_populates="lessons",
    )

    videos = relationship(
        "Video",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )

    vocabularies = relationship(
        "Vocabulary",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )

    grammars = relationship(
        "Grammar",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )

    readings = relationship(
        "Reading",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )

    listenings = relationship(
        "Listening",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )

    writings = relationship(
        "Writing",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )

    speakings = relationship(
        "Speaking",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )