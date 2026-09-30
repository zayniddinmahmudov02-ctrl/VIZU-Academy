"""create vizu_mock lesen content tables

Revision ID: 39f489a43397
Revises: 47c59ed32679
Create Date: 2026-09-30 00:00:00.000000

Adds the real Lesen content/grading schema for VIZU-Mock:
vizu_mock_tasks (Aufgabe: passage + level), vizu_mock_questions
(graded question within a task), vizu_mock_options (answer choices,
exactly one is_correct per question), vizu_mock_answers (one student's
recorded, server-graded answer within an attempt). Also adds
vizu_mock_attempts.lesen_score (raw 0-20 points), alongside the
already-existing lesen_level column. Hören/Schreiben/Sprechen reuse
these same tables later via the `skill` column — no schema change should
be needed for that, only new seed content and write paths.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '39f489a43397'
down_revision: Union[str, Sequence[str], None] = '47c59ed32679'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('vizu_mock_attempts', sa.Column('lesen_score', sa.Integer(), nullable=True))

    op.create_table(
        'vizu_mock_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('skill', sa.String(length=20), nullable=False),
        sa.Column('level', sa.String(length=10), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('passage_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('skill', 'order_index', name='uq_vizu_mock_task_skill_order'),
    )
    op.create_index(op.f('ix_vizu_mock_tasks_skill'), 'vizu_mock_tasks', ['skill'])
    op.create_index(op.f('ix_vizu_mock_tasks_level'), 'vizu_mock_tasks', ['level'])

    op.create_table(
        'vizu_mock_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_type', sa.String(length=20), nullable=False),
        sa.Column('passage_text', sa.Text(), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('points', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['vizu_mock_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_vizu_mock_questions_task_id'), 'vizu_mock_questions', ['task_id'])

    op.create_table(
        'vizu_mock_options',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('option_text', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['vizu_mock_questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_vizu_mock_options_question_id'), 'vizu_mock_options', ['question_id'])

    op.create_table(
        'vizu_mock_answers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('selected_option_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_correct', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('points_earned', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['attempt_id'], ['vizu_mock_attempts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['vizu_mock_questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['selected_option_id'], ['vizu_mock_options.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('attempt_id', 'question_id', name='uq_vizu_mock_answer_attempt_question'),
    )
    op.create_index(op.f('ix_vizu_mock_answers_attempt_id'), 'vizu_mock_answers', ['attempt_id'])
    op.create_index(op.f('ix_vizu_mock_answers_question_id'), 'vizu_mock_answers', ['question_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_vizu_mock_answers_question_id'), table_name='vizu_mock_answers')
    op.drop_index(op.f('ix_vizu_mock_answers_attempt_id'), table_name='vizu_mock_answers')
    op.drop_table('vizu_mock_answers')

    op.drop_index(op.f('ix_vizu_mock_options_question_id'), table_name='vizu_mock_options')
    op.drop_table('vizu_mock_options')

    op.drop_index(op.f('ix_vizu_mock_questions_task_id'), table_name='vizu_mock_questions')
    op.drop_table('vizu_mock_questions')

    op.drop_index(op.f('ix_vizu_mock_tasks_level'), table_name='vizu_mock_tasks')
    op.drop_index(op.f('ix_vizu_mock_tasks_skill'), table_name='vizu_mock_tasks')
    op.drop_table('vizu_mock_tasks')

    op.drop_column('vizu_mock_attempts', 'lesen_score')
