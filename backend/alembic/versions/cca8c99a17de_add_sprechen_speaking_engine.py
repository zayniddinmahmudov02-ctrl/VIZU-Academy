"""add_sprechen_speaking_engine

Revision ID: cca8c99a17de
Revises: 7a643561363c
Create Date: 2026-08-10 15:10:11.149382

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cca8c99a17de'
down_revision: Union[str, Sequence[str], None] = '7a643561363c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'speaking_submissions',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('assessment_id', sa.UUID(), nullable=False),
        sa.Column('section_id', sa.UUID(), nullable=False),
        sa.Column('task_id', sa.UUID(), nullable=False),
        sa.Column('attempt_id', sa.UUID(), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('format', sa.String(length=10), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='PENDING_REVIEW', nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
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
        sa.UniqueConstraint('attempt_id', 'task_id', name='uq_speaking_submission_attempt_task'),
    )
    op.create_index(op.f('ix_speaking_submissions_assessment_id'), 'speaking_submissions', ['assessment_id'], unique=False)
    op.create_index(op.f('ix_speaking_submissions_attempt_id'), 'speaking_submissions', ['attempt_id'], unique=False)
    op.create_index(op.f('ix_speaking_submissions_status'), 'speaking_submissions', ['status'], unique=False)
    op.create_index(op.f('ix_speaking_submissions_task_id'), 'speaking_submissions', ['task_id'], unique=False)
    op.create_index(op.f('ix_speaking_submissions_user_id'), 'speaking_submissions', ['user_id'], unique=False)

    op.create_table(
        'speaking_evaluations',
        sa.Column('submission_id', sa.UUID(), nullable=False),
        sa.Column('reviewed_by_id', sa.UUID(), nullable=True),
        sa.Column('rubric_scores', sa.Text(), nullable=True),
        sa.Column('total_score', sa.Integer(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['submission_id'], ['speaking_submissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_speaking_evaluations_submission_id'), 'speaking_evaluations', ['submission_id'], unique=False)

    op.add_column('assessment_tasks', sa.Column('prep_seconds', sa.Integer(), nullable=True))
    op.add_column('assessment_tasks', sa.Column('speak_seconds', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('assessment_tasks', 'speak_seconds')
    op.drop_column('assessment_tasks', 'prep_seconds')

    op.drop_index(op.f('ix_speaking_evaluations_submission_id'), table_name='speaking_evaluations')
    op.drop_table('speaking_evaluations')

    op.drop_index(op.f('ix_speaking_submissions_user_id'), table_name='speaking_submissions')
    op.drop_index(op.f('ix_speaking_submissions_task_id'), table_name='speaking_submissions')
    op.drop_index(op.f('ix_speaking_submissions_status'), table_name='speaking_submissions')
    op.drop_index(op.f('ix_speaking_submissions_attempt_id'), table_name='speaking_submissions')
    op.drop_index(op.f('ix_speaking_submissions_assessment_id'), table_name='speaking_submissions')
    op.drop_table('speaking_submissions')
