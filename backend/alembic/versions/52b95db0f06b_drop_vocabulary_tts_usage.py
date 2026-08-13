"""drop vocabulary_tts_usage (TTS removed from vocabulary audio workflow)

Revision ID: 52b95db0f06b
Revises: 34da524e9c9d
Create Date: 2026-08-14 00:00:00.000000

Vocabulary audio is no longer AI-generated at all — it's always the
admin's own microphone recording (see
app/services/vocabulary/audio_processing.py). The Gemini-TTS daily/
per-minute budget this table tracked has no caller left once that code
path is removed, so it's dropped rather than left as dead
infrastructure. Contains only a same-day usage counter, no
student-facing or otherwise valuable data.

`vocabularies.audio_status`/`audio_error` are untouched — still
meaningful for the recording flow (PENDING until recorded, GENERATED
once saved, FAILED if saving didn't work out).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '52b95db0f06b'
down_revision: Union[str, Sequence[str], None] = '34da524e9c9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index(op.f('ix_vocabulary_tts_usage_usage_date'), table_name='vocabulary_tts_usage')
    op.drop_table('vocabulary_tts_usage')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        'vocabulary_tts_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('usage_date', sa.Date(), nullable=False),
        sa.Column('request_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('usage_date', name='uq_vocabulary_tts_usage_date'),
    )
    op.create_index(
        op.f('ix_vocabulary_tts_usage_usage_date'),
        'vocabulary_tts_usage',
        ['usage_date'],
    )
