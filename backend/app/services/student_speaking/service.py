from sqlalchemy.orm import Session

from app.repositories.student_speaking import StudentSpeakingRepository
from app.schemas.student_speaking import (
    StudentSpeakingCreate,
    StudentSpeakingUpdate,
)


class StudentSpeakingService:

    def __init__(self, db: Session):
        self.repository = StudentSpeakingRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def get(self, item_id: str):
        return self.repository.get(item_id)

    def create(self, data: StudentSpeakingCreate):
        return self.repository.create(data)

    def update(
        self,
        item_id: str,
        data: StudentSpeakingUpdate,
    ):
        item = self.repository.get(item_id)

        if not item:
            return None

        return self.repository.update(item, data)

    def delete(self, item_id: str):
        item = self.repository.get(item_id)

        if not item:
            return False

        self.repository.delete(item)

        return True