from sqlalchemy.orm import Session

from app.models.quiz_question import QuizQuestion

from app.schemas.quiz_question import (
    QuizQuestionCreate,
    QuizQuestionUpdate,
)


class QuizQuestionRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_all(
        self,
    ):
        return (
            self.db.query(QuizQuestion)
            .order_by(
                QuizQuestion.order_index,
            )
            .all()
        )

    def get(
        self,
        question_id: str,
    ):
        return (
            self.db.query(QuizQuestion)
            .filter(
                QuizQuestion.id == question_id,
            )
            .first()
        )

    def create(
        self,
        data: QuizQuestionCreate,
    ):
        item = QuizQuestion(
            **data.model_dump(),
        )

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def update(
        self,
        item: QuizQuestion,
        data: QuizQuestionUpdate,
    ):
        for key, value in data.model_dump(
            exclude_unset=True,
        ).items():
            setattr(
                item,
                key,
                value,
            )

        self.db.commit()
        self.db.refresh(item)

        return item

    def delete(
        self,
        item: QuizQuestion,
    ):
        self.db.delete(item)
        self.db.commit()