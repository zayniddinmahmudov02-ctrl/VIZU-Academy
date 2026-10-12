from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.api.dependencies.progress import require_lesson_access
from app.db.session import get_db
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.speaking import (
    SpeakingCreate,
    SpeakingAdminResponse,
    SpeakingResponse,
    SpeakingUpdate,
)
from app.schemas.student_speaking import StudentSpeakingOwnResponse
from app.services.lesson_skills.ai_evaluation import STATUS_EVALUATION_FAILED, STATUS_SUBMITTED, run_speaking_evaluation
from app.services.speaking import SpeakingService
from app.services.student_speaking import StudentSpeakingService
from app.services.vizu_pay.access import can_access_lesson

router = APIRouter(
    prefix="/speakings",
    tags=["Speakings"],
)


@router.get("", response_model=list[SpeakingAdminResponse])
def get_speakings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    # Unscoped across every lesson — admin CMS content table only.
    return SpeakingService(db).get_all()


@router.get("/lesson/{lesson_id}", response_model=list[SpeakingResponse])
def get_lesson_speakings(
    lesson_id: str,
    kind: str = Query("SPRECHEN", pattern=r"^(SPRECHEN|FRAGE)$"),
    db: Session = Depends(get_db),
    __: User = Depends(require_lesson_access),
):
    """Student-facing, published-only — Sprechen's source of truth (the
    Assessment Engine's Sprechen implementation is no longer used by the
    student frontend; see lesson-sections.ts). kind=FRAGE returns the
    lesson's Frage des Themas voice task(s) instead."""
    return SpeakingService(db).get_by_lesson(lesson_id, published_only=True, task_kind=kind)


@router.get("/{speaking_id}", response_model=SpeakingResponse)
def get_speaking(
    speaking_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    speaking = SpeakingService(db).get(speaking_id)

    if not speaking:
        raise HTTPException(
            status_code=404,
            detail="Speaking not found",
        )

    # Direct-by-ID must not bypass the free-3-lessons/Premium rule.
    lesson = db.get(Lesson, speaking.lesson_id)
    if lesson is None or not can_access_lesson(current_user, lesson):
        raise HTTPException(status_code=403, detail="PREMIUM_REQUIRED")

    return speaking


@router.post("", response_model=SpeakingAdminResponse)
def create_speaking(
    data: SpeakingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return SpeakingService(db).create(data)


@router.put("/{speaking_id}", response_model=SpeakingAdminResponse)
def update_speaking(
    speaking_id: str,
    data: SpeakingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    speaking = SpeakingService(db).update(
        speaking_id,
        data,
    )

    if not speaking:
        raise HTTPException(
            status_code=404,
            detail="Speaking not found",
        )

    return speaking


@router.delete("/{speaking_id}")
def delete_speaking(
    speaking_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    deleted = SpeakingService(db).delete(speaking_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Speaking not found",
        )

    return {
        "message": "Speaking deleted"
    }


# ==========================
# Real student submission (see app/models/student_speaking.py)
# ==========================


@router.post("/{speaking_id}/submissions", response_model=StudentSpeakingOwnResponse, status_code=201)
async def submit_speaking(
    speaking_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    duration_seconds: int | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aufgabe senden (or a re-record) — always the complete recording in
    one call. AI-evaluated tasks then run speech-to-text + AI evaluation in
    the background; the audio is stored first, so nothing is lost if a
    service is temporarily unavailable."""
    item = await StudentSpeakingService(db).upload_recording(current_user.id, speaking_id, file, duration_seconds)
    if item.speaking is not None and item.speaking.ai_evaluation_enabled:
        background_tasks.add_task(run_speaking_evaluation, item.id)
    return item


@router.post("/{speaking_id}/submissions/me/evaluate", response_model=StudentSpeakingOwnResponse)
def retry_my_speaking_evaluation(
    speaking_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retry after EVALUATION_FAILED (the recording was kept)."""
    item = StudentSpeakingService(db).get_own(current_user.id, speaking_id)
    if item is None or item.status != STATUS_EVALUATION_FAILED:
        raise HTTPException(status_code=409, detail="NOTHING_TO_RETRY")
    # pending again BEFORE responding, so the client keeps polling until the
    # background run (which claims SUBMITTED -> EVALUATING) has finished
    item.status = STATUS_SUBMITTED
    db.commit()
    db.refresh(item)
    background_tasks.add_task(run_speaking_evaluation, item.id)
    return item


@router.get("/{speaking_id}/submissions/me", response_model=StudentSpeakingOwnResponse | None)
def get_my_speaking_submission(
    speaking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return StudentSpeakingService(db).get_own(current_user.id, speaking_id)


@router.get("/submissions/{submission_id}/audio")
def get_speaking_submission_audio(
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The only way to fetch a legacy Sprechen recording's bytes — never
    a public URL. Re-checked on every request: the submitting student, an
    assigned teacher (TeacherAssignment-scoped), or any other admin-panel
    role — see StudentSpeakingService.authorize_audio_access."""
    service = StudentSpeakingService(db)
    item = service.authorize_audio_access(submission_id, current_user)
    path = service.resolve_audio_path(item)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file missing on disk.")
    return FileResponse(path=path, media_type=item.content_type, filename=item.filename)
