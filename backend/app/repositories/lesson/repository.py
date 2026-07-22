from sqlalchemy.orm import Session

from app.models.lesson import Lesson

from app.repositories.base import BaseRepository

from app.schemas.lesson import (
    LessonCreate,
    LessonUpdate,
)


class LessonRepository(BaseRepository[Lesson]):

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            Lesson,
            db,
        )

    # =====================================
    # Create Lesson
    # =====================================

    def create(
        self,
        data: LessonCreate,
    ) -> Lesson:

        lesson = Lesson(
            **data.model_dump(),
        )

        self.db.add(
            lesson,
        )

        self.db.commit()

        self.db.refresh(
            lesson,
        )

        return lesson

    # =====================================
    # Update Lesson
    # =====================================

    def update(
        self,
        lesson: Lesson,
        data: LessonUpdate,
    ) -> Lesson:

        for key, value in data.model_dump(
            exclude_unset=True,
        ).items():
            setattr(
                lesson,
                key,
                value,
            )

        self.db.commit()

        self.db.refresh(
            lesson,
        )

        return lesson

    # =====================================
    # Delete Lesson
    # =====================================

    def delete(
        self,
        lesson: Lesson,
    ) -> None:

        self.db.delete(
            lesson,
        )

        self.db.commit()

    # =====================================
    # Get Lessons By Module
    # =====================================

    def get_by_module(
        self,
        module_id: str,
    ) -> list[Lesson]:

        return (
            self.db.query(
                Lesson,
            )
            .filter(
                Lesson.module_id == module_id,
            )
            .order_by(
                Lesson.number.asc(),
            )
            .all()
        )