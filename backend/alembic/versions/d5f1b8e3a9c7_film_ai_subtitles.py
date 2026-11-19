"""Medienwelt films: AI subtitles (transcription of the film's audio + translation) with an admin approval step.

Additive only (nothing is rewritten or deleted):
  * film_subtitles.status          (DRAFT | APPROVED, default APPROVED: every existing / uploaded track stays visible as before)
  * film_subtitles.source          (UPLOAD | AI | TRANSLATION, default UPLOAD: every existing track was uploaded)
  * film_subtitles.source_language / ai_model / approved_at / approved_by_id / edited_at   (nullable)
  * film_subtitle_jobs             (new: background jobs with status PENDING / PROCESSING / COMPLETED / FAILED, progress, resume data)
Downgrade drops exactly these columns / the table (subtitle files on disk stay; AI tracks become ordinary visible tracks then).

Revision ID: d5f1b8e3a9c7
Revises: a7c4e2f9b1d8
Create Date: 2026-11-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d5f1b8e3a9c7"
down_revision: Union[str, Sequence[str], None] = "a7c4e2f9b1d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.add_column("film_subtitles", sa.Column("status", sa.String(10), nullable=False, server_default="APPROVED"))
    op.add_column("film_subtitles", sa.Column("source", sa.String(12), nullable=False, server_default="UPLOAD"))
    op.add_column("film_subtitles", sa.Column("source_language", sa.String(10), nullable=True))
    op.add_column("film_subtitles", sa.Column("ai_model", sa.String(80), nullable=True))
    op.add_column("film_subtitles", sa.Column("approved_at", TS, nullable=True))
    op.add_column("film_subtitles", sa.Column("approved_by_id", UUID, sa.ForeignKey("users.id", ondelete="SET NULL", name="fk_film_subtitles_approved_by_id"), nullable=True))
    op.add_column("film_subtitles", sa.Column("edited_at", TS, nullable=True))
    op.create_index("ix_film_subtitles_approved_by_id", "film_subtitles", ["approved_by_id"])
    op.create_check_constraint("ck_film_subtitles_status", "film_subtitles", "status IN ('DRAFT','APPROVED')")
    op.create_check_constraint("ck_film_subtitles_source", "film_subtitles", "source IN ('UPLOAD','AI','TRANSLATION')")

    op.create_table(
        "film_subtitle_jobs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TS, server_default=sa.func.now(), nullable=False),
        sa.Column("film_id", UUID, sa.ForeignKey("films.id", ondelete="CASCADE", name="fk_film_subtitle_jobs_film_id"), nullable=False),
        sa.Column("kind", sa.String(12), nullable=False),
        sa.Column("status", sa.String(12), nullable=False, server_default="PENDING"),
        sa.Column("language", sa.String(10), nullable=False),
        sa.Column("detected_language", sa.String(10), nullable=True),
        sa.Column("source_subtitle_id", UUID, sa.ForeignKey("film_subtitles.id", ondelete="SET NULL", name="fk_film_subtitle_jobs_source_subtitle_id"), nullable=True),
        sa.Column("result_subtitle_id", UUID, sa.ForeignKey("film_subtitles.id", ondelete="SET NULL", name="fk_film_subtitle_jobs_result_subtitle_id"), nullable=True),
        sa.Column("translate_to", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("replace_existing", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider", sa.String(40), nullable=True),
        sa.Column("model", sa.String(80), nullable=True),
        sa.Column("progress_done", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("progress_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(60), nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("partial", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("stats", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_by_id", UUID, sa.ForeignKey("users.id", ondelete="SET NULL", name="fk_film_subtitle_jobs_created_by_id"), nullable=True),
        sa.Column("started_at", TS, nullable=True),
        sa.Column("finished_at", TS, nullable=True),
        sa.Column("heartbeat_at", TS, nullable=True),
        sa.CheckConstraint("kind IN ('TRANSCRIBE','TRANSLATE')", name="ck_film_subtitle_jobs_kind"),
        sa.CheckConstraint("status IN ('PENDING','PROCESSING','COMPLETED','FAILED')", name="ck_film_subtitle_jobs_status"),
    )
    for column in ("film_id", "source_subtitle_id", "result_subtitle_id", "created_by_id"):
        op.create_index(f"ix_film_subtitle_jobs_{column}", "film_subtitle_jobs", [column])
    op.create_index("ix_film_subtitle_jobs_status_created", "film_subtitle_jobs", ["status", "created_at"])
    op.create_index("uq_film_subtitle_jobs_active", "film_subtitle_jobs", ["film_id", "kind", "language"], unique=True,
                    postgresql_where=sa.text("status IN ('PENDING','PROCESSING')"))


def downgrade() -> None:
    op.drop_table("film_subtitle_jobs")
    op.drop_constraint("ck_film_subtitles_source", "film_subtitles", type_="check")
    op.drop_constraint("ck_film_subtitles_status", "film_subtitles", type_="check")
    op.drop_index("ix_film_subtitles_approved_by_id", table_name="film_subtitles")
    for column in ("edited_at", "approved_by_id", "approved_at", "ai_model", "source_language", "source", "status"):
        op.drop_column("film_subtitles", column)
