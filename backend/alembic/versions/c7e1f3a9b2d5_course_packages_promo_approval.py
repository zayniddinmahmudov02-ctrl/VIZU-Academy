"""Course packages table, order snapshots, promo codes that need admin approval.

Adds
- table course_packages (code, name, type, included_levels, price, original_price, discount_percent, duration_days,
  status ACTIVE/COMING_SOON/DISABLED, description per language, sort_order) and seeds the eight packages:
  A1 / A2 keep the price currently in force (the admin override in app_settings["angebote"], else the code default);
  B1 100 000 so'm / 60 days, A1–B1 200 000 / 180 days, A1–C1 400 000 / 365 days (owner decision 2026-11-14);
  A1 / A2 30 days; B2, C1 and the new B2–C1 bundle COMING_SOON without a price;
- nullable subscription_orders.included_levels (levels an order opens, snapshot at checkout; NULL = old orders,
  resolved from the package as before);
- promo_codes.requires_approval (default false: existing codes behave as before);
- table promo_code_requests (PENDING_APPROVAL / APPROVED / REJECTED / USED, one open request per code+user+package).

No row is deleted or changed except new columns with defaults. Downgrade drops exactly these objects.

Revision ID: c7e1f3a9b2d5
Revises: a3c9e7b5d1f4
Create Date: 2026-11-14
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c7e1f3a9b2d5"
down_revision: Union[str, Sequence[str], None] = "a3c9e7b5d1f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB

# code, name, type, levels, price, original, discount, days, status, sort
SEED = [
    ("A1", "A1", "LEVEL", ["A1"], 50_000, 100_000, 50, 30, "ACTIVE", 10),
    ("A2", "A2", "LEVEL", ["A2"], 99_000, 200_000, 50, 30, "ACTIVE", 20),
    ("B1", "B1", "LEVEL", ["B1"], 100_000, None, None, 60, "ACTIVE", 30),
    ("B2", "B2", "LEVEL", ["B2"], None, None, None, 90, "COMING_SOON", 40),
    ("C1", "C1", "LEVEL", ["C1"], None, None, None, 60, "COMING_SOON", 50),
    ("A1_B1", "A1 → B1", "PACKAGE", ["A1", "A2", "B1"], 200_000, None, None, 180, "ACTIVE", 60),
    ("A1_C1", "A1 → C1", "PACKAGE", ["A1", "A2", "B1", "B2", "C1"], 400_000, None, None, 365, "ACTIVE", 70),
    ("B2_C1", "B2 → C1", "PACKAGE", ["B2", "C1"], None, None, None, 180, "COMING_SOON", 80),
]
KEEP_CURRENT_PRICE = ("A1", "A2")


def upgrade() -> None:
    op.create_table(
        "course_packages",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("package_type", sa.String(20), nullable=False),
        sa.Column("included_levels", JSONB, nullable=False, server_default="[]"),
        sa.Column("price", sa.Integer(), nullable=True),
        sa.Column("original_price", sa.Integer(), nullable=True),
        sa.Column("discount_percent", sa.Integer(), nullable=True),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="COMING_SOON"),
        sa.Column("description", JSONB, nullable=False, server_default="{}"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_by", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.UniqueConstraint("code", name="uq_course_packages_code"),
        sa.CheckConstraint("status IN ('ACTIVE','COMING_SOON','DISABLED')", name="ck_course_packages_status"),
        sa.CheckConstraint("package_type IN ('LEVEL','PACKAGE')", name="ck_course_packages_type"),
        sa.CheckConstraint("duration_days > 0 AND duration_days <= 3650", name="ck_course_packages_duration"),
        sa.CheckConstraint("price IS NULL OR (price > 0 AND price <= 100000000)", name="ck_course_packages_price"),
    )
    overrides: dict = {}
    if not op.get_context().as_sql:
        row = op.get_bind().execute(sa.text("SELECT value FROM app_settings WHERE key = 'angebote'")).scalar()
        overrides = (row if isinstance(row, dict) else json.loads(row)) if row else {}
    # typed columns so `alembic upgrade --sql` (offline review) can render the seed literals; JSONB has no literal
    # renderer, so offline the two JSON values are written as JSON text (PostgreSQL casts the literal on insert)
    offline = op.get_context().as_sql
    json_type = sa.Text if offline else JSONB
    table = sa.table("course_packages", sa.column("id", UUID), sa.column("code", sa.String), sa.column("name", sa.String),
                     sa.column("package_type", sa.String), sa.column("included_levels", json_type), sa.column("price", sa.Integer),
                     sa.column("original_price", sa.Integer), sa.column("discount_percent", sa.Integer),
                     sa.column("duration_days", sa.Integer), sa.column("status", sa.String),
                     sa.column("description", json_type), sa.column("sort_order", sa.Integer))
    rows = []
    import uuid

    for code, name, kind, levels, price, original, discount, days, status, sort in SEED:
        if code in KEEP_CURRENT_PRICE:
            own = (overrides.get("offers") or {}).get(code) or {}
            price = own.get("sale_price", price)
            original = own.get("original_price", original)
            discount = own.get("discount_percent", discount)
        rows.append({"id": uuid.uuid4(), "code": code, "name": name, "package_type": kind,
                     "included_levels": json.dumps(levels) if offline else levels, "price": price,
                     "original_price": original, "discount_percent": discount, "duration_days": days, "status": status,
                     "description": "{}" if offline else {}, "sort_order": sort})
    op.bulk_insert(table, rows)

    op.add_column("subscription_orders", sa.Column("included_levels", JSONB, nullable=True))
    op.add_column("promo_codes", sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table(
        "promo_code_requests",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("promo_code_id", UUID, sa.ForeignKey("promo_codes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING_APPROVAL"),
        sa.Column("reviewed_by_id", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("order_id", UUID, sa.ForeignKey("subscription_orders.id", ondelete="SET NULL"), nullable=True),
        sa.CheckConstraint("status IN ('PENDING_APPROVAL','APPROVED','REJECTED','USED')", name="ck_promo_code_requests_status"),
    )
    op.create_index("ix_promo_code_requests_promo_code_id", "promo_code_requests", ["promo_code_id"])
    op.create_index("ix_promo_code_requests_user_id", "promo_code_requests", ["user_id"])
    op.create_index("ix_promo_code_requests_status", "promo_code_requests", ["status"])
    op.create_index("uq_promo_code_requests_open", "promo_code_requests", ["promo_code_id", "user_id", "plan"], unique=True,
                    postgresql_where=sa.text("status IN ('PENDING_APPROVAL','APPROVED')"))


def downgrade() -> None:
    op.drop_index("uq_promo_code_requests_open", table_name="promo_code_requests")
    op.drop_index("ix_promo_code_requests_status", table_name="promo_code_requests")
    op.drop_index("ix_promo_code_requests_user_id", table_name="promo_code_requests")
    op.drop_index("ix_promo_code_requests_promo_code_id", table_name="promo_code_requests")
    op.drop_table("promo_code_requests")
    op.drop_column("promo_codes", "requires_approval")
    op.drop_column("subscription_orders", "included_levels")
    op.drop_table("course_packages")
