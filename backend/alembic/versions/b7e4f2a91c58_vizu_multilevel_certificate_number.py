"""vizu multilevel: certificate number per completed attempt

Revision ID: b7e4f2a91c58
Revises: a3d9c6e1b742
Create Date: 2026-10-08

Additive only: a nullable, unique `certificate_number` on vizu_mock_attempts
(issued once, the first time a certificate is requested for an eligible
attempt) and a dedicated sequence for its running number. No data changes.
"""

import sqlalchemy as sa

from alembic import op

revision = "b7e4f2a91c58"
down_revision = "a3d9c6e1b742"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE IF NOT EXISTS vizu_multilevel_certificate_seq START 1")
    op.add_column("vizu_mock_attempts", sa.Column("certificate_number", sa.String(length=32), nullable=True))
    op.create_unique_constraint(
        "uq_vizu_mock_attempts_certificate_number", "vizu_mock_attempts", ["certificate_number"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_vizu_mock_attempts_certificate_number", "vizu_mock_attempts", type_="unique")
    op.drop_column("vizu_mock_attempts", "certificate_number")
    op.execute("DROP SEQUENCE IF EXISTS vizu_multilevel_certificate_seq")
