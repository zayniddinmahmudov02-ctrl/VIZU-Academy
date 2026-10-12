"""VIZU LMS — admin API: levels A1–C1, lesson structure and order, lesson and
competency editing (draft -> publish), learning resources, student progress
and storage health. Reads: any admin-panel role; content changes: SUPER_ADMIN,
ADMIN, CONTENT_MANAGER. Every change is written to audit_logs."""

import json
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.core.audit import write_audit
from app.core.security.roles import UserRole
from app.db.session import get_db
from app.models.lesson import Lesson
from app.models.lesson_skill import SkillExercise
from app.models.listening import Listening
from app.models.lms import COMPETENCY_ORDER, LearningResource, LessonCompetency, StudentCompetencyProgress
from app.models.speaking import Speaking
from app.models.student_progress import StudentProgress
from app.models.user import User
from app.models.video import Video
from app.models.writing import Writing
from app.services.lesson_skills import admin as skill_admin
from app.services.lms import progress, resources, structure
from app.services.video.service import VideoService

router = APIRouter(prefix="/admin/lms", tags=["Admin - LMS"])

CONTENT_EDITOR_ROLES = {UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CONTENT_MANAGER}


async def require_content_editor(user: User = Depends(get_current_user)) -> User:
    if user.role not in CONTENT_EDITOR_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Content editor access required")
    return user


def _audit(db: Session, request: Request, user: User, action: str, **details) -> None:
    write_audit(
        db,
        actor_id=user.id,
        action=action,
        details=json.dumps(details, default=str, ensure_ascii=False)[:2000],
        ip_address=request.client.host if request.client else None,
    )


def _lesson_or_404(db: Session, lesson_id: UUID) -> Lesson:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson


def _resource_or_404(db: Session, resource_id: UUID) -> LearningResource:
    resource = db.get(LearningResource, resource_id)
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resource


# ============================================================
# Levels
# ============================================================


def _level_summary(db: Session, level: str) -> dict:
    course = structure.level_course(db, level)
    module = structure.main_module(db, course) if course else None
    lessons = structure.level_lessons(db, module)
    target = structure.LEVEL_LESSON_COUNTS[level]
    numbers = {lesson.number for lesson in lessons}
    return {
        "level": level,
        "course_id": course.id if course else None,
        "module_id": module.id if module else None,
        "title": course.title if course else None,
        "sequential_unlock": bool(course and course.sequential_unlock),
        "lessons_target": target,
        "lessons_existing": sum(1 for n in numbers if 1 <= n <= target),
        "lessons_published": sum(1 for lesson in lessons if lesson.is_published and 1 <= lesson.number <= target),
        "numbers_missing": [n for n in range(1, target + 1) if n not in numbers],
        "numbers_outside_range": sorted(n for n in numbers if not 1 <= n <= target),
    }


