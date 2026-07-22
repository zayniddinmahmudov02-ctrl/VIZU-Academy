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