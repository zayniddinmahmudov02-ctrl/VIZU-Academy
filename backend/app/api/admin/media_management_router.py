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

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from jose import JWTError
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.core.audit import write_audit
from app.core.security.jwt import create_admin_video_preview_token, decode_admin_video_preview_token
from app.db.session import get_db
from app.models.course import Course
from app.models.language import Language
from app.models.lesson import Lesson
from app.models.listening import Listening
from app.models.listening_audio_archive import ListeningAudioArchive
from app.models.module import Module
from app.models.user import User
from app.models.video import Video
from app.services.lesson_skills import admin as skill_admin
from app.services.lesson_skills import exercises as skill_exercises
from app.services.lesson_skills.a2_audio_manifest import A2_AUDIO_MATERIALS, normalize_filename
from app.services.lesson_skills.admin import audio_tracks_admin, listening_storage
from app.services.lms import structure as lms_structure
from app.services.video.service import stored_file_path, video_media_type

router = APIRouter(prefix="/admin/media-management", tags=["Admin - Media Management"])

LEVELS = ("A1", "A2", "B1", "B2", "C1")


class A2AudioTaskCreate(BaseModel):
    material_key: str = Field(min_length=1, max_length=50)


class A2AudioTaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    order_index: int | None = Field(default=None, ge=1, le=100)
    is_published: bool | None = None


class A2AudioTaskAssign(BaseModel):
    listening_id: UUID


def _a2_lesson(db: Session, lesson_number: int) -> Lesson | None:
    if not 1 <= lesson_number <= 13:
        raise HTTPException(status_code=422, detail="A2 lesson number must be 1–13.")
    course = lms_structure.level_course(db, "A2")
    module = lms_structure.main_module(db, course) if course else None
    return next(
        (lesson for lesson in lms_structure.level_lessons(db, module) if lesson.number == lesson_number),
        None,
    )


def _a2_material_task(db: Session, material_key: str) -> tuple[object, Listening]:
    material = next((item for item in A2_AUDIO_MATERIALS if item.key == material_key), None)
    if material is None:
        raise HTTPException(status_code=404, detail="A2 audio material not found.")
    listening = db.scalar(select(Listening).where(Listening.a2_material_key == material_key))
    if listening is None:
        raise HTTPException(status_code=404, detail="A2 audio task not found.")
    return material, listening


def _a2_audio_task(db: Session, listening: Listening) -> dict:
    from app.services.lesson_skills import admin as skill_admin

    questions = sorted(listening.questions, key=lambda question: (question.order_index, question.created_at))
    return {
        "id": str(listening.id),
        "material_key": listening.a2_material_key,
        "title": listening.title,
        "order_index": listening.order_index,
        "is_published": listening.is_published,
        "audio_original_name": listening.audio_original_name,
        "audio_content_type": listening.audio_content_type,
        "audio_format": Path(listening.audio_storage_path or listening.audio_original_name or "").suffix.lstrip(".").upper() or None,
        "audio_duration_seconds": listening.audio_duration_seconds,
        "file_status": "ok" if _audio_path(listening) else ("missing" if listening.audio_storage_path else ("external" if listening.audio_url else "none")),
        "questions": [skill_admin.admin_question(question) for question in questions],
        "question_count": len(questions),
        "key_missing": sum(1 for question in questions if not skill_exercises.has_key(question)),
        "extra_audio_tracks": audio_tracks_admin(listening),
        "archive": [
            {
                "id": str(version.id),
                "original_name": version.original_name,
                "content_type": version.content_type,
                "size_bytes": version.size_bytes,
                "duration_seconds": version.duration_seconds,
                "archived_at": version.archived_at,
            }
            for version in db.scalars(
                select(ListeningAudioArchive)
                .where(ListeningAudioArchive.listening_id == listening.id)
                .order_by(ListeningAudioArchive.archived_at.desc())
            )
        ],
    }


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


