from sqlalchemy.orm import Session

from app.models.student_speaking import StudentSpeaking
from app.schemas.student_speaking import (
    StudentSpeakingCreate,
    StudentSpeakingUpdate,
)


class StudentSpeakingRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(StudentSpeaking).all()

    def get(self, item_id: str):
        return (
            self.db.query(StudentSpeaking)
            .filter(StudentSpeaking.id == item_id)
            .first()
        )

    def create(self, data: StudentSpeakingCreate):
        item = StudentSpeaking(**data.model_dump())

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def update(
        self,
        item: StudentSpeaking,
        data: StudentSpeakingUpdate,
    ):
        for key, value in data.model_dump(
            exclude_unset=True
        ).items():
            setattr(item, key, value)

        self.db.commit()
        self.db.refresh(item)

        return item

    def delete(self, item: StudentSpeaking):
        self.db.delete(item)
        self.db.commit()