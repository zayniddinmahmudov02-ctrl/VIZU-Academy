from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.base import BaseRepository

ModelType = TypeVar("ModelType")


class BaseService(Generic[ModelType]):
    def __init__(
        self,
        repository: BaseRepository,
    ):
        self.repository = repository

    def get(
        self,
        db: Session,
        id: UUID,
    ):
        return self.repository.get(
            db,
            id,
        )

    def get_all(
        self,
        db: Session,
    ):
        return self.repository.get_all(db)

    def create(
        self,
        db: Session,
        obj: ModelType,
    ):
        return self.repository.create(
            db,
            obj,
        )

    def update(
        self,
        db: Session,
        obj: ModelType,
        data: dict,
    ):
        return self.repository.update(
            db,
            obj,
            data,
        )

    def delete(
        self,
        db: Session,
        obj: ModelType,
    ):
        return self.repository.delete(
            db,
            obj,
        )