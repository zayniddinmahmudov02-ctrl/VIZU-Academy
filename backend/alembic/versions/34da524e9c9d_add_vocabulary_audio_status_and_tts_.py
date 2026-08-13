"""add vocabulary audio_status/audio_error and vocabulary_tts_usage table

Revision ID: 34da524e9c9d
Revises: 8006706ca9db
Create Date: 2026-08-13 00:00:00.000000

Backs the "Fehlende Audios generieren" (generate missing audio) admin
queue: a persistent per-word status (PENDING/GENERATED/FAILED/
RATE_LIMITED) plus a per-day request counter used as this app's own
self-imposed budget against Gemini TTS's real quota.

Purely additive — two new nullable-or-defaulted columns on the existing
`vocabularies` table, one new table. Nothing existing is renamed, typed
differently, or dropped. `audio_status` is backfilled from the current
`audio_url` value so real rows are classified correctly without anyone
re-running generation for words that already have audio.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '34da524e9c9d'
down_revision: Union[str, Sequence[str], None] = '8006706ca9db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'vocabularies',
        sa.Column('audio_status', sa.String(length=20), nullable=False, server_default='PENDING'),
    )
    op.add_column(
        'vocabularies',
        sa.Column('audio_error', sa.Text(), nullable=True),
    )
    op.create_index(
        op.f('ix_vocabularies_audio_status'),
        'vocabularies',
        ['audio_status'],
    )

    # Backfill: a row that already has audio is GENERATED, not PENDING —
    # this is the only place existing data is touched, and only to mark
    # already-successful rows as such (never overwrites audio_url/
    # audio_error, never regresses a row to a worse state).
    op.execute("UPDATE vocabularies SET audio_status = 'GENERATED' WHERE audio_url IS NOT NULL")

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


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_vocabulary_tts_usage_usage_date'), table_name='vocabulary_tts_usage')
    op.drop_table('vocabulary_tts_usage')

    op.drop_index(op.f('ix_vocabularies_audio_status'), table_name='vocabularies')
    op.drop_column('vocabularies', 'audio_error')
    op.drop_column('vocabularies', 'audio_status')
