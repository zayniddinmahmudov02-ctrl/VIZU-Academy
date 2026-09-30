from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db
from app.models.user import User
from app.services.quiz import csv_import_service

router = APIRouter(prefix="/admin/quiz", tags=["Admin - Quiz"])


@router.post("/import-csv")
async def import_quiz_csv(
    lesson_id: UUID = Form(...),
    quiz_type: str = Form(...),
    quiz_title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_panel_access),
):
    """Admin-only CSV import for the legacy Quiz system (currently used
    for HOEREN quizzes — see services/quiz/csv_import_service.py). Safe
    to re-run: matches existing questions/options by their natural key
    and updates them in place instead of duplicating."""
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded.")

    try:
        return csv_import_service.import_csv_text(db, lesson_id, quiz_type, quiz_title, text)
    except csv_import_service.CsvImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
