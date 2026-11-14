"""VIZU Medienwelt: categories, books, songs, playlists, favorites, films, subtitles, purchases, progress, play history.

Adds eleven new tables (media_categories, media_books, songs, playlists, playlist_songs, user_favorite_songs, films,
film_subtitles, media_purchases, media_progress, media_play_history) and seeds the owner's starting categories
(books: Literatur, Grammatik, Zertifikatsbücher, Wortschatz, Lektüren, Prüfungsvorbereitung, Sonstige Bücher; films:
Deutsche Filme, Kurzfilme, Dokumentationen, Lernvideos, Serien, Prüfungsvorbereitung, Kinderfilme, VIZU Originals).
No existing table or row is changed. Downgrade drops exactly these tables (files on disk stay).

Revision ID: f4c8a1e6b9d2
Revises: e8b4d2f6a1c3
Create Date: 2026-11-15
"""
import re
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f4c8a1e6b9d2"
down_revision: Union[str, Sequence[str], None] = "e8b4d2f6a1c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
TABLES = ["media_play_history", "media_progress", "media_purchases", "film_subtitles", "films", "user_favorite_songs",
          "playlist_songs", "playlists", "songs", "media_books", "media_categories"]
BOOK_CATEGORIES = ["Literatur", "Grammatik", "Zertifikatsbücher", "Wortschatz", "Lektüren", "Prüfungsvorbereitung", "Sonstige Bücher"]
FILM_CATEGORIES = ["Deutsche Filme", "Kurzfilme", "Dokumentationen", "Lernvideos", "Serien", "Prüfungsvorbereitung", "Kinderfilme", "VIZU Originals"]


def _slug(name: str) -> str:
    table = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
    return re.sub(r"[^a-z0-9]+", "-", name.lower().translate(table)).strip("-")


def _base() -> list:
    return [sa.Column("id", UUID, primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)]


