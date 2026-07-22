from sqlalchemy.orm import Session

from app.models.writing import Writing
from app.schemas.writing import (
    WritingCreate,
    WritingUpdate,
)


class WritingRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return (
            self.db.query(Writing)
            .order_by(Writing.order_index)
            .all()
        )

    def get(self, writing_id: str):
        return (
            self.db.query(Writing)
            .filter(Writing.id == writing_id)
            .first()
        )

    def create(self, data: WritingCreate):
        writing = Writing(**data.model_dump())

        self.db.add(writing)
        self.db.commit()
        self.db.refresh(writing)

        return writing

    def update(
        self,
        writing: Writing,
        data: WritingUpdate,
    ):
        for key, value in data.model_dump(
            exclude_unset=True
        ).items():
            setattr(writing, key, value)

        self.db.commit()
        self.db.refresh(writing)

        return writing

    def delete(self, writing: Writing):
        self.db.delete(writing)
        self.db.commit()