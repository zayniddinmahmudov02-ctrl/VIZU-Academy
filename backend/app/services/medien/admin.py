"""Admin side of Medienwelt: categories, books, songs, films (+ subtitles, chunked video upload), official playlists,
purchase decisions and statistics. Callers (the router) have already passed the role check: `require_content_editor` for
writes, `require_admin_panel_access` for reads. Every write is audited. Deleting content removes the row first, then the
files (a file that cannot be removed shows up as `file_status` / is harmless, a row without file never blocks a student)."""

import asyncio
import json
import re
import shutil
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.models.medien import (ACCESS_FREE, ACCESS_PAID, ACCESS_TYPES, KIND_BOOK, KIND_FILM, KIND_SONG, PURCHASE_GRANTED, PURCHASE_REJECTED,
                               PURCHASE_REQUESTED, PURCHASE_REVOKED, STATUS_PUBLISHED, STATUSES, Film, FilmSubtitle, MediaBook, MediaCategory,
                               MediaPlayHistory, MediaProgress, MediaPurchase, Playlist, PlaylistSong, Song, UserFavoriteSong)
from app.models.user import User
from app.services.audio_files import service as audio
from app.services.medien import common as c

CONTENT_FIELDS = {"title", "description", "language", "level", "access_type", "price", "old_price", "is_special_offer", "is_featured", "status"}
EXTRA = {KIND_BOOK: {"author", "category_id", "year"}, KIND_SONG: {"artist", "album", "genre"},
         KIND_FILM: {"category_id", "genre", "year", "duration_minutes"}}
CHUNK_SIZE = 8 * c.MB
MAX_CHUNK = 16 * c.MB


def _audit(db: Session, user: User, action: str, details: str) -> None:
    write_audit(db, actor_id=user.id, action=action, details=details[:900])


def _text(value, field: str, limit: int, required: bool = False) -> str | None:
    text = " ".join(str(value).split()) if value is not None else ""
    if required and not text:
        raise c.err(422, f"{field.upper()}_REQUIRED")
    if len(text) > limit:
        raise c.err(422, f"{field.upper()}_TOO_LONG: max {limit} characters.")
    return text or None


def _int(value, field: str, low: int, high: int) -> int | None:
    if value in (None, ""):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise c.err(422, f"INVALID_{field.upper()}") from None
    if not low <= number <= high:
        raise c.err(422, f"INVALID_{field.upper()}: {low}–{high}.")
    return number


def clean(db: Session, kind: str, data: dict, current=None) -> dict:
    """Validated column values for the keys present in `data`; the access rules are checked on the merged result."""
    out: dict = {}
    allowed = CONTENT_FIELDS | EXTRA[kind]
    unknown = set(data) - allowed
    if unknown:
        raise c.err(422, f"UNKNOWN_FIELDS: {', '.join(sorted(unknown))}")
    if "title" in data or current is None:
        out["title"] = _text(data.get("title"), "title", 255, True)
    if "description" in data:
        out["description"] = (str(data["description"]).strip()[:5000] or None) if data["description"] is not None else None
    if "language" in data:
        out["language"] = _text(data["language"], "language", 10, True)
    if "level" in data:
        level = (data["level"] or None)
        if level is not None and level not in c.LEVELS:
            raise c.err(422, "INVALID_LEVEL: A1–C1.")
        out["level"] = level
    for flag in ("is_special_offer", "is_featured"):
        if flag in data:
            out[flag] = bool(data[flag])
    if "status" in data:
        if data["status"] not in STATUSES:
            raise c.err(422, "INVALID_STATUS")
        out["status"] = data["status"]
    for text_field, limit in (("author", 255), ("artist", 255), ("album", 255), ("genre", 80)):
        if text_field in data:
            out[text_field] = _text(data[text_field], text_field, limit)
    if "year" in data:
        out["year"] = _int(data["year"], "year", 1400, 2200)
    if "duration_minutes" in data:
        out["duration_minutes"] = _int(data["duration_minutes"], "duration_minutes", 1, 1000)
    if "category_id" in data:
        cid = data["category_id"] or None
        if cid is not None:
            cat = db.get(MediaCategory, UUID(str(cid)))
            if cat is None or cat.kind != kind:
                raise c.err(422, "INVALID_CATEGORY")
        out["category_id"] = UUID(str(cid)) if cid else None
    # access: FREE has no price; PAID needs one; an old price only counts when it is higher
    touch = {"access_type", "price", "old_price", "is_special_offer"} & set(data)
    if touch or current is None:
        access = data.get("access_type", current.access_type if current else ACCESS_FREE)
        if access not in ACCESS_TYPES:
            raise c.err(422, "INVALID_ACCESS_TYPE")
        price = _int(data["price"], "price", 1, 100_000_000) if "price" in data else (current.price if current else None)
        old = _int(data["old_price"], "old_price", 1, 100_000_000) if "old_price" in data else (current.old_price if current else None)
        if access == ACCESS_PAID:
            if price is None:
                raise c.err(422, "PRICE_REQUIRED: a PAID item needs a price.")
            if old is not None and old <= price:
                old = None
        else:
            price = old = None
            out["is_special_offer"] = False
        out.update(access_type=access, price=price, old_price=old)
        if access == ACCESS_PAID and "is_special_offer" not in data and current is None:
            out["is_special_offer"] = False
    return out


