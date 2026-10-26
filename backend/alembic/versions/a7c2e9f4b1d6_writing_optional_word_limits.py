"""Optional word limits on writing tasks.

A book task that states no word count (VIZU-DEUTSCH A2) is stored with
NULL instead of an invented range; NULL = nothing shown or enforced.
Existing rows keep their values.

Revision ID: a7c2e9f4b1d6
Revises: e5b1c7d9a3f2
Create Date: 2026-10-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7c2e9f4b1d6"
down_revision: Union[str, Sequence[str], None] = "e5b1c7d9a3f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("writings", "min_words", existing_type=sa.Integer(), nullable=True)
    op.alter_column("writings", "max_words", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    # NULL bounds go back to the widest range the old schema could express
    op.execute("UPDATE writings SET min_words = 1 WHERE min_words IS NULL")
    op.execute("UPDATE writings SET max_words = 3000 WHERE max_words IS NULL")
    op.alter_column("writings", "max_words", existing_type=sa.Integer(), nullable=False)
    op.alter_column("writings", "min_words", existing_type=sa.Integer(), nullable=False)
