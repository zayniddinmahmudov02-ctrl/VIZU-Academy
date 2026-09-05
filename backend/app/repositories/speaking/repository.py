from sqlalchemy.orm import Session

from app.models.speaking import Speaking

from app.schemas.speaking import (
    SpeakingCreate,
    SpeakingUpdate,
)


class SpeakingRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_all(
        self,
    ):
        return (
            self.db.query(Speaking)
            .order_by(
                Speaking.order_index,
            )
            .all()
        )

    def get(
        self,
        speaking_id: str,
    ):
        return (
            self.db.query(Speaking)
            .filter(
                Speaking.id == speaking_id,
            )
            .first()
        )

    def get_by_lesson(self, lesson_id, published_only: bool = False):
        query = self.db.query(Speaking).filter(Speaking.lesson_id == lesson_id)
        if published_only:
            query = query.filter(Speaking.is_published.is_(True))
        return query.order_by(Speaking.order_index).all()

    def create(
        self,
        data: SpeakingCreate,
    ):
        item = Speaking(
            **data.model_dump(),
        )

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def update(
        self,
        item: Speaking,
        data: SpeakingUpdate,
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
        item: Speaking,
    ):
        self.db.delete(item)
        self.db.commit()