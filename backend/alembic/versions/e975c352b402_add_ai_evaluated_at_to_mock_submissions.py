"""add ai_evaluated_at to mock submissions

Revision ID: e975c352b402
Revises: 7df134a759e6
Create Date: 2026-08-05 01:41:20.188505

Manually stripped of autogenerate's legacy-drift noise (drops of unrelated
Telegram-bot-era tables/columns) — same pattern as every other migration in
this project, see 7df134a759e6's docstring. Contains ONLY the two intended
columns needed for Phase 5's "AI checked today" dashboard stats.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e975c352b402'
down_revision: Union[str, Sequence[str], None] = '7df134a759e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'mock_writing_submissions',
        sa.Column('ai_evaluated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'mock_speaking_submissions',
        sa.Column('ai_evaluated_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('mock_speaking_submissions', 'ai_evaluated_at')
    op.drop_column('mock_writing_submissions', 'ai_evaluated_at')
