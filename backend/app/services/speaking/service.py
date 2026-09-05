from sqlalchemy.orm import Session

from app.repositories.speaking import SpeakingRepository
from app.schemas.speaking import (
    SpeakingCreate,
    SpeakingUpdate,
)


class SpeakingService:

    def __init__(self, db: Session):
        self.repository = SpeakingRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def get(self, speaking_id: str):
        return self.repository.get(speaking_id)

    def get_by_lesson(self, lesson_id, published_only: bool = False):
        return self.repository.get_by_lesson(lesson_id, published_only=published_only)

    def create(self, data: SpeakingCreate):
        return self.repository.create(data)

    def update(
        self,
        speaking_id: str,
        data: SpeakingUpdate,
    ):
        speaking = self.repository.get(speaking_id)

        if not speaking:
            return None

        return self.repository.update(
            speaking,
            data,
        )

    def delete(self, speaking_id: str):
        speaking = self.repository.get(speaking_id)

        if not speaking:
            return False

        self.repository.delete(speaking)

        return True
