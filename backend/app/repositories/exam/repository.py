from sqlalchemy.orm import Session

from app.models.exam import Exam
from app.models.exam_provider import ExamProvider
from app.models.exam_part import ExamPart
from app.models.exam_session import ExamSession

from app.schemas.exam import (
    ExamCreate,
    ExamUpdate,
)


class ExamRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(Exam).all()

    def get(self, exam_id: str):
        return (
            self.db.query(Exam)
            .filter(
                Exam.id == exam_id
            )
            .first()
        )

    def create(
        self,
        data: ExamCreate,
    ):
        exam = Exam(**data.model_dump())

        self.db.add(exam)

        self.db.commit()

        self.db.refresh(exam)

        return exam

    def update(
        self,
        exam: Exam,
        data: ExamUpdate,
    ):

        for key, value in data.model_dump(
            exclude_unset=True,
        ).items():

            setattr(
                exam,
                key,
                value,
            )

        self.db.commit()

        self.db.refresh(exam)

        return exam

    def delete(
        self,
        exam: Exam,
    ):
        self.db.delete(exam)

        self.db.commit()