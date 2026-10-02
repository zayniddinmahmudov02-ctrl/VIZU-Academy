from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

REASON_BELOW_A1 = "BELOW_A1"
REASON_ABANDONED = "ABANDONED"


class VizuMultilevelDiscardedAttempt(BaseModel):
    """Anonymous tally row for an attempt that is NOT kept in a student's
    permanent history: a finished attempt whose overall result is below A1,
    or an abandoned (never finished) one. Deliberately carries NO user_id
    or any personal data — it exists only so the admin Statistics page can
    report "Below A1 results", "abandoned attempts" and completion rate
    truthfully without retaining the student's history."""

    __tablename__ = "vizu_multilevel_discarded_attempts"

    reason: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lesen_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hoeren_score: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False), nullable=True)
    schreiben_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sprechen_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
