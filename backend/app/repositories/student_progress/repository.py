from sqlalchemy.orm import Session

from app.models.student_progress import StudentProgress

from app.schemas.student_progress import (
    StudentProgressCreate,
    StudentProgressUpdate,
)


class StudentProgressRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(StudentProgress).all()

    def get(self, item_id: str):
        return (
            self.db.query(StudentProgress)
            .filter(StudentProgress.id == item_id)
            .first()
        )

    def create(
        self,
        data: StudentProgressCreate,
    ):
        item = StudentProgress(**data.model_dump())

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def update(
        self,
        item: StudentProgress,
        data: StudentProgressUpdate,
    ):
        for key, value in data.model_dump(
            exclude_unset=True
        ).items():
            setattr(item, key, value)

        self.db.commit()
        self.db.refresh(item)

        return item

    def delete(
        self,
        item: StudentProgress,
    ):
        self.db.delete(item)
        self.db.commit()

    def get_by_user_and_lesson(
        self,
        user_id: str,
        lesson_id: str,
    ) -> StudentProgress | None:
        return (
            self.db.query(StudentProgress)
            .filter(
                StudentProgress.user_id == user_id,
                StudentProgress.lesson_id == lesson_id,
            )
            .first()
        )

    def get_or_create(
        self,
        user_id: str,
        lesson_id: str,
    ) -> StudentProgress:
        progress = self.get_by_user_and_lesson(user_id, lesson_id)

        if progress is not None:
            return progress

        progress = StudentProgress(
            user_id=user_id,
            lesson_id=lesson_id,
        )

        self.db.add(progress)
        self.db.commit()
        self.db.refresh(progress)

        return progress

    def mark_video_completed(
        self,
        progress: StudentProgress,
    ) -> StudentProgress:
        progress.video_completed = True

        self.db.commit()
        self.db.refresh(progress)

        return progress

    def mark_vocabulary_completed(
        self,
        progress: StudentProgress,
    ) -> StudentProgress:
        progress.vocabulary_completed = True

        self.db.commit()
        self.db.refresh(progress)

        return progress