@router.get("/a2-audio")
def a2_audio_overview(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_panel_access),
):
    """Return the 13 declared A2 lesson slots without changing existing content."""
    course = lms_structure.level_course(db, "A2")
    module = lms_structure.main_module(db, course) if course else None
    lesson_by_number = {
        lesson.number: lesson
        for lesson in lms_structure.level_lessons(db, module)
        if 1 <= lesson.number <= 13
    }
    lesson_ids = [lesson.id for lesson in lesson_by_number.values()]
    tasks = list(
        db.scalars(
            select(Listening)
            .where(Listening.lesson_id.in_(lesson_ids))
            .order_by(Listening.order_index, Listening.created_at)
        )
    ) if lesson_ids else []
    material_keys = {item.key for item in A2_AUDIO_MATERIALS}
    expected: dict[int, list[dict]] = {number: [] for number in range(1, 14)}
    for material in A2_AUDIO_MATERIALS:
        lesson = lesson_by_number.get(material.lesson_number)
        assigned = next((task for task in tasks if task.a2_material_key == material.key), None)
        format_matches = (
            Path(assigned.audio_storage_path).suffix.casefold() == f".{material.extension}"
            if assigned and assigned.audio_storage_path
            else None
        )
        candidates = [
            task
            for task in tasks
            if lesson is not None
            and task.lesson_id == lesson.id
            and (
                normalize_filename(task.audio_original_name or "") == normalize_filename(material.source_name)
                or normalize_filename(task.title) == normalize_filename(material.source_name)
            )
        ]
        expected[material.lesson_number].append(
            {
                "key": material.key,
                "slot_number": material.material_number,
                "source_name": material.source_name,
                "expected_format": material.extension.upper(),
                "format_matches": format_matches,
                "listening": _a2_audio_task(db, assigned) if assigned else None,
                "suggested_task_ids": [
                    str(task.id) for task in candidates if task.a2_material_key != material.key
                ],
                "available_task_ids": [
                    str(task.id)
                    for task in tasks
                    if lesson is not None
                    and task.lesson_id == lesson.id
                    and task.a2_material_key is None
                ],
            }
        )

    lesson_payload = []
    mapped_tasks = [task for task in tasks if task.a2_material_key in material_keys]
    for number in range(1, 14):
        lesson = lesson_by_number.get(number)
        lesson_tasks = [task for task in tasks if lesson is not None and task.lesson_id == lesson.id]
        lesson_payload.append(
            {
                "lesson_number": number,
                "lesson_id": str(lesson.id) if lesson else None,
                "lesson_title": lesson.title if lesson else None,
                "lesson_exists": lesson is not None,
                "expected_materials": expected[number],
                "other_tasks": [
                    _a2_audio_task(db, task)
                    for task in lesson_tasks
                    if task.a2_material_key not in material_keys
                ],
            }
        )
    uploaded_count = sum(1 for task in mapped_tasks if _audio_path(task))
    format_mismatch_count = sum(
        1
        for lesson_materials in expected.values()
        for material in lesson_materials
        if material["format_matches"] is False
    )
    return {
        "expected_lesson_count": 13,
        "actual_lesson_count": len(lesson_by_number),
        "expected_audio_count": len(A2_AUDIO_MATERIALS),
        "mapped_audio_count": len(mapped_tasks),
        "uploaded_audio_count": uploaded_count,
        "format_mismatch_count": format_mismatch_count,
        "lesson_count_matches": len(lesson_by_number) == 13,
        "audio_count_matches": len(mapped_tasks) == len(A2_AUDIO_MATERIALS)
        and uploaded_count == len(A2_AUDIO_MATERIALS)
        and format_mismatch_count == 0,
        "lessons": lesson_payload,
    }


@router.post("/a2-audio/lessons/{lesson_number}/materials")
def create_a2_audio_task(
    lesson_number: int,
    data: A2AudioTaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin_panel_access),
):
    """Create a draft task only after an admin explicitly requests the slot."""
    material = next((item for item in A2_AUDIO_MATERIALS if item.key == data.material_key), None)
    if material is None or material.lesson_number != lesson_number:
        raise HTTPException(status_code=422, detail="Material key does not belong to this A2 lesson.")
    lesson = _a2_lesson(db, lesson_number)
    if lesson is None:
        raise HTTPException(status_code=409, detail="A2 lesson does not exist; no lesson was created.")
    if db.scalar(select(Listening.id).where(Listening.a2_material_key == material.key)) is not None:
        raise HTTPException(status_code=409, detail="This A2 material already has a task.")
    listening = Listening(
        lesson_id=lesson.id,
        title=material.source_name,
        order_index=material.material_number,
        is_published=False,
        a2_material_key=material.key,
    )
    db.add(listening)
    db.commit()
    db.refresh(listening)
    write_audit(db, actor_id=str(user.id), action="a2_audio_task_created", details=f"lesson={lesson_number}; key={material.key}")
    return _a2_audio_task(db, listening)


