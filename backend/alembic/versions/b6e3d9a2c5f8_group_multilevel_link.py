"""Multilevel groups: `study_groups.mock_exam_level_id`.

Additive: one nullable UUID column (FK mock_exam_levels.id ON DELETE SET NULL) + its index. A group linked to the Vorbereitung level
"Multilevel B1–C1" works with its Modelltests: the teacher sees the members' results, active student members may take the tests without
the Multilevel Premium (owner decision 2026-11-28). Existing groups stay NULL (course groups as before).

Downgrade: drops the index and the column (the links are lost; group members then need the Premium again).

Revision ID: b6e3d9a2c5f8
Revises: a4c9e1f7b2d6
Create Date: 2026-11-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b6e3d9a2c5f8"
down_revision: Union[str, Sequence[str], None] = "a4c9e1f7b2d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("study_groups", sa.Column("mock_exam_level_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_study_groups_mock_exam_level_id", "study_groups", "mock_exam_levels", ["mock_exam_level_id"], ["id"],
                          ondelete="SET NULL")
    op.create_index("ix_study_groups_mock_exam_level_id", "study_groups", ["mock_exam_level_id"])


def downgrade() -> None:
    op.drop_index("ix_study_groups_mock_exam_level_id", table_name="study_groups")
    op.drop_constraint("fk_study_groups_mock_exam_level_id", "study_groups", type_="foreignkey")
    op.drop_column("study_groups", "mock_exam_level_id")
