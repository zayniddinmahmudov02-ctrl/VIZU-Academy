"""Student side of Medienwelt: catalog (search / filter / sort / pagination), opening content through signed URLs, reading
and watching progress, favorites, playlists, play history and purchase requests. Only PUBLISHED content is listed; a
PAID item shows cover, text and price until the student owns it. No function here returns a storage key or path."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session

from app.models.medien import (ACCESS_FREE, ACCESS_PAID, KIND_BOOK, KIND_FILM, KIND_SONG, PURCHASE_REQUESTED, STATUS_PUBLISHED, Film,
                               FilmSubtitle, MediaBook, MediaCategory, MediaPlayHistory, MediaProgress, MediaPurchase, Playlist, PlaylistSong,
                               Song, UserFavoriteSong)
from app.models.user import User
from app.services.medien import common as c

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


def book_detail(db: Session, user: User, book_id: UUID) -> dict:
    book = c.item_or_404(db, KIND_BOOK, book_id, user)
    return {**book_card(db, user, book, c.owned_ids(db, user, KIND_BOOK), {}), "progress": progress(db, user, KIND_BOOK, book.id)}


def subtitles_of(db: Session, film_id: UUID) -> list[FilmSubtitle]:
    return list(db.scalars(select(FilmSubtitle).where(FilmSubtitle.film_id == film_id).order_by(FilmSubtitle.language)))


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


def open_book(db: Session, user: User, book_id: UUID) -> dict:
    book = c.item_or_404(db, KIND_BOOK, book_id, user)
    c.require_access(db, user, KIND_BOOK, book)
    if not c.file_path(book.file_key):
        raise c.err(404, "FILE_MISSING")
    db.execute(update(MediaBook).where(MediaBook.id == book.id).values(view_count=MediaBook.view_count + 1))
    db.commit()
    return {"url": c.signed_url(f"/api/v1/medien/stream/{KIND_BOOK}/{book.id}", book.id, user), "title": book.title,
            "progress": progress(db, user, KIND_BOOK, book.id)}


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


def watch_film(db: Session, user: User, film_id: UUID) -> dict:
    film = c.item_or_404(db, KIND_FILM, film_id, user)
    c.require_access(db, user, KIND_FILM, film)
    subs = [{"id": s.id, "language": s.language, "label": s.label,
             "url": c.signed_url(f"/api/v1/medien/subtitles/{s.id}", s.id, user, "subtitle")} for s in subtitles_of(db, film.id)]
    if film.video_key and film.processing_status == "READY" and c.file_path(film.video_key):
        source = {"type": "file", "url": c.signed_url(f"/api/v1/medien/stream/{KIND_FILM}/{film.id}", film.id, user)}
    elif film.external_url:
        source = {"type": "external", "url": film.external_url}
    else:
        raise c.err(404, "FILE_MISSING")
    db.execute(update(Film).where(Film.id == film.id).values(view_count=Film.view_count + 1))
    db.commit()
    return {"title": film.title, "source": source, "subtitles": subs, "progress": progress(db, user, KIND_FILM, film.id)}


def stream_target(db: Session, kind: str, item_id: UUID, token: str):
    """(path, content type) for a valid token: the token user must still have access to the item right now."""
    user = c.read_token(db, token, item_id)
    item = c.item_or_404(db, kind, item_id, user)
    c.require_access(db, user, kind, item)
    key = item.video_key if kind == KIND_FILM else item.file_key
    path = c.file_path(key)
    if path is None:
        raise c.err(404, "FILE_MISSING")
    return path, (getattr(item, "video_content_type", None) or getattr(item, "content_type", None) or c.CONTENT_TYPES.get(path.suffix.lstrip("."), "application/octet-stream"))


def subtitle_target(db: Session, subtitle_id: UUID, token: str):
    user = c.read_token(db, token, subtitle_id, "subtitle")
    sub = db.get(FilmSubtitle, subtitle_id)
    if sub is None:
        raise c.err(404, "NOT_FOUND")
    film = c.item_or_404(db, KIND_FILM, sub.film_id, user)
    c.require_access(db, user, KIND_FILM, film)
    path = c.file_path(sub.file_key)
    if path is None:
        raise c.err(404, "FILE_MISSING")
    return path


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
    return {"position": row.position, "total": row.total, "completed": row.completed, "updated_at": row.updated_at}


def save_progress(db: Session, user: User, kind: str, item_id: UUID, position: int, total: int | None, completed: bool | None) -> dict:
    item = c.item_or_404(db, kind, item_id, user)
    c.require_access(db, user, kind, item)
    position = max(0, position)
    total = total if total and total > 0 else None
    done = bool(completed) or (total is not None and kind == KIND_FILM and position >= 0.95 * total) or (total is not None and kind == KIND_BOOK and position >= total)
    row = db.scalar(select(MediaProgress).where(MediaProgress.user_id == user.id, MediaProgress.content_type == kind, MediaProgress.content_id == item_id).with_for_update())
    if row is None:
        row = MediaProgress(user_id=user.id, content_type=kind, content_id=item_id)
        db.add(row)
    row.position, row.total, row.completed = position, total or row.total, done
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
