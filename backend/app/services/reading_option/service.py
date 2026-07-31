from sqlalchemy.orm import Session

from app.repositories.reading_option import (
    ReadingOptionRepository,
)

from app.schemas.reading_option import (
    ReadingOptionCreate,
    ReadingOptionUpdate,
)


class ReadingOptionService:

    def __init__(
        self,
        db: Session,
    ):
        self.repository = ReadingOptionRepository(db)

    def get_all(
        self,
    ):
        return self.repository.get_all()

    def get(
        self,
        option_id: str,
    ):
        return self.repository.get(option_id)

    def create(
        self,
        data: ReadingOptionCreate,
    ):
        return self.repository.create(data)

    def update(
        self,
        option_id: str,
        data: ReadingOptionUpdate,
    ):
        item = self.repository.get(
            option_id,
        )

        if item is None:
            return None

        return self.repository.update(
            item,
            data,
        )

    def delete(
        self,
        option_id: str,
    ):
        item = self.repository.get(
            option_id,
        )

        if item is None:
            return False

        self.repository.delete(item)

        return True
