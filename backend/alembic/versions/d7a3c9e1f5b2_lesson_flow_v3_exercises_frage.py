"""Lesson flow v3 (VIZU-DEUTSCH A1 book): exercise sets, Frage des Themas

Additive and reversible — no existing row is changed or deleted:
* skill_exercises / skill_exercise_questions / skill_exercise_options:
  auto-graded exercise sets of a lesson for Grammatik, Wortschatz and the
  Yakuniy Test (same question types and server-side grading as Lesen/Hören).
* lesson_skill_attempts.exercise_id: the set an attempt belongs to.
* speakings.task_kind: SPRECHEN (default — every existing row) or FRAGE
  (Frage des Themas, a voice answer that reuses the Sprechen recorder).
* grammars.content_id, vocabularies.content_id: stable import identifiers.

Revision ID: d7a3c9e1f5b2
Revises: c4f9a2e7b1d3
Create Date: 2026-10-12
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "d7a3c9e1f5b2"
down_revision = "c4f9a2e7b1d3"
branch_labels = None
depends_on = None


def _timestamps():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "skill_exercises",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="book"),
        sa.Column("content_id", sa.String(length=120), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_skill_exercises_lesson_skill", "skill_exercises", ["lesson_id", "skill"])
    op.create_index("ix_skill_exercises_content_id", "skill_exercises", ["content_id"])

    op.create_table(
        "skill_exercise_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("exercise_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skill_exercises.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=20), nullable=False, server_default="MULTIPLE_CHOICE"),
        sa.Column("points", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *_timestamps(),
    )
    op.create_table(
        "skill_exercise_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skill_exercise_questions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("option_text", sa.String(length=500), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="1"),
        *_timestamps(),
    )

    op.add_column(
        "lesson_skill_attempts",
        sa.Column("exercise_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skill_exercises.id", ondelete="CASCADE"), nullable=True),
    )
    op.create_index("ix_lesson_skill_attempts_exercise_id", "lesson_skill_attempts", ["exercise_id"])

    op.add_column("speakings", sa.Column("task_kind", sa.String(length=20), nullable=False, server_default="SPRECHEN"))
    op.add_column("grammars", sa.Column("content_id", sa.String(length=120), nullable=True))
    op.create_index("ix_grammars_content_id", "grammars", ["content_id"])
    op.add_column("vocabularies", sa.Column("content_id", sa.String(length=120), nullable=True))
    op.create_index("ix_vocabularies_content_id", "vocabularies", ["content_id"])


def downgrade() -> None:
    op.drop_index("ix_vocabularies_content_id", table_name="vocabularies")
    op.drop_column("vocabularies", "content_id")
    op.drop_index("ix_grammars_content_id", table_name="grammars")
    op.drop_column("grammars", "content_id")
    op.drop_column("speakings", "task_kind")
    op.drop_index("ix_lesson_skill_attempts_exercise_id", table_name="lesson_skill_attempts")
    op.drop_column("lesson_skill_attempts", "exercise_id")
    op.drop_table("skill_exercise_options")
    op.drop_table("skill_exercise_questions")
    op.drop_index("ix_skill_exercises_content_id", table_name="skill_exercises")
    op.drop_index("ix_skill_exercises_lesson_skill", table_name="skill_exercises")
    op.drop_table("skill_exercises")