# ---------------- categories ----------------


def list_categories(db: Session, kind: str) -> list[dict]:
    model = MediaBook if kind == KIND_BOOK else Film
    counts = dict(db.execute(select(model.category_id, func.count()).group_by(model.category_id)).all())
    rows = db.scalars(select(MediaCategory).where(MediaCategory.kind == kind).order_by(MediaCategory.sort_order, MediaCategory.name)).all()
    return [{"id": r.id, "kind": r.kind, "name": r.name, "slug": r.slug, "sort_order": r.sort_order, "is_active": r.is_active,
             "item_count": counts.get(r.id, 0)} for r in rows]


def _slug(name: str) -> str:
    table = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
    return re.sub(r"[^a-z0-9]+", "-", name.lower().translate(table)).strip("-") or uuid4().hex[:8]


def save_category(db: Session, user: User, kind: str, data: dict, category: MediaCategory | None = None) -> MediaCategory:
    if kind not in (KIND_BOOK, KIND_FILM):
        raise c.err(422, "INVALID_KIND")
    name = _text(data.get("name", category.name if category else None), "name", 120, True)
    slug = _slug(name)
    clash = db.scalar(select(MediaCategory.id).where(MediaCategory.kind == kind, MediaCategory.slug == slug, MediaCategory.id != (category.id if category else UUID(int=0))))
    if clash:
        raise c.err(409, "CATEGORY_EXISTS")
    if category is None:
        category = MediaCategory(kind=kind, name=name, slug=slug)
        db.add(category)
    category.name, category.slug = name, slug
    if "sort_order" in data:
        category.sort_order = _int(data["sort_order"], "sort_order", 0, 100000) or 0
    if "is_active" in data:
        category.is_active = bool(data["is_active"])
    db.commit()
    db.refresh(category)
    _audit(db, user, "medien_category_saved", f"{kind} {category.id} {category.name}")
    return category


def delete_category(db: Session, user: User, category: MediaCategory) -> None:
    model = MediaBook if category.kind == KIND_BOOK else Film
    if db.scalar(select(func.count()).select_from(model).where(model.category_id == category.id)):
        raise c.err(409, "CATEGORY_IN_USE: move or delete its content first, or hide the category.")
    cid = category.id
    db.delete(category)
    db.commit()
    _audit(db, user, "medien_category_deleted", str(cid))


# ---------------- generic item operations ----------------


def _file_status(key: str | None) -> str:
    if not key:
        return "none"
    return "ok" if c.file_path(key) else "missing"


