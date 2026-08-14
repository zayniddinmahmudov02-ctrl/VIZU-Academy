"""drop vocabulary audio_status/audio_error (pronunciation-audio feature removed)

Revision ID: 141f83a602bd
Revises: 52b95db0f06b
Create Date: 2026-08-14 03:00:00.000000

The microphone-recording pronunciation-audio feature has been removed
entirely — vocabulary audio is not needed for now. `audio_status`/
`audio_error` existed only to track that feature's recording state;
`audio_url` is untouched and remains available for a manually pasted/
uploaded URL, same as before that feature ever existed.

No data loss of consequence: at the time of this migration every real
vocabulary row's audio_status was 'PENDING' with no audio_url set (the
feature was never used successfully in production), and audio_error was
always NULL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '141f83a602bd'
down_revision: Union[str, Sequence[str], None] = '52b95db0f06b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index(op.f('ix_vocabularies_audio_status'), table_name='vocabularies')
    op.drop_column('vocabularies', 'audio_error')
    op.drop_column('vocabularies', 'audio_status')


def downgrade() -> None:
    """Downgrade schema."""
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
