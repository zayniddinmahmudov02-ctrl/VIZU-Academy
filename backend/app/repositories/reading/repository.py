from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reading import Reading
from app.repositories.base import BaseRepository


class ReadingRepository(BaseRepository[Reading]):

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            Reading,
            db,
        )

    def get_by_lesson(
        self,
        lesson_id: UUID,
    ) -> list[Reading]:

        result = self.db.execute(
            select(Reading)
            .where(
                Reading.lesson_id == lesson_id,
            )
            .order_by(
                Reading.order_index,
            )
        )

        return list(
            result.scalars().all()
        )

    def publish(
        self,
        reading: Reading,
    ) -> Reading:

        reading.is_published = True

        self.db.commit()
        self.db.refresh(reading)

        return reading

    def unpublish(
        self,
        reading: Reading,
    ) -> Reading:

        reading.is_published = False

        self.db.commit()
        self.db.refresh(reading)

        return reading