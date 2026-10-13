"""VIZU LMS: competency counts on the lesson progress snapshot

student_progress.competencies_total / competencies_completed — written by
app.services.lms.progress.persist() next to lesson_completed, so the level
overview shows "3 / 7 Kompetenzen" and the same percent as the lesson page
without recomputing every lesson. Additive and reversible.

Revision ID: f3d9b2e7c4a1
Revises: e8b1f4c2a9d6
Create Date: 2026-10-13
"""

import sqlalchemy as sa

from alembic import op

revision = "f3d9b2e7c4a1"
down_revision = "e8b1f4c2a9d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("student_progress", sa.Column("competencies_total", sa.Integer(), nullable=True))
    op.add_column("student_progress", sa.Column("competencies_completed", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("student_progress", "competencies_completed")
    op.drop_column("student_progress", "competencies_total")
