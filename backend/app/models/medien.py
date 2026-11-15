"""VIZU Medienwelt tables (Bibliothek, Musik, Filme). Separate from the course `books` / lesson `videos` tables on purpose:
those are level-gated course material; Medienwelt content has categories, FREE / PAID access, purchases and its own
progress. Files are private (`protected_storage/medien`); covers and posters are served by a cacheable public endpoint.

Status: DRAFT (admin only) | PUBLISHED | HIDDEN (temporarily off, kept). Access: FREE (every student) | PAID (a GRANTED
purchase, or staff). Everything a student reads about PAID content is cover, text and price — never a file."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

STATUS_DRAFT, STATUS_PUBLISHED, STATUS_HIDDEN = "DRAFT", "PUBLISHED", "HIDDEN"
STATUSES = (STATUS_DRAFT, STATUS_PUBLISHED, STATUS_HIDDEN)
ACCESS_FREE, ACCESS_PAID = "FREE", "PAID"
ACCESS_TYPES = (ACCESS_FREE, ACCESS_PAID)
KIND_BOOK, KIND_SONG, KIND_FILM = "BOOK", "SONG", "FILM"
PURCHASE_REQUESTED, PURCHASE_GRANTED, PURCHASE_REJECTED, PURCHASE_REVOKED = "REQUESTED", "GRANTED", "REJECTED", "REVOKED"
LEVELS = ("A1", "A2", "B1", "B2", "C1")


def _uuid_fk(table: str, name: str, *, null: bool = True, on_delete: str = "SET NULL"):
    return mapped_column(UUID(as_uuid=True), ForeignKey(f"{table}.id", ondelete=on_delete, name=name), nullable=null, index=True)


class MediaCategory(BaseModel):
    __tablename__ = "media_categories"
    __table_args__ = (UniqueConstraint("kind", "slug", name="uq_media_categories_kind_slug"),
                      CheckConstraint("kind IN ('BOOK','FILM')", name="ck_media_categories_kind"))

    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


def _common_checks(table: str):
    return (CheckConstraint(f"status IN ('DRAFT','PUBLISHED','HIDDEN')", name=f"ck_{table}_status"),
            CheckConstraint(f"access_type IN ('FREE','PAID')", name=f"ck_{table}_access"),
            CheckConstraint("price IS NULL OR price > 0", name=f"ck_{table}_price"),
            CheckConstraint("access_type = 'FREE' OR price IS NOT NULL", name=f"ck_{table}_paid_price"))


class _Content:
    """Columns every Medienwelt content row has."""

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="de")
    level: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    access_type: Mapped[str] = mapped_column(String(10), nullable=False, default=ACCESS_FREE)
    price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    old_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_special_offer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=STATUS_DRAFT, index=True)


class MediaBook(_Content, BaseModel):
    __tablename__ = "media_books"
    __table_args__ = _common_checks("media_books")

    author: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    category_id: Mapped[UUID | None] = _uuid_fk("media_categories", "fk_media_books_category_id")
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_format: Mapped[str | None] = mapped_column(String(10), nullable=True)
    file_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Song(_Content, BaseModel):
    __tablename__ = "songs"
    __table_args__ = _common_checks("songs")

    artist: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    album: Mapped[str | None] = mapped_column(String(255), nullable=True)
    genre: Mapped[str | None] = mapped_column(String(80), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    play_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Playlist(BaseModel):
    """owner_id NULL = an official VIZU playlist (admin-made, shown to everyone when PUBLISHED); else a student's own."""

    __tablename__ = "playlists"
    __table_args__ = (CheckConstraint("status IN ('DRAFT','PUBLISHED','HIDDEN')", name="ck_playlists_status"),)

    owner_id: Mapped[UUID | None] = _uuid_fk("users", "fk_playlists_owner_id", on_delete="CASCADE")
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=STATUS_PUBLISHED)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class PlaylistSong(BaseModel):
    __tablename__ = "playlist_songs"
    __table_args__ = (UniqueConstraint("playlist_id", "song_id", name="uq_playlist_songs_pair"),)

    playlist_id: Mapped[UUID] = _uuid_fk("playlists", "fk_playlist_songs_playlist_id", null=False, on_delete="CASCADE")
    song_id: Mapped[UUID] = _uuid_fk("songs", "fk_playlist_songs_song_id", null=False, on_delete="CASCADE")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class UserFavoriteSong(BaseModel):
    __tablename__ = "user_favorite_songs"
    __table_args__ = (UniqueConstraint("user_id", "song_id", name="uq_user_favorite_songs_pair"),)

    user_id: Mapped[UUID] = _uuid_fk("users", "fk_user_favorite_songs_user_id", null=False, on_delete="CASCADE")
    song_id: Mapped[UUID] = _uuid_fk("songs", "fk_user_favorite_songs_song_id", null=False, on_delete="CASCADE")


