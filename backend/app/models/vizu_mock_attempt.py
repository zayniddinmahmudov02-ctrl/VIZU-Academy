from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
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

    Lesen and Hören are real end to end and auto-graded (see
    vizu_mock_content.py's models, services/vizu_mock/lesen_service.py
    and .../hoeren_service.py): lesen_level/lesen_score and hoeren_level/
    hoeren_score are each written once, at submit time.

    Schreiben is real too but teacher-graded (see vizu_mock_writing.py's
    models and services/vizu_mock/schreiben_service.py):
    schreiben_submitted_at is set once, when the student clicks "Schreiben
    absenden" (content becomes read-only from that point on); schreiben_
    score/schreiben_level/schreiben_feedback are then filled in — and can
    keep changing — as a teacher grades each Aufgabe from the Teacher
    Panel, until all 5 are graded.

    Sprechen has no question bank or grading yet, so sprechen_level/
    overall_level stay NULL until a later phase fills them in place.
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

    # Raw Lesen/Hören points (0-20 each, auto-graded) and Schreiben points
    # (0-100, teacher-graded — see class docstring). Sprechen has no
    # equivalent yet — that module is still framework-only.
    lesen_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hoeren_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    schreiben_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # CEFR code (A1-C1) per skill, plus the overall result — sprechen/
    # overall stay nullable placeholders (see class docstring); lesen_
    # level/hoeren_level/schreiben_level are real.
    lesen_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    hoeren_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    schreiben_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sprechen_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    overall_level: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Set once, the instant "Schreiben absenden" is clicked — the single
    # source of truth for "can this attempt's Schreiben submissions still
    # be edited by the student" (enforced in schreiben_service, not just
    # the UI) and for the Teacher Panel's "Neue Einsendungen" bucket.
    schreiben_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # "Gesamtfeedback" — one overall comment across all 5 Aufgabe, set by
    # whichever teacher finishes grading (distinct from each submission's
    # own per-Aufgabe teacher_comment, see VizuMockWritingSubmission).
    schreiben_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User")
