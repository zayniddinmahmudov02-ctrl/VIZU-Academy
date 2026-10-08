from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.security.roles import UserRole
from app.db.session import get_db
from app.models.user import User
from app.schemas.advertisement import (
    AdvertisementAdmin,
    AdvertisementAnalytics,
    AdvertisementCreate,
    AdvertisementPublic,
    AdvertisementUpdate,
    ImpressionResult,
)
from app.services import advertisement_service as service

# ============================================================
# Student-facing (dashboard)
# ============================================================

router = APIRouter(prefix="/advertisements", tags=["Advertisements"])


@router.get("/active", response_model=AdvertisementPublic | None)
def get_active_advertisement(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The one advertisement currently eligible for the dashboard (active,
    inside its date range, highest priority) — or null. No analytics and no
    destination URL: the banner links to the click-tracking redirect."""
    ad = service.get_current(db)
    return service.to_public(ad) if ad else None


@router.get("/active-list", response_model=list[AdvertisementPublic])
def list_active_advertisements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """All advertisements currently eligible for the dashboard carousel, in
    display order (priority first). Same public fields as /active — no
    analytics, no destination URL. /active is unchanged (= the first one)."""
    return [service.to_public(ad) for ad in service.list_current(db)]


@router.post("/{advertisement_id}/impression", response_model=ImpressionResult)
def track_impression(
    advertisement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Called once a banner is actually visible (IntersectionObserver).
    Counted at most once per user per 30 minutes, and only for an ad that is
    currently eligible (active and inside its date range)."""
    ad = service.get(db, advertisement_id)
    if ad is None:
        raise HTTPException(status_code=404, detail="Advertisement not found.")
    return {"counted": service.record_impression(db, ad, current_user.id)}


@router.get("/{advertisement_id}/click")
def track_click_and_redirect(
    advertisement_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
):
    """Registers the click, then redirects (302) to the admin-configured,
    validated destination. Only for an advertisement that is currently
    eligible — an expired/inactive one is a 404, never a redirect."""
    ad = service.get(db, advertisement_id)
    if ad is None or not service.is_eligible(ad):
        raise HTTPException(status_code=404, detail="Advertisement not found.")
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() or (request.client.host if request.client else "")
    service.record_click(db, ad, service.client_hash(ip, request.headers.get("user-agent")))
    return RedirectResponse(url=ad.target_url, status_code=302, headers={"Cache-Control": "no-store"})


# ============================================================
# Admin — Werbung-Banner management + analytics
# ============================================================

# Advertisements are shown to every student, so only the roles that manage
# site content may see or change them — not TEACHER / SUPPORT / PAYMENT_MANAGER,
# even though those can open other parts of the admin panel.
ADVERTISEMENT_MANAGER_ROLES = {UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CONTENT_MANAGER}


def require_advertisement_manager(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ADVERTISEMENT_MANAGER_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Advertisement management access required")
    return current_user


admin_router = APIRouter(prefix="/admin/advertisements", tags=["Admin - Werbung-Banner"])


@admin_router.get("", response_model=list[AdvertisementAdmin])
def list_advertisements(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_advertisement_manager),
):
    return service.list_admin(db)


@admin_router.post("", response_model=AdvertisementAdmin, status_code=201)
def create_advertisement(
    data: AdvertisementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_advertisement_manager),
):
    return service.create(db, data)


@admin_router.get("/{advertisement_id}", response_model=AdvertisementAdmin)
def get_advertisement(
    advertisement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_advertisement_manager),
):
    ad = service.get_admin(db, advertisement_id)
    if ad is None:
        raise HTTPException(status_code=404, detail="Advertisement not found.")
    return ad


@admin_router.put("/{advertisement_id}", response_model=AdvertisementAdmin)
def update_advertisement(
    advertisement_id: UUID,
    data: AdvertisementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_advertisement_manager),
):
    try:
        ad = service.update(db, advertisement_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if ad is None:
        raise HTTPException(status_code=404, detail="Advertisement not found.")
    return ad


@admin_router.post("/{advertisement_id}/activate", response_model=AdvertisementAdmin)
def activate_advertisement(
    advertisement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_advertisement_manager),
):
    ad = service.update(db, advertisement_id, AdvertisementUpdate(is_active=True))
    if ad is None:
        raise HTTPException(status_code=404, detail="Advertisement not found.")
    return ad


@admin_router.post("/{advertisement_id}/deactivate", response_model=AdvertisementAdmin)
def deactivate_advertisement(
    advertisement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_advertisement_manager),
):
    ad = service.update(db, advertisement_id, AdvertisementUpdate(is_active=False))
    if ad is None:
        raise HTTPException(status_code=404, detail="Advertisement not found.")
    return ad


@admin_router.delete("/{advertisement_id}", status_code=204)
def delete_advertisement(
    advertisement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_advertisement_manager),
):
    if not service.delete(db, advertisement_id):
        raise HTTPException(status_code=404, detail="Advertisement not found.")


@admin_router.get("/{advertisement_id}/analytics", response_model=AdvertisementAnalytics)
def advertisement_analytics(
    advertisement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_advertisement_manager),
):
    result = service.analytics(db, advertisement_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Advertisement not found.")
    return result
