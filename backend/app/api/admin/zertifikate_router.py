"""Admin -> Zertifikate: every student's certificates in one table (course
certificates + VIZU-Multilevel), filters, pagination, PDF. Read-only — issuing
/ revoking stays on the existing /certificates endpoints."""

from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin_panel_access
from app.db.session import get_db
from app.models.user import User
from app.services.certificate import registry
from app.services.certificate.pdf_access import certificate_pdf

router = APIRouter(prefix="/admin/zertifikate", tags=["Admin - Zertifikate"])


@router.get("")
def list_certificates(
    q: str | None = Query(default=None, max_length=200),
    level: Literal["BELOW_A1", "A1", "A2", "B1", "B2", "C1"] | None = None,
    source: Literal["COURSE", "VORBEREITUNG", "VIZU_MULTILEVEL"] | None = None,
    status: Literal["valid", "revoked", "issued", "available"] | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    user_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_panel_access),
):
    return registry.admin_list(db, page=page, page_size=page_size, user_id=user_id, q=q, level=level, source=source, status=status,
                               date_from=date_from, date_to=date_to)


@router.get("/{item_id}/pdf")
def certificate_pdf_admin(item_id: str, db: Session = Depends(get_db), _: User = Depends(require_admin_panel_access)):
    return certificate_pdf(db, item_id, owner=None)
