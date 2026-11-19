"""Student side of Medienwelt: catalog (search / filter / sort / pagination), opening content through signed URLs, reading
and watching progress, favorites, playlists, play history and purchase requests. Only PUBLISHED content is listed; a
PAID item shows cover, text and price until the student owns it. No function here returns a storage key or path."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session

from app.models.medien import (ACCESS_FREE, ACCESS_PAID, KIND_BOOK, KIND_FILM, KIND_SONG, PURCHASE_REQUESTED, SOURCE_AI, STATUS_PUBLISHED,
                               SUBTITLE_APPROVED, BookPaymentRequest, Film,
                               FilmRendition, FilmSubtitle, MediaBook, MediaCategory, MediaPlayHistory, MediaProgress, MediaPurchase, Playlist,
                               PlaylistSong, Song, UserFavoriteSong)
from app.models.user import User
from app.services.medien import common as c
from app.services.medien import pdf_tools, player, subtitles

log = logging.getLogger("vizu.medien.books")
MAX_PAGE_SIZE = 60
SORTS = {"new", "popular", "title"}


def _like(q: str):
    return f"%{q.strip().replace(chr(92), chr(92) * 2).replace('%', chr(92) + '%').replace('_', chr(92) + '_')}%"


def _paginate(db: Session, stmt, page: int, size: int):
    size = max(1, min(size, MAX_PAGE_SIZE))
    page = max(1, page)
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.scalars(stmt.limit(size).offset((page - 1) * size)).all()
    return rows, {"total": total, "page": page, "page_size": size}


def _published(model):
    return model.status == STATUS_PUBLISHED


def _order(model, sort: str, counter):
    if sort == "popular":
        return (counter.desc(), model.created_at.desc())
    if sort == "title":
        return (func.lower(model.title).asc(),)
    return (model.created_at.desc(),)


# ---------------- serialization ----------------


def _category(db: Session, cache: dict, category_id) -> dict | None:
    if category_id is None:
        return None
    if category_id not in cache:
        cat = db.get(MediaCategory, category_id)
        cache[category_id] = {"id": cat.id, "name": cat.name, "slug": cat.slug} if cat else None
    return cache[category_id]


def book_card(db: Session, user: User | None, book: MediaBook, owned: set, cats: dict) -> dict:
    return {**c.base_card(KIND_BOOK, book, owned, c.is_staff(user)), "author": book.author, "category": _category(db, cats, book.category_id),
            "year": book.year, "file_format": book.file_format, "has_file": bool(book.file_key)}


def song_card(db: Session, user: User | None, song: Song, owned: set, favs: set) -> dict:
    return {**c.base_card(KIND_SONG, song, owned, c.is_staff(user)), "artist": song.artist, "album": song.album, "genre": song.genre,
            "duration_ms": song.duration_ms, "favorite": song.id in favs}


def film_card(db: Session, user: User | None, film: Film, owned: set, cats: dict, subtitle_count: int | None = None) -> dict:
    playable = bool(film.video_key and film.processing_status == "READY") or bool(film.external_url)
    out = {**c.base_card(KIND_FILM, film, owned, c.is_staff(user)), "category": _category(db, cats, film.category_id), "genre": film.genre,
           "year": film.year, "duration_minutes": film.duration_minutes, "playable": playable}
    if subtitle_count is not None:
        out["subtitle_count"] = subtitle_count
    return out


def _favs(db: Session, user: User) -> set:
    return set(db.scalars(select(UserFavoriteSong.song_id).where(UserFavoriteSong.user_id == user.id)))


# ---------------- catalog ----------------


def categories(db: Session, kind: str) -> list[dict]:
    model = MediaBook if kind == KIND_BOOK else Film
    counts = dict(db.execute(select(model.category_id, func.count()).where(_published(model)).group_by(model.category_id)).all())
    rows = db.scalars(select(MediaCategory).where(MediaCategory.kind == kind, MediaCategory.is_active.is_(True))
                      .order_by(MediaCategory.sort_order, MediaCategory.name)).all()
    return [{"id": r.id, "name": r.name, "slug": r.slug, "count": counts.get(r.id, 0)} for r in rows]


def _category_filter(db: Session, kind: str, value: str):
    """A category by id or slug -> its id; an unknown value matches nothing."""
    try:
        return UUID(value)
    except ValueError:
        return db.scalar(select(MediaCategory.id).where(MediaCategory.kind == kind, MediaCategory.slug == value)) or UUID(int=0)


def list_books(db: Session, user: User | None, *, category=None, level=None, q=None, sort="new", special=False, access=None, featured=False,
               page=1, page_size=24) -> dict:
    stmt = select(MediaBook).where(_published(MediaBook))
    if category:
        stmt = stmt.where(MediaBook.category_id == _category_filter(db, KIND_BOOK, category))
    if level in c.LEVELS:
        stmt = stmt.where(MediaBook.level == level)
    if q and q.strip():
        stmt = stmt.where(or_(MediaBook.title.ilike(_like(q), escape="\\"), MediaBook.author.ilike(_like(q), escape="\\")))
    if access in (ACCESS_FREE, ACCESS_PAID):
        stmt = stmt.where(MediaBook.access_type == access)
    if special:
        stmt = stmt.where(MediaBook.is_special_offer.is_(True), MediaBook.access_type == ACCESS_PAID)
    if featured:
        stmt = stmt.where(MediaBook.is_featured.is_(True))
    rows, meta = _paginate(db, stmt.order_by(*_order(MediaBook, sort, MediaBook.view_count)), page, page_size)
    owned, cats = c.owned_ids(db, user, KIND_BOOK), {}
    return {"items": [book_card(db, user, b, owned, cats) for b in rows], **meta}


def list_songs(db: Session, user: User, *, q=None, sort="new", featured=False, favorites=False, playlist_id=None, genre=None, level=None,
               page=1, page_size=30) -> dict:
    stmt = select(Song).where(_published(Song))
    if q and q.strip():
        stmt = stmt.where(or_(Song.title.ilike(_like(q), escape="\\"), Song.artist.ilike(_like(q), escape="\\"), Song.album.ilike(_like(q), escape="\\")))
    if featured:
        stmt = stmt.where(Song.is_featured.is_(True))
    if genre:
        stmt = stmt.where(Song.genre == genre)
    if level in c.LEVELS:
        stmt = stmt.where(Song.level == level)
    if favorites:
        stmt = stmt.where(Song.id.in_(select(UserFavoriteSong.song_id).where(UserFavoriteSong.user_id == user.id)))
    if playlist_id:
        _visible_playlist(db, user, playlist_id)
        stmt = stmt.join(PlaylistSong, PlaylistSong.song_id == Song.id).where(PlaylistSong.playlist_id == playlist_id)
        order = (PlaylistSong.position.asc(),)
    else:
        order = _order(Song, sort, Song.play_count)
    rows, meta = _paginate(db, stmt.order_by(*order), page, page_size)
    owned, favs = c.owned_ids(db, user, KIND_SONG), _favs(db, user)
    return {"items": [song_card(db, user, s, owned, favs) for s in rows], **meta}


def list_films(db: Session, user: User | None, *, category=None, level=None, q=None, genre=None, access=None, min_minutes=None,
               max_minutes=None, featured=False, special=False, sort="new", page=1, page_size=24) -> dict:
    stmt = select(Film).where(_published(Film))
    if category:
        stmt = stmt.where(Film.category_id == _category_filter(db, KIND_FILM, category))
    if level in c.LEVELS:
        stmt = stmt.where(Film.level == level)
    if q and q.strip():
        stmt = stmt.where(Film.title.ilike(_like(q), escape="\\"))
    if genre:
        stmt = stmt.where(Film.genre == genre)
    if access in (ACCESS_FREE, ACCESS_PAID):
        stmt = stmt.where(Film.access_type == access)
    if min_minutes is not None:
        stmt = stmt.where(Film.duration_minutes >= min_minutes)
    if max_minutes is not None:
        stmt = stmt.where(Film.duration_minutes <= max_minutes)
    if featured:
        stmt = stmt.where(Film.is_featured.is_(True))
    if special:
        stmt = stmt.where(Film.is_special_offer.is_(True), Film.access_type == ACCESS_PAID)
    rows, meta = _paginate(db, stmt.order_by(*_order(Film, sort, Film.view_count)), page, page_size)
    owned, cats = c.owned_ids(db, user, KIND_FILM), {}
    return {"items": [film_card(db, user, f, owned, cats) for f in rows], **meta}


def previewable(book: MediaBook) -> bool:
    """A published PAID book with a PDF and a preview of at least one page: its first pages may be read without buying."""
    return bool(book.status == STATUS_PUBLISHED and book.access_type == ACCESS_PAID and (book.preview_pages_count or 0) > 0 and book.file_key)


def preview_limit(book: MediaBook) -> int:
    """How many first pages a student without access may read: the admin's number (default 10), but never the whole book — at least the last page
    stays closed (a 4-page paid book with the default 10 shows 3 pages, a 1-page book none). 0 = no preview, also while the page count is unknown."""
    if not previewable(book) or not book.page_count:
        return 0
    return max(0, min(book.preview_pages_count, book.page_count - 1))


def ensure_page_count(db: Session, book: MediaBook) -> int | None:
    """Pages of the PDF; read once (older books have none stored) and kept."""
    if book.page_count:
        return book.page_count
    path = c.file_path(book.file_key)
    count = pdf_tools.page_count(path) if path else None
    if count:
        book.page_count = count
        db.commit()
    return count


def preview_path(book: MediaBook, pages: int) -> Path:
    """`previews/<book>-<file stem>-<N>.pdf`: a replaced PDF or another N means another name, so a stale preview is never served."""
    return c.storage.ROOT / "previews" / f"{book.id}-{Path(book.file_key).stem}-{pages}.pdf"


def ensure_preview(book: MediaBook) -> Path | None:
    """The preview PDF (only the first `preview_limit` pages, built on the server and cached), or None when there is none or it cannot be made."""
    pages = preview_limit(book)
    if pages <= 0:
        return None
    dest = preview_path(book, pages)
    if dest.is_file():
        return dest
    src = c.file_path(book.file_key)
    if src is None:
        return None
    try:
        pdf_tools.build_preview(src, pages, dest)
    except (pdf_tools.PdfUnreadable, OSError) as exc:
        log.warning("book preview could not be built (%s)", type(exc).__name__)
        return None
    return dest


def _latest_payment(db: Session, user: User, book_id: UUID) -> dict | None:
    row = db.scalar(select(BookPaymentRequest).where(BookPaymentRequest.user_id == user.id, BookPaymentRequest.book_id == book_id)
                    .order_by(BookPaymentRequest.created_at.desc()).limit(1))
    if row is None:
        return None
    return {"id": row.id, "status": row.payment_status, "created_at": row.created_at, "reviewed_at": row.reviewed_at,
            "admin_note": row.admin_note if row.payment_status == "REJECTED" else None}


def book_detail(db: Session, user: User, book_id: UUID) -> dict:
    book = c.item_or_404(db, KIND_BOOK, book_id, user)
    card = book_card(db, user, book, c.owned_ids(db, user, KIND_BOOK), {})
    if card["locked"] and previewable(book):
        ensure_page_count(db, book)  # books from before the preview feature have no page count yet; read once, kept
    limit = preview_limit(book) if card["locked"] else 0
    return {**card, "progress": progress(db, user, KIND_BOOK, book.id), "preview_pages_count": limit or book.preview_pages_count, "page_count": book.page_count,
            "preview_available": limit > 0, "can_download": bool(book.file_key) and not card["locked"], "my_payment": _latest_payment(db, user, book.id)}


def subtitles_of(db: Session, film_id: UUID) -> list[FilmSubtitle]:
    """The tracks students get: APPROVED only (an AI draft waits for the admin)."""
    return list(db.scalars(select(FilmSubtitle).where(FilmSubtitle.film_id == film_id, FilmSubtitle.status == SUBTITLE_APPROVED)
                           .order_by(FilmSubtitle.language)))


def original_language(film: Film, tracks: list[FilmSubtitle]) -> str:
    """The language spoken in the film (shown on top in the dual view): the track transcribed from the audio when there is one, else the
    film's language field."""
    for s in tracks:
        if s.source == SOURCE_AI:
            return s.language
    return film.language or "de"


