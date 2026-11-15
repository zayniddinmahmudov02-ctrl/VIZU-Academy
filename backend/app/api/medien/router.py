"""VIZU Medienwelt — student API (`/medien`). Every route needs a logged-in user (`get_current_user`) except the by-design
public ones: covers/posters (`/cover/...`) and the token-authorized file streams (`/stream/...`, `/subtitles/...` incl.
`/cues`, `/rendition/...`; the signed token is issued by an access-checked call and the access is checked again per
request, so a PAID file is never reachable without a purchase). Business rules: app/services/medien/."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.medien import catalog, lookup, player

router = APIRouter(prefix="/medien", tags=["Medienwelt"])

Kind = Path(pattern="^(BOOK|SONG|FILM)$")
PRIVATE = {"Cache-Control": "private, no-store"}


class PlayerStateIn(BaseModel):
    """What the player remembers per film: restored by "continue watching" (values are validated again in the service)."""

    model_config = ConfigDict(extra="forbid")
    subtitle: str | None = Field(default=None, pattern="^(off|de|uz|en|ru)$")
    dual: StrictBool | None = None
    secondary: str | None = Field(default=None, pattern="^(de|uz|en|ru)$")
    speed: float | None = Field(default=None, ge=0.25, le=4)
    quality: str | None = Field(default=None, max_length=20)
    audio: str | None = Field(default=None, max_length=20)


class ProgressIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    position: int = Field(ge=0, le=10_000_000)
    total: int | None = Field(default=None, ge=0, le=10_000_000)
    completed: bool | None = None
    state: PlayerStateIn | None = None


class PrefsIn(BaseModel):
    """Subtitle appearance + dual-subtitle default of the student; any subset."""

    model_config = ConfigDict(extra="forbid")
    enabled: StrictBool | None = None
    size: Literal["small", "medium", "large"] | None = None
    color: Literal["#ffffff", "#ffe066", "#7dd3fc", "#86efac", "#f9a8d4"] | None = None
    bg_opacity: int | None = Field(default=None, ge=0, le=100)
    position: Literal["bottom", "higher"] | None = None
    font: Literal["sans", "serif", "mono"] | None = None
    dual: StrictBool | None = None
    secondary: Literal["de", "uz", "en", "ru"] | None = None


class PlaylistIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class SongIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    song_id: UUID


class OrderIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    song_ids: list[UUID] = Field(max_length=500)


class PurchaseIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str = Field(pattern="^(BOOK|SONG|FILM)$")
    content_id: UUID


# ---------------- public by design ----------------


@router.get("/cover/{kind}/{item_id}")
def cover(kind: str = Path(pattern="^(BOOK|SONG|FILM|PLAYLIST)$"), item_id: UUID = Path(), db: Session = Depends(get_db)):
    """Cover / poster image: the only public Medienwelt file; cacheable (the URL carries a version)."""
    path, media_type = catalog.cover_target(db, kind, item_id)
    return FileResponse(path, media_type=media_type, headers={"Cache-Control": "public, max-age=86400"})


@router.get("/stream/{kind}/{item_id}")
def stream(item_id: UUID, token: str, kind: str = Kind, db: Session = Depends(get_db)):
    """PDF / audio / video bytes (HTTP Range supported by FileResponse: seeking works) for a valid signed token whose user
    still has access to the item."""
    path, media_type = catalog.stream_target(db, kind, item_id, token)
    return FileResponse(path, media_type=media_type, headers=PRIVATE)


@router.get("/subtitles/{subtitle_id}")
def subtitle(subtitle_id: UUID, token: str, db: Session = Depends(get_db)):
    return FileResponse(catalog.subtitle_target(db, subtitle_id, token), media_type="text/vtt", headers=PRIVATE)


@router.get("/subtitles/{subtitle_id}/cues")
def subtitle_cues(subtitle_id: UUID, token: str, response: Response, db: Session = Depends(get_db)):
    """The player's cue list (plain, sanitised text) for the same token and access check as the file."""
    response.headers.update(PRIVATE)
    return catalog.subtitle_cues(db, subtitle_id, token)


@router.get("/rendition/{rendition_id}")
def rendition(rendition_id: UUID, token: str, db: Session = Depends(get_db)):
    """An additional video quality (HTTP Range supported): signed token, access checked again."""
    path, media_type = catalog.rendition_target(db, rendition_id, token)
    return FileResponse(path, media_type=media_type, headers=PRIVATE)


# ---------------- catalog ----------------


@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.overview(db, user)


