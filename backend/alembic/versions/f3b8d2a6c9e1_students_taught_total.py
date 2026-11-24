"""Teacher profile: `teacher_profiles.students_taught_total` — the teacher's own figure of students taught in the whole career.

Additive: one nullable integer column + CHECK `ck_teacher_profiles_students_taught` (0 … 1 000 000). Existing rows stay NULL (not
entered). The VIZU numbers on the profile are still computed from the database; this figure is shown next to them as
teacher-reported and never below the VIZU total.

Downgrade: drops the check and the column (the entered figures are lost).

Revision ID: f3b8d2a6c9e1
Revises: e2a7c4f9b1d3
Create Date: 2026-11-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f3b8d2a6c9e1"
down_revision: Union[str, Sequence[str], None] = "e2a7c4f9b1d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("teacher_profiles", sa.Column("students_taught_total", sa.Integer(), nullable=True))
    op.create_check_constraint("ck_teacher_profiles_students_taught", "teacher_profiles",
                               "students_taught_total IS NULL OR students_taught_total BETWEEN 0 AND 1000000")


def downgrade() -> None:
    op.drop_constraint("ck_teacher_profiles_students_taught", "teacher_profiles", type_="check")
    op.drop_column("teacher_profiles", "students_taught_total")