def film_detail(db: Session, user: User, film_id: UUID) -> dict:
    film = c.item_or_404(db, KIND_FILM, film_id, user)
    subs = subtitles_of(db, film.id)
    return {**film_card(db, user, film, c.owned_ids(db, user, KIND_FILM), {}, len(subs)),
            "subtitles": [{"id": s.id, "language": s.language, "label": s.label} for s in subs], "progress": progress(db, user, KIND_FILM, film.id)}


def special_offers(db: Session, user: User | None, limit: int = 12) -> list[dict]:
    """PAID, published items the admin put on the special-offer list (books and films)."""
    out = []
    owned_b, owned_f = c.owned_ids(db, user, KIND_BOOK), c.owned_ids(db, user, KIND_FILM)
    for b in db.scalars(select(MediaBook).where(_published(MediaBook), MediaBook.is_special_offer.is_(True), MediaBook.access_type == ACCESS_PAID)
                        .order_by(MediaBook.created_at.desc()).limit(limit)):
        out.append(book_card(db, user, b, owned_b, {}))
    for f in db.scalars(select(Film).where(_published(Film), Film.is_special_offer.is_(True), Film.access_type == ACCESS_PAID)
                        .order_by(Film.created_at.desc()).limit(limit)):
        out.append(film_card(db, user, f, owned_f, {}))
    return out[:limit]