def admin_card(kind: str, item, db: Session) -> dict:
    out = {**c.base_card(kind, item, None, True), "created_at": item.created_at, "updated_at": item.updated_at, "has_cover": bool(item.cover_key)}
    if kind == KIND_BOOK:
        out.update(author=item.author, category_id=item.category_id, year=item.year, file_format=item.file_format, file_size=item.file_size,
                   original_name=item.original_name, file_status=_file_status(item.file_key), views=item.view_count)
    elif kind == KIND_SONG:
        out.update(artist=item.artist, album=item.album, genre=item.genre, duration_ms=item.duration_ms, file_size=item.file_size,
                   original_name=item.original_name, file_status=_file_status(item.file_key), plays=item.play_count)
    else:
        subs = db.scalars(select(FilmSubtitle).where(FilmSubtitle.film_id == item.id).order_by(FilmSubtitle.language)).all()
        out.update(category_id=item.category_id, genre=item.genre, year=item.year, duration_minutes=item.duration_minutes, video_size=item.video_size,
                   original_name=item.original_name, external_url=item.external_url, processing_status=item.processing_status,
                   file_status=_file_status(item.video_key), views=item.view_count,
                   subtitles=[{"id": s.id, "language": s.language, "label": s.label, "file_status": _file_status(s.file_key)} for s in subs])
    return out


def admin_list(db: Session, kind: str, *, q: str | None = None, status: str | None = None, access: str | None = None, page: int = 1,
               page_size: int = 30) -> dict:
    model = c.MODELS[kind]
    stmt = select(model)
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(model.title.ilike(like))
    if status in STATUSES:
        stmt = stmt.where(model.status == status)
    if access in ACCESS_TYPES:
        stmt = stmt.where(model.access_type == access)
    size, page = max(1, min(page_size, 100)), max(1, page)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(model.created_at.desc()).limit(size).offset((page - 1) * size)).all()
    return {"items": [admin_card(kind, r, db) for r in rows], "total": total, "page": page, "page_size": size}


def get_item(db: Session, kind: str, item_id: UUID):
    item = db.get(c.MODELS[kind], item_id)
    if item is None:
        raise c.err(404, "NOT_FOUND")
    return item


def create_item(db: Session, user: User, kind: str, data: dict, **columns):
    item = c.MODELS[kind](**clean(db, kind, data), **columns)
    db.add(item)
    db.commit()
    db.refresh(item)
    _audit(db, user, f"medien_{kind.lower()}_created", f"{item.id} {item.title}")
    return item


def update_item(db: Session, user: User, kind: str, item, data: dict):
    for key, value in clean(db, kind, data, current=item).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    _audit(db, user, f"medien_{kind.lower()}_updated", f"{item.id} {','.join(sorted(data))}")
    return item


async def set_cover(db: Session, user: User, kind: str, item, file: UploadFile):
    key, _, _ = await c.save_upload(file, "covers", c.sniff_image, c.MAX_COVER, "The cover image")
    old, item.cover_key = item.cover_key, key
    db.commit()
    await c.remove_file(old)
    db.refresh(item)
    _audit(db, user, f"medien_{kind.lower()}_cover", str(item.id))
    return item


async def delete_item(db: Session, user: User, kind: str, item) -> None:
    keys = [item.cover_key, getattr(item, "file_key", None), getattr(item, "video_key", None)]
    if kind == KIND_FILM:
        keys += list(db.scalars(select(FilmSubtitle.file_key).where(FilmSubtitle.film_id == item.id)))
    item_id, title = item.id, item.title
    db.execute(delete(MediaPurchase).where(MediaPurchase.content_type == kind, MediaPurchase.content_id == item_id))
    if kind in (KIND_BOOK, KIND_FILM):
        db.execute(delete(MediaProgress).where(MediaProgress.content_type == kind, MediaProgress.content_id == item_id))
    db.delete(item)  # favorites, playlist entries, history, subtitles cascade
    db.commit()
    for key in keys:
        await c.remove_file(key)
    _audit(db, user, f"medien_{kind.lower()}_deleted", f"{item_id} {title}")


