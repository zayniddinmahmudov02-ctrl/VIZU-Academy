from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db
from app.models.user import User
from app.schemas.vizu_mock import (
    VizuMockActivityStats,
    VizuMockAdminAttemptItem,
    VizuMockAdminAttemptsPage,
    VizuMockAnalytics,
    VizuMockAudioCreate,
    VizuMockAudioResponse,
    VizuMockAudioUpdate,
    VizuMockHoerenTaskPublic,
    VizuMockLevelAnalytics,
    VizuMockOverviewStats,
    VizuMockTaskPublic,
    VizuMockWritingTaskAdminCreate,
    VizuMockWritingTaskAdminResponse,
    VizuMockWritingTaskAdminUpdate,
)
from app.services.admin import vizu_mock_admin_service as service
from app.services.admin import vizu_mock_writing_admin_service as writing_service
from app.services.vizu_mock import hoeren_service, lesen_service

router = APIRouter(prefix="/admin/vizu-mock", tags=["Admin - VIZU-Mock"])


# ============================================================
# Overview / Analytics
# ============================================================


@router.get("/overview", response_model=VizuMockOverviewStats)
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return service.get_overview(db)


@router.get("/activity", response_model=VizuMockActivityStats)
def get_activity(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return service.get_activity(db, days)


@router.get("/level-analytics", response_model=VizuMockLevelAnalytics)
def get_level_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return service.get_level_analytics(db)


@router.get("/analytics", response_model=VizuMockAnalytics)
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return service.get_analytics(db)


# ============================================================
# Oxirgi testlar / Natijalar
# ============================================================


@router.get("/attempts", response_model=VizuMockAdminAttemptsPage)
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


@router.get("/attempts/{attempt_id}", response_model=VizuMockAdminAttemptItem)
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
# Lesen — read-only view of the already-seeded content (no generator/
# editor here, per the current phase's explicit scope)
# ============================================================


@router.get("/lesen-content", response_model=list[VizuMockTaskPublic])
def get_lesen_content(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return lesen_service.list_lesen_tasks(db)


# ============================================================
# Hören — read-only view of the already-seeded content, including each
# Aufgabe's attached audio (used by the "Hören" admin tab to drive
# per-Aufgabe audio upload/replace/preview)
# ============================================================


@router.get("/hoeren-content", response_model=list[VizuMockHoerenTaskPublic])
def get_hoeren_content(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return hoeren_service.list_hoeren_tasks(db)


# ============================================================
# Hören Audio management
# ============================================================


@router.get("/audio", response_model=list[VizuMockAudioResponse])
def list_audio(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return service.list_audio(db)


@router.post("/audio", response_model=VizuMockAudioResponse, status_code=201)
def create_audio(
    data: VizuMockAudioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return service.create_audio(db, data)


@router.put("/audio/{audio_id}", response_model=VizuMockAudioResponse)
def update_audio(
    audio_id: UUID,
    data: VizuMockAudioUpdate,
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


@router.get("/schreiben-content", response_model=list[VizuMockWritingTaskAdminResponse])
def list_schreiben_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return writing_service.list_tasks(db)


@router.post("/schreiben-content", response_model=VizuMockWritingTaskAdminResponse, status_code=201)
def create_schreiben_task(
    data: VizuMockWritingTaskAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    return writing_service.create_task(db, data)


@router.put("/schreiben-content/{task_id}", response_model=VizuMockWritingTaskAdminResponse)
def update_schreiben_task(
    task_id: UUID,
    data: VizuMockWritingTaskAdminUpdate,
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
