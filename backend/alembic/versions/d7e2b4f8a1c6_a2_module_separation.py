"""A2 module separation: competency of written tasks, Wortschatz word data and
student word state, Schreiben submission history.

Additive only:
* writings.competency (NULL = SCHREIBEN — every existing task stays what it
  was) + CHECK ck_writings_competency;
* vocabularies: word_type, verb_praeteritum, verb_partizip_ii, verb_auxiliary,
  dictionary_entry_id (-> dictionary_entries, SET NULL), data_sources;
* vocabulary_user_words (saved / learned per student and lesson word);
* student_writing_versions (the text of every final submission);
* ai_evaluations.attempt_number.

Downgrade drops exactly these columns and tables: tasks, words, submissions
and evaluations stay (the per-version texts and the word state are lost —
StudentWriting keeps the latest text).

Revision ID: d7e2b4f8a1c6
Revises: c4f7a9e2d6b3
Create Date: 2026-11-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d7e2b4f8a1c6"
down_revision: Union[str, Sequence[str], None] = "c4f7a9e2d6b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _base_columns():
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.add_column("writings", sa.Column("competency", sa.String(20), nullable=True))
    op.create_check_constraint(
        "ck_writings_competency", "writings", "competency IS NULL OR competency IN ('SCHREIBEN', 'GRAMMATIK', 'WORTSCHATZ', 'LESEN')"
    )

    op.add_column("vocabularies", sa.Column("word_type", sa.String(30), nullable=True))
    op.add_column("vocabularies", sa.Column("verb_praeteritum", sa.String(120), nullable=True))
    op.add_column("vocabularies", sa.Column("verb_partizip_ii", sa.String(120), nullable=True))
    op.add_column("vocabularies", sa.Column("verb_auxiliary", sa.String(20), nullable=True))
    op.add_column("vocabularies", sa.Column("dictionary_entry_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_vocabularies_dictionary_entry_id", "vocabularies", "dictionary_entries", ["dictionary_entry_id"], ["id"], ondelete="SET NULL"
    )
    op.add_column("vocabularies", sa.Column("data_sources", postgresql.JSONB(), nullable=True))

    op.create_table(
        "vocabulary_user_words",
        *_base_columns(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vocabulary_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vocabularies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("saved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("learned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("learned_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "vocabulary_id", name="uq_vocabulary_user_word"),
    )
    op.create_index("ix_vocabulary_user_words_user_id", "vocabulary_user_words", ["user_id"])
    op.create_index("ix_vocabulary_user_words_vocabulary_id", "vocabulary_user_words", ["vocabulary_id"])

    op.create_table(
        "student_writing_versions",
        *_base_columns(),
        sa.Column("student_writing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("student_writings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("writing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("writings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_writing_id", "attempt_number", name="uq_student_writing_version"),
    )
    op.create_index("ix_student_writing_versions_student_writing_id", "student_writing_versions", ["student_writing_id"])

    op.add_column("ai_evaluations", sa.Column("attempt_number", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_evaluations", "attempt_number")
    op.drop_index("ix_student_writing_versions_student_writing_id", table_name="student_writing_versions")
    op.drop_table("student_writing_versions")
    op.drop_index("ix_vocabulary_user_words_vocabulary_id", table_name="vocabulary_user_words")
    op.drop_index("ix_vocabulary_user_words_user_id", table_name="vocabulary_user_words")
    op.drop_table("vocabulary_user_words")
    op.drop_column("vocabularies", "data_sources")
    op.drop_constraint("fk_vocabularies_dictionary_entry_id", "vocabularies", type_="foreignkey")
    for column in ("dictionary_entry_id", "verb_auxiliary", "verb_partizip_ii", "verb_praeteritum", "word_type"):
        op.drop_column("vocabularies", column)
    op.drop_constraint("ck_writings_competency", "writings", type_="check")
    op.drop_column("writings", "competency")
