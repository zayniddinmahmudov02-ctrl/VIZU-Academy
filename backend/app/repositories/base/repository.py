from typing import Generic
from typing import Type
from typing import TypeVar

from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):

    def __init__(
        self,
        model: Type[ModelType],
        db: Session,
    ):
        self.model = model
        self.db = db

    def get(
        self,
        object_id: str,
    ):
        return (
            self.db.query(self.model)
            .filter(self.model.id == object_id)
            .first()
        )

    def get_all(self):
        return (
            self.db.query(self.model)
            .all()
        )

    def paginate(
        self,
        offset: int,
        limit: int,
    ):
        return (
            self.db.query(self.model)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count(self):
        return (
            self.db.query(self.model)
            .count()
        )

    def create(
        self,
        data: dict,
    ):
        db_obj = self.model(**data)

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)

        return db_obj

    def update(
        self,
        db_obj,
        data: dict,
    ):
        for key, value in data.items():
            setattr(
                db_obj,
                key,
                value,
            )

        self.db.commit()
        self.db.refresh(db_obj)

        return db_obj

    def delete(
        self,
        db_obj,
    ):
        self.db.delete(db_obj)
        self.db.commit()

    def exists(
        self,
        object_id: str,
    ):
        return (
            self.db.query(self.model)
            .filter(self.model.id == object_id)
            .first()
            is not None
        )