class Film(_Content, BaseModel):
    __tablename__ = "films"
    __table_args__ = _common_checks("films") + (
        CheckConstraint("processing_status IN ('NONE','UPLOADING','READY','FAILED')", name="ck_films_processing"),)

    category_id: Mapped[UUID | None] = _uuid_fk("media_categories", "fk_films_category_id")
    genre: Mapped[str | None] = mapped_column(String(80), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    video_content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    video_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(12), nullable=False, default="NONE")
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # exact length of the uploaded video (ffprobe); `duration_minutes` stays the admin-facing, rounded value
    video_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class FilmSubtitle(BaseModel):
    """One subtitle track of a film (one per language). The stored file is normalised, sanitised WebVTT; the columns below
    are the result of the last check (`services/medien/subtitles.py`) so the admin list needs no file reads."""

    __tablename__ = "film_subtitles"
    __table_args__ = (UniqueConstraint("film_id", "language", name="uq_film_subtitles_film_language"),)

    film_id: Mapped[UUID] = _uuid_fk("films", "fk_film_subtitles_film_id", null=False, on_delete="CASCADE")
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    file_key: Mapped[str] = mapped_column(String(300), nullable=False)
    cue_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_format: Mapped[str | None] = mapped_column(String(5), nullable=True)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warnings: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")


class FilmRendition(BaseModel):
    """An additional video quality of a film (e.g. 720p / 480p / 360p) uploaded by the admin. The film's own file stays the
    "Original"; the player offers the quality menu only when at least one rendition exists."""

    __tablename__ = "film_renditions"
    __table_args__ = (UniqueConstraint("film_id", "label", name="uq_film_renditions_film_label"),)

    film_id: Mapped[UUID] = _uuid_fk("films", "fk_film_renditions_film_id", null=False, on_delete="CASCADE")
    label: Mapped[str] = mapped_column(String(20), nullable=False)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_key: Mapped[str] = mapped_column(String(300), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)


class MediaPlayerPrefs(BaseModel):
    """A student's player settings (subtitle size / colour / background / position / font, on-off, dual subtitles): one row
    per user, the "profile" part of the video player. Per-film state (position, subtitle language, speed) lives in
    `media_progress.player_state`."""

    __tablename__ = "media_player_prefs"
    __table_args__ = (UniqueConstraint("user_id", name="uq_media_player_prefs_user"),)

    user_id: Mapped[UUID] = _uuid_fk("users", "fk_media_player_prefs_user_id", null=False, on_delete="CASCADE")
    prefs: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")


class MediaPurchase(BaseModel):
    """A student's request to get PAID content and the admin's decision. Access exists only while GRANTED. No money moves
    here: payment stays on the existing manual process; this table is the hook for the Payment System."""

    __tablename__ = "media_purchases"
    __table_args__ = (
        CheckConstraint("content_type IN ('BOOK','SONG','FILM')", name="ck_media_purchases_type"),
        CheckConstraint("status IN ('REQUESTED','GRANTED','REJECTED','REVOKED')", name="ck_media_purchases_status"),
        Index("uq_media_purchases_open", "user_id", "content_type", "content_id", unique=True,
              postgresql_where=text("status IN ('REQUESTED','GRANTED')")),
    )

    user_id: Mapped[UUID] = _uuid_fk("users", "fk_media_purchases_user_id", null=False, on_delete="CASCADE")
    content_type: Mapped[str] = mapped_column(String(10), nullable=False)
    content_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=PURCHASE_REQUESTED, index=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    decided_by_id: Mapped[UUID | None] = _uuid_fk("users", "fk_media_purchases_decided_by_id")
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MediaProgress(BaseModel):
    """Where a student stopped: a book page or a film second. One row per user + content."""

    __tablename__ = "media_progress"
    __table_args__ = (UniqueConstraint("user_id", "content_type", "content_id", name="uq_media_progress_user_content"),
                      CheckConstraint("content_type IN ('BOOK','FILM')", name="ck_media_progress_type"))

    user_id: Mapped[UUID] = _uuid_fk("users", "fk_media_progress_user_id", null=False, on_delete="CASCADE")
    content_type: Mapped[str] = mapped_column(String(10), nullable=False)
    content_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # films: subtitle language / dual subtitles / speed / quality the student used last (restored by "continue watching")
    player_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class MediaPlayHistory(BaseModel):
    __tablename__ = "media_play_history"

    user_id: Mapped[UUID] = _uuid_fk("users", "fk_media_play_history_user_id", null=False, on_delete="CASCADE")
    song_id: Mapped[UUID] = _uuid_fk("songs", "fk_media_play_history_song_id", null=False, on_delete="CASCADE")
