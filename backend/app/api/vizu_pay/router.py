from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.vizu_pay import (
    MySubscriptionStatus,
    OrderItem,
    OrderListResponse,
    PlanOption,
    PromoValidateResponse,
    TrialActivateResponse,
)
from app.services.vizu_pay import VizuPayService

router = APIRouter(
    prefix="/vizu-pay",
    tags=["VIZU Pay"],
)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/plans", response_model=list[PlanOption])
def list_plans(db: Session = Depends(get_db)):
    return VizuPayService(db).list_plans()


@router.get("/status", response_model=MySubscriptionStatus)
def get_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return VizuPayService(db).get_my_status(current_user)


@router.post("/trial", response_model=TrialActivateResponse)
def activate_trial(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return VizuPayService(db).activate_trial(current_user, _client_ip(request))


@router.get("/promo/validate", response_model=PromoValidateResponse)
def validate_promo(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return VizuPayService(db).validate_promo(code, current_user)


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
