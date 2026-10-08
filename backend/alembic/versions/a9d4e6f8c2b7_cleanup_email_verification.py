"""Cleanup: remove the e-mail verification / reset-code storage

Separate cleanup step after f2a7c9d3b415 (which already made every account
able to log in without confirmation). Removes what nothing uses any more:
* table email_verification_codes (short-lived hashed codes — no lasting data)
* users.email_verification_required, users.email_verified_at (flags of the
  removed confirmation step; login never reads them now)

Kept on purpose: users.tokens_valid_after (session revocation, still checked
in get_current_user) and auth_rate_limit_events (now used for login /
registration brute-force protection).

To deploy the new auth flow WITHOUT this cleanup, stop at the previous
revision: `alembic upgrade f2a7c9d3b415`. Downgrade recreates the table and
columns (empty / default false — the dropped codes are not restored).

Revision ID: a9d4e6f8c2b7
Revises: f2a7c9d3b415
Create Date: 2026-10-08
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "a9d4e6f8c2b7"
down_revision = "f2a7c9d3b415"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("uq_email_verification_codes_active", table_name="email_verification_codes")
    op.drop_index("ix_email_verification_codes_expires_at", table_name="email_verification_codes")
    op.drop_index("ix_email_verification_codes_purpose", table_name="email_verification_codes")
    op.drop_index("ix_email_verification_codes_email", table_name="email_verification_codes")
    op.drop_index("ix_email_verification_codes_user_id", table_name="email_verification_codes")
    op.drop_table("email_verification_codes")
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "email_verification_required")


def downgrade() -> None:
    op.add_column("users", sa.Column("email_verification_required", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "email_verification_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("purpose", sa.String(length=40), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_email_verification_codes_user_id", "email_verification_codes", ["user_id"])
    op.create_index("ix_email_verification_codes_email", "email_verification_codes", ["email"])
    op.create_index("ix_email_verification_codes_purpose", "email_verification_codes", ["purpose"])
    op.create_index("ix_email_verification_codes_expires_at", "email_verification_codes", ["expires_at"])
    op.create_index(
        "uq_email_verification_codes_active",
        "email_verification_codes",
        ["user_id", "purpose"],
        unique=True,
        postgresql_where=sa.text("used_at IS NULL AND invalidated_at IS NULL"),
    )
