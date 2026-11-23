"""Team (teacher accounts), Kontroll permission, student activity tracking, Bibliothek categories.

Additive schema:
* `users.must_change_password` (bool, default false): an admin-created teacher must set an own password at the first login.
* `teacher_profiles`: one row per teacher user (unique user_id, CASCADE) with `can_access_student_control` (default false =
  "Nein"), who changed it and when, who created the account. Teachers stay `users` rows with role TEACHER; course
  assignments stay `teacher_assignments`, group assignment stays `study_groups.teacher_id` (nothing is duplicated).
* `student_sessions`: active-use sessions built from heartbeats (one open session per user = partial unique index, a
  session never crosses a Tashkent day), `active_seconds` credited by the server only.
* `student_activity_events`: what the time was spent on (area COURSE / WORTSCHATZ / MUSIC / FILM / BOOK / EXAM + the item id),
  one row per continuous stretch; the timeline and the per-item statistics are read from here.

Data (Bibliothek categories, BOOK kind only; no book and no category row is deleted):
* the six categories Literatur, Historisch, Beruflich, Sonstige, Prüfungsvorbereitung, Wortschatz (this order) — existing rows
  with the same slug keep their id; "Sonstige Bücher" (slug `sonstige-buecher`) is renamed "Sonstige"; Historisch /
  Beruflich are added when missing;
* books of the old categories move: Lektüren -> Literatur, Zertifikatsbücher -> Prüfungsvorbereitung, Grammatik -> Sonstige;
  the three old categories are set inactive (hidden from students, kept for history).

Downgrade: drops the two activity tables, `teacher_profiles` and the column (their data is lost); categories get their old
names / order / active flags back; Historisch / Beruflich are only set inactive (no category row is deleted, their books keep
their category); books moved out of the old categories by the upgrade stay where they are.

Revision ID: c8d3f5a1e7b2
Revises: b7e4c2a9d6f1
Create Date: 2026-11-23
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c8d3f5a1e7b2"
down_revision: Union[str, Sequence[str], None] = "b7e4c2a9d6f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

AREAS = ("COURSE", "WORTSCHATZ", "MUSIC", "FILM", "BOOK", "EXAM")
# (slug, name, sort order) — the six Bibliothek categories in the owner's order
LIBRARY = (("literatur", "Literatur", 10), ("historisch", "Historisch", 20), ("beruflich", "Beruflich", 30),
           ("sonstige-buecher", "Sonstige", 40), ("pruefungsvorbereitung", "Prüfungsvorbereitung", 50), ("wortschatz", "Wortschatz", 60))
# old category slug -> where its books go
LEGACY = (("lektueren", "literatur"), ("zertifikatsbuecher", "pruefungsvorbereitung"), ("grammatik", "sonstige-buecher"))
# before this revision (for the downgrade)
OLD = {"literatur": ("Literatur", 10), "grammatik": ("Grammatik", 20), "zertifikatsbuecher": ("Zertifikatsbücher", 30),
       "wortschatz": ("Wortschatz", 40), "lektueren": ("Lektüren", 50), "pruefungsvorbereitung": ("Prüfungsvorbereitung", 60),
       "sonstige-buecher": ("Sonstige Bücher", 70)}


def _uuid_fk(name: str, target: str, ondelete: str, nullable: bool) -> sa.Column:
    return sa.Column(name, postgresql.UUID(as_uuid=True), sa.ForeignKey(target, ondelete=ondelete), nullable=nullable)


def _times() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def _category_id(conn, slug: str):
    return conn.execute(sa.text("SELECT id FROM media_categories WHERE kind = 'BOOK' AND slug = :s"), {"s": slug}).scalar()


def upgrade() -> None:
    op.add_column("users", sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "teacher_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        _uuid_fk("user_id", "users.id", "CASCADE", False),
        sa.Column("can_access_student_control", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("control_changed_at", sa.DateTime(timezone=True), nullable=True),
        _uuid_fk("control_changed_by", "users.id", "SET NULL", True),
        _uuid_fk("created_by", "users.id", "SET NULL", True),
        *_times(),
        sa.UniqueConstraint("user_id", name="uq_teacher_profiles_user_id"),
    )

    op.create_table(
        "student_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        _uuid_fk("user_id", "users.id", "CASCADE", False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("heartbeats", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tabs", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_times(),
        sa.CheckConstraint("active_seconds >= 0", name="ck_student_sessions_seconds"),
    )
    op.create_index("ix_student_sessions_user_day", "student_sessions", ["user_id", "day"])
    op.create_index("ix_student_sessions_day", "student_sessions", ["day"])
    op.create_index("uq_student_sessions_open", "student_sessions", ["user_id"], unique=True, postgresql_where=sa.text("ended_at IS NULL"))

    op.create_table(
        "student_activity_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        _uuid_fk("user_id", "users.id", "CASCADE", False),
        _uuid_fk("session_id", "student_sessions.id", "SET NULL", True),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("area", sa.String(12), nullable=False),
        sa.Column("ref_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("position", sa.Integer(), nullable=True),
        *_times(),
        sa.CheckConstraint(f"area IN ({', '.join(repr(a) for a in AREAS)})", name="ck_student_activity_events_area"),
        sa.CheckConstraint("seconds >= 0", name="ck_student_activity_events_seconds"),
    )
    op.create_index("ix_student_activity_events_user_day", "student_activity_events", ["user_id", "day"])
    op.create_index("ix_student_activity_events_user_area_ref", "student_activity_events", ["user_id", "area", "ref_id"])
    op.create_index("ix_student_activity_events_user_last_seen", "student_activity_events", ["user_id", "last_seen_at"])

    conn = op.get_bind()
    for slug, name, order in LIBRARY:
        if _category_id(conn, slug) is None:
            conn.execute(sa.text("INSERT INTO media_categories (id, kind, name, slug, sort_order, is_active) VALUES (:id, 'BOOK', :n, :s, :o, true)"),
                         {"id": uuid.uuid4(), "n": name, "s": slug, "o": order})
        else:
            conn.execute(sa.text("UPDATE media_categories SET name = :n, sort_order = :o, is_active = true, updated_at = now() "
                                 "WHERE kind = 'BOOK' AND slug = :s"), {"n": name, "s": slug, "o": order})
    for index, (old, new) in enumerate(LEGACY):
        old_id = _category_id(conn, old)
        if old_id is None:
            continue
        conn.execute(sa.text("UPDATE media_books SET category_id = :new, updated_at = now() WHERE category_id = :old"),
                     {"new": _category_id(conn, new), "old": old_id})
        conn.execute(sa.text("UPDATE media_categories SET is_active = false, sort_order = :o, updated_at = now() WHERE id = :id"),
                     {"o": 900 + index, "id": old_id})


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE media_categories SET is_active = false WHERE kind = 'BOOK' AND slug IN ('historisch', 'beruflich')"))
    for slug, (name, order) in OLD.items():
        conn.execute(sa.text("UPDATE media_categories SET name = :n, sort_order = :o, is_active = true WHERE kind = 'BOOK' AND slug = :s"),
                     {"n": name, "o": order, "s": slug})

    op.drop_index("ix_student_activity_events_user_last_seen", table_name="student_activity_events")
    op.drop_index("ix_student_activity_events_user_area_ref", table_name="student_activity_events")
    op.drop_index("ix_student_activity_events_user_day", table_name="student_activity_events")
    op.drop_table("student_activity_events")
    op.drop_index("uq_student_sessions_open", table_name="student_sessions")
    op.drop_index("ix_student_sessions_day", table_name="student_sessions")
    op.drop_index("ix_student_sessions_user_day", table_name="student_sessions")
    op.drop_table("student_sessions")
    op.drop_table("teacher_profiles")
    op.drop_column("users", "must_change_password")
