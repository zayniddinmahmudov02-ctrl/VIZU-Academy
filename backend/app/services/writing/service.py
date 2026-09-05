from sqlalchemy.orm import Session

from app.repositories.writing import WritingRepository
from app.schemas.writing import (
    WritingCreate,
    WritingUpdate,
)


class WritingService:

    def __init__(self, db: Session):
        self.repository = WritingRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def get(self, writing_id: str):
        return self.repository.get(writing_id)

    def get_by_lesson(self, lesson_id, published_only: bool = False):
        return self.repository.get_by_lesson(lesson_id, published_only=published_only)

    def create(self, data: WritingCreate):
        return self.repository.create(data)

    def update(self, writing_id: str, data: WritingUpdate):
        writing = self.repository.get(writing_id)

        if not writing:
            return None

        return self.repository.update(writing, data)

    def delete(self, writing_id: str):
        writing = self.repository.get(writing_id)

        if not writing:
            return False

        self.repository.delete(writing)

        return True