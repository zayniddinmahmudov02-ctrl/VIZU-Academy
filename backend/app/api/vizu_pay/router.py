from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.vizu_pay import (
    CourseRequestCreate,
    MultilevelRedeemRequest,
    MySubscriptionStatus,
    OfferItem,
    OrderItem,
    OrderListResponse,
    PaymentCardItem,
    PlanOption,
    PromoRedeemRequest,
    PromoRedeemResponse,
    PromoRequestCreate,
    PromoValidateResponse,
)
from app.services.vizu_pay import VizuPayService
from app.services.vizu_pay import multilevel_premium

router = APIRouter(
    prefix="/vizu-pay",
    tags=["VIZU Pay"],
)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/plans", response_model=list[PlanOption])
def list_plans(db: Session = Depends(get_db)):
    return VizuPayService(db).list_plans()


@router.get("/offers", response_model=list[OfferItem])
def list_offers(db: Session = Depends(get_db)):
    """Angebote: course prices (A1, A2, B1, B2, C1) and packages
    (A1 → B1, A1 → C1). Public, like /plans — prices are not secret."""
    return VizuPayService(db).list_offers()


@router.get("/quote")
def get_quote(
    plan: str,
    promo_code: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The caller's checkout price for one offer (sale price, promo, medal
    reward) — computed exactly like POST /orders, which recomputes it again."""
    return VizuPayService(db).quote(current_user, plan, promo_code)


@router.get("/payment-cards", response_model=list[PaymentCardItem])
def list_payment_cards(db: Session = Depends(get_db)):
    return VizuPayService(db).list_payment_cards()


@router.get("/status", response_model=MySubscriptionStatus)
def get_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return VizuPayService(db).get_my_status(current_user)


@router.get("/promo/validate", response_model=PromoValidateResponse)
def validate_promo(
    code: str,
    plan: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return VizuPayService(db).validate_promo(code, current_user, plan)


@router.post("/promo/requests")
def request_promo(
    data: PromoRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """A code that needs an admin's approval: creates (or returns) the student's request for this package.
    Codes without approval answer {"status": "NOT_REQUIRED"}."""
    return VizuPayService(db).request_promo(current_user, data.code, data.plan, _client_ip(request))


@router.get("/promo/requests")
def my_promo_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return VizuPayService(db).my_promo_requests(current_user)


@router.post("/promo/course-requests")
def create_course_promo_request(
    data: CourseRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """"Promo so'rovi": the student asks the admin for a promo for one course / package. Only a request — it opens nothing."""
    return VizuPayService(db).create_course_request(current_user, data.plan, data.message, _client_ip(request))


# ----------------------------------------------------------------------
# Multilevel Modelltest Premium (all 10 Modelltests, one purchase) — services/vizu_pay/multilevel_premium.py
# ----------------------------------------------------------------------


@router.get("/multilevel")
def multilevel_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Price (the server's), card, the caller's own access / pending request / last rejection."""
    return multilevel_premium.status(db, current_user)


@router.get("/multilevel/quote")
def multilevel_quote(promo_code: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return multilevel_premium.quote(db, current_user, promo_code)


@router.post("/multilevel/orders", response_model=OrderItem)
async def multilevel_create_order(
    request: Request,
    promo_code: str | None = Form(None),
    no_receipt: bool = Form(False),
    paid_date: str | None = Form(None),
    paid_time: str | None = Form(None),
    note: str | None = Form(None),
    proof: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manual card payment request (PENDING until the Super Admin approves). The amount is computed on the server — never sent."""
    return await multilevel_premium.create_order(db, current_user, promo_code=promo_code or None, no_receipt=no_receipt, paid_date=paid_date,
                                                 paid_time=paid_time, note=note, proof=proof, ip=_client_ip(request))


@router.post("/multilevel/redeem")
def multilevel_redeem(data: MultilevelRedeemRequest, request: Request, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    """A 100 % Multilevel promo code (approved + ACTIVE): opens all Modelltests without a card payment."""
    multilevel_premium.redeem(db, current_user, data.code, _client_ip(request))
    return multilevel_premium.status(db, current_user)


@router.post("/promo/redeem", response_model=PromoRedeemResponse)
def redeem_promo(
    data: PromoRedeemRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return VizuPayService(db).redeem_promo(data.code, current_user, _client_ip(request))


@router.post("/orders", response_model=OrderItem)
async def create_order(
    request: Request,
    plan: str = Form(...),
    payment_method: str = Form(...),
    promo_code: str | None = Form(None),
    proof: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await VizuPayService(db).create_order(
        current_user,
        plan=plan,
        payment_method=payment_method,
        promo_code=promo_code or None,
        proof_file=proof,
        ip=_client_ip(request),
    )


@router.get("/orders", response_model=OrderListResponse)
def get_my_orders(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return VizuPayService(db).get_my_orders(current_user, page=page, page_size=page_size)


@router.get("/orders/{order_id}/proof")
def get_order_proof(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Receipt image/PDF — never a public URL. Order owner or staff only
    (VizuPayService.get_order_proof enforces this)."""
    path, content_type, filename = VizuPayService(db).get_order_proof(order_id, current_user)
    return FileResponse(path=path, media_type=content_type, filename=filename)
