"""Admin: A1 Hören — answer keys from the VIZU answer-sheet PDF and
automatic publishing (app/services/lesson_skills/hoeren_pdf_import.py).

Preview and apply both read the uploaded PDF on the server (the plan is never
taken from the client); apply writes only new answers plus the review items
the admin accepted, then publishes the A1 tasks that are complete."""

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access, require_content_editor
from app.core.audit import write_audit
from app.db.session import get_db
from app.models.user import User
from app.services.lesson_skills import hoeren_pdf_import as importer

router = APIRouter(prefix="/admin/hoeren-a1", tags=["Admin - A1 Hören"])


async def _plan(db: Session, file: UploadFile):
    data = await file.read(importer.MAX_PDF_BYTES + 1)
    try:
        text = importer.pdf_text(data)
    except importer.PdfImportError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from None
    return importer.build_plan(db, text)


@router.get("/status")
def a1_status(db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """Every A1 Hören task: lesson, audio state, questions, missing keys,
    published, and why it is not published yet."""
    return importer.a1_status(db)


@router.post("/answers-pdf/preview")
async def preview(file: UploadFile = File(...), db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    plans = await _plan(db, file)
    db.rollback()
    return {"summary": importer.summary(plans), "lessons": importer.plan_json(plans)}


@router.post("/answers-pdf/apply")
async def apply(
    request: Request,
    file: UploadFile = File(...),
    accepted: str = Form("[]"),
    db: Session = Depends(get_db),
    user: User = Depends(require_content_editor),
):
    try:
        accepted_ids = {str(x) for x in json.loads(accepted or "[]")}
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="accepted: JSON list of slot ids") from None
    plans = await _plan(db, file)
    result = importer.apply_plan(db, plans, accepted_ids)
    published = importer.publish_ready(db, result["listening_ids"]) if result["listening_ids"] else []
    write_audit(db, str(user.id), "a1_hoeren_pdf_import", details=json.dumps(
        {"file": file.filename, "written": result["written"], "review_skipped": result["review_skipped"], "accepted": len(accepted_ids),
         "published": [p["listening_id"] for p in published if p["result"] == "published"]}, ensure_ascii=False)[:4000],
        ip_address=request.client.host if request.client else None)
    after = await _replan(db, file)
    return {"written": result["written"], "review_skipped": result["review_skipped"], "publish": published,
            "summary_after": importer.summary(after), "lessons_after": importer.plan_json(after)}


async def _replan(db: Session, file: UploadFile):
    await file.seek(0)
    return await _plan(db, file)


@router.post("/publish-ready")
def publish_ready(request: Request, db: Session = Depends(get_db), user: User = Depends(require_content_editor)):
    """Publishes every A1 Hören task whose audio file exists and whose answer
    keys are complete; the others keep their status."""
    out = importer.publish_ready(db)
    newly = [p["listening_id"] for p in out if p["result"] == "published"]
    write_audit(db, str(user.id), "a1_hoeren_publish_ready", details=json.dumps({"published": newly})[:4000],
                ip_address=request.client.host if request.client else None)
    return out
