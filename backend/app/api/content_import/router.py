"""Admin: Claude/JSON content import for every level A1-C1.

JSON -> POST /validate (preview, nothing written) -> POST /commit (valid items
created UNPUBLISHED, batch recorded) -> admin review -> POST /batches/{id}/publish.
Admin-panel roles only (backend-enforced)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db
from app.models.content_import import ContentImport
from app.models.user import User
from app.services.content_import import claude_client, guide
from app.services.content_import import service as importer
from app.services.content_import.schema import json_schema
from app.services.lesson_skills import levels

router = APIRouter(prefix="/admin/content-import", tags=["Admin - Content import"])

MAX_DOCUMENT_ITEMS = importer.MAX_ITEMS


class ImportRequest(BaseModel):
    document: dict
    filename: str | None = Field(default=None, max_length=255)
    create_missing: bool = False
    # re-import: content that already exists (same content_id, or same title
    # in the lesson) is skipped instead of reported as an error
    skip_existing: bool = False


class GenerateRequest(BaseModel):
    level: str = Field(pattern=r"^(A1|A2|B1|B2|C1)$")
    module: int = Field(ge=1, le=100)
    lesson: int = Field(ge=1, le=500)
    topic: str = Field(min_length=1, max_length=300)
    skills: list[str] = Field(min_length=1, max_length=4)
    notes: str | None = Field(default=None, max_length=2000)


def _check_size(document: dict) -> None:
    items = document.get("items") if isinstance(document, dict) else None
    if isinstance(items, list) and len(items) > MAX_DOCUMENT_ITEMS:
        raise HTTPException(status_code=413, detail=f"Max {MAX_DOCUMENT_ITEMS} items per import.")


@router.get("/schema")
def get_schema(_: User = Depends(require_admin_panel_access)):
    """The official JSON Schema of the import format."""
    return json_schema()


@router.get("/guide")
def get_guide(level: str = Query("A1", pattern=r"^(A1|A2|B1|B2|C1)$"), _: User = Depends(require_admin_panel_access)):
    """Claude generation instructions, checklist, ranges and an example for one level."""
    return guide.guide(level)


@router.get("/status")
def get_status(_: User = Depends(require_admin_panel_access)):
    return {**claude_client.status(), "levels": levels.LEVELS, "schema_version": importer.SCHEMA_VERSION}


@router.post("/validate")
def validate(data: ImportRequest, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """Validation + preview. Writes nothing."""
    _check_size(data.document)
    return importer.public_report(importer.validate_document(db, data.document, data.create_missing, data.skip_existing))


@router.post("/commit")
def commit(data: ImportRequest, db: Session = Depends(get_db), actor: User = Depends(require_admin_panel_access)):
    """Creates every VALID item as unpublished content; invalid items are
    listed with their errors. Nothing is published here."""
    _check_size(data.document)
    batch = importer.commit_document(db, data.document, actor, data.filename, data.create_missing, data.skip_existing)
    return importer.batch_summary(batch, with_items=True)


@router.post("/generate")
def generate(data: GenerateRequest, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """Claude draft (only if ANTHROPIC_API_KEY is set) -> returned together
    with its validation report. Nothing is stored."""
    skills = [s for s in data.skills if s in importer.SKILLS]
    if not skills:
        raise HTTPException(status_code=422, detail="Unknown skills.")
    document = claude_client.generate_document(data.level, data.module, data.lesson, data.topic, skills, data.notes)
    _check_size(document)
    return {"document": document, "report": importer.public_report(importer.validate_document(db, document, False))}


@router.get("/batches")
def list_batches(db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    rows = db.scalars(select(ContentImport).order_by(ContentImport.created_at.desc()).limit(50))
    return [importer.batch_summary(b) for b in rows]


@router.get("/batches/{batch_id}")
def get_batch(batch_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    batch = db.get(ContentImport, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Import not found.")
    return importer.batch_summary(batch, with_items=True)


@router.post("/batches/{batch_id}/publish")
def publish(batch_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    """Publishes what the batch created; Hören tasks without uploaded audio stay hidden."""
    return importer.batch_summary(importer.publish_batch(db, batch_id), with_items=True)
