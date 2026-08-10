from sqlalchemy.orm import Session

from app.core.pagination import clamp_page_params, paginated_response
from app.repositories.payment import (
    PaymentRepository,
)

from app.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
)


def _serialize(item):
    return {
        "id": str(item.id),
        "user_id": str(item.user_id),
        "course_id": str(item.course_id),
        "amount": item.amount,
        "currency": item.currency,
        "provider": item.provider,
        "transaction_id": item.transaction_id,
        "status": item.status,
        "created_at": item.created_at,
        "user_email": item.user.email if item.user else None,
        "user_username": item.user.username if item.user else None,
        "course_title": item.course.title if item.course else None,
    }


class PaymentService:

    def __init__(self, db: Session):
        self.repository = PaymentRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def list_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        status: str | None = None,
        year: int | None = None,
        month: int | None = None,
        day: int | None = None,
    ) -> dict:
        page, page_size = clamp_page_params(page, page_size)

        rows, total = self.repository.list_paginated(
            page=page,
            page_size=page_size,
            status=status,
            year=year,
            month=month,
            day=day,
        )

        return paginated_response([_serialize(r) for r in rows], total, page, page_size)

    def get(self, item_id: str):
        return self.repository.get(item_id)

    def create(
        self,
        data: PaymentCreate,
    ):
        return self.repository.create(data)

    def update(
        self,
        item_id: str,
        data: PaymentUpdate,
    ):
        item = self.repository.get(item_id)

        if not item:
            return None

        return self.repository.update(
            item,
            data,
        )

    def delete(
        self,
        item_id: str,
    ):
        item = self.repository.get(item_id)

        if not item:
            return False

        self.repository.delete(item)

        return True