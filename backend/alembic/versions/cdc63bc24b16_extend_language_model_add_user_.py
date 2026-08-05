"""extend language model, add user_languages and language_settings

Revision ID: cdc63bc24b16
Revises: e975c352b402
Create Date: 2026-08-05 10:53:31.054347

Manually stripped of autogenerate's legacy-drift noise (drops of unrelated
Telegram-bot-era tables/columns) — same pattern as every other migration in
this project, see 7df134a759e6's docstring. Contains ONLY the Language
Management module's intended changes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cdc63bc24b16'
down_revision: Union[str, Sequence[str], None] = 'e975c352b402'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # locale starts nullable so existing rows (this project's dev DB already
    # has more than one language row) can be safely backfilled per-row
    # before the NOT NULL + unique constraints are applied, rather than
    # colliding on a single hardcoded default value.
    op.add_column('languages', sa.Column('locale', sa.String(length=20), nullable=True))
    op.add_column('languages', sa.Column('native_name', sa.String(length=100), nullable=True))
    op.add_column('languages', sa.Column('english_name', sa.String(length=100), nullable=True))
    op.add_column('languages', sa.Column('flag_file', sa.String(length=255), nullable=True))
    op.add_column('languages', sa.Column('primary_color', sa.String(length=20), nullable=True))
    op.add_column('languages', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('languages', sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('languages', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('languages', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # `code` is already unique (pre-existing plain constraint, replaced by a
    # partial index below), so backfilling locale from it guarantees no
    # collision regardless of how many rows already exist. Anything that
    # needs a real BCP-47 locale (not just its code) gets fixed by the
    # app-level seed/update step afterward.
    op.execute("UPDATE languages SET locale = code WHERE locale IS NULL")
    op.alter_column('languages', 'locale', nullable=False)

    # server_default above only exists to backfill existing rows without a
    # NOT NULL failure — drop it so future inserts must pass these
    # explicitly, matching the model (no Python-side default either).
    op.alter_column('languages', 'is_default', server_default=None)
    op.alter_column('languages', 'sort_order', server_default=None)

    # Plain UNIQUE(code) predates this migration and, combined with the new
    # soft-delete column, would permanently block re-using a code/locale
    # after its language is soft-deleted. Replace both with partial unique
    # indexes scoped to "still exists" — the correct way to combine unique
    # constraints with soft delete.
    op.drop_constraint('languages_code_key', 'languages', type_='unique')
    op.create_index(
        'uq_languages_code_active', 'languages', ['code'], unique=True,
        postgresql_where=sa.text('deleted_at IS NULL'),
    )
    op.create_index(
        'uq_languages_locale_active', 'languages', ['locale'], unique=True,
        postgresql_where=sa.text('deleted_at IS NULL'),
    )

    op.create_index('ix_languages_is_active', 'languages', ['is_active'])
    op.create_index('ix_languages_deleted_at', 'languages', ['deleted_at'])
    op.create_index('ix_languages_sort_order', 'languages', ['sort_order'])

    op.drop_column('languages', 'flag')

    op.create_table(
        'language_settings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('language_id', sa.UUID(), nullable=False),
        sa.Column('certificates_enabled', sa.Boolean(), nullable=False),
        sa.Column('leaderboard_enabled', sa.Boolean(), nullable=False),
        sa.Column('vocabulary_enabled', sa.Boolean(), nullable=False),
        sa.Column('grammar_enabled', sa.Boolean(), nullable=False),
        sa.Column('reading_enabled', sa.Boolean(), nullable=False),
        sa.Column('listening_enabled', sa.Boolean(), nullable=False),
        sa.Column('writing_enabled', sa.Boolean(), nullable=False),
        sa.Column('speaking_enabled', sa.Boolean(), nullable=False),
        sa.Column('homework_enabled', sa.Boolean(), nullable=False),
        sa.Column('quiz_enabled', sa.Boolean(), nullable=False),
        sa.Column('ai_writing_enabled', sa.Boolean(), nullable=False),
        sa.Column('ai_speaking_enabled', sa.Boolean(), nullable=False),
        sa.Column('mock_exams_enabled', sa.Boolean(), nullable=False),
        sa.Column('video_lessons_enabled', sa.Boolean(), nullable=False),
        sa.Column('media_library_enabled', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['language_id'], ['languages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('language_id'),
    )

    op.create_table(
        'user_languages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('language_id', sa.UUID(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['language_id'], ['languages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'language_id', name='uq_user_languages_user_language'),
    )
    op.create_index('ix_user_languages_user_id', 'user_languages', ['user_id'])
    op.create_index('ix_user_languages_language_id', 'user_languages', ['language_id'])


def downgrade() -> None:
    op.drop_index('ix_user_languages_language_id', table_name='user_languages')
    op.drop_index('ix_user_languages_user_id', table_name='user_languages')
    op.drop_table('user_languages')
    op.drop_table('language_settings')

    op.add_column('languages', sa.Column('flag', sa.String(length=255), nullable=True))
    op.drop_index('ix_languages_sort_order', table_name='languages')
    op.drop_index('ix_languages_deleted_at', table_name='languages')
    op.drop_index('ix_languages_is_active', table_name='languages')
    op.drop_index('uq_languages_locale_active', table_name='languages', postgresql_where=sa.text('deleted_at IS NULL'))
    op.drop_index('uq_languages_code_active', table_name='languages', postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_unique_constraint('languages_code_key', 'languages', ['code'])
    op.drop_column('languages', 'deleted_at')
    op.drop_column('languages', 'sort_order')
    op.drop_column('languages', 'is_default')
    op.drop_column('languages', 'description')
    op.drop_column('languages', 'primary_color')
    op.drop_column('languages', 'flag_file')
    op.drop_column('languages', 'english_name')
    op.drop_column('languages', 'native_name')
    op.drop_column('languages', 'locale')
