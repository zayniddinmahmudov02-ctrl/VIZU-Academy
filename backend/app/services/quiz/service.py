from sqlalchemy.orm import Session

from app.repositories.quiz import QuizRepository

from app.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
)


class QuizService:

    def __init__(self, db: Session):
        self.repository = QuizRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def get(self, quiz_id: str):
        return self.repository.get(quiz_id)

    def create(
        self,
        data: QuizCreate,
    ):
        return self.repository.create(data)

    def update(
        self,
        quiz_id: str,
        data: QuizUpdate,
    ):
        quiz = self.repository.get(quiz_id)

        if not quiz:
            return None

        return self.repository.update(
            quiz,
            data,
        )

    def delete(
        self,
        quiz_id: str,
    ):
        quiz = self.repository.get(quiz_id)

        if not quiz:
            return False

        self.repository.delete(quiz)

        return True