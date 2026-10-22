from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies.auth import require_super_admin
from app.db.session import get_db
from app.models.managed_page import ManagedPageAudit
from app.models.user import User
from app.services.page_management import (
    PAGE_BY_ID,
    list_pages,
    navigation_state,
    page_state,
    save_page_action,
)

router = APIRouter(prefix="/admin/page-management", tags=["Admin - Page Management"])


class PageFlagRequest(BaseModel):
    enabled: bool
    reason: str | None = Field(default=None, max_length=500)


class PageActionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


def _page_or_404(page_id: str):
    page = PAGE_BY_ID.get(page_id)
    if page is None:
        raise HTTPException(status_code=404, detail="Managed page not found.")
    return page


def _save(
    page_id: str,
    action: Literal["navigation", "visibility", "archive", "restore"],
    db: Session,
    user: User,
    *,
    enabled: bool | None = None,
    reason: str | None = None,
):
    page = _page_or_404(page_id)
    try:
        control = save_page_action(db, page, user, action, enabled=enabled, reason=reason)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"page_id": page.page_id, "route": page.route, **page_state(page, control)}


@router.get("/navigation")
def get_navigation_state(
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    return navigation_state(db)


@router.get("/pages")
def get_pages(
    q: str | None = Query(default=None, max_length=120),
    module: str | None = Query(default=None, max_length=80),
    status: Literal["active", "removed", "hidden", "archived"] | None = None,
    route: str | None = Query(default=None, max_length=255),
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    pages = list_pages(db)
    if q:
        needle = q.strip().casefold()
        pages = [
            page for page in pages
            if needle in page["name"].casefold()
            or needle in page["route"].casefold()
            or needle in page["module"].casefold()
        ]
    if module:
        pages = [page for page in pages if page["module"] == module]
    if status:
        pages = [page for page in pages if page["status"] == status]
    if route:
        needle = route.strip().casefold()
        pages = [page for page in pages if needle in page["route"].casefold()]
    return pages


@router.get("/pages/{page_id}")
def get_page_details(
    page_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    page = _page_or_404(page_id)
    return next(item for item in list_pages(db) if item["page_id"] == page.page_id)


@router.get("/pages/{page_id}/history")
def get_page_history(
    page_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    page = _page_or_404(page_id)
    rows = db.scalars(
        select(ManagedPageAudit)
        .where(ManagedPageAudit.route == page.route)
        .options(joinedload(ManagedPageAudit.actor))
        .order_by(ManagedPageAudit.created_at.desc())
        .limit(100)
    ).all()
    return [
        {
            "id": str(row.id),
            "route": row.route,
            "action": row.action,
            "previous_state": row.previous_state,
            "new_state": row.new_state,
            "reason": row.reason,
            "actor": {"id": str(row.actor.id), "name": row.actor.username} if row.actor else None,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.patch("/pages/{page_id}/navigation")
def set_page_navigation(
    page_id: str,
    data: PageFlagRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_super_admin),
):
    return _save(page_id, "navigation", db, user, enabled=data.enabled, reason=data.reason)


@router.patch("/pages/{page_id}/visibility")
def set_page_visibility(
    page_id: str,
    data: PageFlagRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_super_admin),
):
    return _save(page_id, "visibility", db, user, enabled=data.enabled, reason=data.reason)


@router.post("/pages/{page_id}/archive")
def archive_page(
    page_id: str,
    data: PageActionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_super_admin),
):
    return _save(page_id, "archive", db, user, reason=data.reason)


@router.post("/pages/{page_id}/restore")
def restore_page(
    page_id: str,
    data: PageActionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_super_admin),
):
    return _save(page_id, "restore", db, user, reason=data.reason)