# ---------------- open / play / watch (signed URLs) ----------------


def _touch_opened(db: Session, user: User, kind: str, item_id: UUID) -> None:
    row = db.scalar(select(MediaProgress).where(MediaProgress.user_id == user.id, MediaProgress.content_type == kind, MediaProgress.content_id == item_id).with_for_update())
    if row is None:
        row = MediaProgress(user_id=user.id, content_type=kind, content_id=item_id, position=0)
        db.add(row)
    row.last_opened_at = datetime.now(timezone.utc)


def open_book(db: Session, user: User, book_id: UUID) -> dict:
    """The reader's PDF. Owners (free, bought, staff) get the full file; everyone else a PAID book's PREVIEW — a separate PDF that holds only its
    first N pages (the original is never streamed to them). 403 PURCHASE_REQUIRED when there is no preview."""
    book = c.item_or_404(db, KIND_BOOK, book_id, user)
    full = c.can_access(db, user, KIND_BOOK, book)
    if not full and not previewable(book):
        raise c.err(403, "PURCHASE_REQUIRED")
    if not c.file_path(book.file_key):
        raise c.err(404, "FILE_MISSING")
    total = ensure_page_count(db, book)
    stream = f"/api/v1/medien/stream/{KIND_BOOK}/{book.id}"
    if full:
        url, mode, limit = c.signed_url(stream, book.id, user), "full", None
    else:
        if ensure_preview(book) is None:  # no preview (page count unknown / one page / the PDF cannot be read): the book simply stays locked
            raise c.err(403, "PURCHASE_REQUIRED")
        url, mode, limit = c.signed_url(stream, book.id, user, "preview"), "preview", preview_limit(book)
    _touch_opened(db, user, KIND_BOOK, book.id)
    db.execute(update(MediaBook).where(MediaBook.id == book.id).values(view_count=MediaBook.view_count + 1))
    db.commit()
    return {"url": url, "title": book.title, "progress": progress(db, user, KIND_BOOK, book.id), "mode": mode, "preview_pages": limit,
            "total_pages": total, "can_download": full and bool(book.file_key)}


