from sqlalchemy.orm import Session

from app.repositories.student_quiz import (
    StudentQuizRepository,
)

from app.schemas.student_quiz import (
    StudentQuizCreate,
    StudentQuizUpdate,
)


class StudentQuizService:

    def __init__(self, db: Session):
        self.repository = StudentQuizRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def get(self, item_id: str):
        return self.repository.get(item_id)

    def create(
        self,
        data: StudentQuizCreate,
    ):
        return self.repository.create(data)

    def update(
        self,
        item_id: str,
        data: StudentQuizUpdate,
    ):
        item = self.repository.get(item_id)

        if not item:
            return None

        return self.repository.update(
            item,
            data,
        )

    def delete(
        self,
        item_id: str,
    ):
        item = self.repository.get(item_id)

        if not item:
            return False

        self.repository.delete(item)

        return True