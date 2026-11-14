"""VIZU Medienwelt — admin API (`/admin/medien`). Reads: `require_admin_panel_access`. Writes (content, categories,
playlists, uploads): `require_content_editor` (SUPER_ADMIN / ADMIN / CONTENT_MANAGER). Purchase decisions and direct grants:
`require_super_admin` (money-related, like the payment approvals). Every write is audited in the service layer."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Path, Query, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access, require_content_editor, require_super_admin
from app.db.session import get_db
from app.models.medien import KIND_BOOK, KIND_FILM, KIND_SONG, MediaCategory
from app.models.user import User
from app.services.medien import admin as svc
from app.services.medien import common as c

router = APIRouter(prefix="/admin/medien", tags=["Medien (staff)"])
PRIVATE = {"Cache-Control": "private, no-store"}
BOOK_KIND, SONG_KIND, FILM_KIND = KIND_BOOK, KIND_SONG, KIND_FILM


class ItemIn(BaseModel):
    """Any subset of the content fields (validated in the service: access rules, ranges, categories)."""

    model_config = ConfigDict(extra="forbid")
    title: str | None = None
    description: str | None = None
    language: str | None = None
    level: str | None = None
    access_type: str | None = None
    price: int | None = None
    old_price: int | None = None
    is_special_offer: bool | None = None
    is_featured: bool | None = None
    status: str | None = None
    author: str | None = None
    artist: str | None = None
    album: str | None = None
    genre: str | None = None
    year: int | None = None
    duration_minutes: int | None = None
    category_id: UUID | None = None


class CategoryIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str | None = Field(default=None, pattern="^(BOOK|FILM)$")
    name: str | None = Field(default=None, max_length=120)
    sort_order: int | None = Field(default=None, ge=0, le=100000)
    is_active: bool | None = None


class PlaylistIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    status: str | None = None
    sort_order: int | None = None


class SongsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    song_ids: list[UUID] = Field(max_length=1000)


class InitIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filename: str = Field(max_length=255)
    size: int = Field(gt=0)


class UrlIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str | None = Field(default=None, max_length=1000)


class DecisionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str = Field(pattern="^(GRANTED|REJECTED|REVOKED)$")
    note: str | None = Field(default=None, max_length=500)


class GrantIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str = Field(pattern="^(BOOK|SONG|FILM)$")
    content_id: UUID
    user_id: UUID | None = None
    email: str | None = Field(default=None, max_length=255)
    note: str | None = Field(default=None, max_length=500)


def _data(model: BaseModel) -> dict:
    return model.model_dump(exclude_unset=True)


def _form(**fields) -> dict:
    """Multipart fields -> the dict `clean()` expects (booleans parsed, empty strings left out)."""
    out = {}
    for key, value in fields.items():
        if value is None or value == "":
            continue
        out[key] = (str(value).lower() in ("1", "true", "on", "yes")) if key in ("is_featured", "is_special_offer") else value
    return out


def _file_response(path, media_type: str):
    if path is None:
        raise c.err(404, "FILE_MISSING")
    return FileResponse(path, media_type=media_type, headers=PRIVATE)


# ---------------- stats / categories ----------------


@router.get("/stats")
def stats(db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return svc.stats(db)


@router.get("/categories")
def categories(kind: str = Query(pattern="^(BOOK|FILM)$"), db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return svc.list_categories(db, kind)


@router.post("/categories")
def create_category(data: CategoryIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    cat = svc.save_category(db, user, data.kind or "", _data(data))
    return {"id": cat.id, "kind": cat.kind, "name": cat.name, "slug": cat.slug, "sort_order": cat.sort_order, "is_active": cat.is_active}


@router.put("/categories/{category_id}")
def update_category(category_id: UUID, data: CategoryIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    cat = db.get(MediaCategory, category_id)
    if cat is None:
        raise c.err(404, "NOT_FOUND")
    cat = svc.save_category(db, user, cat.kind, _data(data), cat)
    return {"id": cat.id, "kind": cat.kind, "name": cat.name, "slug": cat.slug, "sort_order": cat.sort_order, "is_active": cat.is_active}


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    cat = db.get(MediaCategory, category_id)
    if cat is None:
        raise c.err(404, "NOT_FOUND")
    svc.delete_category(db, user, cat)


# ---------------- books ----------------


@router.get("/books")
def list_books(q: str | None = None, status: str | None = None, access: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100),
               db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return svc.admin_list(db, BOOK_KIND, q=q, status=status, access=access, page=page, page_size=page_size)


@router.post("/books")
def create_book(data: ItemIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return svc.admin_card(BOOK_KIND, svc.create_item(db, user, BOOK_KIND, _data(data)), db)


@router.put("/books/{book_id}")
def update_book(book_id: UUID, data: ItemIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return svc.admin_card(BOOK_KIND, svc.update_item(db, user, BOOK_KIND, svc.get_item(db, BOOK_KIND, book_id), _data(data)), db)


@router.delete("/books/{book_id}", status_code=204)
async def delete_book(book_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    await svc.delete_item(db, user, BOOK_KIND, svc.get_item(db, BOOK_KIND, book_id))


@router.post("/books/{book_id}/cover")
async def book_cover(book_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return svc.admin_card(BOOK_KIND, await svc.set_cover(db, user, BOOK_KIND, svc.get_item(db, BOOK_KIND, book_id), file), db)


@router.post("/books/{book_id}/file")
async def book_file(book_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return svc.admin_card(BOOK_KIND, await svc.set_book_file(db, user, svc.get_item(db, BOOK_KIND, book_id), file), db)


@router.get("/books/{book_id}/file")
def book_preview(book_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return _file_response(c.file_path(svc.get_item(db, BOOK_KIND, book_id).file_key), "application/pdf")


# ---------------- songs ----------------


@router.get("/songs")
def list_songs(q: str | None = None, status: str | None = None, access: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100),
               db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return svc.admin_list(db, SONG_KIND, q=q, status=status, access=access, page=page, page_size=page_size)


@router.post("/songs")
async def create_song(file: UploadFile = File(...), cover: UploadFile | None = File(None), title: str | None = Form(None), artist: str | None = Form(None),
                      album: str | None = Form(None), genre: str | None = Form(None), language: str | None = Form(None), level: str | None = Form(None),
                      access_type: str | None = Form(None), price: str | None = Form(None), old_price: str | None = Form(None),
                      is_featured: str | None = Form(None), status: str | None = Form(None), db: Session = Depends(get_db),
                      user: User = Depends(require_content_editor)):
    """One song with its metadata (the bulk upload calls this once per file, so each has its own progress and error)."""
    data = _form(title=title, artist=artist, album=album, genre=genre, language=language, level=level, access_type=access_type, price=price,
                 old_price=old_price, is_featured=is_featured, status=status)
    if "title" not in data:
        data["title"] = (file.filename or "").rsplit(".", 1)[0]
    return svc.admin_card(SONG_KIND, await svc.create_song(db, user, data, file, cover), db)


@router.put("/songs/{song_id}")
def update_song(song_id: UUID, data: ItemIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return svc.admin_card(SONG_KIND, svc.update_item(db, user, SONG_KIND, svc.get_item(db, SONG_KIND, song_id), _data(data)), db)


@router.delete("/songs/{song_id}", status_code=204)
async def delete_song(song_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    await svc.delete_item(db, user, SONG_KIND, svc.get_item(db, SONG_KIND, song_id))


@router.post("/songs/{song_id}/file")
async def song_file(song_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return svc.admin_card(SONG_KIND, await svc.replace_song_file(db, user, svc.get_item(db, SONG_KIND, song_id), file), db)


@router.post("/songs/{song_id}/cover")
async def song_cover(song_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return svc.admin_card(SONG_KIND, await svc.set_cover(db, user, SONG_KIND, svc.get_item(db, SONG_KIND, song_id), file), db)


@router.get("/songs/{song_id}/file")
def song_preview(song_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    song = svc.get_item(db, SONG_KIND, song_id)
    return _file_response(c.file_path(song.file_key), song.content_type or "audio/mpeg")


# ---------------- films ----------------


@router.get("/films")
def list_films(q: str | None = None, status: str | None = None, access: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100),
               db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return svc.admin_list(db, FILM_KIND, q=q, status=status, access=access, page=page, page_size=page_size)


@router.post("/films")
def create_film(data: ItemIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return svc.admin_card(FILM_KIND, svc.create_item(db, user, FILM_KIND, _data(data)), db)


@router.put("/films/{film_id}")
def update_film(film_id: UUID, data: ItemIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return svc.admin_card(FILM_KIND, svc.update_item(db, user, FILM_KIND, svc.get_item(db, FILM_KIND, film_id), _data(data)), db)


@router.delete("/films/{film_id}", status_code=204)
async def delete_film(film_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    await svc.delete_item(db, user, FILM_KIND, svc.get_item(db, FILM_KIND, film_id))


@router.post("/films/{film_id}/cover")
async def film_cover(film_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return svc.admin_card(FILM_KIND, await svc.set_cover(db, user, FILM_KIND, svc.get_item(db, FILM_KIND, film_id), file), db)


@router.post("/films/{film_id}/video")
async def film_video(film_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    """A video up to 90 MB in one request; larger files use init / part / complete."""
    return svc.admin_card(FILM_KIND, await svc.set_video_file(db, user, svc.get_item(db, FILM_KIND, film_id), file), db)


@router.post("/films/{film_id}/video/init")
def film_video_init(film_id: UUID, data: InitIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return svc.video_init(db, user, svc.get_item(db, FILM_KIND, film_id), data.filename, data.size)


@router.put("/films/{film_id}/video/{upload_id}/{index}")
async def film_video_part(film_id: UUID, upload_id: str, index: int, request: Request, db: Session = Depends(get_db),
                          _: User = Depends(require_content_editor)):
    """One chunk as the raw request body, streamed to disk (never held in memory)."""
    return {"index": index, "bytes": await svc.video_part(svc.get_item(db, FILM_KIND, film_id), upload_id, index, request.stream())}


@router.post("/films/{film_id}/video/{upload_id}/complete")
async def film_video_complete(film_id: UUID, upload_id: str, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return svc.admin_card(FILM_KIND, await svc.video_complete(db, user, svc.get_item(db, FILM_KIND, film_id), upload_id), db)


@router.delete("/films/{film_id}/video/{upload_id}", status_code=204)
def film_video_abort(film_id: UUID, upload_id: str, db: Session = Depends(get_db), _: User = Depends(require_content_editor)):
    svc.video_abort(db, svc.get_item(db, FILM_KIND, film_id), upload_id)


@router.put("/films/{film_id}/external-url")
def film_external_url(film_id: UUID, data: UrlIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return svc.admin_card(FILM_KIND, svc.set_external_url(db, user, svc.get_item(db, FILM_KIND, film_id), data.url), db)


@router.get("/films/{film_id}/file")
def film_preview(film_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    film = svc.get_item(db, FILM_KIND, film_id)
    return _file_response(c.file_path(film.video_key), film.video_content_type or "video/mp4")


@router.post("/films/{film_id}/subtitles")
async def film_subtitle(film_id: UUID, language: str = Form(...), label: str | None = Form(None), file: UploadFile = File(...),
                        db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    film = svc.get_item(db, FILM_KIND, film_id)
    await svc.save_subtitle(db, user, film, language, label, file)
    return svc.admin_card(FILM_KIND, film, db)


@router.delete("/films/{film_id}/subtitles/{subtitle_id}")
async def film_subtitle_delete(film_id: UUID, subtitle_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    film = svc.get_item(db, FILM_KIND, film_id)
    await svc.delete_subtitle(db, user, film, subtitle_id)
    return svc.admin_card(FILM_KIND, film, db)


# ---------------- official playlists ----------------


@router.get("/playlists")
def playlists(db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return svc.list_playlists(db)


@router.post("/playlists")
def create_playlist(data: PlaylistIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    pl = svc.save_playlist(db, user, _data(data))
    return {"id": pl.id, "name": pl.name, "status": pl.status}


@router.put("/playlists/{playlist_id}")
def update_playlist(playlist_id: UUID, data: PlaylistIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    pl = svc.save_playlist(db, user, _data(data), svc._official(db, playlist_id))
    return {"id": pl.id, "name": pl.name, "status": pl.status}


@router.delete("/playlists/{playlist_id}", status_code=204)
async def delete_playlist(playlist_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    await svc.delete_playlist(db, user, svc._official(db, playlist_id))


@router.post("/playlists/{playlist_id}/cover")
async def playlist_cover(playlist_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    pl = await svc.playlist_cover(db, user, svc._official(db, playlist_id), file)
    return {"id": pl.id}


@router.get("/playlists/{playlist_id}/songs")
def playlist_songs(playlist_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return svc.playlist_songs(db, svc._official(db, playlist_id))


@router.put("/playlists/{playlist_id}/songs")
def playlist_set_songs(playlist_id: UUID, data: SongsIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return svc.playlist_set_songs(db, user, svc._official(db, playlist_id), data.song_ids)


# ---------------- purchases (Super Admin) ----------------


@router.get("/purchases")
def purchases(status: str | None = Query(default=None, pattern="^(REQUESTED|GRANTED|REJECTED|REVOKED)$"), db: Session = Depends(get_db),
              _: User = Depends(require_super_admin)):
    return svc.list_purchases(db, status)


@router.post("/purchases/{purchase_id}/decision")
def decide(purchase_id: UUID, data: DecisionIn, db: Session = Depends(get_db), user: User = Depends(require_super_admin)):
    row = svc.decide_purchase(db, user, purchase_id, data.status, data.note)
    return {"id": row.id, "status": row.status}


@router.post("/purchases/grant")
def grant(data: GrantIn, db: Session = Depends(get_db), user: User = Depends(require_super_admin)):
    target = data.user_id
    if target is None and data.email:
        target = db.scalar(select(User.id).where(User.email == data.email.strip().lower()))
    if target is None:
        raise c.err(404, "USER_NOT_FOUND")
    row = svc.grant_to_user(db, user, target, data.kind, data.content_id, data.note)
    return {"id": row.id, "status": row.status}