def download_link(db: Session, user: User, book_id: UUID) -> dict:
    """A short-lived download URL for the ORIGINAL PDF — only for who may read the whole book (free, bought, staff); a preview reader gets 403."""
    book = c.item_or_404(db, KIND_BOOK, book_id, user)
    c.require_access(db, user, KIND_BOOK, book)
    if not c.file_path(book.file_key):
        raise c.err(404, "FILE_MISSING")
    filename = c.safe_filename(book.title)
    log.info("book download link issued for book %s", book.id)
    return {"url": c.signed_url(f"/api/v1/medien/download/book/{book.id}", book.id, user, "download"), "filename": filename}


def download_target(db: Session, book_id: UUID, token: str):
    """(path, download name) for a valid download token whose user still has full access right now."""
    user = c.read_token(db, token, book_id, "download")
    book = c.item_or_404(db, KIND_BOOK, book_id, user)
    c.require_access(db, user, KIND_BOOK, book)
    path = c.file_path(book.file_key)
    if path is None:
        raise c.err(404, "FILE_MISSING")
    return path, c.safe_filename(book.title)


def play_song(db: Session, user: User, song_id: UUID, *, count: bool = True) -> dict:
    song = c.item_or_404(db, KIND_SONG, song_id, user)
    c.require_access(db, user, KIND_SONG, song)
    if not c.file_path(song.file_key):
        raise c.err(404, "FILE_MISSING")
    if count:
        db.execute(update(Song).where(Song.id == song.id).values(play_count=Song.play_count + 1))
        db.add(MediaPlayHistory(user_id=user.id, song_id=song.id))
        db.commit()
    return {"url": c.signed_url(f"/api/v1/medien/stream/{KIND_SONG}/{song.id}", song.id, user), "id": song.id}


