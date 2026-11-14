from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ListeningContent(BaseModel):
    """The audio passage for a Hören Teil. 1:1 with Teil."""

    __tablename__ = "listening_contents"

    teil_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teile.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    audio_url: Mapped[str] = mapped_column(Text, nullable=False)
    # Multilevel Audio (admin page): the private file the exam plays; wins over a legacy `audio_url`
    audio_file_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audio_files.id", ondelete="SET NULL", name="fk_listening_contents_audio_file_id"), nullable=True, index=True,
    )
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)

    teil = relationship("Teil", back_populates="listening_content")
    audio_file = relationship("AudioFile")
    questions = relationship(
        "MockQuestion",
        primaryjoin="ListeningContent.id == foreign(MockQuestion.listening_content_id)",
        cascade="all, delete-orphan",
        order_by="MockQuestion.sort_order",
    )
