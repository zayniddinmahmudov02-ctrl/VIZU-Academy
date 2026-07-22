from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class PaymentBase(BaseSchema):

    user_id: str

    course_id: str

    amount: int

    currency: str = "UZS"

    provider: str = "Manual"

    transaction_id: str | None = None

    status: str = "pending"


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseSchema):

    transaction_id: str | None = None

    status: str | None = None


class PaymentResponse(PaymentBase):

    id: str

    model_config = ConfigDict(
        from_attributes=True,
    )