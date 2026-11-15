"""Medienwelt film player: subtitle analysis, extra video qualities, per-film player state, player preferences.

Additive only (nothing is rewritten or deleted):
  * films.video_duration_ms                      (nullable; exact length from ffprobe, used to check subtitles against the video)
  * film_subtitles.cue_count / last_ms / source_format / original_name / file_size / warnings
                                                 (result of the last subtitle check; existing rows get 0 / NULL / [] = "not checked")
  * media_progress.player_state                  (nullable JSONB: subtitle language, dual subtitles, speed, quality of a film)
  * film_renditions                              (new: additional video qualities of a film)
  * media_player_prefs                           (new: one row per student with the subtitle appearance settings)
Downgrade drops exactly these columns / tables (files on disk stay).

Revision ID: b6e2d9f4a1c8
Revises: f4c8a1e6b9d2
Create Date: 2026-11-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b6e2d9f4a1c8"
down_revision: Union[str, Sequence[str], None] = "f4c8a1e6b9d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def _base() -> list:
    return [sa.Column("id", UUID, primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)]


def upgrade() -> None:
    op.add_column("films", sa.Column("video_duration_ms", sa.Integer(), nullable=True))

    op.add_column("film_subtitles", sa.Column("cue_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("film_subtitles", sa.Column("last_ms", sa.Integer(), nullable=True))
    op.add_column("film_subtitles", sa.Column("source_format", sa.String(5), nullable=True))
    op.add_column("film_subtitles", sa.Column("original_name", sa.String(255), nullable=True))
    op.add_column("film_subtitles", sa.Column("file_size", sa.Integer(), nullable=True))
    op.add_column("film_subtitles", sa.Column("warnings", postgresql.JSONB(), nullable=False, server_default="[]"))

    op.add_column("media_progress", sa.Column("player_state", postgresql.JSONB(), nullable=True))

    op.create_table("film_renditions", *_base(),
                    sa.Column("film_id", UUID, sa.ForeignKey("films.id", ondelete="CASCADE", name="fk_film_renditions_film_id"), nullable=False),
                    sa.Column("label", sa.String(20), nullable=False), sa.Column("height", sa.Integer(), nullable=True),
                    sa.Column("file_key", sa.String(300), nullable=False), sa.Column("content_type", sa.String(100), nullable=False),
                    sa.Column("size", sa.BigInteger(), nullable=False), sa.Column("original_name", sa.String(255), nullable=True),
                    sa.UniqueConstraint("film_id", "label", name="uq_film_renditions_film_label"))
    op.create_index("ix_film_renditions_film_id", "film_renditions", ["film_id"])

    op.create_table("media_player_prefs", *_base(),
                    sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE", name="fk_media_player_prefs_user_id"), nullable=False),
                    sa.Column("prefs", postgresql.JSONB(), nullable=False, server_default="{}"),
                    sa.UniqueConstraint("user_id", name="uq_media_player_prefs_user"))
    op.create_index("ix_media_player_prefs_user_id", "media_player_prefs", ["user_id"])


def downgrade() -> None:
    op.drop_table("media_player_prefs")
    op.drop_table("film_renditions")
    op.drop_column("media_progress", "player_state")
    for column in ("warnings", "file_size", "original_name", "source_format", "last_ms", "cue_count"):
        op.drop_column("film_subtitles", column)
    op.drop_column("films", "video_duration_ms")
