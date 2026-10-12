"""VIZU LMS (A1–C1): competencies, learning resources, competency progress

Additive and reversible (docs/lms-architecture.md). No existing row is
deleted; existing lessons stay visible exactly as before:
* lessons: description, is_published (existing rows: true), access_override.
* courses: sequential_unlock (default false = today's behaviour).
* videos: competency (NULL = Einführung), subtitle_key.
* student_progress: completed_at, last_activity_at.
* lesson_competencies: the ten competencies of every lesson in their fixed
  order (CHECK: position is the kind's canonical slot); rows are created for
  every existing lesson, published, so current content keeps showing.
* learning_resources: audio / PDF / image / document / link per lesson or
  competency (protected storage, or an external URL for links).
* student_competency_progress: per student, lesson and competency.
* UNIQUE(lessons.module_id, number) — only created when the existing data
  has no duplicate numbers (otherwise a NOTICE is raised and the service-
  level check alone applies until the duplicates are resolved).

Revision ID: e8b1f4c2a9d6
Revises: d7a3c9e1f5b2
Create Date: 2026-10-12
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "e8b1f4c2a9d6"
down_revision = "d7a3c9e1f5b2"
branch_labels = None
depends_on = None

COMPETENCIES = (
    "EINFUEHRUNG", "WORTSCHATZ", "GRAMMATIK", "LESEN", "HOEREN",
    "SPRECHEN", "SCHREIBEN", "UEBUNGEN", "ABSCHLUSSTEST", "ZUSAMMENFASSUNG",
)
KINDS_SQL = ", ".join(f"'{k}'" for k in COMPETENCIES)
POSITION_SQL = "position = CASE kind " + " ".join(f"WHEN '{k}' THEN {i}" for i, k in enumerate(COMPETENCIES, start=1)) + " END"


def _timestamps():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.add_column("lessons", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("lessons", sa.Column("is_published", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("lessons", sa.Column("access_override", sa.String(length=10), nullable=True))
    op.create_check_constraint("ck_lessons_access_override", "lessons", "access_override IS NULL OR access_override IN ('OPEN', 'LOCKED')")

    op.add_column("courses", sa.Column("sequential_unlock", sa.Boolean(), nullable=False, server_default="false"))

    op.add_column("videos", sa.Column("competency", sa.String(length=20), nullable=True))
    op.add_column("videos", sa.Column("subtitle_key", sa.String(length=1024), nullable=True))
    op.create_check_constraint("ck_videos_competency", "videos", f"competency IS NULL OR competency IN ({KINDS_SQL})")

    op.add_column("student_progress", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("student_progress", sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "lesson_competencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        *_timestamps(),
        sa.UniqueConstraint("lesson_id", "kind", name="uq_lesson_competencies_lesson_kind"),
        sa.UniqueConstraint("lesson_id", "position", name="uq_lesson_competencies_lesson_position"),
        sa.CheckConstraint(f"kind IN ({KINDS_SQL})", name="ck_lesson_competencies_kind"),
        sa.CheckConstraint(POSITION_SQL, name="ck_lesson_competencies_position"),
    )
    op.create_index("ix_lesson_competencies_lesson_id", "lesson_competencies", ["lesson_id"])

    op.create_table(
        "learning_resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("competency", sa.String(length=20), nullable=True),
        sa.Column("resource_type", sa.String(length=12), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("storage_key", sa.String(length=1024), nullable=True, unique=True),
        sa.Column("external_url", sa.String(length=1000), nullable=True),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        *_timestamps(),
        sa.CheckConstraint("resource_type IN ('AUDIO', 'PDF', 'IMAGE', 'DOCUMENT', 'LINK')", name="ck_learning_resources_type"),
        sa.CheckConstraint(f"competency IS NULL OR competency IN ({KINDS_SQL})", name="ck_learning_resources_competency"),
        sa.CheckConstraint(
            "(resource_type = 'LINK' AND external_url IS NOT NULL AND storage_key IS NULL)"
            " OR (resource_type <> 'LINK' AND storage_key IS NOT NULL AND external_url IS NULL)",
            name="ck_learning_resources_source",
        ),
    )
    op.create_index("ix_learning_resources_lesson_competency", "learning_resources", ["lesson_id", "competency", "order_index"])

    op.create_table(
        "student_competency_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("competency", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False, server_default="not_started"),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("visited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("user_id", "lesson_id", "competency", name="uq_student_competency_progress"),
        sa.CheckConstraint(f"competency IN ({KINDS_SQL})", name="ck_student_competency_progress_competency"),
        sa.CheckConstraint("status IN ('not_started', 'in_progress', 'completed')", name="ck_student_competency_progress_status"),
    )
    op.create_index("ix_student_competency_progress_user_lesson", "student_competency_progress", ["user_id", "lesson_id"])

    # Every existing lesson gets its ten competencies, published, so the
    # content students see today stays visible.
    op.execute(
        "INSERT INTO lesson_competencies (id, lesson_id, kind, position, is_published) "
        "SELECT gen_random_uuid(), l.id, c.kind, c.position, true FROM lessons l "
        f"CROSS JOIN (VALUES {', '.join(f'({chr(39)}{k}{chr(39)}, {i})' for i, k in enumerate(COMPETENCIES, start=1))}) AS c(kind, position)"
    )

    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM lessons GROUP BY module_id, number HAVING count(*) > 1) THEN
            RAISE NOTICE 'lessons have duplicate (module_id, number) - uq_lessons_module_number NOT created';
          ELSE
            CREATE UNIQUE INDEX uq_lessons_module_number ON lessons (module_id, number);
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_lessons_module_number")
    op.drop_index("ix_student_competency_progress_user_lesson", table_name="student_competency_progress")
    op.drop_table("student_competency_progress")
    op.drop_index("ix_learning_resources_lesson_competency", table_name="learning_resources")
    op.drop_table("learning_resources")
    op.drop_index("ix_lesson_competencies_lesson_id", table_name="lesson_competencies")
    op.drop_table("lesson_competencies")
    op.drop_column("student_progress", "last_activity_at")
    op.drop_column("student_progress", "completed_at")
    op.drop_constraint("ck_videos_competency", "videos", type_="check")
    op.drop_column("videos", "subtitle_key")
    op.drop_column("videos", "competency")
    op.drop_column("courses", "sequential_unlock")
    op.drop_constraint("ck_lessons_access_override", "lessons", type_="check")
    op.drop_column("lessons", "access_override")
    op.drop_column("lessons", "is_published")
    op.drop_column("lessons", "description")
