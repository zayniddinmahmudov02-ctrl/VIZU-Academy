"""bridge assessment engine to model test and add task status

Revision ID: d8f4805044a1
Revises: 4a0a651f65e1
Create Date: 2026-08-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8f4805044a1'
down_revision: Union[str, Sequence[str], None] = '4a0a651f65e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Both changes are purely additive (new nullable/defaulted columns) on
    tables that are empty in production (assessments, assessment_tasks —
    0 rows), so there is no data to migrate or risk of breaking existing
    rows. Nothing in Vorbereitung's own tables (certification_providers,
    mock_exam_levels, model_tests, kompetenzen, teile, *_content) is
    touched — the 170 existing ModelTests are unaffected.
    """
    op.add_column(
        'assessments',
        sa.Column('model_test_id', sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        'fk_assessments_model_test_id',
        'assessments', 'model_tests',
        ['model_test_id'], ['id'],
        ondelete='CASCADE',
    )
    op.create_index(op.f('ix_assessments_model_test_id'), 'assessments', ['model_test_id'], unique=False)

    op.add_column(
        'assessment_tasks',
        sa.Column('status', sa.String(length=20), server_default='DRAFT', nullable=False),
    )
    op.create_index(op.f('ix_assessment_tasks_status'), 'assessment_tasks', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_assessment_tasks_status'), table_name='assessment_tasks')
    op.drop_column('assessment_tasks', 'status')

    op.drop_index(op.f('ix_assessments_model_test_id'), table_name='assessments')
    op.drop_constraint('fk_assessments_model_test_id', 'assessments', type_='foreignkey')
    op.drop_column('assessments', 'model_test_id')
