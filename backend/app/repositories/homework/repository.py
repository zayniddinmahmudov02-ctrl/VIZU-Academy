from sqlalchemy.orm import Session

from app.models.homework import Homework

from app.schemas.homework import (
    HomeworkCreate,
    HomeworkUpdate,
)


class HomeworkRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_all(
        self,
    ):
        return (
            self.db.query(Homework)
            .all()
        )

    def get(
        self,
        homework_id: str,
    ):
        return (
            self.db.query(Homework)
            .filter(
                Homework.id == homework_id,
            )
            .first()
        )

    def create(
        self,
        data: HomeworkCreate,
    ):
        item = Homework(
            **data.model_dump(),
        )

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def update(
        self,
        item: Homework,
        data: HomeworkUpdate,
    ):
        for key, value in data.model_dump(
            exclude_unset=True,
        ).items():
            setattr(
                item,
                key,
                value,
            )

        self.db.commit()
        self.db.refresh(item)

        return item

    def delete(
        self,
        item: Homework,
    ):
        self.db.delete(item)
        self.db.commit()