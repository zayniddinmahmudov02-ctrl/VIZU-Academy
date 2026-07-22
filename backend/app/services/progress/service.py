from sqlalchemy.orm import Session

from app.models.student_progress import StudentProgress


class ProgressService:

    def __init__(self, db: Session):
        self.db = db

    def get_progress(
        self,
        user_id: str,
    ):

        progress = (
            self.db.query(StudentProgress)
            .filter(
                StudentProgress.user_id == user_id
            )
            .all()
        )

        total = len(progress)

        completed = len(
            [
                p
                for p in progress
                if p.lesson_completed
            ]
        )

        percent = 0

        if total:

            percent = round(
                completed * 100 / total,
                1,
            )

        return {
            "total": total,
            "completed": completed,
            "percent": percent,
        }