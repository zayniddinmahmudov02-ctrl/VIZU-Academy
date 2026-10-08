"""VIZU-Multilevel: up to 3 attempts per student — attempt number + stored Gesamtergebnis

Additive and reversible:
* vizu_mock_attempts.attempt_number — backfilled 1, 2, 3 … per student in
  start order (existing rows keep everything else untouched), then NOT NULL
  plus a unique (user_id, attempt_number) constraint.
* vizu_mock_attempts.result_score — nullable; filled by the application from
  the existing result calculation (no score is computed in SQL here).

No row is deleted or reset.

Revision ID: e6a2b9d4c871
Revises: c5d8e1f3a296
Create Date: 2026-10-08
"""

import sqlalchemy as sa
from alembic import op

revision = "e6a2b9d4c871"
down_revision = "c5d8e1f3a296"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("vizu_mock_attempts", sa.Column("attempt_number", sa.Integer(), nullable=True))
    op.add_column("vizu_mock_attempts", sa.Column("result_score", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE vizu_mock_attempts AS a
        SET attempt_number = n.rn
        FROM (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY started_at, created_at, id) AS rn
            FROM vizu_mock_attempts
        ) AS n
        WHERE a.id = n.id
        """
    )
    op.alter_column("vizu_mock_attempts", "attempt_number", nullable=False)
    op.create_unique_constraint(
        "uq_vizu_mock_attempts_user_attempt_number", "vizu_mock_attempts", ["user_id", "attempt_number"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_vizu_mock_attempts_user_attempt_number", "vizu_mock_attempts", type_="unique")
    op.drop_column("vizu_mock_attempts", "result_score")
    op.drop_column("vizu_mock_attempts", "attempt_number")
