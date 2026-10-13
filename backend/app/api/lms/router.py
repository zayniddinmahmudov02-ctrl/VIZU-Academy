"""VIZU LMS — student API (docs/lms-architecture.md).

Aggregated course views only; the content of each competency keeps coming
from its existing endpoints (/lesson-skills/..., /videos/..., /vocabularies,
/grammars, /writings, /speakings)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.progress import require_lesson_access
from app.core.security.jwt import create_resource_token, create_video_stream_token, decode_resource_token
from app.db.session import get_db
from app.models.lesson import Lesson
from app.models.lms import COMPETENCY_ORDER, LearningResource
from app.models.user import User
from app.models.video import Video
from app.models.video_progress import VideoProgress
from app.services.lms import progress, resources, structure
from app.services.lms.access import lesson_access

router = APIRouter(prefix="/lms", tags=["LMS"])


@router.get("/levels")
def list_levels(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """A1–C1 with the caller's progress: target / published / completed
    lessons, percent, last lesson and the lesson to continue with."""
    out = []
    for level in structure.LEVELS:
        overview = progress.level_overview(db, user, level, detail=False)
        overview.pop("lessons")
        out.append(overview)
    return {"total_lessons_target": structure.TOTAL_LESSONS, "levels": out}


@router.get("/levels/{level}")
def get_level(level: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """One level with its published lessons (cards) in their order."""
    return progress.level_overview(db, user, level)


def _neighbours(db: Session, lesson: Lesson) -> dict:
    def card(row: Lesson | None):
        return {"id": row.id, "number": row.number, "title": row.title} if row else None

    base = select(Lesson).where(Lesson.module_id == lesson.module_id, Lesson.is_published.is_(True))
    prev_row = db.scalar(base.where(Lesson.number < lesson.number).order_by(Lesson.number.desc()).limit(1))
    next_row = db.scalar(base.where(Lesson.number > lesson.number).order_by(Lesson.number).limit(1))
    return {"previous": card(prev_row), "next": card(next_row)}


def _videos(db: Session, user: User, lesson_id: UUID) -> list[dict]:
    rows = list(
        db.scalars(select(Video).where(Video.lesson_id == lesson_id, Video.is_published.is_(True)).order_by(Video.order_index, Video.created_at))
    )
    ids = [v.id for v in rows]
    prog = {
        p.video_id: p for p in db.scalars(select(VideoProgress).where(VideoProgress.user_id == user.id, VideoProgress.video_id.in_(ids)))
    } if ids else {}
    out = []
    for v in rows:
        if not v.storage_key:
            continue
        token = create_video_stream_token(str(v.id))
        p = prog.get(v.id)
        out.append(
            {
                "id": v.id,
                "title": v.title,
                "description": v.description,
                "competency": v.competency or "EINFUEHRUNG",
                "duration_seconds": v.duration_seconds,
                "thumbnail_url": v.thumbnail_url,
                "order_index": v.order_index,
                "stream_url": f"/api/v1/videos/{v.id}/stream?token={token}",
                "subtitle_url": f"/api/v1/videos/{v.id}/subtitles?token={token}" if v.subtitle_key else None,
                "progress": {"last_position": p.last_position, "watch_percent": p.watch_percent, "completed": p.completed} if p else None,
            }
        )
    return out


@router.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Lesson, its ten competencies (state per competency), videos and
    resources. A locked lesson is still described (title, lock reason,
    competency list) but without content; a draft is 404 for students."""
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    access = lesson_access(db, user, lesson)
    if not access.visible:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    course, _ = structure.lesson_level(db, lesson)
    state = progress.sync_lesson(db, user.id, lesson.id)
    view = progress.present(state, access)
    if not access.unlocked:
        for c in view["competencies"]:
            c["body"] = None
    return {
        "lesson": {
            "id": lesson.id,
            "number": lesson.number,
            "title": lesson.title,
            "description": lesson.description,
            "duration": lesson.duration,
            "level": course.level if course else None,
            "course_id": course.id if course else None,
        },
        "navigation": _neighbours(db, lesson),
        "competency_order": list(COMPETENCY_ORDER),
        **view,
        "videos": _videos(db, user, lesson.id) if access.unlocked else [],
        "resources": [_student_resource(r) for r in resources.lesson_resources(db, lesson.id, published_only=True)] if access.unlocked else [],
    }


def _student_resource(resource: LearningResource) -> dict:
    out = resources.serialize(resource)
    if out["file_url"]:
        out["file_url"] = f"{out['file_url']}?token={create_resource_token(str(resource.id))}"
    return out


@router.post("/lessons/{lesson_id}/competencies/{kind}/visit")
def visit_competency(lesson_id: UUID, kind: str, db: Session = Depends(get_db), user: User = Depends(require_lesson_access)):
    """The student opened a competency. Completes only a competency that has
    nothing to track (text / resources); never completes a lesson by
    itself."""
    kind = kind.strip().upper()
    if kind not in COMPETENCY_ORDER:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UNKNOWN_COMPETENCY")
    lesson = db.get(Lesson, lesson_id)
    state = progress.record_visit(db, user, lesson, kind)
    view = progress.present(state, lesson_access(db, user, lesson))
    return {k: view[k] for k in ("lesson_id", "status", "completed", "percent", "competencies_total", "competencies_completed", "competencies")}


@router.get("/resources/{resource_id}/file")
def resource_file(resource_id: UUID, token: str = Query(..., min_length=10), db: Session = Depends(get_db)):
    """A published resource file. <audio>, the PDF viewer and <img> can't
    send a Bearer header, so — exactly like GET /videos/{id}/stream — the
    short-lived signed token that GET /lms/lessons/{id} put into file_url
    (issued only after the lesson access check) is the authorization.
    Range requests are answered (audio seeking)."""
    try:
        token_resource_id = decode_resource_token(token)
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired resource token") from None
    if token_resource_id != str(resource_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token does not authorize this resource")
    resource = db.get(LearningResource, resource_id)
    if resource is None or not resource.is_published or resource.resource_type == "LINK":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    lesson = db.get(Lesson, resource.lesson_id)
    if lesson is None or not lesson.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    path = resources.file_path(resource)
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RESOURCE_FILE_MISSING")
    disposition = "inline" if resource.resource_type in ("AUDIO", "PDF", "IMAGE") else "attachment"
    return FileResponse(
        path,
        media_type=resource.mime_type or "application/octet-stream",
        filename=resource.original_filename or path.name,
        content_disposition_type=disposition,
        headers={"Cache-Control": "private, no-store"},
    )
