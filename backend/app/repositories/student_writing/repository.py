from sqlalchemy.orm import Session

from app.models.student_writing import StudentWriting

from app.schemas.student_writing import (
    StudentWritingCreate,
    StudentWritingUpdate,
)


class StudentWritingRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(StudentWriting).all()

    def get(self, item_id: str):
        return (
            self.db.query(StudentWriting)
            .filter(StudentWriting.id == item_id)
            .first()
        )

    def create(
        self,
        data: StudentWritingCreate,
    ):
        item = StudentWriting(**data.model_dump())

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def update(
        self,
        item: StudentWriting,
        data: StudentWritingUpdate,
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
        item: StudentWriting,
    ):
        self.db.delete(item)
        self.db.commit()