from sqlalchemy.orm import Session

from app.repositories.exam import (
    ExamRepository,
)

from app.schemas.exam import (
    ExamCreate,
    ExamUpdate,
)


class ExamService:

    def __init__(
        self,
        db: Session,
    ):
        self.repository = ExamRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def get(
        self,
        exam_id: str,
    ):
        return self.repository.get(exam_id)

    def create(
        self,
        data: ExamCreate,
    ):
        return self.repository.create(data)

    def update(
        self,
        exam_id: str,
        data: ExamUpdate,
    ):
        exam = self.repository.get(exam_id)

        if not exam:
            return None

        return self.repository.update(
            exam,
            data,
        )

    def delete(
        self,
        exam_id: str,
    ):
        exam = self.repository.get(exam_id)

        if not exam:
            return False

        self.repository.delete(exam)

        return True