def renditions_of(db: Session, film_id: UUID) -> list[FilmRendition]:
    rows = list(db.scalars(select(FilmRendition).where(FilmRendition.film_id == film_id)))
    return sorted(rows, key=lambda r: (-(r.height or 0), r.label))


def watch_film(db: Session, user: User, film_id: UUID) -> dict:
    """Everything the player needs, in one answer: the video source (+ extra qualities), the subtitle tracks (signed URLs of the
    cue lists), the last position and state, the student's player settings, and the previous / next film."""
    film = c.item_or_404(db, KIND_FILM, film_id, user)
    c.require_access(db, user, KIND_FILM, film)
    subs = []
    tracks = subtitles_of(db, film.id)
    for s in tracks:
        base = f"/api/v1/medien/subtitles/{s.id}"
        subs.append({"id": s.id, "language": s.language, "label": s.label, "url": c.signed_url(base, s.id, user, "subtitle"),
                     "cues_url": c.signed_url(f"{base}/cues", s.id, user, "subtitle"), "cue_count": s.cue_count,
                     "source": s.source, "source_language": s.source_language})
    sources: list[dict] = []
    if film.video_key and film.processing_status == "READY" and c.file_path(film.video_key):
        source = {"type": "file", "url": c.signed_url(f"/api/v1/medien/stream/{KIND_FILM}/{film.id}", film.id, user)}
        sources.append({"id": "main", "label": "Original", "height": None, "url": source["url"]})
        for r in renditions_of(db, film.id):
            if c.file_path(r.file_key):
                sources.append({"id": str(r.id), "label": r.label, "height": r.height,
                                "url": c.signed_url(f"/api/v1/medien/rendition/{r.id}", r.id, user, "rendition")})
    elif film.external_url:
        source = {"type": "external", "url": film.external_url}
    else:
        raise c.err(404, "FILE_MISSING")
    db.execute(update(Film).where(Film.id == film.id).values(view_count=Film.view_count + 1))
    db.commit()
    return {"title": film.title, "source": source, "sources": sources, "subtitles": subs, "progress": progress(db, user, KIND_FILM, film.id),
            "prefs": player.get_prefs(db, user), "neighbors": player.neighbors(db, film), "duration_ms": film.video_duration_ms,
            "original_language": original_language(film, tracks)}


def stream_target(db: Session, kind: str, item_id: UUID, token: str):
    """(path, content type) for a valid token: the token user must still have access to the item right now. A book "preview" token only ever
    reaches the preview PDF (first N pages), never the original."""
    user, what = c.read_token_any(db, token, item_id, ("file", "preview") if kind == KIND_BOOK else ("file",))
    item = c.item_or_404(db, kind, item_id, user)
    if what == "preview":
        if not previewable(item):
            raise c.err(403, "PURCHASE_REQUIRED")
        path = ensure_preview(item)
        if path is None:
            raise c.err(403, "PURCHASE_REQUIRED")
        return path, "application/pdf"
    c.require_access(db, user, kind, item)
    key = item.video_key if kind == KIND_FILM else item.file_key
    path = c.file_path(key)
    if path is None:
        raise c.err(404, "FILE_MISSING")
    return path, (getattr(item, "video_content_type", None) or getattr(item, "content_type", None) or c.CONTENT_TYPES.get(path.suffix.lstrip("."), "application/octet-stream"))


def subtitle_target(db: Session, subtitle_id: UUID, token: str):
    user = c.read_token(db, token, subtitle_id, "subtitle")
    sub = db.get(FilmSubtitle, subtitle_id)
    if sub is None or (sub.status != SUBTITLE_APPROVED and not c.is_staff(user)):  # a draft (also with an old token) is never served to a student
        raise c.err(404, "NOT_FOUND")
    film = c.item_or_404(db, KIND_FILM, sub.film_id, user)
    c.require_access(db, user, KIND_FILM, film)
    path = c.file_path(sub.file_key)
    if path is None:
        raise c.err(404, "FILE_MISSING")
    return path


def subtitle_cues(db: Session, subtitle_id: UUID, token: str) -> dict:
    """The cue list of one subtitle track as plain text ([[start_ms, end_ms, text], …]) — same token / access check as the file;
    the text always went through the sanitiser, and a damaged stored file gives an empty list instead of an error."""
    path = subtitle_target(db, subtitle_id, token)
    sub = db.get(FilmSubtitle, subtitle_id)
    try:
        cues = subtitles.read_cues(path.read_bytes())
    except subtitles.SubtitleError:
        cues = []
    return {"language": sub.language, "label": sub.label, "cues": subtitles.cues_json(cues)}


