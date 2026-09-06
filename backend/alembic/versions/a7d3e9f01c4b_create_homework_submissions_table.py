"""create homework_submissions table

Revision ID: a7d3e9f01c4b
Revises: f2a8c4d61b9e
Create Date: 2026-09-13 00:00:00.000000

Adds `homework_submissions` — one row per (student, homework), the
missing piece that made "review student homework" impossible until now
(the existing `homeworks` table only ever held the admin-authored task
definition, never a student's answer). Powers both the new student
submit flow (POST /homeworks/{id}/submissions) and the new Teacher Panel
grading flow (GET/PATCH /teacher/homework/...). Not backfilled — there is
no prior submission data anywhere to migrate.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a7d3e9f01c4b'
down_revision: Union[str, Sequence[str], None] = 'f2a8c4d61b9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'homework_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('homework_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=False, server_default=''),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='SUBMITTED'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('reviewed_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['homework_id'], ['homeworks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'homework_id', name='uq_homework_submission_student_homework'),
    )
    op.create_index(
        op.f('ix_homework_submissions_homework_id'),
        'homework_submissions',
        ['homework_id'],
    )
    op.create_index(
        op.f('ix_homework_submissions_student_id'),
        'homework_submissions',
        ['student_id'],
    )
    op.create_index(
        op.f('ix_homework_submissions_status'),
        'homework_submissions',
        ['status'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_homework_submissions_status'), table_name='homework_submissions')
    op.drop_index(op.f('ix_homework_submissions_student_id'), table_name='homework_submissions')
    op.drop_index(op.f('ix_homework_submissions_homework_id'), table_name='homework_submissions')
    op.drop_table('homework_submissions')
