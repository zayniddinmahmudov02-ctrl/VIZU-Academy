from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_COMPLETED = "COMPLETED"
ALL_STATUSES = {STATUS_IN_PROGRESS, STATUS_COMPLETED}

# Each student may take the VIZU-Multilevel exam at most this many times.
MAX_ATTEMPTS = 3


class VizuMultilevelAttempt(BaseModel):
    """One student's attempt at the VIZU-Multilevel free level check — a
    standalone product, independent of both the lesson-based courses and
    the Vorbereitung/Zertifikat exam system (see the "VIZU-Multilevel" admin
    nav entry, reserved for this since an earlier phase).

    Lesen and Hören are real end to end and auto-graded (see
    vizu_multilevel_content.py's models, services/vizu_multilevel/lesen_service.py
    and .../hoeren_service.py): lesen_level/lesen_score and hoeren_level/
    hoeren_score are each written once, at submit time.

    Schreiben is real too but teacher-graded (see vizu_multilevel_writing.py's
    models and services/vizu_multilevel/schreiben_service.py):
    schreiben_submitted_at is set once, when the student clicks "Schreiben
    absenden" (content becomes read-only from that point on); schreiben_
    score/schreiben_level/schreiben_feedback are then filled in — and can
    keep changing — as a teacher grades each Aufgabe from the Teacher
    Panel, until all 5 are graded.

    Sprechen has no question bank or grading yet, so sprechen_level/
    overall_level stay NULL until a later phase fills them in place.
    """

    __tablename__ = "vizu_mock_attempts"
    __table_args__ = (UniqueConstraint("user_id", "attempt_number", name="uq_vizu_mock_attempts_user_attempt_number"),)

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # 1, 2, 3 per student (see MAX_ATTEMPTS) — assigned once at creation.
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=STATUS_IN_PROGRESS, server_default=STATUS_IN_PROGRESS, nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Raw Lesen points (0-100, auto-graded, flat per-question weighting)
    # and Schreiben points (0-100, teacher-graded — see class docstring).
    # Sprechen has no equivalent yet — that module is still framework-only.
    lesen_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Numeric, not Integer: Hören weights each question's points by its
    # CEFR level (A1=0.5 ... C1=2.5, see services/vizu_multilevel/
    # hoeren_csv_import_service.py), so a partial attempt's total can be
    # fractional (e.g. one A1 question correct = 0.5) even though a
    # fully-answered attempt's total always lands on a whole number.
    hoeren_score: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False), nullable=True)
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
    # own per-Aufgabe teacher_comment, see VizuMultilevelWritingSubmission).
    schreiben_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Sprechen — teacher-graded like Schreiben (score is the sum of the
    # graded Aufgaben's points; level is the highest unbroken pass chain).
    # Lesen breakdown (kept separately so the competencies can later be
    # merged into one certificate): correct / wrong / unanswered questions.
    lesen_correct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lesen_wrong: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lesen_unanswered: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Set when a finished attempt has no CEFR level: BELOW_A1 (a real result —
    # "Niveau unter A1", certificate included) or NO_CONTENT (no result at
    # all). The name is historical; the row is never deleted.
    discarded_reason: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Hören autosave: {question_id: option_id}. Written while the section is
    # open, restored after a refresh, and the fallback when the time runs out.
    hoeren_draft: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    hoeren_correct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hoeren_wrong: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hoeren_unanswered: Mapped[int | None] = mapped_column(Integer, nullable=True)

    sprechen_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sprechen_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Server-authoritative per-competency timing. `<skill>_started_at` is
    # stamped by the backend the first time the student opens that
    # competency (never by the client); the 20-minute deadline is derived
    # from it, so a reload / manipulated client clock cannot restart or
    # extend the timer. `<skill>_submitted_at` marks the competency as
    # finished (answered or not) and unlocks the next one.
    lesen_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lesen_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hoeren_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hoeren_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    schreiben_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sprechen_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sprechen_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Issued once (first certificate request for an eligible attempt), e.g.
    # "VIZU-ML-2026-000123" — a running number, never an internal id.
    certificate_number: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)

    # Gesamtergebnis 0-100 once the result is final (every competency graded):
    # the same number as the result page and the certificate. Kept in sync by
    # service.sync_result_score whenever a grade changes; NULL while pending.
    result_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user = relationship("User")
