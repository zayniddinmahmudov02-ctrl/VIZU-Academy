from sqlalchemy.orm import Session

from app.repositories.listening import ListeningRepository
from app.schemas.listening import (
    ListeningCreate,
    ListeningUpdate,
)


class ListeningService:

    def __init__(self, db: Session):
        self.repository = ListeningRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def get(self, listening_id: str):
        return self.repository.get(listening_id)

    def get_by_lesson(self, lesson_id, published_only: bool = False):
        return self.repository.get_by_lesson(lesson_id, published_only=published_only)

    def create(self, data: ListeningCreate):
        return self.repository.create(data)

    def update(
        self,
        listening_id: str,
        data: ListeningUpdate,
    ):
        listening = self.repository.get(listening_id)

        if not listening:
            return None

        return self.repository.update(
            listening,
            data,
        )

    def delete(self, listening_id: str):
        listening = self.repository.get(listening_id)

        if not listening:
            return False

        self.repository.delete(listening)

        return True