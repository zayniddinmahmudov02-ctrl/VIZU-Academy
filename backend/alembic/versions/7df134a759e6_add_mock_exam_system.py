"""add mock exam system

Revision ID: 7df134a759e6
Revises: ba6cc6bc25d2
Create Date: 2026-08-02 20:16:32.228017

NOTE: this file started as an `alembic revision --autogenerate` output that
also picked up a large amount of unrelated schema drift against the live
DB (the same leftover legacy/Telegram-bot tables and dropped `users`
columns seen in earlier migrations in this project — e.g.
ba6cc6bc25d2_add_media_assets_table.py). None of that belongs to this
change and was manually stripped out; this migration only ever creates
the 15 new tables for the Phase 4 Mock Exam system.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7df134a759e6'
down_revision: Union[str, Sequence[str], None] = 'ba6cc6bc25d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('certification_providers',
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('code', sa.String(length=30), nullable=False),
    sa.Column('logo_url', sa.Text(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('color', sa.String(length=20), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code'),
    sa.UniqueConstraint('name')
    )
    op.create_table('mock_exam_levels',
    sa.Column('provider_id', sa.UUID(), nullable=False),
    sa.Column('level', sa.String(length=10), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['provider_id'], ['certification_providers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mock_exam_levels_provider_id'), 'mock_exam_levels', ['provider_id'], unique=False)
    op.create_table('model_tests',
    sa.Column('level_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), server_default='DRAFT', nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['level_id'], ['mock_exam_levels.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_tests_level_id'), 'model_tests', ['level_id'], unique=False)
    op.create_index(op.f('ix_model_tests_status'), 'model_tests', ['status'], unique=False)
    op.create_table('kompetenzen',
    sa.Column('model_test_id', sa.UUID(), nullable=False),
    sa.Column('type', sa.String(length=20), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('total_points', sa.Integer(), nullable=False),
    sa.Column('duration_minutes', sa.Integer(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['model_test_id'], ['model_tests.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kompetenzen_model_test_id'), 'kompetenzen', ['model_test_id'], unique=False)
    op.create_index(op.f('ix_kompetenzen_type'), 'kompetenzen', ['type'], unique=False)
    op.create_table('mock_test_attempts',
    sa.Column('model_test_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(length=20), server_default='IN_PROGRESS', nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('total_score', sa.Integer(), nullable=True),
    sa.Column('max_score', sa.Integer(), nullable=True),
    sa.Column('time_spent_seconds', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['model_test_id'], ['model_tests.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mock_test_attempts_model_test_id'), 'mock_test_attempts', ['model_test_id'], unique=False)
    op.create_index(op.f('ix_mock_test_attempts_user_id'), 'mock_test_attempts', ['user_id'], unique=False)
    op.create_table('teile',
    sa.Column('kompetenz_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('instructions', sa.Text(), nullable=True),
    sa.Column('points', sa.Integer(), nullable=False),
    sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['kompetenz_id'], ['kompetenzen.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_teile_kompetenz_id'), 'teile', ['kompetenz_id'], unique=False)
    op.create_table('listening_contents',
    sa.Column('teil_id', sa.UUID(), nullable=False),
    sa.Column('audio_url', sa.Text(), nullable=False),
    sa.Column('image_url', sa.Text(), nullable=True),
    sa.Column('transcript', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['teil_id'], ['teile.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_listening_contents_teil_id'), 'listening_contents', ['teil_id'], unique=True)
    op.create_table('reading_contents',
    sa.Column('teil_id', sa.UUID(), nullable=False),
    sa.Column('content_type', sa.String(length=20), server_default='TEXT', nullable=False),
    sa.Column('text', sa.Text(), nullable=True),
    sa.Column('image_url', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['teil_id'], ['teile.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reading_contents_teil_id'), 'reading_contents', ['teil_id'], unique=True)
    op.create_table('speaking_tasks',
    sa.Column('teil_id', sa.UUID(), nullable=False),
    sa.Column('task_text', sa.Text(), nullable=False),
    sa.Column('image_url', sa.Text(), nullable=True),
    sa.Column('preparation_time_seconds', sa.Integer(), nullable=False),
    sa.Column('speaking_time_seconds', sa.Integer(), nullable=False),
    sa.Column('max_recording_duration_seconds', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['teil_id'], ['teile.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_speaking_tasks_teil_id'), 'speaking_tasks', ['teil_id'], unique=True)
    op.create_table('writing_tasks',
    sa.Column('teil_id', sa.UUID(), nullable=False),
    sa.Column('task_text', sa.Text(), nullable=False),
    sa.Column('image_url', sa.Text(), nullable=True),
    sa.Column('reference_document_url', sa.Text(), nullable=True),
    sa.Column('word_limit', sa.Integer(), nullable=True),
    sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
    sa.Column('points', sa.Integer(), nullable=False),
    sa.Column('difficulty', sa.String(length=20), nullable=True),
    sa.Column('max_points', sa.Integer(), nullable=False),
    sa.Column('evaluation_rubric', sa.Text(), nullable=True),
    sa.Column('passing_score', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['teil_id'], ['teile.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_writing_tasks_teil_id'), 'writing_tasks', ['teil_id'], unique=True)
    op.create_table('mock_questions',
    sa.Column('reading_content_id', sa.UUID(), nullable=True),
    sa.Column('listening_content_id', sa.UUID(), nullable=True),
    sa.Column('question_type', sa.String(length=30), nullable=False),
    sa.Column('question_text', sa.Text(), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=True),
    sa.Column('correct_text_answer', sa.Text(), nullable=True),
    sa.Column('points', sa.Integer(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['listening_content_id'], ['listening_contents.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['reading_content_id'], ['reading_contents.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mock_questions_listening_content_id'), 'mock_questions', ['listening_content_id'], unique=False)
    op.create_index(op.f('ix_mock_questions_reading_content_id'), 'mock_questions', ['reading_content_id'], unique=False)
    op.create_table('mock_speaking_submissions',
    sa.Column('attempt_id', sa.UUID(), nullable=False),
    sa.Column('speaking_task_id', sa.UUID(), nullable=False),
    sa.Column('audio_url', sa.Text(), nullable=False),
    sa.Column('transcript', sa.Text(), nullable=True),
    sa.Column('ai_score', sa.Integer(), nullable=True),
    sa.Column('ai_feedback', sa.Text(), nullable=True),
    sa.Column('teacher_score', sa.Integer(), nullable=True),
    sa.Column('teacher_feedback', sa.Text(), nullable=True),
    sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['attempt_id'], ['mock_test_attempts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['speaking_task_id'], ['speaking_tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mock_speaking_submissions_attempt_id'), 'mock_speaking_submissions', ['attempt_id'], unique=False)
    op.create_index(op.f('ix_mock_speaking_submissions_speaking_task_id'), 'mock_speaking_submissions', ['speaking_task_id'], unique=False)
    op.create_table('mock_writing_submissions',
    sa.Column('attempt_id', sa.UUID(), nullable=False),
    sa.Column('writing_task_id', sa.UUID(), nullable=False),
    sa.Column('answer_text', sa.Text(), nullable=False),
    sa.Column('word_count', sa.Integer(), nullable=False),
    sa.Column('time_spent_seconds', sa.Integer(), nullable=False),
    sa.Column('ai_score', sa.Integer(), nullable=True),
    sa.Column('ai_grammar_score', sa.Integer(), nullable=True),
    sa.Column('ai_vocabulary_score', sa.Integer(), nullable=True),
    sa.Column('ai_structure_score', sa.Integer(), nullable=True),
    sa.Column('ai_task_achievement_score', sa.Integer(), nullable=True),
    sa.Column('ai_coherence_score', sa.Integer(), nullable=True),
    sa.Column('ai_feedback', sa.Text(), nullable=True),
    sa.Column('teacher_score', sa.Integer(), nullable=True),
    sa.Column('teacher_feedback', sa.Text(), nullable=True),
    sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['attempt_id'], ['mock_test_attempts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['writing_task_id'], ['writing_tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mock_writing_submissions_attempt_id'), 'mock_writing_submissions', ['attempt_id'], unique=False)
    op.create_index(op.f('ix_mock_writing_submissions_writing_task_id'), 'mock_writing_submissions', ['writing_task_id'], unique=False)
    op.create_table('mock_question_answers',
    sa.Column('attempt_id', sa.UUID(), nullable=False),
    sa.Column('question_id', sa.UUID(), nullable=False),
    sa.Column('answer_data', sa.Text(), nullable=True),
    sa.Column('is_correct', sa.Boolean(), nullable=True),
    sa.Column('points_earned', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['attempt_id'], ['mock_test_attempts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['question_id'], ['mock_questions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mock_question_answers_attempt_id'), 'mock_question_answers', ['attempt_id'], unique=False)
    op.create_index(op.f('ix_mock_question_answers_question_id'), 'mock_question_answers', ['question_id'], unique=False)
    op.create_table('mock_question_options',
    sa.Column('question_id', sa.UUID(), nullable=False),
    sa.Column('option_text', sa.String(length=1000), nullable=False),
    sa.Column('match_value', sa.String(length=500), nullable=True),
    sa.Column('is_correct', sa.Boolean(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['mock_questions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mock_question_options_question_id'), 'mock_question_options', ['question_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_mock_question_options_question_id'), table_name='mock_question_options')
    op.drop_table('mock_question_options')
    op.drop_index(op.f('ix_mock_question_answers_question_id'), table_name='mock_question_answers')
    op.drop_index(op.f('ix_mock_question_answers_attempt_id'), table_name='mock_question_answers')
    op.drop_table('mock_question_answers')
    op.drop_index(op.f('ix_mock_writing_submissions_writing_task_id'), table_name='mock_writing_submissions')
    op.drop_index(op.f('ix_mock_writing_submissions_attempt_id'), table_name='mock_writing_submissions')
    op.drop_table('mock_writing_submissions')
    op.drop_index(op.f('ix_mock_speaking_submissions_speaking_task_id'), table_name='mock_speaking_submissions')
    op.drop_index(op.f('ix_mock_speaking_submissions_attempt_id'), table_name='mock_speaking_submissions')
    op.drop_table('mock_speaking_submissions')
    op.drop_index(op.f('ix_mock_questions_reading_content_id'), table_name='mock_questions')
    op.drop_index(op.f('ix_mock_questions_listening_content_id'), table_name='mock_questions')
    op.drop_table('mock_questions')
    op.drop_index(op.f('ix_writing_tasks_teil_id'), table_name='writing_tasks')
    op.drop_table('writing_tasks')
    op.drop_index(op.f('ix_speaking_tasks_teil_id'), table_name='speaking_tasks')
    op.drop_table('speaking_tasks')
    op.drop_index(op.f('ix_reading_contents_teil_id'), table_name='reading_contents')
    op.drop_table('reading_contents')
    op.drop_index(op.f('ix_listening_contents_teil_id'), table_name='listening_contents')
    op.drop_table('listening_contents')
    op.drop_index(op.f('ix_teile_kompetenz_id'), table_name='teile')
    op.drop_table('teile')
    op.drop_index(op.f('ix_mock_test_attempts_user_id'), table_name='mock_test_attempts')
    op.drop_index(op.f('ix_mock_test_attempts_model_test_id'), table_name='mock_test_attempts')
    op.drop_table('mock_test_attempts')
    op.drop_index(op.f('ix_kompetenzen_type'), table_name='kompetenzen')
    op.drop_index(op.f('ix_kompetenzen_model_test_id'), table_name='kompetenzen')
    op.drop_table('kompetenzen')
    op.drop_index(op.f('ix_model_tests_status'), table_name='model_tests')
    op.drop_index(op.f('ix_model_tests_level_id'), table_name='model_tests')
    op.drop_table('model_tests')
    op.drop_index(op.f('ix_mock_exam_levels_provider_id'), table_name='mock_exam_levels')
    op.drop_table('mock_exam_levels')
    op.drop_table('certification_providers')
