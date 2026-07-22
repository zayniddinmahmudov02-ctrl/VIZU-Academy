from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vocabulary import Vocabulary
from app.repositories.base import BaseRepository


class VocabularyRepository(BaseRepository[Vocabulary]):

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            Vocabulary,
            db,
        )

    def get_by_lesson(
        self,
        lesson_id: UUID,
    ) -> list[Vocabulary]:

        result = self.db.execute(
            select(Vocabulary)
            .where(
                Vocabulary.lesson_id == lesson_id,
            )
            .order_by(
                Vocabulary.order_index,
            )
        )

        return list(
            result.scalars().all()
        )

    def publish(
        self,
        vocabulary: Vocabulary,
    ) -> Vocabulary:

        vocabulary.is_published = True

        self.db.commit()
        self.db.refresh(vocabulary)

        return vocabulary

    def unpublish(
        self,
        vocabulary: Vocabulary,
    ) -> Vocabulary:

        vocabulary.is_published = False

        self.db.commit()
        self.db.refresh(vocabulary)

        return vocabulary