def rendition_target(db: Session, rendition_id: UUID, token: str):
    """(path, content type) of an additional video quality: signed token, access checked again (PAID = purchased)."""
    user = c.read_token(db, token, rendition_id, "rendition")
    rendition = db.get(FilmRendition, rendition_id)
    if rendition is None:
        raise c.err(404, "NOT_FOUND")
    film = c.item_or_404(db, KIND_FILM, rendition.film_id, user)
    c.require_access(db, user, KIND_FILM, film)
    path = c.file_path(rendition.file_key)
    if path is None:
        raise c.err(404, "FILE_MISSING")
    return path, rendition.content_type


def cover_target(db: Session, kind: str, item_id: UUID):
    """Covers and posters are the only public Medienwelt files (a PAID item shows its cover to everyone)."""
    model = Playlist if kind == "PLAYLIST" else c.MODELS.get(kind)
    item = db.get(model, item_id) if model is not None else None
    path = c.file_path(item.cover_key) if item is not None else None
    if path is None:
        raise c.err(404, "NOT_FOUND")
    return path, c.CONTENT_TYPES.get(path.suffix.lstrip("."), "image/jpeg")


# ---------------- progress / continue ----------------


def progress(db: Session, user: User, kind: str, item_id: UUID) -> dict | None:
    row = db.scalar(select(MediaProgress).where(MediaProgress.user_id == user.id, MediaProgress.content_type == kind, MediaProgress.content_id == item_id))
    if row is None:
        return None
    return {"position": row.position, "total": row.total, "completed": row.completed, "updated_at": row.updated_at,
            "state": player.clean_state(row.player_state) or None, "scroll": row.scroll_position, "opened_at": row.last_opened_at}


def save_progress(db: Session, user: User, kind: str, item_id: UUID, position: int, total: int | None, completed: bool | None,
                  state: dict | None = None, scroll: float | None = None) -> dict:
    item = c.item_or_404(db, kind, item_id, user)
    free_pages = None
    if not c.can_access(db, user, kind, item):
        if kind == KIND_BOOK and preview_limit(item) > 0:  # a preview reader keeps a reading position too, but only inside the free pages
            free_pages = preview_limit(item)
        else:
            raise c.err(403, "PURCHASE_REQUIRED")
    position = max(0, position)
    if free_pages is not None:  # the preview PDF is shorter than the book: its length is never the book's total, and a preview is never "finished"
        position, total, completed = min(position, free_pages), item.page_count, False
    total = total if total and total > 0 else None
    done = bool(completed) or (total is not None and kind == KIND_FILM and position >= 0.95 * total) or (total is not None and kind == KIND_BOOK and position >= total)
    row = db.scalar(select(MediaProgress).where(MediaProgress.user_id == user.id, MediaProgress.content_type == kind, MediaProgress.content_id == item_id).with_for_update())
    if row is None:
        row = MediaProgress(user_id=user.id, content_type=kind, content_id=item_id)
        db.add(row)
    moved = row.position != position
    row.position, row.total, row.completed = position, total or row.total, done
    if kind == KIND_BOOK:  # how far down the page the student is (0..1); a new page without a value starts at the top
        row.scroll_position = min(max(float(scroll), 0.0), 1.0) if scroll is not None else (None if moved else row.scroll_position)
    if state and kind == KIND_FILM:  # subtitle language, dual subtitles, speed, quality of this film (restored on the next visit)
        row.player_state = {**player.clean_state(row.player_state), **player.clean_state(state)}
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    return progress(db, user, kind, item_id)


def continue_list(db: Session, user: User, *, completed: bool = False, limit: int = 20) -> list[dict]:
    """Books and films the student started (not finished) — or finished, for the history — newest first."""
    rows = db.scalars(select(MediaProgress).where(MediaProgress.user_id == user.id, MediaProgress.completed.is_(completed),
                                                  MediaProgress.position > 0).order_by(MediaProgress.updated_at.desc()).limit(limit)).all()
    out, cats = [], {}
    owned = {KIND_BOOK: c.owned_ids(db, user, KIND_BOOK), KIND_FILM: c.owned_ids(db, user, KIND_FILM)}
    for row in rows:
        item = db.get(c.MODELS[row.content_type], row.content_id)
        if item is None or item.status != STATUS_PUBLISHED or not c.can_access(db, user, row.content_type, item):
            continue
        card = book_card(db, user, item, owned[KIND_BOOK], cats) if row.content_type == KIND_BOOK else film_card(db, user, item, owned[KIND_FILM], cats)
        out.append({**card, "progress": {"position": row.position, "total": row.total, "completed": row.completed, "updated_at": row.updated_at}})
    return out


