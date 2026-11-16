from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

TYPE_LESEN = "LESEN"
TYPE_HOEREN = "HOEREN"
TYPE_SCHREIBEN = "SCHREIBEN"
TYPE_SPRECHEN = "SPRECHEN"
ALL_TYPES = {TYPE_LESEN, TYPE_HOEREN, TYPE_SCHREIBEN, TYPE_SPRECHEN}


class Kompetenz(BaseModel):
    """One of the four skills (Lesen/Hören/Schreiben/Sprechen) within a
    ModelTest."""

    __tablename__ = "kompetenzen"

    model_test_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("model_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # Hören of a Modelltest in "shared audio" mode (Modelltest 1): the ONE audio all its Teile play; independent of duration_minutes (the exam time)
    audio_file_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audio_files.id", ondelete="SET NULL", name="fk_kompetenzen_audio_file_id"), nullable=True, index=True,
    )

    model_test = relationship("ModelTest", back_populates="kompetenzen")
    audio_file = relationship("AudioFile")
    teile = relationship(
        "Teil",
        back_populates="kompetenz",
        cascade="all, delete-orphan",
        order_by="Teil.sort_order",
    )
