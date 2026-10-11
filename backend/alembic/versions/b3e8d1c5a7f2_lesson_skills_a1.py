"""Lesson skills: Lesen/Hören tests, Hören audio + questions, AI evaluation for Schreiben/Sprechen

Additive and reversible — no existing row is changed or deleted:
* reading_questions: question_type, points (defaults keep old rows valid).
* listenings: instruction + private audio storage metadata; audio_url becomes
  nullable (uploaded audio is streamed through an access-checked endpoint).
* listening_questions / listening_options: Hören questions + answer key.
* lesson_skill_attempts: graded Lesen/Hören test runs (answers, score, time).
* writings / speakings: per-task AI settings; ai_evaluation_enabled defaults
  to false, so every existing task keeps today's teacher grading.
* student_writings / student_speakings: AI result fields, attempt counters.
* ai_evaluations: append-only history of AI runs and manual overrides.

Revision ID: b3e8d1c5a7f2
Revises: a9d4e6f8c2b7
Create Date: 2026-10-11
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "b3e8d1c5a7f2"
down_revision = "a9d4e6f8c2b7"
branch_labels = None
depends_on = None


def _timestamps():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def _ai_task_columns(table: str) -> None:
    op.add_column(table, sa.Column("ai_evaluation_enabled", sa.Boolean(), server_default="false", nullable=False))
    op.add_column(table, sa.Column("ai_instructions", sa.Text(), nullable=True))
    op.add_column(table, sa.Column("feedback_language", sa.String(length=10), server_default="uz", nullable=False))
    op.add_column(table, sa.Column("max_score", sa.Integer(), server_default="100", nullable=False))
    op.add_column(table, sa.Column("rubric", postgresql.JSONB(), nullable=True))
    op.add_column(table, sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False))


def _ai_submission_columns(table: str) -> None:
    op.add_column(table, sa.Column("ai_evaluation", postgresql.JSONB(), nullable=True))
    op.add_column(table, sa.Column("ai_score", sa.Integer(), nullable=True))
    op.add_column(table, sa.Column("evaluation_error", sa.String(length=500), nullable=True))
    op.add_column(table, sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(table, sa.Column("evaluation_runs", sa.Integer(), server_default="0", nullable=False))
    op.add_column(table, sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False))


AI_TASK_COLS = ("ai_evaluation_enabled", "ai_instructions", "feedback_language", "max_score", "rubric", "max_attempts")
AI_SUB_COLS = ("ai_evaluation", "ai_score", "evaluation_error", "evaluated_at", "evaluation_runs", "attempt_count")


def upgrade() -> None:
    # Lesen
    op.add_column("reading_questions", sa.Column("question_type", sa.String(length=20), server_default="MULTIPLE_CHOICE", nullable=False))
    op.add_column("reading_questions", sa.Column("points", sa.Integer(), server_default="1", nullable=False))

    # Hören
    op.alter_column("listenings", "audio_url", existing_type=sa.String(length=500), nullable=True)
    op.add_column("listenings", sa.Column("instruction", sa.Text(), nullable=True))
    op.add_column("listenings", sa.Column("audio_storage_path", sa.String(length=500), nullable=True))
    op.add_column("listenings", sa.Column("audio_content_type", sa.String(length=100), nullable=True))
    op.add_column("listenings", sa.Column("audio_size_bytes", sa.Integer(), nullable=True))
    op.add_column("listenings", sa.Column("audio_duration_seconds", sa.Integer(), nullable=True))
    op.add_column("listenings", sa.Column("audio_original_name", sa.String(length=255), nullable=True))

    op.create_table(
        "listening_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("listening_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("listenings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=20), server_default="MULTIPLE_CHOICE", nullable=False),
        sa.Column("points", sa.Integer(), server_default="1", nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), server_default="1", nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_listening_questions_listening_id", "listening_questions", ["listening_id"])
    op.create_table(
        "listening_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("listening_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("option_text", sa.String(length=500), nullable=False),
        sa.Column("is_correct", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("order_index", sa.Integer(), server_default="1", nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_listening_options_question_id", "listening_options", ["question_id"])

    # Graded Lesen / Hören runs
    op.create_table(
        "lesson_skill_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill", sa.String(length=20), nullable=False),
        sa.Column("listening_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("listenings.id", ondelete="CASCADE"), nullable=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="IN_PROGRESS", nullable=False),
        sa.Column("answers", postgresql.JSONB(), nullable=True),
        sa.Column("correct_count", sa.Integer(), nullable=True),
        sa.Column("question_count", sa.Integer(), nullable=True),
        sa.Column("points", sa.Numeric(7, 2), nullable=True),
        sa.Column("max_points", sa.Numeric(7, 2), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_lesson_skill_attempts_user_lesson_skill", "lesson_skill_attempts", ["user_id", "lesson_id", "skill"])
    op.create_index("ix_lesson_skill_attempts_listening_id", "lesson_skill_attempts", ["listening_id"])

    # Schreiben / Sprechen AI evaluation
    _ai_task_columns("writings")
    op.add_column("writings", sa.Column("helper_words", sa.Text(), nullable=True))
    op.add_column("writings", sa.Column("image_url", sa.String(length=500), nullable=True))
    op.add_column("writings", sa.Column("opens_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("writings", sa.Column("closes_at", sa.DateTime(timezone=True), nullable=True))
    _ai_task_columns("speakings")
    op.add_column("speakings", sa.Column("min_duration_seconds", sa.Integer(), server_default="0", nullable=False))
    _ai_submission_columns("student_writings")
    _ai_submission_columns("student_speakings")

    op.create_table(
        "ai_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.String(length=500), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_ai_evaluations_submission", "ai_evaluations", ["kind", "submission_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_evaluations_submission", table_name="ai_evaluations")
    op.drop_table("ai_evaluations")
    for table in ("student_speakings", "student_writings"):
        for col in AI_SUB_COLS:
            op.drop_column(table, col)
    op.drop_column("speakings", "min_duration_seconds")
    for col in AI_TASK_COLS:
        op.drop_column("speakings", col)
    for col in ("closes_at", "opens_at", "image_url", "helper_words"):
        op.drop_column("writings", col)
    for col in AI_TASK_COLS:
        op.drop_column("writings", col)
    op.drop_index("ix_lesson_skill_attempts_listening_id", table_name="lesson_skill_attempts")
    op.drop_index("ix_lesson_skill_attempts_user_lesson_skill", table_name="lesson_skill_attempts")
    op.drop_table("lesson_skill_attempts")
    op.drop_index("ix_listening_options_question_id", table_name="listening_options")
    op.drop_table("listening_options")
    op.drop_index("ix_listening_questions_listening_id", table_name="listening_questions")
    op.drop_table("listening_questions")
    for col in ("audio_original_name", "audio_duration_seconds", "audio_size_bytes", "audio_content_type", "audio_storage_path", "instruction"):
        op.drop_column("listenings", col)
    # Uploaded-only tasks have no URL; give them a placeholder so NOT NULL can return.
    op.execute("UPDATE listenings SET audio_url = '' WHERE audio_url IS NULL")
    op.alter_column("listenings", "audio_url", existing_type=sa.String(length=500), nullable=False)
    op.drop_column("reading_questions", "points")
    op.drop_column("reading_questions", "question_type")
