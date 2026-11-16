"""Multilevel Modelltest 1: one shared Hören audio for all Teile (kompetenzen.audio_file_id).

Additive only — nothing is rewritten or deleted; every Hören Teil keeps its own listening_contents row, questions, answers and (for the other
Modelltests) its own audio file link:
  * kompetenzen.audio_file_id (nullable FK to audio_files, ON DELETE SET NULL, indexed): the single audio the Hören section of a Modelltest in "shared
    audio" mode plays for all its Teile (only Modelltest 1 uses it; see multilevel_service.SHARED_AUDIO_NUMBERS)
Downgrade drops exactly this column (the audio files themselves stay).

Revision ID: e6d2b9a4c8f3
Revises: d4b9e2a7c3f1
Create Date: 2026-11-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e6d2b9a4c8f3"
down_revision: Union[str, Sequence[str], None] = "d4b9e2a7c3f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("kompetenzen", sa.Column("audio_file_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_kompetenzen_audio_file_id", "kompetenzen", "audio_files", ["audio_file_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_kompetenzen_audio_file_id", "kompetenzen", ["audio_file_id"])


def downgrade() -> None:
    op.drop_index("ix_kompetenzen_audio_file_id", table_name="kompetenzen")
    op.drop_constraint("fk_kompetenzen_audio_file_id", "kompetenzen", type_="foreignkey")
    op.drop_column("kompetenzen", "audio_file_id")
