from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin

from app.db.session import get_db

from app.models.user import User

from app.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
    PaymentResponse,
)

from app.services.payment import (
    PaymentService,
)

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.get(
    "",
    response_model=list[PaymentResponse],
)
def get_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return PaymentService(db).get_all()


@router.get(
    "/{item_id}",
    response_model=PaymentResponse,
)
def get_one(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    item = PaymentService(db).get(item_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return item


@router.post(
    "",
    response_model=PaymentResponse,
)
def create(
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    return PaymentService(db).create(data)


@router.put(
    "/{item_id}",
    response_model=PaymentResponse,
)
def update(
    item_id: str,
    data: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    item = PaymentService(db).update(
        item_id,
        data,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return item


@router.delete("/{item_id}")
def delete(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    deleted = PaymentService(db).delete(item_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return {
        "message": "Deleted",
    }
