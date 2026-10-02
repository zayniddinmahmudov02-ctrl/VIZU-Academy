"""vizu multilevel hoeren: protected audio per Aufgabe, autosave draft, result counts

Revision ID: c8f1d3a65b20
Revises: b6e2a41c7d95
Create Date: 2026-10-04 00:00:00.000000

Additive: audio rows get aufgabe_number (unique) / file_name / storage_path /
content_type (audio_url becomes nullable — protected audio has no public
URL); attempts get the Hören autosave draft and correct/wrong/unanswered.
No data is deleted or rewritten.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c8f1d3a65b20"
down_revision: Union[str, None] = "b6e2a41c7d95"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("vizu_mock_audios", sa.Column("aufgabe_number", sa.Integer(), nullable=True))
    op.add_column("vizu_mock_audios", sa.Column("file_name", sa.String(255), nullable=True))
    op.add_column("vizu_mock_audios", sa.Column("storage_path", sa.String(255), nullable=True))
    op.add_column("vizu_mock_audios", sa.Column("content_type", sa.String(100), nullable=True))
    op.alter_column("vizu_mock_audios", "audio_url", existing_type=sa.Text(), nullable=True)
    op.create_unique_constraint("uq_vizu_mock_audios_aufgabe_number", "vizu_mock_audios", ["aufgabe_number"])

    op.add_column("vizu_mock_attempts", sa.Column("hoeren_draft", postgresql.JSONB(), nullable=True))
    for col in ("hoeren_correct", "hoeren_wrong", "hoeren_unanswered"):
        op.add_column("vizu_mock_attempts", sa.Column(col, sa.Integer(), nullable=True))


def downgrade() -> None:
    for col in ("hoeren_unanswered", "hoeren_wrong", "hoeren_correct", "hoeren_draft"):
        op.drop_column("vizu_mock_attempts", col)
    op.drop_constraint("uq_vizu_mock_audios_aufgabe_number", "vizu_mock_audios", type_="unique")
    # audio_url stays nullable: rows without a public URL may exist now.
    for col in ("content_type", "storage_path", "file_name", "aufgabe_number"):
        op.drop_column("vizu_mock_audios", col)
