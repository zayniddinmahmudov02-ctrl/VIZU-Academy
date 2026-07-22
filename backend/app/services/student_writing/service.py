from sqlalchemy.orm import Session

from app.repositories.student_writing import (
    StudentWritingRepository,
)

from app.schemas.student_writing import (
    StudentWritingCreate,
    StudentWritingUpdate,
)


class StudentWritingService:

    def __init__(self, db: Session):
        self.repository = StudentWritingRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def get(self, item_id: str):
        return self.repository.get(item_id)

    def create(
        self,
        data: StudentWritingCreate,
    ):
        return self.repository.create(data)

    def update(
        self,
        item_id: str,
        data: StudentWritingUpdate,
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