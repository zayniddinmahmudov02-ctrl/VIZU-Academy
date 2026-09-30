from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
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

    Framework only, per spec: there is no question bank, no AI grading and
    no level-determination algorithm yet, so the four *_level columns and
    overall_level stay NULL forever for now. What this table exists to
    support today is real: creating an attempt when a student starts,
    marking it completed when they finish the four skill steps, and
    listing a student's own past attempts (their results-history view).
    A later phase fills the level columns in place — no migration should
    be needed for that, only new write paths.
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

    # CEFR code (A1-C1) per skill, plus the overall result — all nullable
    # placeholders, never computed today (see class docstring).
    lesen_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    hoeren_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    schreiben_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sprechen_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    overall_level: Mapped[str | None] = mapped_column(String(10), nullable=True)

    user = relationship("User")
