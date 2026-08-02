from uuid import UUID

from sqlalchemy.orm import Session

from app.models.vocabulary import Vocabulary
from app.repositories.vocabulary import VocabularyRepository


class VocabularyService:

    def __init__(
        self,
        db: Session,
    ):
        self.repository = VocabularyRepository(db)

    def get_all(
        self,
    ) -> list[Vocabulary]:
        return self.repository.get_all()

    def get(
        self,
        vocabulary_id: UUID,
    ) -> Vocabulary | None:
        return self.repository.get(vocabulary_id)

    def get_by_lesson(
        self,
        lesson_id: UUID,
    ) -> list[Vocabulary]:
        return self.repository.get_by_lesson(lesson_id)

    def create(
        self,
        data,
    ) -> Vocabulary:
        return self.repository.create(data)

    def update(
        self,
        vocabulary: Vocabulary,
        data,
    ) -> Vocabulary:
        return self.repository.update(
            vocabulary,
            data,
        )

    def publish(
        self,
        vocabulary: Vocabulary,
    ) -> Vocabulary:
        return self.repository.publish(vocabulary)

    def unpublish(
        self,
        vocabulary: Vocabulary,
    ) -> Vocabulary:
        return self.repository.unpublish(vocabulary)

    def delete(
        self,
        vocabulary: Vocabulary,
    ) -> None:
        self.repository.delete(vocabulary)