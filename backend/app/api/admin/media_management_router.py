"""Media Management — one admin overview of the lesson videos and Hören
audio of every level (A1-C1).

Read-only on purpose: uploading, replacing, publishing and deleting go
through the existing endpoints (POST /admin/videos/upload[/init|chunk|
complete], PUT /admin/videos/{id}[/replace], DELETE /admin/videos/{id},
POST|DELETE /admin/lesson-skills/listenings/{id}/audio, PUT /listenings/{id})
so storage, validation, publish rules (Hören: audio + answer key) and audit
stay in one place. No storage paths are returned — only file names, sizes
and whether the file is on disk.

Exception: the A2 Audio Manager (/a2-audio/...) — the A2 audio library
with batch upload, manifest, explicit linking to Hören tasks and the A2
sales readiness (app/services/a2_audio). Reads need admin-panel access,
changes a content editor, confirming a manual sales check a SUPER_ADMIN.
"""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from jose import JWTError
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access, require_content_editor, require_super_admin
from app.core.audit import write_audit
from app.core.security.jwt import create_admin_video_preview_token, decode_admin_video_preview_token
from app.db.session import get_db
from app.models.a2_audio_asset import A2AudioAsset
from app.models.course import Course
from app.models.language import Language
from app.models.lesson import Lesson
from app.models.listening import Listening
from app.models.listening_audio_archive import ListeningAudioArchive
from app.models.listening_audio_track import ListeningAudioTrack
from app.models.module import Module
from app.models.user import User
from app.models.video import Video
from app.services.a2_audio import assets as a2_assets
from app.services.a2_audio import readiness as a2_readiness
from app.services.lesson_skills import exercises as skill_exercises
from app.services.lesson_skills.admin import audio_tracks_admin, listening_storage
from app.services.lms import structure as lms_structure
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




@router.get("/a2-audio")
def a2_audio_overview(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_panel_access),
):
    """A2 Hören audio per real LMS lesson. Read-only. The lesson list comes
    from the LMS course structure (not a fixed count) and every card is an
    existing Hören task; no audio slot is invented. The A2 book itself is not
    available to the system, so the expected slot count is unknown (None) and
    nothing here is confirmed against the book."""
    course = lms_structure.level_course(db, "A2")
    module = lms_structure.main_module(db, course) if course else None
    lessons = lms_structure.level_lessons(db, module)
    ids = [lesson.id for lesson in lessons]
    tasks = (
        list(
            db.scalars(
                select(Listening).where(Listening.lesson_id.in_(ids)).order_by(Listening.order_index, Listening.created_at)
            )
        )
        if ids
        else []
    )
    tasks = [task for task in tasks if not (task.title or "").startswith("[Archiv]")]
    by_lesson: dict[str, list[dict]] = {str(lesson.id): [] for lesson in lessons}
    for task in tasks:
        path = _audio_path(task)
        suffix = Path(task.audio_storage_path or "").suffix.lstrip(".").lower()
        by_lesson[str(task.lesson_id)].append(
            {
                "id": str(task.id),
                "title": task.title,
                "order_index": task.order_index,
                "is_published": task.is_published,
                "audio_original_name": task.audio_original_name if task.audio_storage_path else None,
                "audio_format": suffix.upper() or None,
                "audio_size_bytes": task.audio_size_bytes if path else None,
                "audio_duration_seconds": task.audio_duration_seconds,
                "file_status": "ok" if path else ("missing" if task.audio_storage_path else ("external" if task.audio_url else "none")),
                "format_error": bool(suffix) and suffix not in ("mp3", "m4a"),
                "question_count": len(task.questions),
                "key_missing": sum(1 for question in task.questions if not skill_exercises.has_key(question)),
                "audio_slots": audio_tracks_admin(task),
                "material_key": task.a2_material_key,
                "archived_versions": db.scalar(
                    select(func.count()).select_from(ListeningAudioArchive).where(ListeningAudioArchive.listening_id == task.id)
                ),
            }
        )
    lesson_payload = []
    for lesson in lessons:
        items = by_lesson[str(lesson.id)]
        lesson_payload.append(
            {
                "lesson_id": str(lesson.id),
                "lesson_number": lesson.number,
                "lesson_title": lesson.title,
                "tasks": items,
                "task_count": len(items),
                # real files on disk: main audio + extra tracks (not the same number as the tasks)
                "media_file_count": sum(1 for item in items for slot in item["audio_slots"] if slot["file_status"] == "ok"),
                "question_count": sum(item["question_count"] for item in items),
                "uploaded_count": sum(1 for item in items if item["file_status"] == "ok"),
                "missing_count": sum(1 for item in items if item["file_status"] in ("none", "missing")),
            }
        )
    return {
        "book_confirmed": False,
        "lesson_count": len(lessons),
        "expected_audio_slots": None,
        "task_count": len(tasks),
        "uploaded_audio_count": sum(item["uploaded_count"] for item in lesson_payload),
        "missing_audio_count": sum(item["missing_count"] for item in lesson_payload),
        "format_error_count": sum(1 for lesson in lesson_payload for item in lesson["tasks"] if item["format_error"]),
        # DB says a file exists, storage has none (cleaned by hand): shown, and removable with the normal delete
        "stale_record_count": sum(1 for lesson in lesson_payload for item in lesson["tasks"] if item["file_status"] == "missing"),
        "unreferenced_files": _unreferenced_audio_files(db),
        "lessons": lesson_payload,
    }


