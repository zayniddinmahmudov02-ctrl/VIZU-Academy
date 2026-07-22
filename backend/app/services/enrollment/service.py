from sqlalchemy.orm import Session

from app.repositories.enrollment import (
    EnrollmentRepository,
)

from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentUpdate,
)


class EnrollmentService:

    def __init__(
        self,
        db: Session,
    ):
        self.repository = EnrollmentRepository(db)

    def get_all(
        self,
    ):
        return self.repository.get_all()

    def get(
        self,
        enrollment_id: str,
    ):
        return self.repository.get(enrollment_id)

    def create(
        self,
        data: EnrollmentCreate,
    ):
        return self.repository.create(data)

    def update(
        self,
        enrollment_id: str,
        data: EnrollmentUpdate,
    ):
        item = self.repository.get(
            enrollment_id,
        )

        if item is None:
            return None

        return self.repository.update(
            item,
            data,
        )

    def delete(
        self,
        enrollment_id: str,
    ):
        item = self.repository.get(
            enrollment_id,
        )

        if item is None:
            return False

        self.repository.delete(item)

        return True