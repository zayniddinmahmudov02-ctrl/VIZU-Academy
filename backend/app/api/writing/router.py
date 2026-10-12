from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_admin_panel_access
from app.api.dependencies.progress import require_lesson_access
from app.db.session import get_db

from app.models.lesson import Lesson
from app.models.user import User

from app.schemas.writing import (
    WritingCreate,
    WritingUpdate,
    WritingResponse,
    WritingAdminResponse,
)
from app.services.lesson_skills.ai_evaluation import STATUS_EVALUATION_FAILED, STATUS_SUBMITTED, run_writing_evaluation
from app.schemas.student_writing import StudentWritingOwnResponse, WritingSubmitRequest

from app.services.writing import WritingService
from app.services.student_writing import StudentWritingService
from app.services.lms.access import ensure_lesson_open

router = APIRouter(
    prefix="/writings",
    tags=["Writings"],
)


@router.get("", response_model=list[WritingAdminResponse])
def get_writings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    # Unscoped across every lesson — admin CMS content table only.
    return WritingService(db).get_all()


@router.get("/lesson/{lesson_id}", response_model=list[WritingResponse])
def get_lesson_writings(
    lesson_id: str,
    db: Session = Depends(get_db),
    __: User = Depends(require_lesson_access),
):
    """Student-facing, published-only — Schreiben's source of truth (the
    Assessment Engine's Schreiben implementation is no longer used by the
    student frontend; see lesson-sections.ts)."""
    return WritingService(db).get_by_lesson(lesson_id, published_only=True)


@router.get("/{writing_id}", response_model=WritingResponse)
def get_writing(
    writing_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    writing = WritingService(db).get(writing_id)

    if not writing:
        raise HTTPException(
            status_code=404,
            detail="Writing not found",
        )

    # Direct-by-ID must not bypass the free-3-lessons/Premium rule.
    lesson = db.get(Lesson, writing.lesson_id)
    if lesson is None:
        raise HTTPException(status_code=403, detail="PREMIUM_REQUIRED")
    ensure_lesson_open(db, current_user, lesson)

    return writing


@router.post("", response_model=WritingAdminResponse)
def create_writing(
    data: WritingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return WritingService(db).create(data)


@router.put("/{writing_id}", response_model=WritingAdminResponse)
def update_writing(
    writing_id: str,
    data: WritingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    writing = WritingService(db).update(
        writing_id,
        data,
    )

    if not writing:
        raise HTTPException(
            status_code=404,
            detail="Writing not found",
        )

    return writing


@router.delete("/{writing_id}")
def delete_writing(
    writing_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    deleted = WritingService(db).delete(writing_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Writing not found",
        )

    return {
        "message": "Writing deleted"
    }


# ==========================
# Real student submission (see app/models/student_writing.py) — the
# Homework/{id}/submissions pattern, applied here.
# ==========================


@router.post("/{writing_id}/submissions", response_model=StudentWritingOwnResponse)
def submit_writing(
    writing_id: UUID,
    data: WritingSubmitRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Entwurf speichern (submit=false) or final submission (submit=true).
    For AI-evaluated tasks a final submission is evaluated in the
    background (status SUBMITTED -> EVALUATING -> GRADED / EVALUATION_FAILED)."""
    item = StudentWritingService(db).submit(current_user.id, writing_id, data.answer_text, data.submit)
    if data.submit and item.writing is not None and item.writing.ai_evaluation_enabled:
        background_tasks.add_task(run_writing_evaluation, item.id)
    return item


@router.post("/{writing_id}/submissions/me/evaluate", response_model=StudentWritingOwnResponse)
def retry_my_writing_evaluation(
    writing_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retry after EVALUATION_FAILED (the text was kept). Nothing else."""
    item = StudentWritingService(db).get_own(current_user.id, writing_id)
    if item is None or item.status != STATUS_EVALUATION_FAILED:
        raise HTTPException(status_code=409, detail="NOTHING_TO_RETRY")
    # pending again BEFORE responding, so the client keeps polling until the
    # background run (which claims SUBMITTED -> EVALUATING) has finished
    item.status = STATUS_SUBMITTED
    db.commit()
    db.refresh(item)
    background_tasks.add_task(run_writing_evaluation, item.id)
    return item


@router.get("/{writing_id}/submissions/me", response_model=StudentWritingOwnResponse | None)
def get_my_writing_submission(
    writing_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return StudentWritingService(db).get_own(current_user.id, writing_id)