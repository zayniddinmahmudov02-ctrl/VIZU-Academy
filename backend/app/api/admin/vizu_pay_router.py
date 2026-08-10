from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import AuditLogResponse
from app.schemas.vizu_pay import (
    AdminOrderItem,
    AdminOrderListResponse,
    PromoCodeCreateRequest,
    PromoCodeItem,
    PromoCodeUpdateRequest,
    RefundOrderRequest,
    RejectOrderRequest,
    RevenueOverview,
)
from app.services.vizu_pay import AdminVizuPayService

router = APIRouter(
    prefix="/admin/vizu-pay",
    tags=["Admin - VIZU Pay"],
)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/orders", response_model=AdminOrderListResponse)
def list_orders(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    plan: str | None = None,
    search: str | None = None,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminVizuPayService(db).list_orders(
        page=page,
        page_size=page_size,
        status=status,
        plan=plan,
        search=search,
        year=year,
        month=month,
        day=day,
    )


@router.post("/orders/{order_id}/approve", response_model=AdminOrderItem)
def approve_order(
    order_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminVizuPayService(db).approve_order(order_id, current_user, _client_ip(request))


@router.post("/orders/{order_id}/reject", response_model=AdminOrderItem)
def reject_order(
    order_id: str,
    data: RejectOrderRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminVizuPayService(db).reject_order(order_id, data.reason, current_user, _client_ip(request))


@router.post("/orders/{order_id}/refund", response_model=AdminOrderItem)
def refund_order(
    order_id: str,
    data: RefundOrderRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminVizuPayService(db).refund_order(order_id, data.reason, current_user, _client_ip(request))


@router.get("/promo-codes", response_model=list[PromoCodeItem])
def list_promo_codes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminVizuPayService(db).list_promos()


@router.post("/promo-codes", response_model=PromoCodeItem)
def create_promo_code(
    data: PromoCodeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminVizuPayService(db).create_promo(
        code=data.code,
        campaign=data.campaign,
        discount_type=data.discount_type,
        discount_value=data.discount_value,
        max_uses=data.max_uses,
        expires_at=data.expires_at,
        actor=current_user,
    )


@router.patch("/promo-codes/{promo_id}", response_model=PromoCodeItem)
def update_promo_code(
    promo_id: str,
    data: PromoCodeUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminVizuPayService(db).update_promo(
        promo_id,
        campaign=data.campaign,
        is_active=data.is_active,
        expires_at=data.expires_at,
        actor=current_user,
    )


@router.delete("/promo-codes/{promo_id}")
def delete_promo_code(
    promo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    AdminVizuPayService(db).delete_promo(promo_id, current_user)
    return {"success": True}


@router.get("/revenue", response_model=RevenueOverview)
def revenue_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminVizuPayService(db).revenue_overview()


@router.get("/logs", response_model=AuditLogResponse)
def payment_logs(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminVizuPayService(db).get_payment_logs(page=page, page_size=page_size)