@router.get("/levels")
def admin_levels(db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    levels = [_level_summary(db, level) for level in structure.LEVELS]
    return {"total_lessons_target": structure.TOTAL_LESSONS, "levels": levels}


class LevelUpdate(BaseModel):
    sequential_unlock: bool


@router.patch("/levels/{level}")
def update_level(level: str, data: LevelUpdate, request: Request, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    level = structure.normalize_level(level)
    course = structure.level_course(db, level)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LEVEL_NOT_SET_UP")
    course.sequential_unlock = data.sequential_unlock
    db.commit()
    _audit(db, request, user, "lms_level_updated", level=level, sequential_unlock=data.sequential_unlock)
    return _level_summary(db, level)


@router.post("/levels/{level}/ensure-structure")
def ensure_structure(level: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    """Creates the missing course / module / lessons 1..N of a level as
    drafts. Never deletes or renumbers anything."""
    result = structure.ensure_structure(db, level)
    _audit(db, request, user, "lms_structure_ensured", level=result["level"], created=result["created"])
    return {**result, "summary": _level_summary(db, result["level"])}


def _admin_lesson_card(db: Session, lesson: Lesson) -> dict:
    comps = {c.kind: c for c in db.scalars(select(LessonCompetency).where(LessonCompetency.lesson_id == lesson.id))}
    return {
        "id": lesson.id,
        "number": lesson.number,
        "title": lesson.title,
        "description": lesson.description,
        "duration": lesson.duration,
        "is_published": lesson.is_published,
        "access_override": lesson.access_override,
        "competencies_published": sum(1 for c in comps.values() if c.is_published),
        "videos": db.scalar(select(func.count()).select_from(Video).where(Video.lesson_id == lesson.id)) or 0,
        "videos_published": db.scalar(select(func.count()).select_from(Video).where(Video.lesson_id == lesson.id, Video.is_published.is_(True))) or 0,
        "resources": db.scalar(select(func.count()).select_from(LearningResource).where(LearningResource.lesson_id == lesson.id)) or 0,
    }


@router.get("/levels/{level}/lessons")
def admin_level_lessons(level: str, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    level = structure.normalize_level(level)
    course = structure.level_course(db, level)
    module = structure.main_module(db, course) if course else None
    return {**_level_summary(db, level), "lessons": [_admin_lesson_card(db, lesson) for lesson in structure.level_lessons(db, module)]}


class ReorderBody(BaseModel):
    lesson_ids: list[UUID] = Field(..., min_length=1, max_length=60)


@router.post("/levels/{level}/reorder")
def reorder_lessons(level: str, data: ReorderBody, request: Request, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    lessons = structure.reorder(db, level, data.lesson_ids)
    _audit(db, request, user, "lms_lessons_reordered", level=level.upper(), order=[str(lesson.id) for lesson in lessons])
    return {"lessons": [_admin_lesson_card(db, lesson) for lesson in lessons]}


# ============================================================
# Lesson + competencies
# ============================================================


def _competency_content(db: Session, lesson_id: UUID) -> dict[str, dict]:
    counts = progress.content_counts(db, lesson_id)

    def exercises(skill: str) -> dict:
        rows = list(db.scalars(select(SkillExercise).where(SkillExercise.lesson_id == lesson_id, SkillExercise.skill == skill)))
        return {"total": len(rows), "published": sum(1 for r in rows if r.is_published)}

    def speakings(kind: str) -> dict:
        rows = list(db.scalars(select(Speaking).where(Speaking.lesson_id == lesson_id, Speaking.task_kind == kind)))
        return {"total": len(rows), "published": sum(1 for r in rows if r.is_published)}

    writings = list(db.scalars(select(Writing).where(Writing.lesson_id == lesson_id)))
    videos: dict[str, int] = {}
    for comp, n in db.execute(select(Video.competency, func.count()).where(Video.lesson_id == lesson_id).group_by(Video.competency)):
        videos[comp or "EINFUEHRUNG"] = videos.get(comp or "EINFUEHRUNG", 0) + n
    out = {
        "EINFUEHRUNG": {"frage": speakings("FRAGE")},
        "WORTSCHATZ": {"words": counts["vocabulary"], "exercises": exercises("WORTSCHATZ")},
        "GRAMMATIK": {"rules": counts["grammar"], "exercises": exercises("GRAMMATIK")},
        "LESEN": {"readings": counts["readings"]},
        "HOEREN": {"listenings": counts["listenings"]},
        "SPRECHEN": {"tasks": speakings("SPRECHEN")},
        "SCHREIBEN": {"tasks": {"total": len(writings), "published": sum(1 for w in writings if w.is_published)}},
        "UEBUNGEN": {"exercises": exercises("UEBUNGEN")},
        "ABSCHLUSSTEST": {"exercises": exercises("YAKUNIY")},
        "ZUSAMMENFASSUNG": {},
    }
    for kind in COMPETENCY_ORDER:
        out[kind]["videos"] = videos.get(kind, 0)
        out[kind]["resources"] = counts["resources"].get(kind, 0)
    return out


def _video_admin(video: Video, service: VideoService) -> dict:
    file_ok = bool(video.storage_key) and service.resolve_video_path(video).is_file()
    subtitle_ok = bool(video.subtitle_key) and (service.video_storage.ROOT / video.subtitle_key).is_file()
    return {
        "id": video.id,
        "title": video.title,
        "competency": video.competency or "EINFUEHRUNG",
        "order_index": video.order_index,
        "duration_seconds": video.duration_seconds,
        "is_published": video.is_published,
        "file_status": "ok" if file_ok else ("missing" if video.storage_key else "no_file"),
        "has_subtitles": bool(video.subtitle_key),
        "subtitle_status": None if not video.subtitle_key else ("ok" if subtitle_ok else "missing"),
    }


def _admin_lesson(db: Session, lesson: Lesson) -> dict:
    course, _ = structure.lesson_level(db, lesson)
    comps = structure.ensure_competencies(db, lesson)
    db.commit()
    content = _competency_content(db, lesson.id)
    service = VideoService(db)
    videos = list(db.scalars(select(Video).where(Video.lesson_id == lesson.id).order_by(Video.order_index, Video.created_at)))
    return {
        "lesson": {
            "id": lesson.id,
            "number": lesson.number,
            "title": lesson.title,
            "description": lesson.description,
            "duration": lesson.duration,
            "is_published": lesson.is_published,
            "access_override": lesson.access_override,
            "level": course.level if course else None,
            "lessons_in_level": structure.LEVEL_LESSON_COUNTS.get(course.level) if course else None,
        },
        "competencies": [
            {"kind": c.kind, "position": c.position, "body": c.body, "is_published": c.is_published, "content": content[c.kind]} for c in comps
        ],
        "videos": [_video_admin(v, service) for v in videos],
        "resources": [resources.serialize(r, admin=True) for r in resources.lesson_resources(db, lesson.id, published_only=False)],
    }


@router.get("/lessons/{lesson_id}")
def admin_lesson(lesson_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return _admin_lesson(db, _lesson_or_404(db, lesson_id))


class LessonUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)
    duration: int | None = Field(None, ge=0, le=24 * 60)
    is_published: bool | None = None
    access_override: Literal["OPEN", "LOCKED"] | None = None
    number: int | None = Field(None, ge=1, le=100)


@router.patch("/lessons/{lesson_id}")
def update_lesson(lesson_id: UUID, data: LessonUpdate, request: Request, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    lesson = _lesson_or_404(db, lesson_id)
    changes = data.model_dump(exclude_unset=True)
    if "number" in changes:
        if changes["number"] is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="LESSON_NUMBER_REQUIRED")
        structure.validate_lesson_number(db, lesson, changes["number"])
    for field in ("title", "is_published"):
        if field in changes and changes[field] is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{field.upper()}_REQUIRED")
    if "description" in changes and changes["description"] is not None:
        changes["description"] = changes["description"].strip() or None
    for field, value in changes.items():
        setattr(lesson, field, value.strip() if field == "title" else value)
    db.commit()
    _audit(db, request, user, "lms_lesson_updated", lesson_id=lesson.id, changes=changes)
    return _admin_lesson(db, lesson)


class CompetencyUpdate(BaseModel):
    body: str | None = Field(None, max_length=50000)
    is_published: bool | None = None


@router.patch("/lessons/{lesson_id}/competencies/{kind}")
def update_competency(
    lesson_id: UUID, kind: str, data: CompetencyUpdate, request: Request, db: Session = Depends(get_db), user: User = Depends(require_content_editor)
):
    lesson = _lesson_or_404(db, lesson_id)
    kind = kind.strip().upper()
    if kind not in COMPETENCY_ORDER:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UNKNOWN_COMPETENCY")
    comp = {c.kind: c for c in structure.ensure_competencies(db, lesson)}[kind]
    changes = data.model_dump(exclude_unset=True)
    if "is_published" in changes and changes["is_published"] is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="IS_PUBLISHED_REQUIRED")
    if "body" in changes:
        # same sanitising as the existing Grammatik rules (rich text from the admin editor)
        comp.body = skill_admin.clean_html(changes["body"]) if changes["body"] else None
    if "is_published" in changes:
        comp.is_published = changes["is_published"]
    db.commit()
    _audit(db, request, user, "lms_competency_updated", lesson_id=lesson.id, kind=kind, fields=sorted(changes))
    return _admin_lesson(db, lesson)


# ============================================================
# Resources
# ============================================================


@router.post("/lessons/{lesson_id}/resources", status_code=status.HTTP_201_CREATED)
async def upload_resource(
    lesson_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    resource_type: str = Form(...),
    title: str = Form(..., min_length=1, max_length=255),
    competency: str | None = Form(None),
    description: str | None = Form(None),
    duration_seconds: int | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_content_editor),
):
    lesson = _lesson_or_404(db, lesson_id)
    resource = await resources.create_file_resource(
        db, lesson, resource_type=resource_type, file=file, title=title, competency=competency,
        description=description, duration_seconds=duration_seconds, actor_id=user.id,
    )
    _audit(db, request, user, "lms_resource_uploaded", lesson_id=lesson.id, resource_id=resource.id, type=resource.resource_type, size=resource.size_bytes)
    return resources.serialize(resource, admin=True)


class LinkCreate(BaseModel):
    url: str = Field(..., max_length=1000)
    title: str = Field(..., min_length=1, max_length=255)
    competency: str | None = None
    description: str | None = Field(None, max_length=5000)


@router.post("/lessons/{lesson_id}/links", status_code=status.HTTP_201_CREATED)
def create_link(lesson_id: UUID, data: LinkCreate, request: Request, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    lesson = _lesson_or_404(db, lesson_id)
    resource = resources.create_link_resource(
        db, lesson, url=data.url, title=data.title, competency=data.competency, description=data.description, actor_id=user.id
    )
    _audit(db, request, user, "lms_link_created", lesson_id=lesson.id, resource_id=resource.id)
    return resources.serialize(resource, admin=True)


class ResourceUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)
    competency: str | None = None
    order_index: int | None = Field(None, ge=1, le=10000)
    is_published: bool | None = None
    url: str | None = Field(None, max_length=1000)


@router.patch("/resources/{resource_id}")
def update_resource(resource_id: UUID, data: ResourceUpdate, request: Request, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    resource = _resource_or_404(db, resource_id)
    changes = data.model_dump(exclude_unset=True)
    for field in ("title", "order_index", "is_published"):
        if field in changes and changes[field] is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{field.upper()}_REQUIRED")
    if "competency" in changes:
        resource.competency = resources.validate_competency(changes["competency"])
    if "url" in changes:
        if resource.resource_type != "LINK" or not changes["url"] or not resources.URL_RE.match(changes["url"].strip()):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="INVALID_URL: https:// links only")
        resource.external_url = changes["url"].strip()
    if "title" in changes:
        resource.title = changes["title"].strip()
    if "description" in changes:
        resource.description = (changes["description"] or "").strip() or None
    for field in ("order_index", "is_published"):
        if field in changes:
            setattr(resource, field, changes[field])
    db.commit()
    _audit(db, request, user, "lms_resource_updated", resource_id=resource.id, fields=sorted(changes))
    db.refresh(resource)
    return resources.serialize(resource, admin=True)


@router.put("/resources/{resource_id}/file")
async def replace_resource_file(
    resource_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    duration_seconds: int | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_content_editor),
):
    resource = _resource_or_404(db, resource_id)
    resource = await resources.replace_file(db, resource, file, duration_seconds)
    _audit(db, request, user, "lms_resource_file_replaced", resource_id=resource.id, size=resource.size_bytes)
    return resources.serialize(resource, admin=True)


@router.delete("/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(resource_id: UUID, request: Request, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    resource = _resource_or_404(db, resource_id)
    info = {"resource_id": resource.id, "lesson_id": resource.lesson_id, "title": resource.title}
    await resources.delete_resource(db, resource)
    _audit(db, request, user, "lms_resource_deleted", **info)


@router.get("/resources/{resource_id}/file")
def preview_resource_file(resource_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    resource = _resource_or_404(db, resource_id)
    path = resources.file_path(resource)
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RESOURCE_FILE_MISSING")
    return FileResponse(path, media_type=resource.mime_type or "application/octet-stream", headers={"Cache-Control": "private, no-store"})


# ============================================================
# Student progress + storage health
# ============================================================


@router.get("/lessons/{lesson_id}/progress")
def lesson_progress(
    lesson_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_panel_access),
):
    """Students with any activity in the lesson (snapshot), newest first."""
    _lesson_or_404(db, lesson_id)
    base = select(StudentProgress).where(StudentProgress.lesson_id == lesson_id)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = list(
        db.scalars(
            base.order_by(StudentProgress.last_activity_at.desc().nulls_last(), StudentProgress.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    user_ids = [r.user_id for r in rows]
    users = {u.id: u for u in db.scalars(select(User).where(User.id.in_(user_ids)))} if user_ids else {}
    comps: dict = {}
    if user_ids:
        for row in db.scalars(
            select(StudentCompetencyProgress).where(StudentCompetencyProgress.lesson_id == lesson_id, StudentCompetencyProgress.user_id.in_(user_ids))
        ):
            comps.setdefault(row.user_id, {})[row.competency] = {"status": row.status, "score": row.score, "completed_at": row.completed_at}
    items = []
    for r in rows:
        u = users.get(r.user_id)
        name = " ".join(x for x in (u.first_name, u.last_name) if x) if u else None
        items.append(
            {
                "user_id": r.user_id,
                "name": name or (u.email if u else None),
                "lesson_completed": r.lesson_completed,
                "completed_at": r.completed_at,
                "last_activity_at": r.last_activity_at,
                "competencies": comps.get(r.user_id, {}),
            }
        )
    return {"page": page, "page_size": page_size, "total": total, "items": items}


@router.get("/storage-health")
def storage_health(level: str | None = Query(None), db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """Every file the course content points at: present on disk or missing
    (videos, subtitles, resources, Hören audio). Per lesson, problems only."""
    levels = [structure.normalize_level(level)] if level else list(structure.LEVELS)
    service = VideoService(db)
    report, totals = [], {"checked": 0, "missing": 0}
    for lvl in levels:
        course = structure.level_course(db, lvl)
        module = structure.main_module(db, course) if course else None
        for lesson in structure.level_lessons(db, module):
            problems = []
            for v in db.scalars(select(Video).where(Video.lesson_id == lesson.id)):
                info = _video_admin(v, service)
                totals["checked"] += 1
                if info["file_status"] != "ok":
                    problems.append({"kind": "video", "id": v.id, "title": v.title, "status": info["file_status"], "published": v.is_published})
                if info["subtitle_status"] == "missing":
                    problems.append({"kind": "subtitle", "id": v.id, "title": v.title, "status": "missing", "published": v.is_published})
            for r in db.scalars(select(LearningResource).where(LearningResource.lesson_id == lesson.id, LearningResource.storage_key.is_not(None))):
                totals["checked"] += 1
                if resources.file_path(r) is None:
                    problems.append({"kind": "resource", "id": r.id, "title": r.title, "status": "missing", "published": r.is_published})
            for lst in db.scalars(select(Listening).where(Listening.lesson_id == lesson.id, Listening.audio_storage_path.is_not(None))):
                totals["checked"] += 1
                if skill_admin.listening_audio_path(lst) is None:
                    problems.append({"kind": "hoeren_audio", "id": lst.id, "title": lst.title, "status": "missing", "published": lst.is_published})
            if problems:
                totals["missing"] += len(problems)
                report.append({"level": lvl, "lesson_id": lesson.id, "number": lesson.number, "title": lesson.title, "problems": problems})
    return {"totals": totals, "lessons": report}
