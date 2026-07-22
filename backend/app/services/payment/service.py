from sqlalchemy.orm import Session

from app.repositories.payment import (
    PaymentRepository,
)

from app.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
)


class PaymentService:

    def __init__(self, db: Session):
        self.repository = PaymentRepository(db)

    def get_all(self):
        return self.repository.get_all()

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