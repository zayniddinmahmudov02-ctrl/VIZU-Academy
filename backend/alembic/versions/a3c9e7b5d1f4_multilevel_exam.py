"""Multilevel exam mode: per-section state and results of a mock-exam attempt.

Adds
- table mock_attempt_sections: one row per (attempt, section LESEN/HOEREN/SCHREIBEN/SPRECHEN) with the server-set
  start / deadline / submit times, raw points, the 0–75 section score (CHECK) and its level, grader + feedback;
- nullable columns mock_test_attempts.result_level / result_rule (overall level and the rule that produced it);
- unique (attempt, question / writing task / speaking task) on mock_question_answers, mock_writing_submissions and
  mock_speaking_submissions, so a repeated save updates one row instead of adding a second score.
  The upgrade stops (nothing changed) if such duplicates already exist — they are never deleted automatically.

Downgrade drops the three unique constraints, the two columns and the table (section results are lost; attempts,
answers and submissions stay).

Revision ID: a3c9e7b5d1f4
Revises: f2b6d8a4c1e9
Create Date: 2026-11-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a3c9e7b5d1f4"
down_revision: Union[str, Sequence[str], None] = "f2b6d8a4c1e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
UNIQUE = [
    ("mock_question_answers", "question_id", "uq_mock_question_answers_attempt_question"),
    ("mock_writing_submissions", "writing_task_id", "uq_mock_writing_submissions_attempt_task"),
    ("mock_speaking_submissions", "speaking_task_id", "uq_mock_speaking_submissions_attempt_task"),
]


def upgrade() -> None:
    bind = op.get_bind()
    if not op.get_context().as_sql:  # offline --sql preview has no rows to check
        for table, column, _ in UNIQUE:
            dup = bind.execute(sa.text(f"SELECT count(*) FROM (SELECT 1 FROM {table} GROUP BY attempt_id, {column} HAVING count(*) > 1) d")).scalar()
            if dup:
                raise RuntimeError(f"{table}: {dup} duplicate (attempt, {column}) groups — resolve them manually first")
    op.create_table(
        "mock_attempt_sections",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("attempt_id", UUID, sa.ForeignKey("mock_test_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kompetenz_id", UUID, sa.ForeignKey("kompetenzen.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_points", sa.Integer(), nullable=True),
        sa.Column("raw_max", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("level", sa.String(20), nullable=True),
        sa.Column("graded_by", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("graded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.UniqueConstraint("attempt_id", "section_type", name="uq_mock_attempt_sections_attempt_type"),
        sa.CheckConstraint("score IS NULL OR (score >= 0 AND score <= 75)", name="ck_mock_attempt_sections_score_0_75"),
    )
    op.create_index("ix_mock_attempt_sections_attempt_id", "mock_attempt_sections", ["attempt_id"])
    op.add_column("mock_test_attempts", sa.Column("result_level", sa.String(20), nullable=True))
    op.add_column("mock_test_attempts", sa.Column("result_rule", sa.String(20), nullable=True))
    for table, column, name in UNIQUE:
        op.create_unique_constraint(name, table, ["attempt_id", column])


def downgrade() -> None:
    for table, _, name in UNIQUE:
        op.drop_constraint(name, table, type_="unique")
    op.drop_column("mock_test_attempts", "result_rule")
    op.drop_column("mock_test_attempts", "result_level")
    op.drop_index("ix_mock_attempt_sections_attempt_id", table_name="mock_attempt_sections")
    op.drop_table("mock_attempt_sections")
