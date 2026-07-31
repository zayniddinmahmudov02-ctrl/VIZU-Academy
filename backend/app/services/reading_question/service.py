from sqlalchemy.orm import Session

from app.repositories.reading_question import (
    ReadingQuestionRepository,
)

from app.schemas.reading_question import (
    ReadingQuestionCreate,
    ReadingQuestionUpdate,
)


class ReadingQuestionService:

    def __init__(self, db: Session):
        self.repository = ReadingQuestionRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def get(self, question_id: str):
        return self.repository.get(question_id)

    def create(self, data: ReadingQuestionCreate):
        return self.repository.create(data)

    def update(
        self,
        question_id: str,
        data: ReadingQuestionUpdate,
    ):
        item = self.repository.get(question_id)

        if not item:
            return None

        return self.repository.update(
            item,
            data,
        )

    def delete(self, question_id: str):
        item = self.repository.get(question_id)

        if not item:
            return False

        self.repository.delete(item)

        return True
