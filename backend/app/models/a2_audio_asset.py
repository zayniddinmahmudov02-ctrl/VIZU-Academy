"""A2 Audio Manager: one row per uploaded A2 audio file (Admin -> Media
Management -> A2 Audio Manager, app/services/a2_audio).

The file itself lives in the private Hören storage (lesson-listening, prefix
"a2-audio/"), so the existing streaming and access rules stay the only way
students reach it. A row is the library entry: what the admin (or the file
name) says it is, the original file name, size, format, SHA-256 (one row per
file content: duplicates are refused), whether an admin listened to it, and
which Hören task (listening) it is linked to. Linking is always an explicit
admin action — a parsed file name only produces a suggestion."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

KIND_HOEREN = "HOEREN"
KIND_TEXT = "TEXT"
KIND_UNTERRICHT = "UNTERRICHT"
KIND_OTHER = "OTHER"
AUDIO_KINDS = (KIND_HOEREN, KIND_TEXT, KIND_UNTERRICHT, KIND_OTHER)

VERIFY_PENDING = "pending"  # nobody listened yet
VERIFY_OK = "verified"  # an admin listened: right file, plays to the end
VERIFY_PROBLEM = "problem"  # an admin listened: wrong / broken (note says why)
VERIFY_STATES = (VERIFY_PENDING, VERIFY_OK, VERIFY_PROBLEM)


def _ids(*values: str) -> str:
    return ", ".join(f"'{v}'" for v in values)


class A2AudioAsset(BaseModel):
    __tablename__ = "a2_audio_assets"
    __table_args__ = (
        CheckConstraint("level = 'A2'", name="ck_a2_audio_assets_level"),
        CheckConstraint(f"audio_kind IS NULL OR audio_kind IN ({_ids(*AUDIO_KINDS)})", name="ck_a2_audio_assets_kind"),
        CheckConstraint(f"verification IN ({_ids(*VERIFY_STATES)})", name="ck_a2_audio_assets_verification"),
        CheckConstraint("unterricht IS NULL OR unterricht BETWEEN 1 AND 99", name="ck_a2_audio_assets_unterricht"),
        CheckConstraint("part IS NULL OR part BETWEEN 1 AND 99", name="ck_a2_audio_assets_part"),
        # one row per file content: the same audio cannot be uploaded twice
        Index("uq_a2_audio_assets_sha256", "sha256", unique=True),
        # a Hören task has one main audio, so at most one asset is linked to it
        Index("uq_a2_audio_assets_listening", "listening_id", unique=True, postgresql_where=text("listening_id IS NOT NULL")),
        Index("ix_a2_audio_assets_unterricht_order", "unterricht", "sort_order"),
    )

    level: Mapped[str] = mapped_column(String(5), nullable=False, default="A2", server_default="A2")
    unterricht: Mapped[int | None] = mapped_column(Integer, nullable=True)
    audio_kind: Mapped[str | None] = mapped_column(String(20), nullable=True)
    part: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Teil / Text number; NULL if none
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # what the file name parser read, kept so the admin sees where a value came from
    parsed: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)  # relative to the lesson-listening storage
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    audio_format: Mapped[str] = mapped_column(String(10), nullable=False)  # detected from the content
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    verification: Mapped[str] = mapped_column(String(10), nullable=False, default=VERIFY_PENDING, server_default=VERIFY_PENDING)
    verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    listening_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("listenings.id", ondelete="SET NULL"), nullable=True)
    linked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    linked_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    uploaded_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    listening = relationship("Listening", foreign_keys=[listening_id], lazy="joined")
