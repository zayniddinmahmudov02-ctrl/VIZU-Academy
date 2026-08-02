from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

CONTENT_TEXT = "TEXT"
CONTENT_IMAGE = "IMAGE"
CONTENT_TEXT_IMAGE = "TEXT_IMAGE"


class ReadingContent(BaseModel):
    """The reading passage for a Lesen Teil. 1:1 with Teil."""

    __tablename__ = "reading_contents"

    teil_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teile.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    content_type: Mapped[str] = mapped_column(
        String(20), default=CONTENT_TEXT, server_default=CONTENT_TEXT, nullable=False
    )
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    teil = relationship("Teil", back_populates="reading_content")
    questions = relationship(
        "MockQuestion",
        primaryjoin="ReadingContent.id == foreign(MockQuestion.reading_content_id)",
        cascade="all, delete-orphan",
        order_by="MockQuestion.sort_order",
    )
