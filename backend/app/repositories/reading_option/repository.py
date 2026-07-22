from sqlalchemy.orm import Session

from app.models.reading_option import ReadingOption

from app.schemas.reading_option import (
    ReadingOptionCreate,
    ReadingOptionUpdate,
)


class ReadingOptionRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_all(
        self,
    ):
        return (
            self.db.query(ReadingOption)
            .order_by(
                ReadingOption.order_index,
            )
            .all()
        )

    def get(
        self,
        option_id: str,
    ):
        return (
            self.db.query(ReadingOption)
            .filter(
                ReadingOption.id == option_id,
            )
            .first()
        )

    def create(
        self,
        data: ReadingOptionCreate,
    ):
        item = ReadingOption(
            **data.model_dump(),
        )

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def update(
        self,
        item: ReadingOption,
        data: ReadingOptionUpdate,
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
        item: ReadingOption,
    ):
        self.db.delete(item)
        self.db.commit()