# ---------------- books ----------------


async def set_book_file(db: Session, user: User, book: MediaBook, file: UploadFile) -> MediaBook:
    key, ext, size = await c.save_upload(file, "books", c.sniff_pdf, c.MAX_BOOK, "The book file (PDF)")
    old = book.file_key
    book.file_key, book.file_format, book.file_size = key, ext, size
    book.original_name = (file.filename or "")[:255] or None
    db.commit()
    await c.remove_file(old)
    db.refresh(book)
    _audit(db, user, "medien_book_file", f"{book.id} {size} bytes")
    return book


# ---------------- songs ----------------


async def _store_song_file(file: UploadFile) -> tuple[str, str, int, int | None]:
    key, ext, size = await c.save_upload(file, "songs", c.sniff_audio, c.MAX_AUDIO, "The audio file")
    path = c.storage.ROOT / key
    duration = await asyncio.to_thread(audio.probe_duration_ms, path)
    if duration is None:
        path.unlink(missing_ok=True)
        raise c.err(400, "UNSUPPORTED_FILE: the audio file could not be read.")
    return key, ext, size, duration


async def create_song(db: Session, user: User, data: dict, file: UploadFile, cover: UploadFile | None = None) -> Song:
    """One song = one request (the bulk upload sends up to 10, each with its own metadata and progress; one failure
    never stops the others). Duration is read from the file."""
    values = clean(db, KIND_SONG, data)
    key, ext, size, duration = await _store_song_file(file)
    cover_key = None
    try:
        if cover is not None:
            cover_key, _, _ = await c.save_upload(cover, "covers", c.sniff_image, c.MAX_COVER, "The cover image")
        song = Song(**values, file_key=key, content_type=c.CONTENT_TYPES[ext], file_size=size, duration_ms=duration, cover_key=cover_key,
                    original_name=(file.filename or "")[:255] or None)
        db.add(song)
        db.commit()
    except Exception:
        db.rollback()
        await c.remove_file(key)
        await c.remove_file(cover_key)
        raise
    db.refresh(song)
    _audit(db, user, "medien_song_created", f"{song.id} {song.title}")
    return song


async def replace_song_file(db: Session, user: User, song: Song, file: UploadFile) -> Song:
    key, ext, size, duration = await _store_song_file(file)
    old = song.file_key
    song.file_key, song.content_type, song.file_size, song.duration_ms = key, c.CONTENT_TYPES[ext], size, duration
    song.original_name = (file.filename or "")[:255] or None
    db.commit()
    await c.remove_file(old)
    db.refresh(song)
    _audit(db, user, "medien_song_file", str(song.id))
    return song


# ---------------- films ----------------


def set_external_url(db: Session, user: User, film: Film, url: str | None) -> Film:
    url = (url or "").strip() or None
    if url is not None and not re.match(r"^https://[^\s]+$", url):
        raise c.err(422, "INVALID_URL: only https:// links are allowed.")
    film.external_url = url
    db.commit()
    db.refresh(film)
    _audit(db, user, "medien_film_external_url", f"{film.id} set={bool(url)}")
    return film


def _finish_video(db: Session, film: Film, key: str, ext: str, size: int, name: str | None) -> tuple[str | None, int | None]:
    old, film.video_key = film.video_key, key
    film.video_content_type, film.video_size, film.original_name, film.processing_status = c.CONTENT_TYPES[ext], size, name, "READY"
    duration = audio.probe_duration_ms(c.storage.ROOT / key)
    if duration and not film.duration_minutes:
        film.duration_minutes = max(1, round(duration / 60000))
    db.commit()
    return old, duration


async def set_video_file(db: Session, user: User, film: Film, file: UploadFile) -> Film:
    """Single request for a video up to 90 MB; larger files use the chunked upload below."""
    key, ext, size = await c.save_upload(file, "films", c.sniff_video, c.MAX_VIDEO_SINGLE, "The video file")
    old, _ = await asyncio.to_thread(_finish_video, db, film, key, ext, size, (file.filename or "")[:255] or None)
    await c.remove_file(old)
    db.refresh(film)
    _audit(db, user, "medien_film_video", f"{film.id} {size} bytes")
    return film