def _unreferenced_audio_files(db: Session) -> list[dict]:
    """Stored audio files no Hören task, extra track or archived version of ANY
    level points at. Report only — nothing is deleted automatically."""
    root = listening_storage.ROOT.resolve()
    if not root.is_dir():
        return []
    referenced: set[str] = set()
    for column in (Listening.audio_storage_path, ListeningAudioTrack.storage_path, ListeningAudioArchive.storage_path, A2AudioAsset.storage_path):
        referenced.update(str((root / path).resolve()) for path in db.scalars(select(column).where(column.is_not(None))))
    return [
        {"file_name": f.name, "size_bytes": f.stat().st_size}
        for f in sorted(root.rglob("*"))
        if f.is_file() and str(f.resolve()) not in referenced
    ]


# ============================================================
# A2 Audio Manager
# ============================================================

class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class A2AssetUpdate(_In):
    unterricht: int | None = Field(None, ge=1, le=99)
    audio_kind: str | None = Field(None, max_length=20)
    part: int | None = Field(None, ge=1, le=99)
    title: str | None = Field(None, max_length=255)
    sort_order: int | None = Field(None, ge=0, le=10_000)
    duration_seconds: int | None = Field(None, ge=1)


class A2Verify(_In):
    state: str = Field(pattern="^(verified|problem|pending)$")
    note: str | None = Field(None, max_length=1000)


class A2Link(_In):
    listening_id: UUID


class A2ReadinessCheck(_In):
    key: str = Field(max_length=40)
    done: bool
    note: str | None = Field(None, max_length=500)


