from sqlalchemy.orm import Session

from app.models.listening import Listening
from app.schemas.listening import (
    ListeningCreate,
    ListeningUpdate,
)


class ListeningRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return (
            self.db.query(Listening)
            .order_by(Listening.order_index)
            .all()
        )

    def get(self, listening_id: str):
        return (
            self.db.query(Listening)
            .filter(Listening.id == listening_id)
            .first()
        )

    def get_by_lesson(self, lesson_id, published_only: bool = False):
        query = self.db.query(Listening).filter(Listening.lesson_id == lesson_id)
        if published_only:
            query = query.filter(Listening.is_published.is_(True))
        return query.order_by(Listening.order_index).all()

    def create(self, data: ListeningCreate):
        listening = Listening(**data.model_dump())

        self.db.add(listening)
        self.db.commit()
        self.db.refresh(listening)

        return listening

    def update(
        self,
        listening: Listening,
        data: ListeningUpdate,
    ):
        for key, value in data.model_dump(
            exclude_unset=True
        ).items():
            setattr(listening, key, value)

        self.db.commit()
        self.db.refresh(listening)

        return listening

    def delete(self, listening: Listening):
        self.db.delete(listening)
        self.db.commit()