"""extend student_writings/student_speakings for real submissions

Revision ID: c9e4f2b8a1d7
Revises: a7d3e9f01c4b
Create Date: 2026-09-20 00:00:00.000000

Turns the two existing-but-unused StudentWriting/StudentSpeaking tables
into a real submission workflow for the legacy Schreiben/Sprechen lesson
content (writings/speakings), instead of creating a third pair of
parallel tables. Per-table changes:

student_writings — adds submitted_at/score/feedback/reviewed_by_id/
reviewed_at (a teacher-grading pass this table never had). The existing
status column is reused as-is (was a free string defaulting to
"pending"; the app now writes DRAFT/SUBMITTED/GRADED/NEEDS_REVISION —
no column change needed for that).

student_speakings — adds the same grading columns, PLUS `user_id`
(this table had NO way to record which student a row belongs to at
all — its own API router already assumed `item.user_id` existed and
would have crashed the instant it was actually called; this was a
real, previously-undiscovered gap, not a design choice being reversed)
and the real recording metadata (storage_path/filename/content_type/
duration_seconds/file_size_bytes) a private-storage audio upload needs.
`audio_url` (NOT NULL today) is relaxed to nullable since new rows use
storage_path instead — nothing has ever successfully written a row here
to migrate (see user_id above), so there is no existing data to reconcile.

Both new `user_id`/`reviewed_by_id` FKs are nullable — neither table is
known to be empty in every environment this runs against, and a nullable
add is always safe regardless of row count.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c9e4f2b8a1d7'
down_revision: Union[str, Sequence[str], None] = 'a7d3e9f01c4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # student_writings
    op.add_column('student_writings', sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('student_writings', sa.Column('score', sa.Integer(), nullable=True))
    op.add_column('student_writings', sa.Column('feedback', sa.Text(), nullable=True))
    op.add_column('student_writings', sa.Column('reviewed_by_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('student_writings', sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        'fk_student_writings_reviewed_by_id_users',
        'student_writings', 'users', ['reviewed_by_id'], ['id'], ondelete='SET NULL',
    )

    # student_speakings
    op.add_column('student_speakings', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_student_speakings_user_id_users',
        'student_speakings', 'users', ['user_id'], ['id'], ondelete='CASCADE',
    )
    op.create_index(op.f('ix_student_speakings_user_id'), 'student_speakings', ['user_id'])

    op.alter_column('student_speakings', 'audio_url', existing_type=sa.String(length=500), nullable=True)
    op.add_column('student_speakings', sa.Column('storage_path', sa.String(length=500), nullable=True))
    op.add_column('student_speakings', sa.Column('filename', sa.String(length=255), nullable=True))
    op.add_column('student_speakings', sa.Column('content_type', sa.String(length=100), nullable=True))
    op.add_column('student_speakings', sa.Column('duration_seconds', sa.Integer(), nullable=True))
    op.add_column('student_speakings', sa.Column('file_size_bytes', sa.Integer(), nullable=True))
    op.add_column('student_speakings', sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('student_speakings', sa.Column('score', sa.Integer(), nullable=True))
    op.add_column('student_speakings', sa.Column('feedback', sa.Text(), nullable=True))
    op.add_column('student_speakings', sa.Column('reviewed_by_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('student_speakings', sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        'fk_student_speakings_reviewed_by_id_users',
        'student_speakings', 'users', ['reviewed_by_id'], ['id'], ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_student_speakings_reviewed_by_id_users', 'student_speakings', type_='foreignkey')
    op.drop_column('student_speakings', 'reviewed_at')
    op.drop_column('student_speakings', 'reviewed_by_id')
    op.drop_column('student_speakings', 'feedback')
    op.drop_column('student_speakings', 'score')
    op.drop_column('student_speakings', 'submitted_at')
    op.drop_column('student_speakings', 'file_size_bytes')
    op.drop_column('student_speakings', 'duration_seconds')
    op.drop_column('student_speakings', 'content_type')
    op.drop_column('student_speakings', 'filename')
    op.drop_column('student_speakings', 'storage_path')
    op.alter_column('student_speakings', 'audio_url', existing_type=sa.String(length=500), nullable=False)
    op.drop_index(op.f('ix_student_speakings_user_id'), table_name='student_speakings')
    op.drop_constraint('fk_student_speakings_user_id_users', 'student_speakings', type_='foreignkey')
    op.drop_column('student_speakings', 'user_id')

    op.drop_constraint('fk_student_writings_reviewed_by_id_users', 'student_writings', type_='foreignkey')
    op.drop_column('student_writings', 'reviewed_at')
    op.drop_column('student_writings', 'reviewed_by_id')
    op.drop_column('student_writings', 'feedback')
    op.drop_column('student_writings', 'score')
    op.drop_column('student_writings', 'submitted_at')
