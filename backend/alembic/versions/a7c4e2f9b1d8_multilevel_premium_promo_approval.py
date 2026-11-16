"""Multilevel Modelltest Premium (one purchase opens Modelltest 1–10), promo code approval + product category, course promo requests.

Additive, nothing is deleted on upgrade:
  * user_entitlements (new): one row per granted product access (MULTILEVEL_MODELLTEST_PREMIUM), source PAYMENT (an approved order) or PROMO
    (a 100 % promo code); at most one active (revoked_at IS NULL) row per user and product (uq_user_entitlements_active)
  * promo_codes.product_category COURSES / PACKAGES / MULTILEVEL (existing rows: PACKAGES when they name only packages, else COURSES)
  * promo_codes.approval_status PENDING / APPROVED / ACTIVE / REJECTED / DISABLED (+ approved_by_id, approved_at, review_note): a code works only
    when ACTIVE and approved. New codes start PENDING. Existing codes were created and switched on by a Super Admin before this rule existed and are
    in use: they become ACTIVE (is_active) or DISABLED, approved_at = now, approved_by = their creator, with a review note saying so.
  * promo_codes.assigned_user_id: a code made for one student (course promo request) works for nobody else
  * promo_code_requests.kind CODE_APPROVAL (existing rows: a student asks to use a code that needs approval) / COURSE_REQUEST (new: a student asks for
    a promo for a course; promo_code_id is NULL until an admin attaches a code), message (student's text); promo_code_id becomes nullable
  * subscription_orders.paid_at (payment date + time given by the student), no_receipt ("Chek mavjud emas"), student_note, admin_note
Downgrade drops exactly these; course promo requests without a code (kind COURSE_REQUEST) are deleted first, because promo_code_id is NOT NULL again.

Revision ID: a7c4e2f9b1d8
Revises: e6d2b9a4c8f3
Create Date: 2026-11-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a7c4e2f9b1d8"
down_revision: Union[str, Sequence[str], None] = "e6d2b9a4c8f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LEGACY_NOTE = "Bestandscode: vor der Freigabepflicht vom Super Admin erstellt (Migration a7c4e2f9b1d8)"


def upgrade() -> None:
    op.create_table(
        "user_entitlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product", sa.String(40), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscription_orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("promo_code_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("promo_codes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("granted_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("revoke_reason", sa.Text(), nullable=True),
        sa.CheckConstraint("source IN ('PAYMENT','PROMO')", name="ck_user_entitlements_source"),
    )
    op.create_index("ix_user_entitlements_user_id", "user_entitlements", ["user_id"])
    op.create_index("ix_user_entitlements_order_id", "user_entitlements", ["order_id"])
    op.create_index("uq_user_entitlements_active", "user_entitlements", ["user_id", "product"], unique=True,
                    postgresql_where=sa.text("revoked_at IS NULL"))

    op.add_column("promo_codes", sa.Column("product_category", sa.String(20), server_default="COURSES", nullable=False))
    op.add_column("promo_codes", sa.Column("approval_status", sa.String(20), server_default="PENDING", nullable=False))
    op.add_column("promo_codes", sa.Column("approved_by_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("promo_codes", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("promo_codes", sa.Column("review_note", sa.Text(), nullable=True))
    op.add_column("promo_codes", sa.Column("assigned_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_promo_codes_approved_by_id", "promo_codes", "users", ["approved_by_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_promo_codes_assigned_user_id", "promo_codes", "users", ["assigned_user_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_promo_codes_assigned_user_id", "promo_codes", ["assigned_user_id"])
    op.execute("UPDATE promo_codes SET product_category = 'PACKAGES' "
               "WHERE jsonb_array_length(applicable_package_codes) > 0 AND jsonb_array_length(applicable_course_ids) = 0")
    op.execute(sa.text("UPDATE promo_codes SET approval_status = CASE WHEN is_active THEN 'ACTIVE' ELSE 'DISABLED' END, "
                       "approved_at = now(), approved_by_id = created_by_id, review_note = :note").bindparams(note=LEGACY_NOTE))
    op.create_check_constraint("ck_promo_codes_product_category", "promo_codes", "product_category IN ('COURSES','PACKAGES','MULTILEVEL')")
    op.create_check_constraint("ck_promo_codes_approval_status", "promo_codes",
                               "approval_status IN ('PENDING','APPROVED','ACTIVE','REJECTED','DISABLED')")

    op.add_column("promo_code_requests", sa.Column("kind", sa.String(20), server_default="CODE_APPROVAL", nullable=False))
    op.add_column("promo_code_requests", sa.Column("message", sa.Text(), nullable=True))
    op.alter_column("promo_code_requests", "promo_code_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)
    op.create_check_constraint("ck_promo_code_requests_kind", "promo_code_requests", "kind IN ('CODE_APPROVAL','COURSE_REQUEST')")
    op.create_check_constraint("ck_promo_code_requests_code_needed", "promo_code_requests", "kind = 'COURSE_REQUEST' OR promo_code_id IS NOT NULL")
    op.create_index("uq_promo_code_requests_course_open", "promo_code_requests", ["user_id", "plan"], unique=True,
                    postgresql_where=sa.text("kind = 'COURSE_REQUEST' AND status = 'PENDING_APPROVAL'"))

    op.add_column("subscription_orders", sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("subscription_orders", sa.Column("no_receipt", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("subscription_orders", sa.Column("student_note", sa.Text(), nullable=True))
    op.add_column("subscription_orders", sa.Column("admin_note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("subscription_orders", "admin_note")
    op.drop_column("subscription_orders", "student_note")
    op.drop_column("subscription_orders", "no_receipt")
    op.drop_column("subscription_orders", "paid_at")

    op.drop_index("uq_promo_code_requests_course_open", table_name="promo_code_requests")
    op.drop_constraint("ck_promo_code_requests_code_needed", "promo_code_requests", type_="check")
    op.drop_constraint("ck_promo_code_requests_kind", "promo_code_requests", type_="check")
    op.execute("DELETE FROM promo_code_requests WHERE promo_code_id IS NULL")
    op.alter_column("promo_code_requests", "promo_code_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    op.drop_column("promo_code_requests", "message")
    op.drop_column("promo_code_requests", "kind")

    op.drop_constraint("ck_promo_codes_approval_status", "promo_codes", type_="check")
    op.drop_constraint("ck_promo_codes_product_category", "promo_codes", type_="check")
    op.drop_index("ix_promo_codes_assigned_user_id", table_name="promo_codes")
    op.drop_constraint("fk_promo_codes_assigned_user_id", "promo_codes", type_="foreignkey")
    op.drop_constraint("fk_promo_codes_approved_by_id", "promo_codes", type_="foreignkey")
    for column in ("assigned_user_id", "review_note", "approved_at", "approved_by_id", "approval_status", "product_category"):
        op.drop_column("promo_codes", column)

    op.drop_index("uq_user_entitlements_active", table_name="user_entitlements")
    op.drop_index("ix_user_entitlements_order_id", table_name="user_entitlements")
    op.drop_index("ix_user_entitlements_user_id", table_name="user_entitlements")
    op.drop_table("user_entitlements")
