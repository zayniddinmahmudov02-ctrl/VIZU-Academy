"""achievements (medals + rewards), learning activity (Lernserie)

Revision ID: e7c3a9f1b5d2
Revises: d8a4f1c6b2e7
Create Date: 2026-10-20 18:00:00.000000

Additive and backward-compatible:
* new tables achievement_categories, achievements, user_achievements,
  learning_activity;
* subscription_orders.reward_discount_amount (NOT NULL DEFAULT 0 — every
  existing order keeps its amounts);
* seed: category "Daraja medallari" + medal "Starter" (A1 lesson 1 ->
  5 000 UZS off an A1 order);
* backfill: learning_activity from already SUBMITTED Lesen / Hören / Übungen
  attempts (server started_at -> submitted_at, capped like new credits).
  Nothing existing is changed or deleted.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e7c3a9f1b5d2"
down_revision: Union[str, None] = "d8a4f1c6b2e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = sa.DateTime(timezone=True)
ATTEMPT_MAX_CREDIT = 20 * 60  # same as app.services.learning_activity


def _base():
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", _TS, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _TS, server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "achievement_categories", *_base(),
        sa.Column("key", sa.String(60), nullable=False, unique=True),
        sa.Column("name_de", sa.String(120), nullable=False),
        sa.Column("name_uz", sa.String(120), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_table(
        "achievements", *_base(),
        sa.Column("key", sa.String(60), nullable=False, unique=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("achievement_categories.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("name_de", sa.String(120), nullable=False),
        sa.Column("name_uz", sa.String(120), nullable=False),
        sa.Column("description_de", sa.Text(), nullable=True),
        sa.Column("description_uz", sa.Text(), nullable=True),
        sa.Column("icon_preset", sa.String(40), nullable=False, server_default="rocket"),
        sa.Column("icon_color", sa.String(20), nullable=False, server_default="green"),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("condition_type", sa.String(40), nullable=False),
        sa.Column("condition_params", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("reward_type", sa.String(30), nullable=False, server_default="NONE"),
        sa.Column("reward_value", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reward_offers", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("reward_combine_with_promo", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false", index=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "user_achievements", *_base(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("achievement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("awarded_at", _TS, nullable=False),
        sa.Column("reward_type", sa.String(30), nullable=False, server_default="NONE"),
        sa.Column("reward_value", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reward_offers", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("reward_status", sa.String(20), nullable=False, server_default="NONE"),
        sa.Column("reward_order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscription_orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reward_used_at", _TS, nullable=True),
        sa.UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )
    op.create_index("ix_user_achievements_reward_order_id", "user_achievements", ["reward_order_id"])
    op.create_table(
        "learning_activity", *_base(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("source_ref", sa.String(64), nullable=False),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("bucket_start", _TS, nullable=False),
        sa.Column("seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_event_at", _TS, nullable=False),
        sa.UniqueConstraint("user_id", "source", "source_ref", "bucket_start", name="uq_learning_activity_bucket"),
    )
    op.add_column("subscription_orders", sa.Column("reward_discount_amount", sa.Integer(), nullable=False, server_default="0"))

    # ---- seed: "Daraja medallari" + Starter (id from md5 -> stable, no extension needed)
    op.execute("""
        INSERT INTO achievement_categories (id, key, name_de, name_uz, order_index, is_active)
        VALUES (md5('achievement-category:level_medals')::uuid, 'level_medals', 'Stufenmedaillen', 'Daraja medallari', 0, true)
        ON CONFLICT (key) DO NOTHING
    """)
    op.execute("""
        INSERT INTO achievements (id, key, category_id, name_de, name_uz, description_de, description_uz, icon_preset, icon_color,
                                  condition_type, condition_params, reward_type, reward_value, reward_offers, reward_combine_with_promo,
                                  is_active, order_index)
        SELECT md5('achievement:starter')::uuid, 'starter', c.id, 'Starter', 'Starter',
               'Dein Start ist geschafft: Du hast die erste Lektion des A1-Kurses erfolgreich abgeschlossen.',
               'Boshlanish uddalandi: A1 kursining birinchi darsini muvaffaqiyatli yakunlading.',
               'rocket', 'green', 'LESSON_COMPLETED', '{"level": "A1", "lesson_number": 1}'::jsonb,
               'ORDER_DISCOUNT', 5000, '["A1"]'::jsonb, false, true, 0
        FROM achievement_categories c WHERE c.key = 'level_medals'
        ON CONFLICT (key) DO NOTHING
    """)

    # ---- backfill Lernserie from submitted attempts (server timestamps only)
    op.execute(f"""
        INSERT INTO learning_activity (id, user_id, source, source_ref, lesson_id, bucket_start, seconds, last_event_at, created_at, updated_at)
        SELECT md5('learning-activity:' || a.id::text)::uuid, a.user_id, 'SKILL_ATTEMPT', a.id::text, a.lesson_id,
               date_trunc('hour', a.submitted_at AT TIME ZONE 'UTC') AT TIME ZONE 'UTC',
               LEAST(a.duration_seconds, {ATTEMPT_MAX_CREDIT}), a.submitted_at, now(), now()
        FROM lesson_skill_attempts a
        WHERE a.status = 'SUBMITTED' AND a.submitted_at IS NOT NULL AND COALESCE(a.duration_seconds, 0) > 0
        ON CONFLICT ON CONSTRAINT uq_learning_activity_bucket DO NOTHING
    """)


def downgrade() -> None:
    op.drop_column("subscription_orders", "reward_discount_amount")
    op.drop_table("learning_activity")
    op.drop_index("ix_user_achievements_reward_order_id", table_name="user_achievements")
    op.drop_table("user_achievements")
    op.drop_table("achievements")
    op.drop_table("achievement_categories")
