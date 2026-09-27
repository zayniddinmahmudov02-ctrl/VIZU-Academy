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

IDEMPOTENCY: at least one production database already has
student_speakings.user_id (plus a FK named "student_speakings_user_id_
fkey" and an index named "ix_student_speakings_user_id") and
student_writings.user_id/its FK/its index — none of those were created
by this migration (student_writings.user_id predates it entirely; the
student_speakings trio was evidently added out-of-band before this
migration first ran there), but Alembic still recorded this revision as
not-yet-applied for that database, so a plain re-run hit DuplicateColumn
on the very first `add_column`. Every operation below is now written to
check for the target object first (columns via "ADD COLUMN IF NOT
EXISTS", indexes via "CREATE INDEX IF NOT EXISTS", FK constraints via an
information_schema lookup keyed on the column — not a fixed constraint
name, since the pre-existing FKs use Postgres's own default naming, not
this file's) — so running this migration is safe whether a given object
already exists (in any of these databases) or not, and never drops or
recreates anything that's already there.
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


def _add_foreign_key_if_missing(
    constraint_name: str,
    source_table: str,
    column: str,
    referent_table: str,
    referent_column: str,
    ondelete: str,
) -> None:
    """Adds the FK only if no foreign key already exists on `column` —
    checked by column, not by `constraint_name`, since a pre-existing FK
    on that column (e.g. Postgres's own default-named
    "student_speakings_user_id_fkey") must block a second, redundant FK
    on the same column just as much as one already carrying this exact
    name would."""
    op.execute(
        sa.text(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.table_schema = current_schema()
                        AND tc.table_name = '{source_table}'
                        AND tc.constraint_type = 'FOREIGN KEY'
                        AND kcu.column_name = '{column}'
                ) THEN
                    ALTER TABLE {source_table}
                    ADD CONSTRAINT {constraint_name}
                    FOREIGN KEY ({column}) REFERENCES {referent_table} ({referent_column})
                    ON DELETE {ondelete};
                END IF;
            END $$;
            """
        )
    )


def _drop_foreign_key_if_present(source_table: str, column: str) -> None:
    """Downgrade counterpart of _add_foreign_key_if_missing — drops
    whatever FK constraint currently exists on `column` (this file's own
    name, or a pre-existing differently-named one), by name, looked up
    the same way. A no-op if none exists."""
    op.execute(
        sa.text(
            f"""
            DO $$
            DECLARE
                fk_name text;
            BEGIN
                SELECT tc.constraint_name INTO fk_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.table_schema = current_schema()
                    AND tc.table_name = '{source_table}'
                    AND tc.constraint_type = 'FOREIGN KEY'
                    AND kcu.column_name = '{column}'
                LIMIT 1;

                IF fk_name IS NOT NULL THEN
                    EXECUTE format('ALTER TABLE {source_table} DROP CONSTRAINT %I', fk_name);
                END IF;
            END $$;
            """
        )
    )


def _set_column_nullable_if_needed(table: str, column: str, nullable: bool) -> None:
    """Only touches the column if it exists and its current nullability
    doesn't already match — makes both directions (upgrade's "relax to
    nullable" and downgrade's "restore NOT NULL") safe to re-run and safe
    against a column that was already changed out-of-band."""
    target = "TRUE" if nullable else "FALSE"
    drop_or_set = "DROP NOT NULL" if nullable else "SET NOT NULL"
    op.execute(
        sa.text(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = current_schema()
                        AND table_name = '{table}'
                        AND column_name = '{column}'
                        AND (is_nullable = 'YES') IS DISTINCT FROM {target}
                ) THEN
                    ALTER TABLE {table} ALTER COLUMN {column} {drop_or_set};
                END IF;
            END $$;
            """
        )
    )


def upgrade() -> None:
    """Upgrade schema."""
    # student_writings — new grading columns only; user_id/its FK/index
    # predate this migration entirely (original table shape) and are
    # never touched here.
    op.execute("ALTER TABLE student_writings ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMPTZ")
    op.execute("ALTER TABLE student_writings ADD COLUMN IF NOT EXISTS score INTEGER")
    op.execute("ALTER TABLE student_writings ADD COLUMN IF NOT EXISTS feedback TEXT")
    op.execute("ALTER TABLE student_writings ADD COLUMN IF NOT EXISTS reviewed_by_id UUID")
    op.execute("ALTER TABLE student_writings ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ")
    _add_foreign_key_if_missing(
        'fk_student_writings_reviewed_by_id_users',
        'student_writings', 'reviewed_by_id', 'users', 'id', ondelete='SET NULL',
    )

    # student_speakings
    op.execute("ALTER TABLE student_speakings ADD COLUMN IF NOT EXISTS user_id UUID")
    _add_foreign_key_if_missing(
        'fk_student_speakings_user_id_users',
        'student_speakings', 'user_id', 'users', 'id', ondelete='CASCADE',
    )
    op.execute(
        sa.text(f"CREATE INDEX IF NOT EXISTS {op.f('ix_student_speakings_user_id')} ON student_speakings (user_id)")
    )

    _set_column_nullable_if_needed('student_speakings', 'audio_url', nullable=True)

    op.execute("ALTER TABLE student_speakings ADD COLUMN IF NOT EXISTS storage_path VARCHAR(500)")
    op.execute("ALTER TABLE student_speakings ADD COLUMN IF NOT EXISTS filename VARCHAR(255)")
    op.execute("ALTER TABLE student_speakings ADD COLUMN IF NOT EXISTS content_type VARCHAR(100)")
    op.execute("ALTER TABLE student_speakings ADD COLUMN IF NOT EXISTS duration_seconds INTEGER")
    op.execute("ALTER TABLE student_speakings ADD COLUMN IF NOT EXISTS file_size_bytes INTEGER")
    op.execute("ALTER TABLE student_speakings ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMPTZ")
    op.execute("ALTER TABLE student_speakings ADD COLUMN IF NOT EXISTS score INTEGER")
    op.execute("ALTER TABLE student_speakings ADD COLUMN IF NOT EXISTS feedback TEXT")
    op.execute("ALTER TABLE student_speakings ADD COLUMN IF NOT EXISTS reviewed_by_id UUID")
    op.execute("ALTER TABLE student_speakings ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ")
    _add_foreign_key_if_missing(
        'fk_student_speakings_reviewed_by_id_users',
        'student_speakings', 'reviewed_by_id', 'users', 'id', ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    _drop_foreign_key_if_present('student_speakings', 'reviewed_by_id')
    op.execute("ALTER TABLE student_speakings DROP COLUMN IF EXISTS reviewed_at")
    op.execute("ALTER TABLE student_speakings DROP COLUMN IF EXISTS reviewed_by_id")
    op.execute("ALTER TABLE student_speakings DROP COLUMN IF EXISTS feedback")
    op.execute("ALTER TABLE student_speakings DROP COLUMN IF EXISTS score")
    op.execute("ALTER TABLE student_speakings DROP COLUMN IF EXISTS submitted_at")
    op.execute("ALTER TABLE student_speakings DROP COLUMN IF EXISTS file_size_bytes")
    op.execute("ALTER TABLE student_speakings DROP COLUMN IF EXISTS duration_seconds")
    op.execute("ALTER TABLE student_speakings DROP COLUMN IF EXISTS content_type")
    op.execute("ALTER TABLE student_speakings DROP COLUMN IF EXISTS filename")
    op.execute("ALTER TABLE student_speakings DROP COLUMN IF EXISTS storage_path")

    _set_column_nullable_if_needed('student_speakings', 'audio_url', nullable=False)

    op.execute(f"DROP INDEX IF EXISTS {op.f('ix_student_speakings_user_id')}")
    _drop_foreign_key_if_present('student_speakings', 'user_id')
    op.execute("ALTER TABLE student_speakings DROP COLUMN IF EXISTS user_id")

    _drop_foreign_key_if_present('student_writings', 'reviewed_by_id')
    op.execute("ALTER TABLE student_writings DROP COLUMN IF EXISTS reviewed_at")
    op.execute("ALTER TABLE student_writings DROP COLUMN IF EXISTS reviewed_by_id")
    op.execute("ALTER TABLE student_writings DROP COLUMN IF EXISTS feedback")
    op.execute("ALTER TABLE student_writings DROP COLUMN IF EXISTS score")
    op.execute("ALTER TABLE student_writings DROP COLUMN IF EXISTS submitted_at")
