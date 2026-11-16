"""Central audio endpoints (reused by Media Management and Multilevel Audio).

`/admin/audio-files`: upload an ORIGINAL, trim it (new TRIMMED file, original kept), metadata, admin preview stream.
  write `require_content_editor`, read / preview `require_admin_panel_access`.
`/admin/multilevel-audio`: the Hören slots of the Multilevel Modelltests (list, status, attach = upload/replace, trim,
  delete, preview). Same permissions. Students hear the audio through the signed URL of the exam paper:
  `GET /multilevel-exam/audio/{content_id}?token=` (token issued with the paper, rechecked per request).
`/admin/multilevel-audio/shared/{model_test_id}`: Modelltest 1 plays ONE audio for all its Hören Teile (status, attach, trim, delete, preview);
  students: `GET /multilevel-exam/audio-shared/{kompetenz_id}?token=` (same token rules)."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access, require_content_editor
from app.core.audit import write_audit
from app.db.session import get_db
from app.models.user import User
from app.services.audio_files import service as audio_service
from app.services.mock_exam import multilevel_audio as ml_audio

files_router = APIRouter(prefix="/admin/audio-files", tags=["Audio files (staff)"])
slots_router = APIRouter(prefix="/admin/multilevel-audio", tags=["Multilevel Audio (staff)"])
stream_router = APIRouter(prefix="/multilevel-exam", tags=["Multilevel exam (student)"])

PRIVATE = {"Cache-Control": "private, no-store"}


class TrimIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_ms: int = Field(ge=0, le=6 * 3600 * 1000)
    end_ms: int = Field(gt=0, le=6 * 3600 * 1000)


class AttachIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    audio_file_id: UUID


# ---------------- /admin/audio-files ----------------


@files_router.post("")
async def upload_original(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    """MP3 / WAV / M4A (checked by content, max 100 MB, readable by ffprobe) — stored privately as an ORIGINAL."""
    audio = await audio_service.store_original(db, file, user)
    write_audit(db, actor_id=user.id, action="audio_file_uploaded", details=f"audio={audio.id} bytes={audio.size_bytes}")
    return audio_service.serialize(audio)


@files_router.post("/{audio_id}/trim")
async def trim_file(audio_id: UUID, data: TrimIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    audio = await audio_service.trim(db, audio_id, data.start_ms, data.end_ms, user)
    write_audit(db, actor_id=user.id, action="audio_file_trimmed",
                details=f"audio={audio.id} source={audio.source_id} {data.start_ms}-{data.end_ms}ms")
    return audio_service.serialize(audio)


@files_router.get("/{audio_id}")
def file_info(audio_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return audio_service.serialize(audio_service.get_active(db, audio_id))


@files_router.get("/{audio_id}/file")
def file_stream(audio_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """Admin preview player (Bearer auth, fetched as a blob — never a public URL)."""
    audio = audio_service.get_active(db, audio_id)
    path = audio_service.path_of(audio)
    if path is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="AUDIO_FILE_MISSING")
    return FileResponse(path, media_type=audio.content_type, headers=PRIVATE)


# ---------------- /admin/multilevel-audio ----------------


@slots_router.get("")
def overview(db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return ml_audio.overview(db)


@slots_router.get("/slots/{content_id}")
def slot_status(content_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return ml_audio.slot_status(db, content_id)


@slots_router.put("/slots/{content_id}")
async def attach_audio(content_id: UUID, data: AttachIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    """Upload / replace: the slot plays the given (already uploaded, possibly trimmed) file."""
    return await ml_audio.attach(db, content_id, data.audio_file_id, user)


@slots_router.post("/slots/{content_id}/trim")
async def trim_slot(content_id: UUID, data: TrimIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return await ml_audio.trim_slot(db, content_id, data.start_ms, data.end_ms, user)


@slots_router.delete("/slots/{content_id}")
async def delete_audio(content_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return await ml_audio.detach(db, content_id, user)


@slots_router.get("/shared/{model_test_id}")
def shared_status(model_test_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return ml_audio.shared_status(db, model_test_id)


@slots_router.put("/shared/{model_test_id}")
async def attach_shared(model_test_id: UUID, data: AttachIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    """Upload / replace: every Hören Teil of this Modelltest plays the given (already uploaded, possibly trimmed) file."""
    return await ml_audio.attach_shared(db, model_test_id, data.audio_file_id, user)


@slots_router.post("/shared/{model_test_id}/trim")
async def trim_shared(model_test_id: UUID, data: TrimIn, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return await ml_audio.trim_shared(db, model_test_id, data.start_ms, data.end_ms, user)


@slots_router.delete("/shared/{model_test_id}")
async def delete_shared(model_test_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    return await ml_audio.detach_shared(db, model_test_id, user)


@slots_router.get("/shared/{model_test_id}/file")
def shared_file(model_test_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    from fastapi import HTTPException

    path, content_type = ml_audio.shared_file_path(db, model_test_id)
    if path is None:
        raise HTTPException(status_code=404, detail="AUDIO_NOT_FOUND")
    return FileResponse(path, media_type=content_type, headers=PRIVATE)


@slots_router.get("/slots/{content_id}/file")
def slot_file(content_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    from fastapi import HTTPException

    path, content_type = ml_audio.file_path(db, content_id)
    if path is None:
        raise HTTPException(status_code=404, detail="AUDIO_NOT_FOUND")
    return FileResponse(path, media_type=content_type, headers=PRIVATE)


# ---------------- students ----------------


@stream_router.get("/audio/{content_id}")
def exam_audio(content_id: UUID, token: str, db: Session = Depends(get_db)):
    """The only place Multilevel Hören bytes are served from; the signed token comes with the exam paper."""
    path, content_type = ml_audio.stream_target(db, content_id, token)
    return FileResponse(path, media_type=content_type, headers=PRIVATE)


@stream_router.get("/audio-shared/{kompetenz_id}")
def exam_audio_shared(kompetenz_id: UUID, token: str, db: Session = Depends(get_db)):
    """The one audio of a shared-audio Hören section (Modelltest 1); HTTP Range works, so seeking and a resumed position cost nothing."""
    path, content_type = ml_audio.stream_target_shared(db, kompetenz_id, token)
    return FileResponse(path, media_type=content_type, headers=PRIVATE)
