"""create teacher_assignments table

Revision ID: f2a8c4d61b9e
Revises: b3c7f1a2d5e8
Create Date: 2026-09-06 00:00:00.000000

Adds `teacher_assignments` — scopes a TEACHER-role user to the course(s)
whose enrolled students they may see in the new Teacher Panel (GET
/teacher/students). Managed exclusively by a SUPER_ADMIN via
/admin/teacher-assignments; a teacher with no rows here sees an empty
student list rather than every student in the system. Not backfilled —
no existing TEACHER-role user is auto-assigned to any course.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f2a8c4d61b9e'
down_revision: Union[str, Sequence[str], None] = 'b3c7f1a2d5e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'teacher_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('teacher_id', 'course_id', name='uq_teacher_assignment_teacher_course'),
    )
    op.create_index(
        op.f('ix_teacher_assignments_teacher_id'),
        'teacher_assignments',
        ['teacher_id'],
    )
    op.create_index(
        op.f('ix_teacher_assignments_course_id'),
        'teacher_assignments',
        ['course_id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_teacher_assignments_course_id'), table_name='teacher_assignments')
    op.drop_index(op.f('ix_teacher_assignments_teacher_id'), table_name='teacher_assignments')
    op.drop_table('teacher_assignments')
