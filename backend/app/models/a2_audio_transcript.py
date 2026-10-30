"""A2 audio processing: one row per audio CONTENT (SHA-256) — the machine
transcript of that file and what it was matched to (app/services/a2_audio/
processing.py, Admin -> Media Management -> A2 -> Audio-Verarbeitung).

The same content is transcribed once: a second upload of identical bytes (a
copy under another name, or another lesson's slot) finds the row by SHA-256.
`storage_paths` are the stored files known to have this content, so the
admin overview maps a task's audio to its transcript without hashing files on
every request; a new upload has a new storage path and shows as "Uploaded"
until it is processed. `matches` holds the per-task result of comparing the
transcript with the task ({listening_id: {status, note}}) — the same audio
can fit one task and be the wrong file for another (A2 13. Unterricht)."""

from sqlalchemy import CheckConstraint, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

STATUS_TRANSCRIBING = "TRANSCRIBING"
STATUS_TRANSCRIBED = "TRANSCRIBED"
STATUS_NEEDS_REVIEW = "NEEDS_REVIEW"
STATUS_FAILED = "FAILED"
TRANSCRIPT_STATES = (STATUS_TRANSCRIBING, STATUS_TRANSCRIBED, STATUS_NEEDS_REVIEW, STATUS_FAILED)

MATCH_MATCHED = "MATCHED"
MATCH_NEEDS_REVIEW = "NEEDS_REVIEW"
MATCH_MISMATCH = "MISMATCH"
MATCH_STATES = (MATCH_MATCHED, MATCH_NEEDS_REVIEW, MATCH_MISMATCH)


class A2AudioTranscript(BaseModel):
    __tablename__ = "a2_audio_transcripts"
    __table_args__ = (
        CheckConstraint("status IN ('TRANSCRIBING', 'TRANSCRIBED', 'NEEDS_REVIEW', 'FAILED')", name="ck_a2_audio_transcripts_status"),
        Index("uq_a2_audio_transcripts_sha256", "sha256", unique=True),
    )

    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=STATUS_TRANSCRIBING)
    # plain text (as heard, uncertain spots marked "[unverständlich]") and the timed segments
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    segments: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{start, end, text}]
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    quality: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # second model agreement, low-confidence words, uncertain spots
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_paths: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    matches: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
