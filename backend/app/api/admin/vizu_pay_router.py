from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import AuditLogResponse
from app.schemas.vizu_pay import (
    AdminOrderItem,
    AdminOrderListResponse,
    BlockedUserItem,
    CourseRequestReview,
    ExtendOrderAccessRequest,
    OrderNoteRequest,
    PackageWrite,
    PaymentSettingsUpdate,
    PromoReviewRequest,
    PromoCodeCreateRequest,
    PromoCodeItem,
    PromoCodeReviewRequest,
    PromoCodeUpdateRequest,
    RefundOrderRequest,
    RejectOrderRequest,
    RevenueOverview,
)
from app.services.vizu_pay import AdminVizuPayService
from app.services.vizu_pay import multilevel_premium

router = APIRouter(
    prefix="/admin/vizu-pay",
    tags=["Admin - VIZU Pay"],
)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


# ----------------------------------------------------------------------
# Angebote configuration: prices, sale on / off, package contents, free
# lessons per course, level availability ("Tez orada"). Stored as admin
# overrides of the code defaults (app/services/vizu_pay/offers.py); takes
# effect at once — no deploy, no code change.
# ----------------------------------------------------------------------


@router.get("/angebote-config")
def get_angebote_config(db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    from app.services.vizu_pay import offers as offer_config

    eff = offer_config.effective()
    return {
        "offers": offer_config.list_offers(),
        "levels": eff["levels"],
        # sales approval per level (separate from "available" and from the course's active flag)
        "sales": eff["sales"],
        "free_lessons": eff["free_lessons"],
        "defaults": {
            "levels": offer_config.LEVEL_AVAILABLE_DEFAULT,
            "sales": offer_config.LEVEL_SALES_DEFAULT,
            "free_lessons": offer_config.FREE_LESSONS_PER_COURSE,
        },
    }


@router.put("/angebote-config")
def put_angebote_config(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Replaces the level settings with `payload` ({levels: {B2: true}, sales: {A2: true}, free_lessons: 1}).
    Prices, durations, status and contents are package fields (PUT /admin/vizu-pay/packages/{code}). Releasing a
    level opens it at once for every buyer of a package that contains it — no new payment."""
    import json

    from fastapi import HTTPException
    from sqlalchemy import select

    from app.core.audit import write_audit
    from app.models.app_setting import AppSetting
    from app.services.vizu_pay import offers as offer_config

    try:
        clean = offer_config.validate_overrides(payload or {})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"INVALID_ANGEBOTE_CONFIG: {exc}") from None
    row = db.scalar(select(AppSetting).where(AppSetting.key == offer_config.SETTINGS_KEY))
    before = dict(row.value) if row else {}
    if row is None:
        row = AppSetting(key=offer_config.SETTINGS_KEY, value=clean, updated_by=current_user.id)
        db.add(row)
    else:
        row.value = clean
        row.updated_by = current_user.id
    db.commit()
    offer_config.invalidate_cache()
    write_audit(db, str(current_user.id), "angebote_config_updated",
                details=json.dumps({"before": before, "after": clean}, ensure_ascii=False)[:4000], ip_address=_client_ip(request))
    return get_angebote_config(db, current_user)


# ----------------------------------------------------------------------
# Course packages (table course_packages; rules in services/vizu_pay/packages.py). No delete: set DISABLED.
# ----------------------------------------------------------------------


@router.get("/packages")
def list_packages(db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    from app.services.vizu_pay import packages

    return packages.list_packages(db)


@router.post("/packages")
def create_package(data: PackageWrite, request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    from app.services.vizu_pay import packages

    return packages.create_package(db, current_user, data.model_dump(exclude_unset=True), _client_ip(request))


@router.put("/packages/{code}")
def update_package(code: str, data: PackageWrite, request: Request, db: Session = Depends(get_db),
                   current_user: User = Depends(require_super_admin)):
    from app.services.vizu_pay import packages

    payload = data.model_dump(exclude_unset=True)
    payload.pop("code", None)  # the code of a package never changes (orders store it)
    return packages.update_package(db, current_user, code, payload, _client_ip(request))


# ----------------------------------------------------------------------
# Promo codes that need approval, discount statistics
# ----------------------------------------------------------------------


@router.get("/promo-requests")
def list_promo_requests(
    status: str | None = Query(None, pattern="^(PENDING_APPROVAL|APPROVED|REJECTED|USED)$"),
    promo_id: str | None = None,
    search: str | None = None,
    plan: str | None = None,
    kind: str | None = Query(None, pattern="^(CODE_APPROVAL|COURSE_REQUEST)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminVizuPayService(db).list_promo_requests(status, promo_id, search, plan, page, page_size, kind=kind)


@router.post("/promo-requests/{request_id}/course-review")
def review_course_promo_request(request_id: str, data: CourseRequestReview, request: Request, db: Session = Depends(get_db),
                                current_user: User = Depends(require_super_admin)):
    """"Promo so'rovi": reject, or approve with a new personal code (mode create) / an existing approved code (mode attach)."""
    return AdminVizuPayService(db).review_course_request(
        request_id, data.approve, data.reason, current_user, _client_ip(request), mode=data.mode, discount_type=data.discount_type,
        discount_value=data.discount_value, expires_at=data.expires_at, promo_code_id=data.promo_code_id)


# ----------------------------------------------------------------------
# Overview, payment settings, Multilevel Premium holders
# ----------------------------------------------------------------------


@router.get("/overview")
def payments_overview(db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    return AdminVizuPayService(db).payments_overview()


@router.get("/payment-settings")
def get_payment_settings(db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    from app.services.vizu_pay import plans as plan_config

    return {"cards": plan_config.PAYMENT_CARDS, "multilevel": multilevel_premium.product(db),
            "review_window_days": plan_config.ORDER_REVIEW_WINDOW_DAYS, "max_rejections": plan_config.MAX_REJECTIONS}


@router.put("/payment-settings")
def put_payment_settings(data: PaymentSettingsUpdate, request: Request, db: Session = Depends(get_db),
                         current_user: User = Depends(require_super_admin)):
    multilevel_premium.update_settings(db, current_user, {"price": data.multilevel_price, "status": data.multilevel_status}, _client_ip(request))
    return get_payment_settings(db, current_user)


@router.get("/multilevel-entitlements")
def list_multilevel_entitlements(search: str | None = None, include_revoked: bool = False, db: Session = Depends(get_db),
                                 current_user: User = Depends(require_super_admin)):
    return multilevel_premium.list_entitlements(db, search, include_revoked)


@router.post("/promo-requests/{request_id}/review")
def review_promo_request(request_id: str, data: PromoReviewRequest, request: Request, db: Session = Depends(get_db),
                         current_user: User = Depends(require_super_admin)):
    return AdminVizuPayService(db).review_promo_request(request_id, data.approve, data.reason, current_user, _client_ip(request))


@router.get("/discount-statistics")
def discount_statistics(db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    return AdminVizuPayService(db).discount_statistics()


@router.get("/orders", response_model=AdminOrderListResponse)
def list_orders(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    plan: str | None = None,
    search: str | None = None,
    user_id: str | None = None,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
    kind: str | None = Query(None, pattern="^(course|multilevel)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminVizuPayService(db).list_orders(
        kind=kind,
        page=page,
        page_size=page_size,
        status=status,
        plan=plan,
        search=search,
        user_id=user_id,
        year=year,
        month=month,
        day=day,
    )


@router.get("/blocked-users", response_model=list[BlockedUserItem])
def list_blocked_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Users with >= MAX_REJECTIONS rejected payment requests — see
    AdminVizuPayService.list_blocked_users. A separate endpoint rather
    than a status filter on /orders because this is grouped by user, not
    a flat list of orders."""
    return AdminVizuPayService(db).list_blocked_users()


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


@router.patch("/orders/{order_id}/note", response_model=AdminOrderItem)
def set_order_note(
    order_id: str,
    data: OrderNoteRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminVizuPayService(db).set_order_note(order_id, data.note, current_user, _client_ip(request))


@router.post("/orders/{order_id}/extend", response_model=AdminOrderItem)
def extend_order_access(
    order_id: str,
    data: ExtendOrderAccessRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminVizuPayService(db).extend_order_access(
        order_id, data.months, data.reason, current_user, _client_ip(request)
    )


@router.get("/promo-codes", response_model=list[PromoCodeItem])
def list_promo_codes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminVizuPayService(db).list_promos()


@router.get("/promo-codes/{promo_id}/orders")
def list_promo_code_orders(
    promo_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    plan: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminVizuPayService(db).list_promo_orders(promo_id, page, page_size, search=search, plan=plan)


@router.get("/promo-products")
def list_promo_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return AdminVizuPayService(db).promo_products()


@router.post("/promo-codes/{promo_id}/review", response_model=PromoCodeItem)
def review_promo_code(
    promo_id: str,
    data: PromoCodeReviewRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """The approval step every promo code needs before it works (approve / approve_activate / activate / reject / disable)."""
    return AdminVizuPayService(db).review_promo(promo_id, data.action, data.note, current_user, _client_ip(request))


@router.post("/promo-codes", response_model=PromoCodeItem)
def create_promo_code(
    data: PromoCodeCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Creates the code as PENDING — it does not work until approved and activated."""
    return AdminVizuPayService(db).create_promo(
        code=data.code,
        campaign=data.campaign,
        discount_type=data.discount_type,
        discount_value=data.discount_value,
        applicable_course_ids=data.applicable_course_ids,
        applicable_package_codes=data.applicable_package_codes,
        starts_at=data.starts_at,
        max_uses=data.max_uses,
        max_uses_per_user=data.max_uses_per_user,
        expires_at=data.expires_at,
        is_active=data.is_active,
        requires_approval=data.requires_approval,
        product_category=data.product_category,
        actor=current_user,
        ip=_client_ip(request),
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
        changes=data.model_dump(exclude_unset=True),
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
