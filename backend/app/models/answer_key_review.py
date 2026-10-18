from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

REVIEW_VERIFIED = "verified"
REVIEW_NEEDS_REVIEW = "needs_review"
REVIEW_UNVERIFIED = "unverified"
REVIEW_STATUSES = (REVIEW_VERIFIED, REVIEW_NEEDS_REVIEW, REVIEW_UNVERIFIED)


class AnswerKeyReview(BaseModel):
    """Manual review of ONE Lesen or Hören question's answer key (Admin ->
    LMS A1–C1 -> Lösung). The key itself stays where the scoring engine reads
    it (options.is_correct / question.config); this row only records who
    checked which key. `key_fingerprint` is the hash of the question + key at
    verification time: when the key changes afterwards, the verification no
    longer counts (see app/services/lesson_skills/loesung.py)."""

    __tablename__ = "answer_key_reviews"
    __table_args__ = (
        CheckConstraint("(reading_question_id IS NULL) <> (listening_question_id IS NULL)", name="ck_answer_key_reviews_one_question"),
        CheckConstraint("status IN ('verified', 'needs_review', 'unverified')", name="ck_answer_key_reviews_status"),
        Index("uq_answer_key_reviews_reading", "reading_question_id", unique=True, postgresql_where="reading_question_id IS NOT NULL"),
        Index("uq_answer_key_reviews_listening", "listening_question_id", unique=True, postgresql_where="listening_question_id IS NOT NULL"),
    )

    reading_question_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("reading_questions.id", ondelete="CASCADE"), nullable=True)
    listening_question_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("listening_questions.id", ondelete="CASCADE"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    key_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
