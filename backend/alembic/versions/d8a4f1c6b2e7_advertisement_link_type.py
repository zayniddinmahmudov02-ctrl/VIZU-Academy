"""advertisements: link type (external URL / internal student page)

Revision ID: d8a4f1c6b2e7
Revises: c3e7a9d2f4b1
Create Date: 2026-10-20 00:00:00.000000

Additive and backward-compatible: existing rows become link_type EXTERNAL
with their target_url unchanged; target_url turns nullable (an internal link
has none). Downgrade refuses while internal-link rows exist (it would have
to invent a target_url for them) — no row is changed or lost.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d8a4f1c6b2e7"
down_revision: Union[str, None] = "c3e7a9d2f4b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("advertisements", sa.Column("link_type", sa.String(length=20), nullable=False, server_default="EXTERNAL"))
    op.add_column("advertisements", sa.Column("internal_route", sa.String(length=60), nullable=True))
    op.add_column("advertisements", sa.Column("internal_params", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.alter_column("advertisements", "target_url", existing_type=sa.String(length=1000), nullable=True)
    op.create_check_constraint("ck_advertisements_link_type", "advertisements", "link_type IN ('EXTERNAL', 'INTERNAL')")


def downgrade() -> None:
    bind = op.get_bind()
    internal = bind.execute(sa.text("SELECT count(*) FROM advertisements WHERE target_url IS NULL")).scalar()
    if internal:
        raise RuntimeError(f"{internal} advertisement(s) use an internal link (no target_url) — change or delete them before downgrading.")
    op.drop_constraint("ck_advertisements_link_type", "advertisements", type_="check")
    op.alter_column("advertisements", "target_url", existing_type=sa.String(length=1000), nullable=False)
    op.drop_column("advertisements", "internal_params")
    op.drop_column("advertisements", "internal_route")
    op.drop_column("advertisements", "link_type")
