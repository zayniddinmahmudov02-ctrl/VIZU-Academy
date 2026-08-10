"""add_schreiben_writing_engine

Revision ID: 7a643561363c
Revises: bad96c1fb729
Create Date: 2026-08-10 14:19:29.706891

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7a643561363c'
down_revision: Union[str, Sequence[str], None] = 'bad96c1fb729'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'writing_rubric_criteria',
        sa.Column('task_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('max_score', sa.Integer(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['assessment_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_writing_rubric_criteria_task_id'), 'writing_rubric_criteria', ['task_id'], unique=False)

    op.create_table(
        'writing_submissions',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('assessment_id', sa.UUID(), nullable=False),
        sa.Column('section_id', sa.UUID(), nullable=False),
        sa.Column('task_id', sa.UUID(), nullable=False),
        sa.Column('attempt_id', sa.UUID(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=False),
        sa.Column('character_count', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='DRAFT', nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('final_score', sa.Integer(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['attempt_id'], ['assessment_attempts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['section_id'], ['assessment_sections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['assessment_tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('attempt_id', 'task_id', name='uq_writing_submission_attempt_task'),
    )
    op.create_index(op.f('ix_writing_submissions_assessment_id'), 'writing_submissions', ['assessment_id'], unique=False)
    op.create_index(op.f('ix_writing_submissions_attempt_id'), 'writing_submissions', ['attempt_id'], unique=False)
    op.create_index(op.f('ix_writing_submissions_status'), 'writing_submissions', ['status'], unique=False)
    op.create_index(op.f('ix_writing_submissions_task_id'), 'writing_submissions', ['task_id'], unique=False)
    op.create_index(op.f('ix_writing_submissions_user_id'), 'writing_submissions', ['user_id'], unique=False)

    op.create_table(
        'writing_evaluations',
        sa.Column('submission_id', sa.UUID(), nullable=False),
        sa.Column('evaluator_type', sa.String(length=10), nullable=False),
        sa.Column('reviewed_by_id', sa.UUID(), nullable=True),
        sa.Column('rubric_scores', sa.Text(), nullable=True),
        sa.Column('total_score', sa.Integer(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('strengths', sa.Text(), nullable=True),
        sa.Column('errors', sa.Text(), nullable=True),
        sa.Column('suggestions', sa.Text(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['submission_id'], ['writing_submissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_writing_evaluations_submission_id'), 'writing_evaluations', ['submission_id'], unique=False)

    op.add_column('assessment_tasks', sa.Column('image_url', sa.String(length=500), nullable=True))
    op.add_column('assessment_tasks', sa.Column('min_words', sa.Integer(), nullable=True))
    op.add_column('assessment_tasks', sa.Column('max_words', sa.Integer(), nullable=True))
    op.add_column('assessment_tasks', sa.Column('time_limit_minutes', sa.Integer(), nullable=True))
    op.add_column(
        'assessment_tasks',
        sa.Column('evaluation_mode', sa.String(length=20), server_default='AI_ONLY', nullable=False),
    )


def downgrade() -> None:
    op.drop_column('assessment_tasks', 'evaluation_mode')
    op.drop_column('assessment_tasks', 'time_limit_minutes')
    op.drop_column('assessment_tasks', 'max_words')
    op.drop_column('assessment_tasks', 'min_words')
    op.drop_column('assessment_tasks', 'image_url')

    op.drop_index(op.f('ix_writing_evaluations_submission_id'), table_name='writing_evaluations')
    op.drop_table('writing_evaluations')

    op.drop_index(op.f('ix_writing_submissions_user_id'), table_name='writing_submissions')
    op.drop_index(op.f('ix_writing_submissions_task_id'), table_name='writing_submissions')
    op.drop_index(op.f('ix_writing_submissions_status'), table_name='writing_submissions')
    op.drop_index(op.f('ix_writing_submissions_attempt_id'), table_name='writing_submissions')
    op.drop_index(op.f('ix_writing_submissions_assessment_id'), table_name='writing_submissions')
    op.drop_table('writing_submissions')

    op.drop_index(op.f('ix_writing_rubric_criteria_task_id'), table_name='writing_rubric_criteria')
    op.drop_table('writing_rubric_criteria')
