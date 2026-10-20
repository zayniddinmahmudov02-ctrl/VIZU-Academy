"""Media Management — one admin overview of the lesson videos and Hören
audio of every level (A1-C1).

Read-only on purpose: uploading, replacing, publishing and deleting go
through the existing endpoints (POST /admin/videos/upload[/init|chunk|
complete], PUT /admin/videos/{id}[/replace], DELETE /admin/videos/{id},
POST|DELETE /admin/lesson-skills/listenings/{id}/audio, PUT /listenings/{id})
so storage, validation, publish rules (Hören: audio + answer key) and audit
stay in one place. No storage paths are returned — only file names, sizes
and whether the file is on disk.
"""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.core.security.jwt import create_admin_video_preview_token, decode_admin_video_preview_token
from app.db.session import get_db
from app.models.course import Course
from app.models.language import Language
from app.models.lesson import Lesson
from app.models.listening import Listening
from app.models.module import Module
from app.models.user import User
from app.models.video import Video
from app.services.lesson_skills.admin import audio_tracks_admin, listening_storage
from app.services.video.service import stored_file_path, video_media_type

router = APIRouter(prefix="/admin/media-management", tags=["Admin - Media Management"])

LEVELS = ("A1", "A2", "B1", "B2", "C1")


def _lessons(db: Session, language: str) -> list[tuple[Lesson, Module, Course]]:
    rows = db.execute(
        select(Lesson, Module, Course)
        .join(Module, Module.id == Lesson.module_id)
        .join(Course, Course.id == Module.course_id)
        .join(Language, Language.id == Course.language_id)
        .where(Language.code == language, Course.level.in_(LEVELS))
        .order_by(Course.level, Module.number, Lesson.number)
    ).all()
    return [tuple(r) for r in rows]


def _audio_path(listening: Listening) -> Path | None:
    if not listening.audio_storage_path:
        return None
    root = listening_storage.ROOT.resolve()
    path = (root / listening.audio_storage_path).resolve()
    return path if root in path.parents and path.is_file() else None


@router.get("/tree")
def lesson_tree(language: str = Query("de", max_length=10), db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """Level -> module -> lesson, from the real course structure."""
    levels: dict[str, dict] = {}
    for lesson, module, course in _lessons(db, language):
        lv = levels.setdefault(course.level, {"level": course.level, "course_id": course.id, "modules": {}})
        mod = lv["modules"].setdefault(module.id, {"id": module.id, "number": module.number, "title": module.title, "lessons": []})
        mod["lessons"].append({"id": lesson.id, "number": lesson.number, "title": lesson.title})
    return [{**lv, "modules": list(lv["modules"].values())} for lv in levels.values()]


@router.get("/items")
def media_items(language: str = Query("de", max_length=10), db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """Every lesson video and Hören task (with or without audio) of the
    language. Archived Hören tasks of an earlier import are left out."""
    lessons = _lessons(db, language)
    by_id = {lesson.id: (lesson, module, course) for lesson, module, course in lessons}
    ids = list(by_id)
    out: list[dict] = []
    if not ids:
        return out

    def where(lesson_id):
        lesson, module, course = by_id[lesson_id]
        return {"level": course.level, "module_number": module.number, "lesson_id": lesson.id, "lesson_number": lesson.number,
                "lesson_title": lesson.title}

    for v in db.scalars(select(Video).where(Video.lesson_id.in_(ids)).order_by(Video.order_index, Video.created_at)):
        path = stored_file_path(v.storage_key) if v.storage_key else None
        out.append({
            "kind": "VIDEO", "id": v.id, **where(v.lesson_id), "title": v.title,
            "file_name": Path(v.storage_key).name if v.storage_key else None,
            "size_bytes": path.stat().st_size if path else None, "duration_seconds": v.duration_seconds or None,
            "file_status": "ok" if path else ("missing" if v.storage_key else ("external" if v.video_url else "none")),
            "task": v.competency or "EINFUEHRUNG", "is_published": v.is_published, "has_key": None,
            "created_at": v.created_at, "updated_at": v.updated_at,
        })
    from app.services.lesson_skills.exercises import has_key

    for listening in db.scalars(select(Listening).where(Listening.lesson_id.in_(ids)).order_by(Listening.order_index, Listening.created_at)):
        if (listening.title or "").startswith("[Archiv]"):
            continue
        path = _audio_path(listening)
        out.append({
            "kind": "AUDIO", "id": listening.id, **where(UUID(str(listening.lesson_id))), "title": listening.title,
            "file_name": listening.audio_original_name if listening.audio_storage_path else None,
            "size_bytes": listening.audio_size_bytes if path else None, "duration_seconds": listening.audio_duration_seconds,
            "file_status": "ok" if path else ("missing" if listening.audio_storage_path else ("external" if listening.audio_url else "none")),
            "task": listening.title, "is_published": listening.is_published,
            "has_key": bool(listening.questions) and all(has_key(q) for q in listening.questions),
            "questions": len(listening.questions), "created_at": listening.created_at, "updated_at": listening.updated_at,
            # main audio + labelled extra tracks (A1 L14: "Audio von Alisa" / "Audio von Alex")
            "audio_slots": [{**s, "uploaded_at": (listening.updated_at if s["id"] == "main" else
                                                  next((t.updated_at for t in listening.audio_tracks if str(t.id) == s["id"]), None))}
                            for s in audio_tracks_admin(listening)],
        })
    return out


@router.get("/videos/{video_id}/preview")
def video_preview(video_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """A short-lived signed URL for the admin player — drafts too (own token
    purpose, see create_admin_video_preview_token); never the storage path."""
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    if stored_file_path(video.storage_key) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VIDEO_FILE_MISSING")
    return {"url": f"/api/v1/admin/media-management/videos/{video.id}/stream?token={create_admin_video_preview_token(str(video.id))}"}


@router.get("/videos/{video_id}/stream")
def video_preview_stream(video_id: UUID, token: str, db: Session = Depends(get_db)):
    """Bytes for the admin preview (Range / 206 via FileResponse). A <video>
    can't send the Bearer header, so the admin-only preview token is the
    authorization — a student stream token is refused here."""
    try:
        token_video_id = decode_admin_video_preview_token(token)
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired preview token") from None
    if token_video_id != str(video_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token does not authorize this video")
    video = db.get(Video, video_id)
    path = stored_file_path(video.storage_key) if video else None
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VIDEO_FILE_MISSING")
    return FileResponse(path=path, media_type=video_media_type(path), headers={"Cache-Control": "private, no-store"})
