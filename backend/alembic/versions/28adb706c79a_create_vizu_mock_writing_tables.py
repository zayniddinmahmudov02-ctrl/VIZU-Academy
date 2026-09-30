"""create vizu_mock writing (Schreiben) tables

Revision ID: 28adb706c79a
Revises: 4927dd36c79d
Create Date: 2026-09-30 00:00:00.000000

Adds the Schreiben module for VIZU-Mock: vizu_mock_writing_tasks (5
Aufgabe — topic/instruction/word limits/optional image), vizu_mock_
writing_rubric_criteria (per-task teacher-scoring rubric),
vizu_mock_writing_submissions (one student answer per attempt+task,
teacher-graded), vizu_mock_writing_criterion_scores (per-criterion
scores within a graded submission). Also adds schreiben_score,
schreiben_submitted_at and schreiben_feedback to vizu_mock_attempts
(schreiben_level already existed as a nullable placeholder column).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '28adb706c79a'
down_revision: Union[str, Sequence[str], None] = '4927dd36c79d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('vizu_mock_attempts', sa.Column('schreiben_score', sa.Integer(), nullable=True))
    op.add_column('vizu_mock_attempts', sa.Column('schreiben_submitted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('vizu_mock_attempts', sa.Column('schreiben_feedback', sa.Text(), nullable=True))

    op.create_table(
        'vizu_mock_writing_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('level', sa.String(length=10), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('instruction', sa.Text(), nullable=False),
        sa.Column('min_words', sa.Integer(), nullable=False),
        sa.Column('max_words', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('points', sa.Integer(), server_default='20', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_index'),
    )
    op.create_index(op.f('ix_vizu_mock_writing_tasks_level'), 'vizu_mock_writing_tasks', ['level'])

    op.create_table(
        'vizu_mock_writing_rubric_criteria',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('max_score', sa.Integer(), nullable=False),
        sa.Column('order_index', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['vizu_mock_writing_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_vizu_mock_writing_rubric_criteria_task_id'), 'vizu_mock_writing_rubric_criteria', ['task_id']
    )

    op.create_table(
        'vizu_mock_writing_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), server_default='', nullable=False),
        sa.Column('word_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='DRAFT', nullable=False),
        sa.Column('saved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('teacher_score', sa.Integer(), nullable=True),
        sa.Column('teacher_comment', sa.Text(), nullable=True),
        sa.Column('reviewed_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['attempt_id'], ['vizu_mock_attempts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['vizu_mock_writing_tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('attempt_id', 'task_id', name='uq_vizu_mock_writing_submission_attempt_task'),
    )
    op.create_index(
        op.f('ix_vizu_mock_writing_submissions_attempt_id'), 'vizu_mock_writing_submissions', ['attempt_id']
    )
    op.create_index(op.f('ix_vizu_mock_writing_submissions_task_id'), 'vizu_mock_writing_submissions', ['task_id'])

    op.create_table(
        'vizu_mock_writing_criterion_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('criterion_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['vizu_mock_writing_submissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['criterion_id'], ['vizu_mock_writing_rubric_criteria.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('submission_id', 'criterion_id', name='uq_vizu_mock_writing_score_submission_criterion'),
    )
    op.create_index(
        op.f('ix_vizu_mock_writing_criterion_scores_submission_id'),
        'vizu_mock_writing_criterion_scores',
        ['submission_id'],
    )
    op.create_index(
        op.f('ix_vizu_mock_writing_criterion_scores_criterion_id'),
        'vizu_mock_writing_criterion_scores',
        ['criterion_id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('ix_vizu_mock_writing_criterion_scores_criterion_id'), table_name='vizu_mock_writing_criterion_scores'
    )
    op.drop_index(
        op.f('ix_vizu_mock_writing_criterion_scores_submission_id'), table_name='vizu_mock_writing_criterion_scores'
    )
    op.drop_table('vizu_mock_writing_criterion_scores')

    op.drop_index(op.f('ix_vizu_mock_writing_submissions_task_id'), table_name='vizu_mock_writing_submissions')
    op.drop_index(op.f('ix_vizu_mock_writing_submissions_attempt_id'), table_name='vizu_mock_writing_submissions')
    op.drop_table('vizu_mock_writing_submissions')

    op.drop_index(op.f('ix_vizu_mock_writing_rubric_criteria_task_id'), table_name='vizu_mock_writing_rubric_criteria')
    op.drop_table('vizu_mock_writing_rubric_criteria')

    op.drop_index(op.f('ix_vizu_mock_writing_tasks_level'), table_name='vizu_mock_writing_tasks')
    op.drop_table('vizu_mock_writing_tasks')

    op.drop_column('vizu_mock_attempts', 'schreiben_feedback')
    op.drop_column('vizu_mock_attempts', 'schreiben_submitted_at')
    op.drop_column('vizu_mock_attempts', 'schreiben_score')
