"""listenings.task_key: a stable key for Hören tasks that a page manages by
name (A2 4. Unterricht "Text 1" / "Text 2" / "Text 3").

Additive only: a nullable column and a unique partial index; existing rows
keep NULL. Downgrade drops both — the tasks themselves stay.

Revision ID: b8e3d1a7c5f2
Revises: a6d2f9c4e8b1
Create Date: 2026-10-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8e3d1a7c5f2"
down_revision: Union[str, Sequence[str], None] = "a6d2f9c4e8b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("listenings", sa.Column("task_key", sa.String(80), nullable=True))
    op.create_index("uq_listenings_task_key", "listenings", ["task_key"], unique=True,
                    postgresql_where=sa.text("task_key IS NOT NULL"))


def downgrade() -> None:
    op.drop_index("uq_listenings_task_key", table_name="listenings")
    op.drop_column("listenings", "task_key")
