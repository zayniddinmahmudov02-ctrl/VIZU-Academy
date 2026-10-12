"""VIZU LMS (A1–C1): the per-lesson competency configuration, learning
resources (audio / PDF / image / document / link) and the per-student
competency progress snapshot.

Everything else the LMS needs already exists and is reused: courses (one per
CEFR level), modules, lessons, videos + video_progress, the exercise sets /
skill tasks and their attempts, student_progress (lesson level). See
docs/lms-architecture.md."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

# The ten competencies of every lesson, in their fixed order (position 1..10).
COMPETENCY_ORDER: tuple[str, ...] = (
    "EINFUEHRUNG",
    "WORTSCHATZ",
    "GRAMMATIK",
    "LESEN",
    "HOEREN",
    "SPRECHEN",
    "SCHREIBEN",
    "UEBUNGEN",
    "ABSCHLUSSTEST",
    "ZUSAMMENFASSUNG",
)
COMPETENCY_POSITION: dict[str, int] = {kind: i for i, kind in enumerate(COMPETENCY_ORDER, start=1)}

# DB-level guard: position must be the canonical slot of the kind.
_POSITION_SQL = "position = CASE kind " + " ".join(f"WHEN '{k}' THEN {p}" for k, p in COMPETENCY_POSITION.items()) + " END"
_KINDS_SQL = ", ".join(f"'{k}'" for k in COMPETENCY_ORDER)

RESOURCE_TYPES: tuple[str, ...] = ("AUDIO", "PDF", "IMAGE", "DOCUMENT", "LINK")

PROGRESS_NOT_STARTED = "not_started"
PROGRESS_IN_PROGRESS = "in_progress"
PROGRESS_COMPLETED = "completed"
PROGRESS_STATUSES = (PROGRESS_NOT_STARTED, PROGRESS_IN_PROGRESS, PROGRESS_COMPLETED)

ACCESS_OPEN = "OPEN"
ACCESS_LOCKED = "LOCKED"


class LessonCompetency(BaseModel):
    """One of the ten competencies of a lesson: admin text (introduction,
    explanations, summary) and its publish state. The content itself lives
    in the existing tables (vocabularies, grammars, readings, listenings,
    speakings, writings, skill_exercises, videos) and learning_resources."""

    __tablename__ = "lesson_competencies"
    __table_args__ = (
        UniqueConstraint("lesson_id", "kind", name="uq_lesson_competencies_lesson_kind"),
        UniqueConstraint("lesson_id", "position", name="uq_lesson_competencies_lesson_position"),
        CheckConstraint(f"kind IN ({_KINDS_SQL})", name="ck_lesson_competencies_kind"),
        CheckConstraint(_POSITION_SQL, name="ck_lesson_competencies_position"),
    )

    lesson_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")


class LearningResource(BaseModel):
    """A file or link of a lesson, optionally tied to one competency. Files
    live in protected storage (never /uploads) and are only served through
    GET /lms/resources/{id}/file after the lesson access check."""

    __tablename__ = "learning_resources"
    __table_args__ = (
        CheckConstraint(f"resource_type IN ({', '.join(repr(t) for t in RESOURCE_TYPES)})", name="ck_learning_resources_type"),
        CheckConstraint(f"competency IS NULL OR competency IN ({_KINDS_SQL})", name="ck_learning_resources_competency"),
        CheckConstraint(
            "(resource_type = 'LINK' AND external_url IS NOT NULL AND storage_key IS NULL)"
            " OR (resource_type <> 'LINK' AND storage_key IS NOT NULL AND external_url IS NULL)",
            name="ck_learning_resources_source",
        ),
        Index("ix_learning_resources_lesson_competency", "lesson_id", "competency", "order_index"),
    )

    lesson_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    competency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    resource_type: Mapped[str] = mapped_column(String(12), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True, unique=True)
    external_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class StudentCompetencyProgress(BaseModel):
    """Snapshot of one student's state in one competency of one lesson —
    written only by app.services.lms.progress (derived from the real
    signals: video progress, exercise attempts, graded submissions)."""

    __tablename__ = "student_competency_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", "competency", name="uq_student_competency_progress"),
        CheckConstraint(f"competency IN ({_KINDS_SQL})", name="ck_student_competency_progress_competency"),
        CheckConstraint(f"status IN ({', '.join(repr(s) for s in PROGRESS_STATUSES)})", name="ck_student_competency_progress_status"),
        Index("ix_student_competency_progress_user_lesson", "user_id", "lesson_id"),
    )

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    competency: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default=PROGRESS_NOT_STARTED, server_default=PROGRESS_NOT_STARTED)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    visited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
