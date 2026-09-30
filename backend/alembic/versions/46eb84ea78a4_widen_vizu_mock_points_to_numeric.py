"""widen vizu_mock points columns to numeric

Revision ID: 46eb84ea78a4
Revises: 384d4fb96e12
Create Date: 2026-09-30 00:00:00.000000

Widens vizu_mock_questions.points, vizu_mock_answers.points_earned and
vizu_mock_attempts.hoeren_score from Integer to Numeric(4,1)/Numeric(5,1)
so VIZU-Mock's Hören module can weight each question's points by its
CEFR level (A1=0.5, A2=1.0, B1=1.5, B2=2.0, C1=2.5 — see
services/vizu_mock/hoeren_csv_import_service.py) instead of a flat
integer per question. Lesen's existing flat 5-points-per-question values
store fine as Numeric too (5 -> 5.0), so this is purely a type widening
— no existing data changes meaning, and no other VIZU-Mock table is
affected (lesen_score/schreiben_score stay Integer; Schreiben has its
own independent scoring, untouched).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46eb84ea78a4'
down_revision: Union[str, Sequence[str], None] = '384d4fb96e12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'vizu_mock_questions', 'points',
        existing_type=sa.Integer(),
        type_=sa.Numeric(4, 1),
        existing_nullable=False,
        existing_server_default='1',
    )
    op.alter_column(
        'vizu_mock_answers', 'points_earned',
        existing_type=sa.Integer(),
        type_=sa.Numeric(4, 1),
        existing_nullable=False,
        existing_server_default='0',
    )
    op.alter_column(
        'vizu_mock_attempts', 'hoeren_score',
        existing_type=sa.Integer(),
        type_=sa.Numeric(5, 1),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'vizu_mock_attempts', 'hoeren_score',
        existing_type=sa.Numeric(5, 1),
        type_=sa.Integer(),
        existing_nullable=True,
    )
    op.alter_column(
        'vizu_mock_answers', 'points_earned',
        existing_type=sa.Numeric(4, 1),
        type_=sa.Integer(),
        existing_nullable=False,
        existing_server_default='0',
    )
    op.alter_column(
        'vizu_mock_questions', 'points',
        existing_type=sa.Numeric(4, 1),
        type_=sa.Integer(),
        existing_nullable=False,
        existing_server_default='1',
    )
