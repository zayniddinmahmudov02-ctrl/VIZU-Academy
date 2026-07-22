from uuid import UUID

from sqlalchemy.orm import Session

from app.models.reading import Reading
from app.repositories.reading import ReadingRepository


class ReadingService:

    def __init__(
        self,
        db: Session,
    ):
        self.repository = ReadingRepository(db)

    def get(
        self,
        reading_id: UUID,
    ) -> Reading | None:
        return self.repository.get(reading_id)

    def get_by_lesson(
        self,
        lesson_id: UUID,
    ) -> list[Reading]:
        return self.repository.get_by_lesson(lesson_id)

    def create(
        self,
        data,
    ) -> Reading:
        return self.repository.create(data)

    def update(
        self,
        reading: Reading,
        data,
    ) -> Reading:
        return self.repository.update(
            reading,
            data,
        )

    def publish(
        self,
        reading: Reading,
    ) -> Reading:
        return self.repository.publish(reading)

    def unpublish(
        self,
        reading: Reading,
    ) -> Reading:
        return self.repository.unpublish(reading)

    def delete(
        self,
        reading: Reading,
    ) -> None:
        self.repository.delete(reading)