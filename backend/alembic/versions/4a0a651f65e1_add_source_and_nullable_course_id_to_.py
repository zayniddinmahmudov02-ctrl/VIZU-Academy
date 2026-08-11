"""add source and nullable course_id to certificates

Revision ID: 4a0a651f65e1
Revises: cca8c99a17de
Create Date: 2026-08-11 14:46:18.386912

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a0a651f65e1'
down_revision: Union[str, Sequence[str], None] = 'cca8c99a17de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Scoped to the certificates table only. Autogenerate also proposed
    dropping ix_audit_logs_created_at, ix_login_history_created_at,
    uq_promo_codes_code, and ix_subscription_orders_created_at — that is
    pre-existing, unrelated model/DB drift, intentionally left untouched
    here and flagged separately rather than dropped blindly.
    """
    op.add_column('certificates', sa.Column('source', sa.String(length=20), server_default='COURSE', nullable=False))
    op.alter_column('certificates', 'course_id',
               existing_type=sa.UUID(),
               nullable=True)
    op.create_index(op.f('ix_certificates_source'), 'certificates', ['source'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_certificates_source'), table_name='certificates')
    op.alter_column('certificates', 'course_id',
               existing_type=sa.UUID(),
               nullable=False)
    op.drop_column('certificates', 'source')