# ---------------- favorites / history ----------------


def set_favorite(db: Session, user: User, song_id: UUID, on: bool) -> dict:
    song = c.item_or_404(db, KIND_SONG, song_id, user)
    exists = db.scalar(select(UserFavoriteSong.id).where(UserFavoriteSong.user_id == user.id, UserFavoriteSong.song_id == song.id))
    if on and exists is None:
        db.add(UserFavoriteSong(user_id=user.id, song_id=song.id))
    elif not on and exists is not None:
        db.execute(delete(UserFavoriteSong).where(UserFavoriteSong.id == exists))
    db.commit()
    return {"song_id": song.id, "favorite": on}


def history(db: Session, user: User, limit: int = 50) -> list[dict]:
    latest = (select(MediaPlayHistory.song_id, func.max(MediaPlayHistory.created_at).label("at")).where(MediaPlayHistory.user_id == user.id)
              .group_by(MediaPlayHistory.song_id).subquery())
    songs = db.execute(select(Song).join(latest, latest.c.song_id == Song.id).where(_published(Song)).order_by(latest.c.at.desc()).limit(limit)).scalars().all()
    owned, favs = c.owned_ids(db, user, KIND_SONG), _favs(db, user)
    return [song_card(db, user, s, owned, favs) for s in songs]


# ---------------- playlists ----------------


def _visible_playlist(db: Session, user: User, playlist_id: UUID) -> Playlist:
    pl = db.get(Playlist, playlist_id)
    if pl is None or not (pl.owner_id == user.id or (pl.owner_id is None and pl.status == STATUS_PUBLISHED) or c.is_staff(user)):
        raise c.err(404, "NOT_FOUND")
    return pl


def _own_playlist(db: Session, user: User, playlist_id: UUID) -> Playlist:
    pl = db.get(Playlist, playlist_id)
    if pl is None or pl.owner_id != user.id:  # official playlists are edited only in the admin panel
        raise c.err(404, "NOT_FOUND")
    return pl


def _playlist_out(db: Session, pl: Playlist, count: int | None = None) -> dict:
    n = count if count is not None else db.scalar(select(func.count()).select_from(PlaylistSong).where(PlaylistSong.playlist_id == pl.id)) or 0
    return {"id": pl.id, "name": pl.name, "description": pl.description, "official": pl.owner_id is None, "song_count": n,
            "cover_url": f"/api/v1/medien/cover/PLAYLIST/{pl.id}?v={int(pl.updated_at.timestamp())}" if pl.cover_key else None}


def list_playlists(db: Session, user: User) -> list[dict]:
    rows = db.scalars(select(Playlist).where(or_(Playlist.owner_id == user.id, (Playlist.owner_id.is_(None)) & (Playlist.status == STATUS_PUBLISHED)))
                      .order_by(Playlist.owner_id.is_(None).desc(), Playlist.sort_order, Playlist.created_at)).all()
    counts = dict(db.execute(select(PlaylistSong.playlist_id, func.count()).group_by(PlaylistSong.playlist_id)).all())
    return [_playlist_out(db, p, counts.get(p.id, 0)) for p in rows]


def create_playlist(db: Session, user: User, name: str, description: str | None) -> dict:
    name = " ".join((name or "").split())[:160]
    if not name:
        raise c.err(422, "NAME_REQUIRED")
    if (db.scalar(select(func.count()).select_from(Playlist).where(Playlist.owner_id == user.id)) or 0) >= 100:
        raise c.err(409, "PLAYLIST_LIMIT: at most 100 playlists.")
    pl = Playlist(owner_id=user.id, name=name, description=(description or None), status=STATUS_PUBLISHED)
    db.add(pl)
    db.commit()
    db.refresh(pl)
    return _playlist_out(db, pl, 0)


def rename_playlist(db: Session, user: User, playlist_id: UUID, name: str, description: str | None) -> dict:
    pl = _own_playlist(db, user, playlist_id)
    name = " ".join((name or "").split())[:160]
    if not name:
        raise c.err(422, "NAME_REQUIRED")
    pl.name, pl.description = name, description or None
    db.commit()
    return _playlist_out(db, pl)


