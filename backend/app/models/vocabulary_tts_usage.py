from datetime import date

from sqlalchemy import Date, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class VocabularyTtsUsage(BaseModel):
    """One row per calendar day, tracking how many Gemini TTS requests
    this app has made — a local, self-imposed budget so the "Fehlende
    Audios generieren" queue can refuse to even attempt a call once
    VOCAB_BULK_TTS_MAX_PER_DAY is reached, instead of discovering that
    the hard way via a 429 for every remaining word in a batch.

    This is a best-effort mirror of Google's own daily quota, not an
    authoritative source — if the real account usage differs (e.g. a
    call made outside this app, or Google's reset window not lining up
    with UTC midnight), a live 429 can still happen; when it carries
    Google's own "GenerateRequestsPerDayPerProjectPerModel" violation,
    the caller clamps request_count up to the configured max so this
    table self-corrects instead of drifting further from reality."""

    __tablename__ = "vocabulary_tts_usage"

    usage_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        unique=True,
        index=True,
    )

    request_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
