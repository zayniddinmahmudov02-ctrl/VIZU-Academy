from sqlalchemy.orm import Session

from app.models.quiz_option import QuizOption

from app.schemas.quiz_option import (
    QuizOptionCreate,
    QuizOptionUpdate,
)


class QuizOptionRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_all(
        self,
    ) -> list[QuizOption]:

        return (
            self.db.query(QuizOption)
            .order_by(
                QuizOption.order_index,
            )
            .all()
        )

    def get(
        self,
        option_id: str,
    ) -> QuizOption | None:

        return (
            self.db.query(QuizOption)
            .filter(
                QuizOption.id == option_id,
            )
            .first()
        )

    def create(
        self,
        data: QuizOptionCreate,
    ) -> QuizOption:

        item = QuizOption(
            **data.model_dump(),
        )

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def update(
        self,
        item: QuizOption,
        data: QuizOptionUpdate,
    ) -> QuizOption:

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
        item: QuizOption,
    ) -> None:

        self.db.delete(item)
        self.db.commit()