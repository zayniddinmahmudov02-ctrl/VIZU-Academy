from sqlalchemy.orm import Session

from app.models.quiz import Quiz
from app.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
)


class QuizRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_all(
        self,
    ):
        return (
            self.db.query(Quiz)
            .order_by(Quiz.order_index)
            .all()
        )

    def get(
        self,
        quiz_id: str,
    ):
        return (
            self.db.query(Quiz)
            .filter(
                Quiz.id == quiz_id,
            )
            .first()
        )

    def create(
        self,
        data: QuizCreate,
    ):
        quiz = Quiz(
            **data.model_dump()
        )

        self.db.add(quiz)
        self.db.commit()
        self.db.refresh(quiz)

        return quiz

    def update(
        self,
        quiz: Quiz,
        data: QuizUpdate,
    ):
        for key, value in data.model_dump(
            exclude_unset=True,
        ).items():
            setattr(
                quiz,
                key,
                value,
            )

        self.db.commit()
        self.db.refresh(quiz)

        return quiz

    def delete(
        self,
        quiz: Quiz,
    ):
        self.db.delete(quiz)
        self.db.commit()