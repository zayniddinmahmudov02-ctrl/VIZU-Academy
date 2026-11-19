"""Metadata of uploaded songs as a background queue (Musik bulk upload of up to 500 songs).

The upload request only stores the original (checked by content, SHA-256) and the song row with `metadata_status = PENDING`; ffprobe
(`audio_meta.read`: duration, bitrate, codec, title / artist / album / genre tags) runs here, ONE file at a time in a worker thread of the
backend process — so 500 uploads never start 500 ffprobe processes, and an upload never waits for it.

Queue = the songs table itself: PENDING → PROCESSING → OK | FAILED (tool missing / crashed: the original is kept, playable) | INVALID (the tool
says it is not audio: the song is set to DRAFT so no student gets a broken file; the admin sees why). A song is claimed with
`FOR UPDATE SKIP LOCKED`; PROCESSING older than STALE (backend restarted mid-file) is picked up again; the start of the backend puts PROCESSING
back to PENDING (`main.py` lifespan). Tags only fill what the admin left empty (a title equal to the file name is the form's default)."""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.medien import STATUS_DRAFT, STATUS_PUBLISHED, Song
from app.services.medien import audio_meta
from app.services.medien import common as c

log = logging.getLogger("vizu.medien.song_processing")

PENDING, PROCESSING, OK, FAILED, INVALID = "PENDING", "PROCESSING", "OK", "FAILED", "INVALID"
STALE = timedelta(minutes=10)


def stem_of(filename: str | None) -> str:
    """The file name without extension, spaces collapsed (the bulk form's default title)."""
    return " ".join(((filename or "").rsplit(".", 1)[0]).split())


def fill_from_tags(song: Song, info: audio_meta.AudioInfo, stem: str) -> None:
    """Tags fill only what the admin left empty; a title equal to the file name is the form's default, not a choice."""
    if info.title and (song.title or "") in ("", stem):
        song.title = info.title[:255]
    for field, limit in (("artist", 255), ("album", 255), ("genre", 80)):
        value = getattr(info, field)
        if value and not getattr(song, field):
            setattr(song, field, value[:limit])


def apply_audio(song: Song, ext: str | None, info: audio_meta.AudioInfo) -> None:
    song.audio_format, song.bitrate_kbps, song.duration_ms = ext, info.bitrate_kbps, info.duration_ms
    song.metadata_status, song.metadata_note = info.status, info.note


# ---------------- worker ----------------

_lock = threading.Lock()
_running = False


def kick() -> None:
    """Starts the worker thread unless it already runs (switched off in the test suite: tests call `run_one`)."""
    global _running
    if not settings.SONG_PROCESSING_WORKER_ENABLED:
        return
    with _lock:
        if _running:
            return
        _running = True
    threading.Thread(target=_loop, name="song-processing", daemon=True).start()


def _loop() -> None:
    global _running
    from app.db.session import SessionLocal

    try:
        while True:
            with SessionLocal() as db:
                if not run_one(db):
                    break
    except Exception:
        log.exception("song processing worker stopped")
    finally:
        with _lock:
            _running = False
    try:
        with SessionLocal() as db:  # a song queued while the loop was ending
            if db.scalar(select(Song.id).where(Song.metadata_status == PENDING).limit(1)):
                kick()
    except Exception:
        log.exception("song processing re-check failed")


def on_startup() -> None:
    if not settings.SONG_PROCESSING_WORKER_ENABLED or settings.APP_ENV == "test":
        return
    try:
        from app.db.session import SessionLocal

        with SessionLocal() as db:
            for song in db.scalars(select(Song).where(Song.metadata_status == PROCESSING)).all():
                song.metadata_status = PENDING
            db.commit()
            pending = db.scalar(select(Song.id).where(Song.metadata_status == PENDING).limit(1))
        if pending:
            kick()
    except Exception:
        log.exception("song processing: start-up recovery failed")


def claim(db: Session) -> Song | None:
    stale = datetime.now(timezone.utc) - STALE
    song = db.scalars(select(Song).where(or_(Song.metadata_status == PENDING, and_(Song.metadata_status == PROCESSING, Song.updated_at < stale)))
                      .order_by(Song.created_at).limit(1).with_for_update(skip_locked=True)).first()
    if song is None:
        db.rollback()
        return None
    song.metadata_status = PROCESSING
    db.commit()
    return song


def run_one(db: Session) -> bool:
    """Reads the metadata of one queued song. False when the queue is empty. Never raises for one bad file."""
    song = claim(db)
    if song is None:
        return False
    song_id = song.id
    try:
        path = c.file_path(song.file_key)
        if path is None:
            song.metadata_status, song.metadata_note = FAILED, "the stored file is missing"
        else:
            try:
                info = audio_meta.read(path)
            except audio_meta.AudioUnreadable:
                song.metadata_status, song.metadata_note = INVALID, "not readable as audio — set to draft; replace the file"
                if song.status == STATUS_PUBLISHED:
                    song.status = STATUS_DRAFT
            else:
                fill_from_tags(song, info, stem_of(song.original_name))
                apply_audio(song, song.audio_format, info)
        db.commit()
    except Exception:
        db.rollback()
        log.exception("song %s: metadata step crashed", song_id)
        row = db.get(Song, song_id)
        if row is not None:
            row.metadata_status, row.metadata_note = FAILED, "metadata step failed"
            db.commit()
    return True


def counts(db: Session) -> dict:
    rows = dict(db.execute(select(Song.metadata_status, func.count()).where(Song.metadata_status.in_((PENDING, PROCESSING)))
                           .group_by(Song.metadata_status)).all())
    pending = rows.get(PENDING, 0) + rows.get(PROCESSING, 0)
    if pending:
        kick()  # self-healing: somebody is looking, the queue is not empty
    return {"pending": rows.get(PENDING, 0), "processing": rows.get(PROCESSING, 0)}
