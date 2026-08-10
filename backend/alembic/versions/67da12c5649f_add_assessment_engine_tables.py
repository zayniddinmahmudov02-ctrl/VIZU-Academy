"""add assessment engine tables

Revision ID: 67da12c5649f
Revises: 32bad8669352
Create Date: 2026-08-10 10:37:46.523785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '67da12c5649f'
down_revision: Union[str, Sequence[str], None] = '32bad8669352'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('assessments',
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('assessment_type', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), server_default='DRAFT', nullable=False),
    sa.Column('lesson_id', sa.UUID(), nullable=True),
    sa.Column('language_id', sa.UUID(), nullable=True),
    sa.Column('level', sa.String(length=20), nullable=True),
    sa.Column('created_by_id', sa.UUID(), nullable=True),
    sa.Column('attempt_limit', sa.Integer(), nullable=True),
    sa.Column('allow_retry', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('allow_edit', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('allow_resubmit', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('show_correct_answers', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('show_score', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('show_feedback', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['language_id'], ['languages.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assessments_assessment_type'), 'assessments', ['assessment_type'], unique=False)
    op.create_index(op.f('ix_assessments_language_id'), 'assessments', ['language_id'], unique=False)
    op.create_index(op.f('ix_assessments_lesson_id'), 'assessments', ['lesson_id'], unique=False)
    op.create_index(op.f('ix_assessments_status'), 'assessments', ['status'], unique=False)
    op.create_table('assessment_attempts',
    sa.Column('assessment_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(length=20), server_default='IN_PROGRESS', nullable=False),
    sa.Column('attempt_number', sa.Integer(), nullable=False),
    sa.Column('locked', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assessment_attempts_assessment_id'), 'assessment_attempts', ['assessment_id'], unique=False)
    op.create_index(op.f('ix_assessment_attempts_user_id'), 'assessment_attempts', ['user_id'], unique=False)
    op.create_table('assessment_sections',
    sa.Column('assessment_id', sa.UUID(), nullable=False),
    sa.Column('skill', sa.String(length=20), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('instructions', sa.Text(), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assessment_sections_assessment_id'), 'assessment_sections', ['assessment_id'], unique=False)
    op.create_index(op.f('ix_assessment_sections_skill'), 'assessment_sections', ['skill'], unique=False)
    op.create_table('assessment_results',
    sa.Column('assessment_attempt_id', sa.UUID(), nullable=False),
    sa.Column('total_score', sa.Integer(), nullable=False),
    sa.Column('max_score', sa.Integer(), nullable=False),
    sa.Column('percentage', sa.Float(), nullable=False),
    sa.Column('graded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['assessment_attempt_id'], ['assessment_attempts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assessment_results_assessment_attempt_id'), 'assessment_results', ['assessment_attempt_id'], unique=True)
    op.create_table('assessment_tasks',
    sa.Column('section_id', sa.UUID(), nullable=False),
    sa.Column('task_type', sa.String(length=30), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('instructions', sa.Text(), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('config', sa.Text(), nullable=True),
    sa.Column('max_points', sa.Integer(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['section_id'], ['assessment_sections.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assessment_tasks_section_id'), 'assessment_tasks', ['section_id'], unique=False)
    op.create_index(op.f('ix_assessment_tasks_task_type'), 'assessment_tasks', ['task_type'], unique=False)
    op.create_table('section_results',
    sa.Column('assessment_attempt_id', sa.UUID(), nullable=False),
    sa.Column('section_id', sa.UUID(), nullable=False),
    sa.Column('section_score', sa.Integer(), nullable=False),
    sa.Column('max_section_score', sa.Integer(), nullable=False),
    sa.Column('percentage', sa.Float(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['assessment_attempt_id'], ['assessment_attempts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['section_id'], ['assessment_sections.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_section_results_assessment_attempt_id'), 'section_results', ['assessment_attempt_id'], unique=False)
    op.create_index(op.f('ix_section_results_section_id'), 'section_results', ['section_id'], unique=False)
    op.create_table('task_attempts',
    sa.Column('assessment_attempt_id', sa.UUID(), nullable=False),
    sa.Column('task_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(length=20), server_default='IN_PROGRESS', nullable=False),
    sa.Column('score', sa.Integer(), nullable=False),
    sa.Column('max_score', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['assessment_attempt_id'], ['assessment_attempts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['task_id'], ['assessment_tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_attempts_assessment_attempt_id'), 'task_attempts', ['assessment_attempt_id'], unique=False)
    op.create_index(op.f('ix_task_attempts_task_id'), 'task_attempts', ['task_id'], unique=False)
    op.create_table('task_questions',
    sa.Column('task_id', sa.UUID(), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=False),
    sa.Column('correct_text_answer', sa.Text(), nullable=True),
    sa.Column('alternative_answers', sa.Text(), nullable=True),
    sa.Column('case_sensitive', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('points', sa.Integer(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['task_id'], ['assessment_tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_questions_task_id'), 'task_questions', ['task_id'], unique=False)
    op.create_table('answers',
    sa.Column('task_attempt_id', sa.UUID(), nullable=False),
    sa.Column('question_id', sa.UUID(), nullable=False),
    sa.Column('answer_data', sa.Text(), nullable=True),
    sa.Column('is_correct', sa.Boolean(), nullable=True),
    sa.Column('points_earned', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['task_questions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['task_attempt_id'], ['task_attempts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_answers_question_id'), 'answers', ['question_id'], unique=False)
    op.create_index(op.f('ix_answers_task_attempt_id'), 'answers', ['task_attempt_id'], unique=False)
    op.create_table('task_options',
    sa.Column('question_id', sa.UUID(), nullable=False),
    sa.Column('option_text', sa.String(length=1000), nullable=False),
    sa.Column('match_value', sa.String(length=500), nullable=True),
    sa.Column('is_correct', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['task_questions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_options_question_id'), 'task_options', ['question_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('task_options')
    op.drop_table('answers')
    op.drop_table('task_questions')
    op.drop_table('task_attempts')
    op.drop_table('section_results')
    op.drop_table('assessment_tasks')
    op.drop_table('assessment_results')
    op.drop_table('assessment_sections')
    op.drop_table('assessment_attempts')
    op.drop_table('assessments')
