from sqlalchemy.orm import Session

from app.repositories.quiz_question import (
    QuizQuestionRepository,
)

from app.schemas.quiz_question import (
    QuizQuestionCreate,
    QuizQuestionUpdate,
)


class QuizQuestionService:

    def __init__(self, db: Session):
        self.repository = QuizQuestionRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def get(self, question_id: str):
        return self.repository.get(question_id)

    def create(self, data: QuizQuestionCreate):
        return self.repository.create(data)

    def update(
        self,
        question_id: str,
        data: QuizQuestionUpdate,
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