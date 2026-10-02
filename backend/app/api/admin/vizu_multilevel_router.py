from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db
from app.models.user import User
from app.schemas.vizu_multilevel import (
    VizuMultilevelActivityStats,
    VizuMultilevelAdminAttemptItem,
    VizuMultilevelAdminAttemptsPage,
    VizuMultilevelAnalytics,
    VizuMultilevelAudioCreate,
    VizuMultilevelAudioResponse,
    VizuMultilevelAudioUpdate,
    VizuMultilevelLevelAnalytics,
    VizuMultilevelOverviewStats,
    VizuMultilevelQuestionInput,
    VizuMultilevelSpeakingTaskAdminCreate,
    VizuMultilevelSpeakingTaskAdminResponse,
    VizuMultilevelSpeakingTaskAdminUpdate,
    VizuMultilevelStatistics,
    VizuMultilevelTaskAdmin,
    VizuMultilevelTaskAdminCreate,
    VizuMultilevelTaskAdminUpdate,
    VizuMultilevelWritingTaskAdminCreate,
    VizuMultilevelWritingTaskAdminResponse,
    VizuMultilevelWritingTaskAdminUpdate,
)
from app.services.admin import vizu_multilevel_admin_service as service
from app.services.admin import vizu_multilevel_writing_admin_service as writing_service
from app.services.admin import vizu_multilevel_content_admin_service as content_service
from app.services.admin import vizu_multilevel_speaking_admin_service as speaking_service
from app.services.admin.vizu_multilevel_content_admin_service import ContentConflictError
from app.services.vizu_multilevel import hoeren_csv_import_service, lesen_csv_import_service

router = APIRouter(prefix="/admin/vizu-multilevel", tags=["Admin - VIZU-Multilevel"])


# ============================================================
# Overview / Analytics
# ============================================================


@router.get("/overview", response_model=VizuMultilevelOverviewStats)
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return service.get_overview(db)


