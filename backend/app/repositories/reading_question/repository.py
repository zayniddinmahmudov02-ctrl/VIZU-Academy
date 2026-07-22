from sqlalchemy.orm import Session

from app.models.reading_question import ReadingQuestion

from app.schemas.reading_question import (
    ReadingQuestionCreate,
    ReadingQuestionUpdate,
)


class ReadingQuestionRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_all(
        self,
    ):
        return (
            self.db.query(ReadingQuestion)
            .order_by(
                ReadingQuestion.order_index,
            )
            .all()
        )

    def get(
        self,
        question_id: str,
    ):
        return (
            self.db.query(ReadingQuestion)
            .filter(
                ReadingQuestion.id == question_id,
            )
            .first()
        )

    def create(
        self,
        data: ReadingQuestionCreate,
    ):
        item = ReadingQuestion(
            **data.model_dump(),
        )

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def update(
        self,
        item: ReadingQuestion,
        data: ReadingQuestionUpdate,
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
        item: ReadingQuestion,
    ):
        self.db.delete(item)
        self.db.commit()