@router.get("/categories")
def categories(kind: str = Query(pattern="^(BOOK|FILM)$"), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return catalog.categories(db, kind)


@router.get("/special-offers")
def special_offers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.special_offers(db, user, 24)


@router.get("/books")
def books(category: str | None = None, level: str | None = None, q: str | None = Query(default=None, max_length=100), sort: str = "new",
          special: bool = False, access: str | None = None, featured: bool = False, page: int = Query(1, ge=1), page_size: int = Query(24, ge=1, le=60),
          db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.list_books(db, user, category=category, level=level, q=q, sort=sort if sort in catalog.SORTS else "new", special=special,
                              access=access, featured=featured, page=page, page_size=page_size)


@router.get("/books/{book_id}")
def book(book_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.book_detail(db, user, book_id)


@router.post("/books/{book_id}/open")
def open_book(book_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The reader's PDF URL (signed, short-lived) — 403 PURCHASE_REQUIRED for PAID books that are not owned."""
    return catalog.open_book(db, user, book_id)


@router.get("/songs")
def songs(q: str | None = Query(default=None, max_length=100), sort: str = "new", featured: bool = False, favorites: bool = False,
          playlist_id: UUID | None = None, genre: str | None = None, level: str | None = None, page: int = Query(1, ge=1),
          page_size: int = Query(30, ge=1, le=60), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.list_songs(db, user, q=q, sort=sort if sort in catalog.SORTS else "new", featured=featured, favorites=favorites,
                              playlist_id=playlist_id, genre=genre, level=level, page=page, page_size=page_size)


@router.post("/songs/{song_id}/play")
def play_song(song_id: UUID, count: bool = True, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The audio URL (signed) and one entry in the play history (`count=false` for a resume after a page reload)."""
    return catalog.play_song(db, user, song_id, count=count)


@router.put("/songs/{song_id}/favorite")
def favorite(song_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.set_favorite(db, user, song_id, True)


@router.delete("/songs/{song_id}/favorite")
def unfavorite(song_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.set_favorite(db, user, song_id, False)


@router.get("/history")
def play_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.history(db, user)


@router.get("/films")
def films(category: str | None = None, level: str | None = None, q: str | None = Query(default=None, max_length=100), genre: str | None = None,
          access: str | None = None, min_minutes: int | None = Query(default=None, ge=0), max_minutes: int | None = Query(default=None, ge=0),
          featured: bool = False, special: bool = False, sort: str = "new", page: int = Query(1, ge=1), page_size: int = Query(24, ge=1, le=60),
          db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.list_films(db, user, category=category, level=level, q=q, genre=genre, access=access, min_minutes=min_minutes,
                              max_minutes=max_minutes, featured=featured, special=special, sort=sort if sort in catalog.SORTS else "new",
                              page=page, page_size=page_size)


@router.get("/films/{film_id}")
def film(film_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.film_detail(db, user, film_id)


@router.post("/films/{film_id}/watch")
def watch_film(film_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Video source + subtitle tracks (signed URLs) and the last position — 403 PURCHASE_REQUIRED for PAID films not owned."""
    return catalog.watch_film(db, user, film_id)


# ---------------- progress / continue ----------------


@router.get("/continue")
def continue_list(completed: bool = False, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.continue_list(db, user, completed=completed)


@router.get("/progress/{kind}/{item_id}")
def get_progress(item_id: UUID, kind: str = Path(pattern="^(BOOK|FILM)$"), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.progress(db, user, kind, item_id)


@router.put("/progress/{kind}/{item_id}")
def put_progress(data: ProgressIn, item_id: UUID, kind: str = Path(pattern="^(BOOK|FILM)$"), db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    return catalog.save_progress(db, user, kind, item_id, data.position, data.total, data.completed,
                                 data.state.model_dump(exclude_none=True) if data.state else None)


# ---------------- player settings / word look-up ----------------


@router.get("/player-prefs")
def get_player_prefs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The student's subtitle settings (size, colour, background, position, font, on/off, dual subtitles)."""
    return player.get_prefs(db, user)


@router.put("/player-prefs")
def put_player_prefs(data: PrefsIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return player.save_prefs(db, user, data.model_dump(exclude_none=True))


@router.get("/lookup")
def lookup_word(word: str = Query(min_length=1, max_length=80), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """A clicked subtitle word answered from the Wörterbuch (exact / inflected form / similar entries / nothing) — no translation is made up."""
    return lookup.lookup(db, user, word)


# ---------------- playlists ----------------


@router.get("/playlists")
def playlists(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.list_playlists(db, user)


@router.post("/playlists")
def create_playlist(data: PlaylistIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.create_playlist(db, user, data.name, data.description)


@router.get("/playlists/{playlist_id}")
def playlist(playlist_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.playlist_detail(db, user, playlist_id)


@router.put("/playlists/{playlist_id}")
def rename_playlist(playlist_id: UUID, data: PlaylistIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.rename_playlist(db, user, playlist_id, data.name, data.description)


@router.delete("/playlists/{playlist_id}", status_code=204)
def delete_playlist(playlist_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    catalog.delete_playlist(db, user, playlist_id)


@router.post("/playlists/{playlist_id}/songs")
def playlist_add(playlist_id: UUID, data: SongIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.playlist_add_song(db, user, playlist_id, data.song_id)


@router.delete("/playlists/{playlist_id}/songs/{song_id}")
def playlist_remove(playlist_id: UUID, song_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.playlist_remove_song(db, user, playlist_id, song_id)


@router.put("/playlists/{playlist_id}/order")
def playlist_order(playlist_id: UUID, data: OrderIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.playlist_reorder(db, user, playlist_id, data.song_ids)


# ---------------- purchase requests ----------------


@router.post("/purchases")
def request_purchase(data: PurchaseIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """A request for PAID content. It gives no access; an admin grants it after the payment arrived (manual process)."""
    return catalog.request_purchase(db, user, data.kind, data.content_id)


@router.get("/purchases/mine")
def my_purchases(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return catalog.my_purchases(db, user)