@router.get("/activity", response_model=VizuMultilevelActivityStats)
def get_activity(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return service.get_activity(db, days)


@router.get("/level-analytics", response_model=VizuMultilevelLevelAnalytics)
def get_level_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return service.get_level_analytics(db)


@router.get("/statistics", response_model=VizuMultilevelStatistics)
def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return service.get_statistics(db)


@router.get("/analytics", response_model=VizuMultilevelAnalytics)
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return service.get_analytics(db)


# ============================================================
# Oxirgi testlar / Natijalar
# ============================================================


@router.get("/attempts", response_model=VizuMultilevelAdminAttemptsPage)
def list_attempts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    level: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return service.list_attempts(db, page=page, page_size=page_size, search=search, level=level, status=status)


@router.get("/attempts/{attempt_id}", response_model=VizuMultilevelAdminAttemptItem)
def get_attempt_detail(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    detail = service.get_attempt_detail(db, attempt_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Attempt not found.")
    return detail


# ============================================================
# Lesen — read-only preview of the seeded content, plus a CSV import for
# re-entering/updating it (see services/vizu_multilevel/
# lesen_csv_import_service.py) — no manual question-by-question editor,
# per the module's original scope.
# ============================================================


@router.get("/lesen-content", response_model=list[VizuMultilevelTaskAdmin])
def get_lesen_content(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return content_service.list_tasks(db, "lesen")


@router.post("/lesen-content/import-csv")
async def import_lesen_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    """CSV import for VIZU-Multilevel's own Lesen Aufgabe/question/option
    content. Safe to re-run: matches existing tasks/questions/options by
    their natural key and updates them in place instead of duplicating."""
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded.")

    try:
        return lesen_csv_import_service.import_csv_text(db, text)
    except lesen_csv_import_service.CsvImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ============================================================
# Hören — read-only view of the already-seeded content, including each
# Aufgabe's attached audio (used by the "Hören" admin tab to drive
# per-Aufgabe audio upload/replace/preview)
# ============================================================


@router.get("/hoeren-content", response_model=list[VizuMultilevelTaskAdmin])
def get_hoeren_content(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return content_service.list_tasks(db, "hoeren")


@router.post("/hoeren-content/import-csv")
async def import_hoeren_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    """CSV import for VIZU-Multilevel's own Hören Aufgabe/question/option
    content (see services/vizu_multilevel/hoeren_csv_import_service.py) —
    entirely independent of the regular course lesson's Quiz system.
    Safe to re-run: matches existing tasks/questions/options by their
    natural key and updates them in place instead of duplicating."""
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded.")

    try:
        return hoeren_csv_import_service.import_csv_text(db, text)
    except hoeren_csv_import_service.CsvImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ============================================================
# Hören Audio management
# ============================================================


@router.get("/audio", response_model=list[VizuMultilevelAudioResponse])
def list_audio(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return service.list_audio(db)


@router.post("/audio", response_model=VizuMultilevelAudioResponse, status_code=201)
def create_audio(
    data: VizuMultilevelAudioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return service.create_audio(db, data)


@router.put("/audio/{audio_id}", response_model=VizuMultilevelAudioResponse)
def update_audio(
    audio_id: UUID,
    data: VizuMultilevelAudioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    audio = service.update_audio(db, audio_id, data)
    if audio is None:
        raise HTTPException(status_code=404, detail="Audio not found.")
    return audio


@router.delete("/audio/{audio_id}", status_code=204)
def delete_audio(
    audio_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    if not service.delete_audio(db, audio_id):
        raise HTTPException(status_code=404, detail="Audio not found.")


# ============================================================
# Schreiben — full Aufgabe management (topic/instruction/word limits/
# image/points/rubric/order/status), unlike Lesen/Hören's read-only
# preview — this module explicitly asked for a real admin editor.
# ============================================================


@router.get("/schreiben-content", response_model=list[VizuMultilevelWritingTaskAdminResponse])
def list_schreiben_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return writing_service.list_tasks(db)


@router.post("/schreiben-content", response_model=VizuMultilevelWritingTaskAdminResponse, status_code=201)
def create_schreiben_task(
    data: VizuMultilevelWritingTaskAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return writing_service.create_task(db, data)


@router.put("/schreiben-content/{task_id}", response_model=VizuMultilevelWritingTaskAdminResponse)
def update_schreiben_task(
    task_id: UUID,
    data: VizuMultilevelWritingTaskAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    task = writing_service.update_task(db, task_id, data)
    if task is None:
        raise HTTPException(status_code=404, detail="Aufgabe not found.")
    return task


@router.delete("/schreiben-content/{task_id}", status_code=204)
def delete_schreiben_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    if not writing_service.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Aufgabe not found.")


# ============================================================
# Lesen / Hören content authoring (Aufgabe + questions + options)
# ============================================================


def _skill_or_404(skill: str) -> str:
    if skill not in content_service.CONTENT_SKILLS:
        raise HTTPException(status_code=404, detail="Unknown skill.")
    return skill


@router.post("/content/{skill}/tasks", response_model=VizuMultilevelTaskAdmin, status_code=201)
def create_content_task(
    skill: str,
    data: VizuMultilevelTaskAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    try:
        return content_service.create_task(db, _skill_or_404(skill), data)
    except ContentConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put("/content/tasks/{task_id}", response_model=VizuMultilevelTaskAdmin)
def update_content_task(
    task_id: UUID,
    data: VizuMultilevelTaskAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    try:
        task = content_service.update_task(db, task_id, data)
    except ContentConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if task is None:
        raise HTTPException(status_code=404, detail="Aufgabe not found.")
    return task


@router.delete("/content/tasks/{task_id}", status_code=204)
def delete_content_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    if not content_service.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Aufgabe not found.")


@router.post("/content/tasks/{task_id}/questions", response_model=VizuMultilevelTaskAdmin, status_code=201)
def create_content_question(
    task_id: UUID,
    data: VizuMultilevelQuestionInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    try:
        task = content_service.create_question(db, task_id, data)
    except ContentConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if task is None:
        raise HTTPException(status_code=404, detail="Aufgabe not found.")
    return task


@router.put("/content/questions/{question_id}", response_model=VizuMultilevelTaskAdmin)
def update_content_question(
    question_id: UUID,
    data: VizuMultilevelQuestionInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    try:
        task = content_service.update_question(db, question_id, data)
    except ContentConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if task is None:
        raise HTTPException(status_code=404, detail="Question not found.")
    return task


@router.delete("/content/questions/{question_id}", response_model=VizuMultilevelTaskAdmin)
def delete_content_question(
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    task = content_service.delete_question(db, question_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Question not found.")
    return task


# ============================================================
# Sprechen content authoring
# ============================================================


@router.get("/sprechen-content", response_model=list[VizuMultilevelSpeakingTaskAdminResponse])
def list_sprechen_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return speaking_service.list_tasks(db)


@router.post("/sprechen-content", response_model=VizuMultilevelSpeakingTaskAdminResponse, status_code=201)
def create_sprechen_task(
    data: VizuMultilevelSpeakingTaskAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    try:
        return speaking_service.create_task(db, data)
    except ContentConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put("/sprechen-content/{task_id}", response_model=VizuMultilevelSpeakingTaskAdminResponse)
def update_sprechen_task(
    task_id: UUID,
    data: VizuMultilevelSpeakingTaskAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    try:
        task = speaking_service.update_task(db, task_id, data)
    except ContentConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if task is None:
        raise HTTPException(status_code=404, detail="Aufgabe not found.")
    return task


@router.delete("/sprechen-content/{task_id}", status_code=204)
def delete_sprechen_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    if not speaking_service.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Aufgabe not found.")
