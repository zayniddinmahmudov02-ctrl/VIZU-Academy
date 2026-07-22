from sqlalchemy.orm import Session

from app.repositories.quiz_option import (
    QuizOptionRepository,
)

from app.schemas.quiz_option import (
    QuizOptionCreate,
    QuizOptionUpdate,
)


class QuizOptionService:

    def __init__(
        self,
        db: Session,
    ):
        self.repository = QuizOptionRepository(db)

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
        data: QuizOptionCreate,
    ):
        return self.repository.create(data)

    def update(
        self,
        option_id: str,
        data: QuizOptionUpdate,
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