def _content() -> list:
    return [sa.Column("title", sa.String(255), nullable=False), sa.Column("description", sa.Text(), nullable=True),
            sa.Column("cover_key", sa.String(300), nullable=True), sa.Column("language", sa.String(10), nullable=False, server_default="de"),
            sa.Column("level", sa.String(10), nullable=True), sa.Column("access_type", sa.String(10), nullable=False, server_default="FREE"),
            sa.Column("price", sa.Integer(), nullable=True), sa.Column("old_price", sa.Integer(), nullable=True),
            sa.Column("is_special_offer", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("status", sa.String(10), nullable=False, server_default="DRAFT")]


def _checks(t: str) -> list:
    return [sa.CheckConstraint("status IN ('DRAFT','PUBLISHED','HIDDEN')", name=f"ck_{t}_status"),
            sa.CheckConstraint("access_type IN ('FREE','PAID')", name=f"ck_{t}_access"),
            sa.CheckConstraint("price IS NULL OR price > 0", name=f"ck_{t}_price"),
            sa.CheckConstraint("access_type = 'FREE' OR price IS NOT NULL", name=f"ck_{t}_paid_price")]


def _fk(col: str, table: str, name: str, *, null: bool = True, on_delete: str = "SET NULL") -> sa.Column:
    return sa.Column(col, UUID, sa.ForeignKey(f"{table}.id", ondelete=on_delete, name=name), nullable=null)


def _ix(table: str, *cols: str) -> None:
    for c in cols:
        op.create_index(f"ix_{table}_{c}", table, [c])


def upgrade() -> None:
    op.create_table("media_categories", *_base(), sa.Column("kind", sa.String(10), nullable=False), sa.Column("name", sa.String(120), nullable=False),
                    sa.Column("slug", sa.String(140), nullable=False), sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
                    sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
                    sa.UniqueConstraint("kind", "slug", name="uq_media_categories_kind_slug"),
                    sa.CheckConstraint("kind IN ('BOOK','FILM')", name="ck_media_categories_kind"))

    op.create_table("media_books", *_base(), *_content(), sa.Column("author", sa.String(255), nullable=True),
                    _fk("category_id", "media_categories", "fk_media_books_category_id"), sa.Column("year", sa.Integer(), nullable=True),
                    sa.Column("file_format", sa.String(10), nullable=True), sa.Column("file_key", sa.String(300), nullable=True),
                    sa.Column("file_size", sa.BigInteger(), nullable=True), sa.Column("original_name", sa.String(255), nullable=True),
                    sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"), *_checks("media_books"))
    _ix("media_books", "level", "status", "author", "category_id")

    op.create_table("songs", *_base(), *_content(), sa.Column("artist", sa.String(255), nullable=True), sa.Column("album", sa.String(255), nullable=True),
                    sa.Column("genre", sa.String(80), nullable=True), sa.Column("duration_ms", sa.Integer(), nullable=True),
                    sa.Column("file_key", sa.String(300), nullable=True), sa.Column("content_type", sa.String(100), nullable=True),
                    sa.Column("file_size", sa.BigInteger(), nullable=True), sa.Column("original_name", sa.String(255), nullable=True),
                    sa.Column("play_count", sa.Integer(), nullable=False, server_default="0"), *_checks("songs"))
    _ix("songs", "level", "status", "artist")

    op.create_table("playlists", *_base(), _fk("owner_id", "users", "fk_playlists_owner_id", on_delete="CASCADE"),
                    sa.Column("name", sa.String(160), nullable=False), sa.Column("description", sa.Text(), nullable=True),
                    sa.Column("cover_key", sa.String(300), nullable=True), sa.Column("status", sa.String(10), nullable=False, server_default="PUBLISHED"),
                    sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
                    sa.CheckConstraint("status IN ('DRAFT','PUBLISHED','HIDDEN')", name="ck_playlists_status"))
    _ix("playlists", "owner_id")

    op.create_table("playlist_songs", *_base(), _fk("playlist_id", "playlists", "fk_playlist_songs_playlist_id", null=False, on_delete="CASCADE"),
                    _fk("song_id", "songs", "fk_playlist_songs_song_id", null=False, on_delete="CASCADE"),
                    sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
                    sa.UniqueConstraint("playlist_id", "song_id", name="uq_playlist_songs_pair"))
    _ix("playlist_songs", "playlist_id", "song_id")

    op.create_table("user_favorite_songs", *_base(), _fk("user_id", "users", "fk_user_favorite_songs_user_id", null=False, on_delete="CASCADE"),
                    _fk("song_id", "songs", "fk_user_favorite_songs_song_id", null=False, on_delete="CASCADE"),
                    sa.UniqueConstraint("user_id", "song_id", name="uq_user_favorite_songs_pair"))
    _ix("user_favorite_songs", "user_id", "song_id")

    op.create_table("films", *_base(), *_content(), _fk("category_id", "media_categories", "fk_films_category_id"),
                    sa.Column("genre", sa.String(80), nullable=True), sa.Column("year", sa.Integer(), nullable=True),
                    sa.Column("duration_minutes", sa.Integer(), nullable=True), sa.Column("video_key", sa.String(300), nullable=True),
                    sa.Column("video_content_type", sa.String(100), nullable=True), sa.Column("video_size", sa.BigInteger(), nullable=True),
                    sa.Column("original_name", sa.String(255), nullable=True), sa.Column("external_url", sa.String(1000), nullable=True),
                    sa.Column("processing_status", sa.String(12), nullable=False, server_default="NONE"),
                    sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"), *_checks("films"),
                    sa.CheckConstraint("processing_status IN ('NONE','UPLOADING','READY','FAILED')", name="ck_films_processing"))
    _ix("films", "level", "status", "category_id")

    op.create_table("film_subtitles", *_base(), _fk("film_id", "films", "fk_film_subtitles_film_id", null=False, on_delete="CASCADE"),
                    sa.Column("language", sa.String(10), nullable=False), sa.Column("label", sa.String(80), nullable=False),
                    sa.Column("file_key", sa.String(300), nullable=False),
                    sa.UniqueConstraint("film_id", "language", name="uq_film_subtitles_film_language"))
    _ix("film_subtitles", "film_id")

    op.create_table("media_purchases", *_base(), _fk("user_id", "users", "fk_media_purchases_user_id", null=False, on_delete="CASCADE"),
                    sa.Column("content_type", sa.String(10), nullable=False), sa.Column("content_id", UUID, nullable=False),
                    sa.Column("price", sa.Integer(), nullable=True), sa.Column("status", sa.String(10), nullable=False, server_default="REQUESTED"),
                    sa.Column("note", sa.String(500), nullable=True), _fk("decided_by_id", "users", "fk_media_purchases_decided_by_id"),
                    sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
                    sa.CheckConstraint("content_type IN ('BOOK','SONG','FILM')", name="ck_media_purchases_type"),
                    sa.CheckConstraint("status IN ('REQUESTED','GRANTED','REJECTED','REVOKED')", name="ck_media_purchases_status"))
    _ix("media_purchases", "user_id", "content_id", "status", "decided_by_id")
    op.create_index("uq_media_purchases_open", "media_purchases", ["user_id", "content_type", "content_id"], unique=True,
                    postgresql_where=sa.text("status IN ('REQUESTED','GRANTED')"))

    op.create_table("media_progress", *_base(), _fk("user_id", "users", "fk_media_progress_user_id", null=False, on_delete="CASCADE"),
                    sa.Column("content_type", sa.String(10), nullable=False), sa.Column("content_id", UUID, nullable=False),
                    sa.Column("position", sa.Integer(), nullable=False, server_default="0"), sa.Column("total", sa.Integer(), nullable=True),
                    sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
                    sa.UniqueConstraint("user_id", "content_type", "content_id", name="uq_media_progress_user_content"),
                    sa.CheckConstraint("content_type IN ('BOOK','FILM')", name="ck_media_progress_type"))
    _ix("media_progress", "user_id")

    op.create_table("media_play_history", *_base(), _fk("user_id", "users", "fk_media_play_history_user_id", null=False, on_delete="CASCADE"),
                    _fk("song_id", "songs", "fk_media_play_history_song_id", null=False, on_delete="CASCADE"))
    _ix("media_play_history", "user_id", "song_id")

    cats = sa.table("media_categories", sa.column("id", UUID), sa.column("kind", sa.String), sa.column("name", sa.String),
                    sa.column("slug", sa.String), sa.column("sort_order", sa.Integer))
    rows = [{"id": uuid.uuid4(), "kind": kind, "name": name, "slug": _slug(name), "sort_order": i * 10}
            for kind, names in (("BOOK", BOOK_CATEGORIES), ("FILM", FILM_CATEGORIES)) for i, name in enumerate(names, 1)]
    op.bulk_insert(cats, rows)


def downgrade() -> None:
    for table in TABLES:
        op.drop_table(table)
