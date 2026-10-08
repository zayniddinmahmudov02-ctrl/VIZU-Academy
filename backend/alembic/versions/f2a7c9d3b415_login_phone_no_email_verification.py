"""Auth: phone number as login identifier; registration without e-mail confirmation

Additive and non-destructive:
* users.login_phone (String(20), nullable, unique) — the login identifier of
  accounts that register with a phone number. Every existing row gets NULL,
  so existing e-mail / Telegram / admin / teacher logins are unchanged.
* Accounts that registered while e-mail confirmation existed and never
  confirmed are marked verified (is_verified, email_verified_at), since the
  confirmation step no longer exists. No row is deleted.

Downgrade removes login_phone (phone-registered accounts then keep their
placeholder e-mail and cannot log in by phone); the verified flags set
here are intentionally left as they are.

Revision ID: f2a7c9d3b415
Revises: e6a2b9d4c871
Create Date: 2026-10-08
"""

import sqlalchemy as sa
from alembic import op

revision = "f2a7c9d3b415"
down_revision = "e6a2b9d4c871"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("login_phone", sa.String(length=20), nullable=True))
    op.create_index("ix_users_login_phone", "users", ["login_phone"], unique=True)
    op.execute(
        """
        UPDATE users
        SET is_verified = true,
            email_verified_at = COALESCE(email_verified_at, now())
        WHERE email_verification_required = true AND email_verified_at IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_users_login_phone", table_name="users")
    op.drop_column("users", "login_phone")