def _chunk_dir(upload_id: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{32}", upload_id):
        raise c.err(404, "UPLOAD_NOT_FOUND")
    return c.storage.ROOT / "chunks" / upload_id


def video_init(db: Session, user: User, film: Film, filename: str, size: int) -> dict:
    if not 0 < size <= c.MAX_VIDEO:
        raise c.err(422, f"INVALID_SIZE: 1 byte – {c.MAX_VIDEO // (1024 * c.MB)} GB.")
    upload_id = uuid4().hex
    folder = _chunk_dir(upload_id)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "meta.json").write_text(json.dumps({"film_id": str(film.id), "user_id": str(user.id), "name": (filename or "")[:255], "size": size}))
    film.processing_status = "UPLOADING"
    db.commit()
    return {"upload_id": upload_id, "chunk_size": CHUNK_SIZE, "chunks": -(-size // CHUNK_SIZE)}


def _meta(upload_id: str, film: Film) -> tuple[Path, dict]:
    folder = _chunk_dir(upload_id)
    try:
        meta = json.loads((folder / "meta.json").read_text())
    except (OSError, ValueError):
        raise c.err(404, "UPLOAD_NOT_FOUND") from None
    if meta["film_id"] != str(film.id):
        raise c.err(404, "UPLOAD_NOT_FOUND")
    return folder, meta


async def video_part(film: Film, upload_id: str, index: int, stream) -> int:
    """Writes one chunk (raw request body) to disk without holding it in memory; a repeated index replaces it (retry)."""
    folder, meta = _meta(upload_id, film)
    total = -(-meta["size"] // CHUNK_SIZE)
    if not 0 <= index < total:
        raise c.err(422, "INVALID_CHUNK_INDEX")
    target, written = folder / f"part_{index:06d}", 0
    with open(target, "wb") as handle:
        async for piece in stream:
            written += len(piece)
            if written > MAX_CHUNK:
                handle.close()
                target.unlink(missing_ok=True)
                raise c.err(413, "CHUNK_TOO_LARGE")
            await asyncio.to_thread(handle.write, piece)
    return written


def _assemble(folder: Path, total: int, size: int, key: str) -> int:
    destination = c.storage.ROOT / key
    destination.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(destination, "wb") as out:
        for i in range(total):
            with open(folder / f"part_{i:06d}", "rb") as part:
                written += shutil.copyfileobj(part, out) or 0
    return destination.stat().st_size


async def video_complete(db: Session, user: User, film: Film, upload_id: str) -> Film:
    folder, meta = _meta(upload_id, film)
    total = -(-meta["size"] // CHUNK_SIZE)
    missing = [i for i in range(total) if not (folder / f"part_{i:06d}").is_file()]
    if missing:
        raise c.err(409, f"MISSING_CHUNKS: {len(missing)} of {total} chunks are missing (first: {missing[0]}).")
    first = (folder / "part_000000").read_bytes()[:16]
    ext = c.sniff_video(first)
    if ext is None:
        shutil.rmtree(folder, ignore_errors=True)
        film.processing_status = "FAILED"
        db.commit()
        raise c.err(400, "UNSUPPORTED_FILE: the video must be MP4, MOV or WebM.")
    key = f"films/{uuid4().hex}.{ext}"
    size = await asyncio.to_thread(_assemble, folder, total, meta["size"], key)
    shutil.rmtree(folder, ignore_errors=True)
    if size != meta["size"]:
        await c.remove_file(key)
        film.processing_status = "FAILED"
        db.commit()
        raise c.err(422, "SIZE_MISMATCH: the assembled file does not have the announced size.")
    old, _ = await asyncio.to_thread(_finish_video, db, film, key, ext, size, meta["name"] or None)
    await c.remove_file(old)
    db.refresh(film)
    _audit(db, user, "medien_film_video", f"{film.id} {size} bytes (chunked)")
    return film


def video_abort(db: Session, film: Film, upload_id: str) -> None:
    folder, _ = _meta(upload_id, film)
    shutil.rmtree(folder, ignore_errors=True)
    if film.processing_status == "UPLOADING":
        film.processing_status = "READY" if film.video_key else "NONE"
        db.commit()


def _to_vtt(raw: bytes) -> bytes:
    """WebVTT as is; SubRip (.srt) converted (comma -> dot in the timestamps, header added)."""
    text = raw.decode("utf-8-sig", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    if text.lstrip().startswith("WEBVTT"):
        return text.encode("utf-8")
    if not re.search(r"\d\d:\d\d:\d\d[,.]\d{3}\s*-->\s*\d\d:\d\d:\d\d[,.]\d{3}", text):
        raise c.err(400, "UNSUPPORTED_FILE: the subtitle file must be WebVTT or SRT.")
    return ("WEBVTT\n\n" + re.sub(r"(\d\d:\d\d:\d\d),(\d{3})", r"\1.\2", text)).encode("utf-8")


async def save_subtitle(db: Session, user: User, film: Film, language: str, label: str | None, file: UploadFile) -> FilmSubtitle:
    language = (language or "").strip().lower()
    if language not in ("de", "uz", "en", "ru"):
        raise c.err(422, "INVALID_LANGUAGE: de, uz, en or ru.")
    raw = await file.read(c.MAX_SUBTITLE + 1)
    if len(raw) > c.MAX_SUBTITLE:
        raise c.err(400, "FILE_TOO_LARGE: subtitles are limited to 2 MB.")
    vtt = _to_vtt(raw)
    key = f"subtitles/{uuid4().hex}.vtt"
    path = c.storage.ROOT / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(vtt)
    sub = db.scalar(select(FilmSubtitle).where(FilmSubtitle.film_id == film.id, FilmSubtitle.language == language))
    old = sub.file_key if sub else None
    labels = {"de": "Deutsch", "uz": "O'zbekcha", "en": "English", "ru": "Русский"}
    if sub is None:
        sub = FilmSubtitle(film_id=film.id, language=language, label=_text(label, "label", 80) or labels[language], file_key=key)
        db.add(sub)
    else:
        sub.file_key = key
        if label:
            sub.label = _text(label, "label", 80) or sub.label
    db.commit()
    await c.remove_file(old)
    _audit(db, user, "medien_film_subtitle", f"{film.id} {language}")
    return sub


async def delete_subtitle(db: Session, user: User, film: Film, subtitle_id: UUID) -> None:
    sub = db.get(FilmSubtitle, subtitle_id)
    if sub is None or sub.film_id != film.id:
        raise c.err(404, "NOT_FOUND")
    key = sub.file_key
    db.delete(sub)
    db.commit()
    await c.remove_file(key)
    _audit(db, user, "medien_film_subtitle_deleted", f"{film.id} {subtitle_id}")


# ---------------- official playlists ----------------


def list_playlists(db: Session) -> list[dict]:
    counts = dict(db.execute(select(PlaylistSong.playlist_id, func.count()).group_by(PlaylistSong.playlist_id)).all())
    rows = db.scalars(select(Playlist).where(Playlist.owner_id.is_(None)).order_by(Playlist.sort_order, Playlist.created_at)).all()
    return [{"id": p.id, "name": p.name, "description": p.description, "status": p.status, "sort_order": p.sort_order, "song_count": counts.get(p.id, 0),
             "has_cover": bool(p.cover_key), "cover_url": f"/api/v1/medien/cover/PLAYLIST/{p.id}?v={int(p.updated_at.timestamp())}" if p.cover_key else None} for p in rows]


def _official(db: Session, playlist_id: UUID) -> Playlist:
    pl = db.get(Playlist, playlist_id)
    if pl is None or pl.owner_id is not None:
        raise c.err(404, "NOT_FOUND")
    return pl


def save_playlist(db: Session, user: User, data: dict, playlist: Playlist | None = None) -> Playlist:
    name = _text(data.get("name", playlist.name if playlist else None), "name", 160, True)
    if playlist is None:
        playlist = Playlist(owner_id=None, name=name)
        db.add(playlist)
    playlist.name = name
    if "description" in data:
        playlist.description = (data["description"] or "").strip()[:2000] or None
    if "status" in data:
        if data["status"] not in STATUSES:
            raise c.err(422, "INVALID_STATUS")
        playlist.status = data["status"]
    if "sort_order" in data:
        playlist.sort_order = _int(data["sort_order"], "sort_order", 0, 100000) or 0
    db.commit()
    db.refresh(playlist)
    _audit(db, user, "medien_playlist_saved", f"{playlist.id} {playlist.name}")
    return playlist


async def playlist_cover(db: Session, user: User, playlist: Playlist, file: UploadFile) -> Playlist:
    key, _, _ = await c.save_upload(file, "covers", c.sniff_image, c.MAX_COVER, "The cover image")
    old, playlist.cover_key = playlist.cover_key, key
    db.commit()
    await c.remove_file(old)
    db.refresh(playlist)
    return playlist


async def delete_playlist(db: Session, user: User, playlist: Playlist) -> None:
    key, pid = playlist.cover_key, playlist.id
    db.delete(playlist)
    db.commit()
    await c.remove_file(key)
    _audit(db, user, "medien_playlist_deleted", str(pid))


def playlist_songs(db: Session, playlist: Playlist) -> list[dict]:
    rows = db.execute(select(Song, PlaylistSong.position).join(PlaylistSong, PlaylistSong.song_id == Song.id)
                      .where(PlaylistSong.playlist_id == playlist.id).order_by(PlaylistSong.position)).all()
    return [{"id": s.id, "title": s.title, "artist": s.artist, "status": s.status, "position": p} for s, p in rows]


def playlist_set_songs(db: Session, user: User, playlist: Playlist, song_ids: list[UUID]) -> list[dict]:
    """Replaces the songs and their order by `song_ids` (no duplicates, every song must exist)."""
    if len(set(song_ids)) != len(song_ids):
        raise c.err(422, "DUPLICATE_SONGS")
    found = set(db.scalars(select(Song.id).where(Song.id.in_(song_ids)))) if song_ids else set()
    if found != set(song_ids):
        raise c.err(422, "UNKNOWN_SONG")
    db.execute(delete(PlaylistSong).where(PlaylistSong.playlist_id == playlist.id))
    db.add_all([PlaylistSong(playlist_id=playlist.id, song_id=sid, position=i) for i, sid in enumerate(song_ids)])
    db.commit()
    _audit(db, user, "medien_playlist_songs", f"{playlist.id} {len(song_ids)} songs")
    return playlist_songs(db, playlist)


# ---------------- purchases ----------------


def list_purchases(db: Session, status: str | None = None, limit: int = 200) -> list[dict]:
    stmt = select(MediaPurchase, User.email, User.username).join(User, User.id == MediaPurchase.user_id).order_by(MediaPurchase.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(MediaPurchase.status == status)
    out = []
    for p, email, username in db.execute(stmt).all():
        item = db.get(c.MODELS[p.content_type], p.content_id)
        out.append({"id": p.id, "user_id": p.user_id, "user_email": email, "user_name": username, "kind": p.content_type, "content_id": p.content_id,
                    "title": item.title if item else None, "price": p.price, "status": p.status, "note": p.note, "created_at": p.created_at,
                    "decided_at": p.decided_at})
    return out


def decide_purchase(db: Session, user: User, purchase_id: UUID, new_status: str, note: str | None) -> MediaPurchase:
    from datetime import datetime, timezone

    row = db.scalar(select(MediaPurchase).where(MediaPurchase.id == purchase_id).with_for_update())
    if row is None:
        raise c.err(404, "NOT_FOUND")
    allowed = {PURCHASE_GRANTED: {PURCHASE_REQUESTED}, PURCHASE_REJECTED: {PURCHASE_REQUESTED}, PURCHASE_REVOKED: {PURCHASE_GRANTED}}
    if new_status not in allowed or row.status not in allowed[new_status]:
        raise c.err(409, f"INVALID_TRANSITION: {row.status} -> {new_status}")
    row.status, row.note = new_status, (note or "").strip()[:500] or None
    row.decided_by_id, row.decided_at = user.id, datetime.now(timezone.utc)
    db.commit()
    _audit(db, user, f"medien_purchase_{new_status.lower()}", f"{row.id} user={row.user_id} {row.content_type} {row.content_id}")
    return row


def grant_to_user(db: Session, user: User, target_user_id: UUID, kind: str, item_id: UUID, note: str | None) -> MediaPurchase:
    """Admin gives a student access without a request (e.g. after a payment arrived by the usual manual way)."""
    from datetime import datetime, timezone

    item = get_item(db, kind, item_id)
    if item.access_type != ACCESS_PAID:
        raise c.err(409, "NOT_PAID: this content is free.")
    if db.get(User, target_user_id) is None:
        raise c.err(404, "USER_NOT_FOUND")
    row = db.scalar(select(MediaPurchase).where(MediaPurchase.user_id == target_user_id, MediaPurchase.content_type == kind,
                                                 MediaPurchase.content_id == item.id, MediaPurchase.status.in_(("REQUESTED", "GRANTED"))).with_for_update())
    if row is not None and row.status == PURCHASE_GRANTED:
        return row
    if row is None:
        row = MediaPurchase(user_id=target_user_id, content_type=kind, content_id=item.id, price=item.price)
        db.add(row)
    row.status, row.note = PURCHASE_GRANTED, (note or "").strip()[:500] or None
    row.decided_by_id, row.decided_at = user.id, datetime.now(timezone.utc)
    db.commit()
    _audit(db, user, "medien_purchase_granted", f"{row.id} user={target_user_id} {kind} {item.id} (direct)")
    return row


# ---------------- statistics ----------------


def stats(db: Session) -> dict:
    def count(model, *where):
        return db.scalar(select(func.count()).select_from(model).where(*where)) or 0

    def top(model, counter, label):
        rows = db.execute(select(model.id, model.title, counter).where(counter > 0).order_by(counter.desc()).limit(5)).all()
        return [{"id": r[0], "title": r[1], label: r[2]} for r in rows]

    books = {"total": count(MediaBook), "free": count(MediaBook, MediaBook.access_type == ACCESS_FREE), "paid": count(MediaBook, MediaBook.access_type == ACCESS_PAID),
             "published": count(MediaBook, MediaBook.status == STATUS_PUBLISHED)}
    songs = {"total": count(Song), "published": count(Song, Song.status == STATUS_PUBLISHED), "playlists": count(Playlist, Playlist.owner_id.is_(None)),
             "student_playlists": count(Playlist, Playlist.owner_id.is_not(None))}
    films = {"total": count(Film), "free": count(Film, Film.access_type == ACCESS_FREE), "paid": count(Film, Film.access_type == ACCESS_PAID),
             "published": count(Film, Film.status == STATUS_PUBLISHED)}
    total = books["total"] + songs["total"] + films["total"]
    published = books["published"] + songs["published"] + films["published"]
    return {"books": books, "songs": songs, "films": films, "published": published, "draft": total - published, "total": total,
            "pending_purchases": count(MediaPurchase, MediaPurchase.status == PURCHASE_REQUESTED),
            "most_read_books": top(MediaBook, MediaBook.view_count, "views"), "most_played_songs": top(Song, Song.play_count, "plays"),
            "most_watched_films": top(Film, Film.view_count, "views"), "plays_total": db.scalar(select(func.count()).select_from(MediaPlayHistory)) or 0}
