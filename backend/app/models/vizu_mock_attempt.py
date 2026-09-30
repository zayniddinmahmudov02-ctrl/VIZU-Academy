from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_COMPLETED = "COMPLETED"
ALL_STATUSES = {STATUS_IN_PROGRESS, STATUS_COMPLETED}


class VizuMockAttempt(BaseModel):
    """One student's attempt at the VIZU-Mock free level check — a
    standalone product, independent of both the lesson-based courses and
    the Vorbereitung/Zertifikat exam system (see the "VIZU-MOCK" admin
    nav entry, reserved for this since an earlier phase).

    Lesen and Hören are now real end to end (see vizu_mock_content.py's
    models, services/vizu_mock/lesen_service.py and .../hoeren_service.py):
    lesen_level/lesen_score and hoeren_level/hoeren_score are each written
    once, at submit time. Schreiben/Sprechen have no question bank or
    grading yet, so schreiben_level/sprechen_level/overall_level stay
    NULL until a later phase fills them in place.
    """

    __tablename__ = "vizu_mock_attempts"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=STATUS_IN_PROGRESS, server_default=STATUS_IN_PROGRESS, nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Raw Lesen/Hören points (0-20 each), set once by
    # services/vizu_mock/lesen_service.submit_lesen and
    # services/vizu_mock/hoeren_service.submit_hoeren respectively,
    # alongside their matching *_level column below. Schreiben/Sprechen
    # have no equivalent yet — those modules are still framework-only.
    lesen_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hoeren_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # CEFR code (A1-C1) per skill, plus the overall result — hoeren/
    # schreiben/sprechen/overall stay nullable placeholders (see class
    # docstring); lesen_level is now real, written by submit_lesen.
    lesen_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    hoeren_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    schreiben_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sprechen_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    overall_level: Mapped[str | None] = mapped_column(String(10), nullable=True)

    user = relationship("User")
