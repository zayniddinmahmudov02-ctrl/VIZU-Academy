"""Student activity tracking (Medien statistics, Kontroll): server-credited active time.

* StudentSession — one stretch of real use built from heartbeats (app.services.activity.tracker). At most one open session
  per user (partial unique index), a session never crosses a Tashkent day (`day`), `active_seconds` is only ever credited by
  the server from its own clock (never a duration the browser reports).
* StudentActivityEvent — what that time was spent on: one row per continuous stretch of one area + item (a lesson, a song, a
  film, a book …). `position` = the last media position the server saw (seconds), used to tell playing from paused.

Learning streak ("Lernserie", table learning_activity) and lesson progress (student_progress / student_competency_progress)
are separate and unchanged; these tables never feed them."""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

AREA_COURSE = "COURSE"
AREA_WORTSCHATZ = "WORTSCHATZ"
AREA_MUSIC = "MUSIC"
AREA_FILM = "FILM"
AREA_BOOK = "BOOK"
AREA_EXAM = "EXAM"
AREAS = (AREA_COURSE, AREA_WORTSCHATZ, AREA_MUSIC, AREA_FILM, AREA_BOOK, AREA_EXAM)
MEDIA_AREAS = (AREA_MUSIC, AREA_FILM, AREA_BOOK)


class StudentSession(BaseModel):
    __tablename__ = "student_sessions"
    __table_args__ = (
        CheckConstraint("active_seconds >= 0", name="ck_student_sessions_seconds"),
        Index("ix_student_sessions_user_day", "user_id", "day"),
        Index("ix_student_sessions_day", "day"),
        Index("uq_student_sessions_open", "user_id", unique=True, postgresql_where=text("ended_at IS NULL")),
    )

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    day: Mapped[date] = mapped_column(Date, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    active_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    heartbeats: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # tab id -> ISO time of its last heartbeat (a closing tab ends the session only when no other tab is alive)
    tabs: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))


class StudentActivityEvent(BaseModel):
    __tablename__ = "student_activity_events"
    __table_args__ = (
        CheckConstraint(f"area IN ({', '.join(repr(a) for a in AREAS)})", name="ck_student_activity_events_area"),
        CheckConstraint("seconds >= 0", name="ck_student_activity_events_seconds"),
        Index("ix_student_activity_events_user_day", "user_id", "day"),
        Index("ix_student_activity_events_user_area_ref", "user_id", "area", "ref_id"),
        Index("ix_student_activity_events_user_last_seen", "user_id", "last_seen_at"),
    )

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("student_sessions.id", ondelete="SET NULL"), nullable=True)
    day: Mapped[date] = mapped_column(Date, nullable=False)
    area: Mapped[str] = mapped_column(String(12), nullable=False)
    ref_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
