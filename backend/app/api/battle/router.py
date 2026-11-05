"""VIZU DEUTSCH BATTLE API.

Student routes (/battle) need a logged-in user; the caller is always the token's user, bodies never carry
a user id, score, time or correct answer (extra fields are rejected) — the server measures time and grades.
Two public reads carry no user data: /battle/media/{token} (a signed, short-lived picture URL of a running
round) and /battle/themes/assets/{name} (uploaded arena backgrounds).

Admin routes (/admin/battle): read = require_admin_panel_access, write = require_content_editor."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access, require_content_editor
from app.db.session import get_db
from app.models.user import User
from app.services.battle import admin, commons, config, engine, home, profiles, themes

router = APIRouter(prefix="/battle", tags=["Battle"])
admin_router = APIRouter(prefix="/admin/battle", tags=["Admin Battle"])

Stage = Literal["A1", "A2", "B1", "B2", "C1", "C1+"]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AnswerIn(_In):
    round: int = Field(ge=1, le=config.ROUNDS)
    choice: int = Field(ge=0, lt=config.OPTIONS)


class RoomJoinIn(_In):
    code: str = Field(min_length=4, max_length=8)


class AvatarIn(_In):
    avatar: str = Field(max_length=30)


# ── student ──────────────────────────────────────────────────────────────────


@router.get("/home")
def battle_home(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return home.home(db, user)


@router.get("/themes")
def battle_themes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": themes.public_list(db)}


@router.get("/leaderboard")
def leaderboard(stage: Stage | None = None, page: int = Query(1, ge=1, le=500), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return profiles.leaderboard(db, user, stage, page)


@router.put("/profile/avatar")
def set_avatar(data: AvatarIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return profiles.set_avatar(db, user, data.avatar)


@router.post("/queue")
def join_queue(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Ranked matchmaking (same stage). Returns the open match if the caller already has one (reconnect)."""
    return engine.queue(db, user)


@router.post("/practice")
def practice(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """A match against VIZU Bot — no Battle Points."""
    return engine.practice(db, user)


@router.post("/rooms")
def create_room(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """A private room with a 6-character code — no Battle Points."""
    return engine.create_room(db, user)


@router.post("/rooms/join")
def join_room(data: RoomJoinIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return engine.join_room(db, user, data.code)


@router.get("/matches/current")
def current_match(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"match": engine.current(db, user)}


@router.get("/matches/{match_id}")
def match_state(match_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Polling + heartbeat: 404 unless the caller plays in this match."""
    return engine.state(db, match_id, user)


@router.post("/matches/{match_id}/answer")
def answer(match_id: UUID, data: AnswerIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return engine.answer(db, user, match_id, data.round, data.choice)


@router.post("/matches/{match_id}/leave")
def leave(match_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Waiting: cancels. Running: the caller forfeits."""
    return engine.leave(db, user, match_id)


@router.get("/media/{token}")
def round_picture(token: str, db: Session = Depends(get_db)):
    return engine.media_for(db, token)


@router.get("/themes/assets/{name}")
def theme_asset(name: str):
    return themes.serve_asset(name)


# ── admin ────────────────────────────────────────────────────────────────────


class WordAddIn(_In):
    dictionary_id: str = Field(min_length=3, max_length=12)
    category: str = Field(max_length=30)


class WordPatchIn(_In):
    category: str | None = Field(None, max_length=30)
    status: Literal["draft", "published", "disabled"] | None = None


class ImageStatusIn(_In):
    status: Literal["draft", "verified", "published", "rejected"]
    note: str | None = Field(None, max_length=1000)


class CommonsImportIn(_In):
    title: str = Field(min_length=6, max_length=300)


class AttributionIn(_In):
    title: str | None = Field(None, max_length=300)
    author: str | None = Field(None, max_length=300)
    license: str | None = Field(None, max_length=80)
    license_url: str | None = Field(None, max_length=500)
    source_url: str | None = Field(None, max_length=500)


class ThemeDraftIn(_In):
    city: str | None = Field(None, max_length=60)
    title: str | None = Field(None, max_length=120)
    subtitle: str | None = Field(None, max_length=200)
    desktop_image: str | None = Field(None, max_length=300)
    mobile_image: str | None = Field(None, max_length=300)
    accent: str | None = Field(None, max_length=9)
    overlay: int | None = Field(None, ge=0, le=90)
    attribution: AttributionIn | None = None
    is_active: bool | None = None


@admin_router.get("/overview")
def admin_overview(db: Session = Depends(get_db), user: User = Depends(require_admin_panel_access)):
    return admin.overview(db)


@admin_router.get("/words")
def admin_words(level: Literal["A1", "A2", "B1", "B2", "C1"] | None = None, status: str | None = Query(None, max_length=12),
                category: str | None = Query(None, max_length=30), q: str = Query("", max_length=80), page: int = Query(1, ge=1),
                db: Session = Depends(get_db), user: User = Depends(require_admin_panel_access)):
    return admin.list_words(db, level, status, category, q, page)


@admin_router.post("/words", status_code=201)
def admin_add_word(data: WordAddIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return admin.add_word(db, user, data.dictionary_id, data.category)


@admin_router.patch("/words/{word_id}")
def admin_patch_word(word_id: UUID, data: WordPatchIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return admin.update_word(db, user, word_id, data.model_dump(exclude_none=True))


@admin_router.post("/words/{word_id}/image")
async def admin_upload_image(word_id: UUID, file: UploadFile = File(...), author: str = Form(..., min_length=2, max_length=300),
                             license: str = Form(..., min_length=2, max_length=80), source_url: str | None = Form(None, max_length=500),
                             db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    """JPEG / PNG / WebP, max 12 MB; content-checked, re-encoded to WebP, stored privately as Draft."""
    data = await file.read(12 * 1024 * 1024 + 1)
    return admin.upload_image(db, user, word_id, data, file.filename, file.content_type, author, license, source_url)


@admin_router.post("/words/{word_id}/commons")
def admin_commons_import(word_id: UUID, data: CommonsImportIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return admin.commons_import(db, user, word_id, data.title)


@admin_router.get("/commons/search")
def admin_commons_search(q: str = Query(..., min_length=2, max_length=80), user: User = Depends(require_content_editor)):
    return {"items": commons.search(q)}


@admin_router.get("/images/{image_id}/file")
def admin_image_file(image_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_admin_panel_access)):
    return admin.image_file(db, image_id)


@admin_router.post("/images/{image_id}/status")
def admin_image_status(image_id: UUID, data: ImageStatusIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return admin.set_image_status(db, user, image_id, data.status, data.note)


@admin_router.get("/themes")
def admin_themes(db: Session = Depends(get_db), user: User = Depends(require_admin_panel_access)):
    return {"items": themes.admin_list(db)}


@admin_router.put("/themes/{stage}/draft")
def admin_theme_draft(stage: Stage, data: ThemeDraftIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    payload = data.model_dump(exclude_unset=True)
    return themes.save_draft(db, user, stage, payload)


@admin_router.post("/themes/{stage}/publish")
def admin_theme_publish(stage: Stage, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return themes.publish(db, user, stage)


@admin_router.post("/themes/{stage}/discard")
def admin_theme_discard(stage: Stage, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return themes.discard(db, user, stage)


@admin_router.post("/themes/assets", status_code=201)
async def admin_theme_asset(kind: Literal["desktop", "mobile"] = Form(...), file: UploadFile = File(...),
                            db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    data = await file.read(12 * 1024 * 1024 + 1)
    return themes.upload_asset(db, user, data, file.filename, file.content_type, kind)
