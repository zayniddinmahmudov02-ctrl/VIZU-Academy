from sqlalchemy.orm import Session

from app.models.student_quiz import StudentQuiz

from app.schemas.student_quiz import (
    StudentQuizCreate,
    StudentQuizUpdate,
)


class StudentQuizRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(StudentQuiz).all()

    def get(self, item_id: str):
        return (
            self.db.query(StudentQuiz)
            .filter(StudentQuiz.id == item_id)
            .first()
        )

    def create(
        self,
        data: StudentQuizCreate,
    ):
        item = StudentQuiz(**data.model_dump())

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def update(
        self,
        item: StudentQuiz,
        data: StudentQuizUpdate,
    ):
        for key, value in data.model_dump(
            exclude_unset=True
        ).items():
            setattr(item, key, value)

        self.db.commit()
        self.db.refresh(item)

        return item

    def delete(
        self,
        item: StudentQuiz,
    ):
        self.db.delete(item)
        self.db.commit()