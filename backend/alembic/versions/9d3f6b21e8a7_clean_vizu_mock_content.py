"""clean all legacy VIZU-Mock content (VIZU-Multilevel starts empty)

Revision ID: 9d3f6b21e8a7
Revises: 7c1e5a90d2b4
Create Date: 2026-10-02 00:00:01.000000

Data-only migration. Removes every row of the old VIZU-Mock system so
VIZU-Multilevel starts with ZERO questions/tasks/attempts, while keeping
the table structure. Deletion is done child-first, table by table, so it
never depends on ON DELETE CASCADE being present; and it touches ONLY
tables that are owned exclusively by VIZU-Mock/Multilevel (verified from
the models: nothing outside this module references them except the
`certificates` table, handled below). Idempotent: re-running deletes
nothing further.

Certificates are a SHARED table (COURSE / VORBEREITUNG / VIZU_MOCK
sources). Only rows with source = 'VIZU_MOCK' (the old VIZU-Mock system's
certificates) are removed; COURSE and VORBEREITUNG certificates are not
touched.

Not reversible: the deleted content cannot be restored by a downgrade.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "9d3f6b21e8a7"
down_revision: Union[str, None] = "7c1e5a90d2b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Child -> parent order.
_VIZU_ONLY_TABLES = (
    "vizu_mock_writing_criterion_scores",
    "vizu_mock_writing_submissions",
    "vizu_multilevel_speaking_submissions",
    "vizu_mock_answers",
    "vizu_mock_audios",
    "vizu_mock_options",
    "vizu_mock_questions",
    "vizu_mock_tasks",
    "vizu_mock_writing_rubric_criteria",
    "vizu_mock_writing_tasks",
    "vizu_multilevel_speaking_tasks",
    "vizu_mock_attempts",
    "vizu_multilevel_discarded_attempts",
)


def upgrade() -> None:
    op.execute("DELETE FROM certificates WHERE source = 'VIZU_MOCK'")
    for table in _VIZU_ONLY_TABLES:
        op.execute(f"DELETE FROM {table}")


def downgrade() -> None:
    # Deleted content cannot be restored.
    pass
