"""Multilevel scoring trail: AI grading + Super Admin overrides on `mock_attempt_sections`.

Additive: nullable columns auto_score, override_score (CHECK 0–75 each), score_source, ai_status (+ index), ai_raw, ai_raw_max (numeric 6,2),
ai_claimed_at, and ai_runs (int NOT NULL DEFAULT 0). `score` stays the section score that counts (override if set, else the rule / AI score).
Every AI run and every override is a row in the existing ai_evaluations table (kind ML_SECTION) — no new table. Existing rows keep their
scores; the rescoring of old attempts under the owner's tables is a separate plan / apply script (multilevel_rescore).

Downgrade: drops the index, the checks and the columns (the scores themselves stay in `score`; the trail of who / what scored is lost —
ai_evaluations rows stay).

Revision ID: c7f4a1e9d3b2
Revises: b6e3d9a2c5f8
Create Date: 2026-11-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c7f4a1e9d3b2"
down_revision: Union[str, Sequence[str], None] = "b6e3d9a2c5f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

T = "mock_attempt_sections"


def upgrade() -> None:
    op.add_column(T, sa.Column("auto_score", sa.Integer(), nullable=True))
    op.add_column(T, sa.Column("override_score", sa.Integer(), nullable=True))
    op.add_column(T, sa.Column("score_source", sa.String(length=10), nullable=True))
    op.add_column(T, sa.Column("ai_status", sa.String(length=20), nullable=True))
    op.add_column(T, sa.Column("ai_raw", sa.Numeric(6, 2), nullable=True))
    op.add_column(T, sa.Column("ai_raw_max", sa.Numeric(6, 2), nullable=True))
    op.add_column(T, sa.Column("ai_claimed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(T, sa.Column("ai_runs", sa.Integer(), nullable=False, server_default="0"))
    op.create_check_constraint("ck_mock_attempt_sections_auto_score_0_75", T, "auto_score IS NULL OR (auto_score >= 0 AND auto_score <= 75)")
    op.create_check_constraint("ck_mock_attempt_sections_override_0_75", T, "override_score IS NULL OR (override_score >= 0 AND override_score <= 75)")
    op.create_index("ix_mock_attempt_sections_ai_status", T, ["ai_status"])


def downgrade() -> None:
    op.drop_index("ix_mock_attempt_sections_ai_status", table_name=T)
    op.drop_constraint("ck_mock_attempt_sections_override_0_75", T, type_="check")
    op.drop_constraint("ck_mock_attempt_sections_auto_score_0_75", T, type_="check")
    for column in ("ai_runs", "ai_claimed_at", "ai_raw_max", "ai_raw", "ai_status", "score_source", "override_score", "auto_score"):
        op.drop_column(T, column)