def delete_playlist(db: Session, user: User, playlist_id: UUID) -> None:
    db.delete(_own_playlist(db, user, playlist_id))
    db.commit()


def playlist_add_song(db: Session, user: User, playlist_id: UUID, song_id: UUID) -> dict:
    pl = _own_playlist(db, user, playlist_id)
    song = c.item_or_404(db, KIND_SONG, song_id, user)
    if db.scalar(select(PlaylistSong.id).where(PlaylistSong.playlist_id == pl.id, PlaylistSong.song_id == song.id)) is None:
        last = db.scalar(select(func.max(PlaylistSong.position)).where(PlaylistSong.playlist_id == pl.id))
        db.add(PlaylistSong(playlist_id=pl.id, song_id=song.id, position=(last + 1) if last is not None else 0))
        db.commit()
    return _playlist_out(db, pl)


def playlist_remove_song(db: Session, user: User, playlist_id: UUID, song_id: UUID) -> dict:
    pl = _own_playlist(db, user, playlist_id)
    db.execute(delete(PlaylistSong).where(PlaylistSong.playlist_id == pl.id, PlaylistSong.song_id == song_id))
    db.commit()
    return _playlist_out(db, pl)


def playlist_reorder(db: Session, user: User, playlist_id: UUID, song_ids: list[UUID]) -> dict:
    """Sets the order to `song_ids` (every song of the playlist exactly once)."""
    pl = _own_playlist(db, user, playlist_id)
    rows = {r.song_id: r for r in db.scalars(select(PlaylistSong).where(PlaylistSong.playlist_id == pl.id))}
    if set(song_ids) != set(rows) or len(song_ids) != len(rows):
        raise c.err(422, "INVALID_ORDER: send every song of the playlist exactly once.")
    for position, sid in enumerate(song_ids):
        rows[sid].position = position
    db.commit()
    return _playlist_out(db, pl)


def playlist_detail(db: Session, user: User, playlist_id: UUID) -> dict:
    pl = _visible_playlist(db, user, playlist_id)
    return {**_playlist_out(db, pl), "songs": list_songs(db, user, playlist_id=pl.id, page=1, page_size=MAX_PAGE_SIZE)["items"]}


# ---------------- purchase requests (access only after an admin grants) ----------------


def request_purchase(db: Session, user: User, kind: str, item_id: UUID) -> dict:
    item = c.item_or_404(db, kind, item_id, user)
    if item.access_type != ACCESS_PAID:
        raise c.err(409, "NOT_PAID: this content is free.")
    if kind == KIND_BOOK:  # books are paid for by card with a receipt / transfer time (services/medien/book_payments.py)
        raise c.err(409, "BOOK_PAYMENT_REQUIRED: pay for a book through the book payment request.")
    open_row = db.scalar(select(MediaPurchase).where(MediaPurchase.user_id == user.id, MediaPurchase.content_type == kind,
                                                      MediaPurchase.content_id == item.id, MediaPurchase.status.in_(("REQUESTED", "GRANTED"))))
    if open_row is not None:
        return {"id": open_row.id, "status": open_row.status}
    row = MediaPurchase(user_id=user.id, content_type=kind, content_id=item.id, price=item.price, status=PURCHASE_REQUESTED)
    db.add(row)
    db.commit()
    return {"id": row.id, "status": row.status}


def my_purchases(db: Session, user: User) -> list[dict]:
    rows = db.scalars(select(MediaPurchase).where(MediaPurchase.user_id == user.id).order_by(MediaPurchase.created_at.desc())).all()
    out = []
    for r in rows:
        item = db.get(c.MODELS[r.content_type], r.content_id)
        out.append({"id": r.id, "kind": r.content_type, "content_id": r.content_id, "title": item.title if item else None, "price": r.price,
                    "status": r.status, "created_at": r.created_at})
    return out


# ---------------- overview ----------------


def overview(db: Session, user: User) -> dict:
    count = lambda m: db.scalar(select(func.count()).select_from(m).where(_published(m))) or 0  # noqa: E731
    return {"counts": {"books": count(MediaBook), "songs": count(Song), "films": count(Film)},
            "continue": continue_list(db, user, limit=6), "special_offers": special_offers(db, user, 8),
            "featured_film": next(iter(list_films(db, user, featured=True, page_size=1)["items"]), None)}
