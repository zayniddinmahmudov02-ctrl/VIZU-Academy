"""email verification + password reset codes

Revision ID: c5d8e1f3a296
Revises: b7e4f2a91c58
Create Date: 2026-10-08

Additive and reversible:
* users.email_verification_required (default false for EVERY existing row —
  existing accounts keep logging in exactly as before; only new
  self-registrations set it to true), users.email_verified_at,
  users.tokens_valid_after (NULL = no restriction).
* email_verification_codes: hashed 6-digit codes per (user, purpose), at
  most one active code per pair (partial unique index).
* auth_rate_limit_events: hashed email/IP counters for rate limiting.
No existing data is changed or deleted.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "c5d8e1f3a296"
down_revision = "b7e4f2a91c58"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verification_required", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("tokens_valid_after", sa.DateTime(timezone=True), nullable=True))

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

    op.create_table(
        "auth_rate_limit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("email_hash", sa.String(length=64), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_auth_rate_limit_events_email", "auth_rate_limit_events", ["action", "email_hash", "created_at"])
    op.create_index("ix_auth_rate_limit_events_ip", "auth_rate_limit_events", ["action", "ip_hash", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_auth_rate_limit_events_ip", table_name="auth_rate_limit_events")
    op.drop_index("ix_auth_rate_limit_events_email", table_name="auth_rate_limit_events")
    op.drop_table("auth_rate_limit_events")
    op.drop_index("uq_email_verification_codes_active", table_name="email_verification_codes")
    op.drop_index("ix_email_verification_codes_expires_at", table_name="email_verification_codes")
    op.drop_index("ix_email_verification_codes_purpose", table_name="email_verification_codes")
    op.drop_index("ix_email_verification_codes_email", table_name="email_verification_codes")
    op.drop_index("ix_email_verification_codes_user_id", table_name="email_verification_codes")
    op.drop_table("email_verification_codes")
    op.drop_column("users", "tokens_valid_after")
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "email_verification_required")
