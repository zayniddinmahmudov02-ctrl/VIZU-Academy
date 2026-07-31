"""fk cascade and unique constraints

Revision ID: a3f5c9e1b7d4
Revises: f7a8b9c0d1e2
Create Date: 2026-07-31 00:00:00.000000

Two independent integrity fixes found during the Super Admin Panel audit:

1. `courses.language_id`, `modules.course_id`, `lessons.module_id` were the
   only gap in an otherwise-consistent CASCADE chain — everything hanging
   off `lessons` (videos, vocabularies, grammars, ...) already cascades on
   delete, but deleting a Language/Course/Module directly would previously
   hit an FK violation (or orphan rows, depending on how it was deleted)
   instead of cleanly cascading. This migration re-creates those three FKs
   with `ondelete=CASCADE`.

2. `enrollments` and `student_progress` had no unique constraint on their
   natural key, allowing duplicate (user, course) / (user, lesson) rows.
   `video_progress` already has the equivalent constraint as the correct
   reference pattern this migration brings the other two in line with.
   Verified against the live database before writing this migration: zero
   duplicate rows exist today, so no data cleanup step is needed.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a3f5c9e1b7d4'
down_revision: Union[str, Sequence[str], None] = 'f7a8b9c0d1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('courses_language_id_fkey', 'courses', type_='foreignkey')
    op.create_foreign_key(
        'courses_language_id_fkey',
        'courses',
        'languages',
        ['language_id'],
        ['id'],
        ondelete='CASCADE',
    )

    op.drop_constraint('modules_course_id_fkey', 'modules', type_='foreignkey')
    op.create_foreign_key(
        'modules_course_id_fkey',
        'modules',
        'courses',
        ['course_id'],
        ['id'],
        ondelete='CASCADE',
    )

    op.drop_constraint('lessons_module_id_fkey', 'lessons', type_='foreignkey')
    op.create_foreign_key(
        'lessons_module_id_fkey',
        'lessons',
        'modules',
        ['module_id'],
        ['id'],
        ondelete='CASCADE',
    )

    op.create_unique_constraint(
        'uq_enrollments_user_course',
        'enrollments',
        ['user_id', 'course_id'],
    )

    op.create_unique_constraint(
        'uq_student_progress_user_lesson',
        'student_progress',
        ['user_id', 'lesson_id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_student_progress_user_lesson', 'student_progress', type_='unique')
    op.drop_constraint('uq_enrollments_user_course', 'enrollments', type_='unique')

    op.drop_constraint('lessons_module_id_fkey', 'lessons', type_='foreignkey')
    op.create_foreign_key(
        'lessons_module_id_fkey',
        'lessons',
        'modules',
        ['module_id'],
        ['id'],
    )

    op.drop_constraint('modules_course_id_fkey', 'modules', type_='foreignkey')
    op.create_foreign_key(
        'modules_course_id_fkey',
        'modules',
        'courses',
        ['course_id'],
        ['id'],
    )

    op.drop_constraint('courses_language_id_fkey', 'courses', type_='foreignkey')
    op.create_foreign_key(
        'courses_language_id_fkey',
        'courses',
        'languages',
        ['language_id'],
        ['id'],
    )
