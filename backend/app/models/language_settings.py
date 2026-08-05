from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class LanguageSettings(BaseModel):
    """Per-language feature toggles — 1:1 with Language, lazily created on
    first access (see services/language/settings_service.py) so existing
    languages never need a backfill migration when a new toggle is added."""

    __tablename__ = "language_settings"

    language_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("languages.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    certificates_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    leaderboard_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    vocabulary_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    grammar_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reading_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    listening_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    writing_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    speaking_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    homework_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    quiz_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ai_writing_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ai_speaking_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mock_exams_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    video_lessons_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    media_library_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    language = relationship("Language", back_populates="settings")
