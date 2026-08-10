from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.models.payment import Payment

from app.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
)


class PaymentRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(Payment).all()

    def list_paginated(
        self,
        page: int,
        page_size: int,
        status: str | None = None,
        year: int | None = None,
        month: int | None = None,
        day: int | None = None,
    ) -> tuple[list[Payment], int]:
        # user/course are `lazy="joined"` on the Payment model itself, so
        # this already avoids N+1 without an explicit .join()/.options()
        # here — every row comes back with its user and course preloaded
        # in the same query.
        query = self.db.query(Payment)

        if status:
            query = query.filter(Payment.status == status)

        if year is not None:
            query = query.filter(extract("year", Payment.created_at) == year)
        if month is not None:
            query = query.filter(extract("month", Payment.created_at) == month)
        if day is not None:
            query = query.filter(extract("day", Payment.created_at) == day)

        total = query.count()

        rows = (
            query.order_by(Payment.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return rows, total

    def get(self, item_id: str):
        return (
            self.db.query(Payment)
            .filter(Payment.id == item_id)
            .first()
        )

    def create(
        self,
        data: PaymentCreate,
    ):
        item = Payment(**data.model_dump())

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def update(
        self,
        item: Payment,
        data: PaymentUpdate,
    ):
        for key, value in data.model_dump(
            exclude_unset=True,
        ).items():
            setattr(item, key, value)

        self.db.commit()
        self.db.refresh(item)

        return item

    def delete(
        self,
        item: Payment,
    ):
        self.db.delete(item)
        self.db.commit()