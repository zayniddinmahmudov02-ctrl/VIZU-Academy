"""add feedback audio columns to speaking_evaluations

Revision ID: a0b7ea1ef39b
Revises: 0c3d0f8ef47d
Create Date: 2026-08-18 00:20:00.000000

Sprechen teacher feedback can be text or voice (spec: "feedback (text or
voice)"). Voice feedback is stored the same way student speaking audio
already is — via ProtectedLocalStorage, never a public URL — so these
mirror SpeakingSubmission's storage_path/filename/content_type naming.
All nullable: a review with only text feedback leaves them null.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0b7ea1ef39b'
down_revision: Union[str, Sequence[str], None] = '0c3d0f8ef47d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'speaking_evaluations',
        sa.Column('feedback_audio_path', sa.String(length=500), nullable=True),
    )
    op.add_column(
        'speaking_evaluations',
        sa.Column('feedback_audio_filename', sa.String(length=255), nullable=True),
    )
    op.add_column(
        'speaking_evaluations',
        sa.Column('feedback_audio_content_type', sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('speaking_evaluations', 'feedback_audio_content_type')
    op.drop_column('speaking_evaluations', 'feedback_audio_filename')
    op.drop_column('speaking_evaluations', 'feedback_audio_path')