@router.put("/a2-audio/materials/{material_key}/assign")
def assign_a2_audio_task(
    material_key: str,
    data: A2AudioTaskAssign,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin_panel_access),
):
    material = next((item for item in A2_AUDIO_MATERIALS if item.key == material_key), None)
    if material is None:
        raise HTTPException(status_code=404, detail="A2 audio material not found.")
    task = db.get(Listening, data.listening_id)
    lesson = _a2_lesson(db, material.lesson_number)
    if task is None or lesson is None or task.lesson_id != lesson.id:
        raise HTTPException(status_code=422, detail="Choose an existing Hören task from the same A2 lesson.")
    existing = db.scalar(select(Listening).where(Listening.a2_material_key == material_key))
    if existing is not None and existing.id != task.id:
        raise HTTPException(status_code=409, detail="This A2 material is already assigned to another task.")
    if task.a2_material_key and task.a2_material_key != material_key:
        raise HTTPException(status_code=409, detail="This task is already assigned to another A2 material.")
    task.a2_material_key = material_key
    db.commit()
    db.refresh(task)
    write_audit(db, actor_id=str(user.id), action="a2_audio_task_assigned", details=f"task={task.id}; key={material_key}")
    return _a2_audio_task(db, task)


@router.patch("/a2-audio/materials/{material_key}")
def update_a2_audio_task(
    material_key: str,
    data: A2AudioTaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin_panel_access),
):
    material, task = _a2_material_task(db, material_key)
    changes = data.model_dump(exclude_unset=True)
    if "title" in changes:
        task.title = changes["title"].strip()
    if "order_index" in changes:
        task.order_index = changes["order_index"]
    if changes.get("is_published") is True:
        if skill_admin.listening_audio_path(task) is None or not task.questions:
            raise HTTPException(status_code=409, detail="Add audio and the task's real questions before publishing.")
        if any(not skill_exercises.has_key(question) for question in task.questions):
            raise HTTPException(status_code=409, detail="Resolve all answer keys before publishing.")
    if "is_published" in changes:
        task.is_published = changes["is_published"]
    db.commit()
    db.refresh(task)
    write_audit(
        db,
        actor_id=str(user.id),
        action="a2_audio_task_updated",
        details=f"key={material.key}; fields={','.join(sorted(changes))}",
    )
    return _a2_audio_task(db, task)


@router.post("/a2-audio/materials/{material_key}/audio")
async def upload_a2_audio(
    material_key: str,
    file: UploadFile = File(...),
    duration_seconds: int | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin_panel_access),
):
    material, task = _a2_material_task(db, material_key)
    await skill_admin.upload_listening_audio(
        db,
        task.id,
        file,
        duration_seconds,
        preserve_previous=True,
        replaced_by_id=user.id,
        allow_auto_publish=False,
        expected_format=material.extension,
    )
    write_audit(
        db,
        actor_id=str(user.id),
        action="a2_audio_replaced",
        details=f"key={material.key}; task={task.id}; original_name={(file.filename or '')[:255]}",
    )
    db.refresh(task)
    return _a2_audio_task(db, task)


@router.get("/a2-audio/materials/{material_key}/preview")
def preview_a2_audio(
    material_key: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_panel_access),
):
    _, task = _a2_material_task(db, material_key)
    path = skill_admin.listening_audio_path(task)
    if path is None:
        raise HTTPException(status_code=404, detail="A2 audio file is missing.")
    return FileResponse(path, media_type=task.audio_content_type or "application/octet-stream", headers={"Cache-Control": "private, no-store"})


@router.get("/a2-audio/materials/{material_key}/archive/{archive_id}/preview")
def preview_archived_a2_audio(
    material_key: str,
    archive_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_panel_access),
):
    _, task = _a2_material_task(db, material_key)
    archived = db.get(ListeningAudioArchive, archive_id)
    if archived is None or archived.listening_id != task.id:
        raise HTTPException(status_code=404, detail="Archived audio not found.")
    root = listening_storage.ROOT.resolve()
    path = (root / archived.storage_path).resolve()
    if root not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="Archived audio file is missing.")
    return FileResponse(path, media_type=archived.content_type or "application/octet-stream", headers={"Cache-Control": "private, no-store"})