@router.get("/a2-audio/assets")
def a2_audio_assets(db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """The A2 audio library (no storage paths), with link suggestions from the file names."""
    return a2_assets.list_assets(db)


@router.get("/a2-audio/manifest")
def a2_audio_manifest(db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """Manifest from the real data: files per Unterricht, every current Hören task and its audio state."""
    return a2_assets.manifest(db)


@router.get("/a2-audio/targets")
def a2_audio_targets(db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """Current Hören tasks of the A2 lessons — the only valid link targets."""
    linked = {a.listening_id: a.id for a in db.scalars(select(a2_assets.A2AudioAsset).where(a2_assets.A2AudioAsset.listening_id.is_not(None)))}
    return [{"listening_id": t.id, "lesson_number": lesson.number, "lesson_title": lesson.title, "title": t.title, "order_index": t.order_index,
             "content_id": t.content_id, "is_published": t.is_published, "has_audio": bool(t.audio_storage_path or t.audio_url),
             "asset_id": linked.get(t.id)} for t, lesson in a2_assets.a2_tasks(db)]


@router.post("/a2-audio/assets", status_code=201)
async def a2_audio_upload(
    file: UploadFile = File(...),
    unterricht: int | None = Form(None),
    audio_kind: str | None = Form(None),
    part: int | None = Form(None),
    title: str | None = Form(None),
    duration_seconds: int | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_content_editor),
):
    """One file per request (the batch upload sends them one after another, each with its own progress).
    409 DUPLICATE if the same content is already in the library. Nothing is linked here."""
    fields = {k: v for k, v in {"unterricht": unterricht, "audio_kind": audio_kind, "part": part, "title": title,
                                "duration_seconds": duration_seconds}.items() if v not in (None, "")}
    asset = await a2_assets.upload(db, user, file, fields)
    write_audit(db, actor_id=str(user.id), action="a2_audio_uploaded",
                details=f"asset={asset['id']}; original_name={asset['original_filename']}; sha256={asset['sha256'][:16]}")
    return asset


@router.patch("/a2-audio/assets/{asset_id}")
def a2_audio_update(asset_id: UUID, data: A2AssetUpdate, db: Session = Depends(get_db), _: User = Depends(require_content_editor)):
    """Admin corrections: Unterricht, kind, part, title, order, duration."""
    return a2_assets.update(db, asset_id, data.model_dump(exclude_unset=True))


@router.post("/a2-audio/assets/{asset_id}/verify")
def a2_audio_verify(asset_id: UUID, data: A2Verify, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    """An admin listened: verified, or a problem (with a note), or back to pending."""
    return a2_assets.verify(db, user, asset_id, data.state, data.note)


@router.post("/a2-audio/assets/{asset_id}/link")
def a2_audio_link(asset_id: UUID, data: A2Link, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    """Explicit link to a current A2 Hören task. The task's earlier audio is archived, the task becomes a draft."""
    asset = a2_assets.link(db, user, asset_id, data.listening_id)
    write_audit(db, actor_id=str(user.id), action="a2_audio_linked", details=f"asset={asset_id}; listening={data.listening_id}")
    return asset


@router.post("/a2-audio/assets/{asset_id}/unlink")
def a2_audio_unlink(asset_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    asset = a2_assets.unlink(db, asset_id)
    write_audit(db, actor_id=str(user.id), action="a2_audio_unlinked", details=f"asset={asset_id}")
    return asset


@router.delete("/a2-audio/assets/{asset_id}")
async def a2_audio_delete(asset_id: UUID, delete_file: bool = Query(False), db: Session = Depends(get_db),
                          user: User = Depends(require_content_editor)):
    """Removes the library entry; the physical file only with delete_file=true and only if nothing else uses it."""
    result = await a2_assets.remove(db, asset_id, delete_file)
    write_audit(db, actor_id=str(user.id), action="a2_audio_deleted", details=f"asset={asset_id}; file_deleted={result['file_deleted']}")
    return result


@router.get("/a2-audio/assets/{asset_id}/audio")
def a2_audio_preview(asset_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """Admin preview player (Bearer auth, fetched as a blob — never a public URL)."""
    asset = a2_assets.get(db, asset_id)
    path = a2_assets.stored_path(asset)
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio not found.")
    return FileResponse(path, media_type=asset.content_type, headers={"Cache-Control": "private, no-store"})


@router.get("/a2-readiness")
def a2_sales_readiness(db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """A2 sales readiness: READY / NEEDS_CONTENT / NEEDS_CONFIGURATION / NEEDS_TESTING with every check."""
    return a2_readiness.compute(db)


@router.post("/a2-readiness/checks")
def a2_sales_readiness_confirm(data: A2ReadinessCheck, db: Session = Depends(get_db), user: User = Depends(require_super_admin)):
    """A person confirms (or reopens) a manual check — payment test, access test, mobile/desktop, tests."""
    result = a2_readiness.confirm(db, user, data.key, data.done, data.note)
    write_audit(db, actor_id=str(user.id), action="a2_readiness_check", details=f"{data.key}={data.done}")
    return result
