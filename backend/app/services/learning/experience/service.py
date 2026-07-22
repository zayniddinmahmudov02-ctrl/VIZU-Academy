from sqlalchemy.orm import Session

from app.models.student_progress import StudentProgress


class ExperienceService:

    XP = {
        "video": 10,
        "grammar": 10,
        "vocabulary": 10,
        "reading": 20,
        "listening": 20,
        "writing": 30,
        "speaking": 30,
        "quiz": 20,
        "homework": 20,
        "lesson": 50,
        "module": 100,
        "course": 300,
    }

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def add(
        self,
        progress: StudentProgress,
        activity: str,
    ):

        amount = self.XP.get(
            activity,
            0,
        )

        progress.total_score += amount

        self.db.commit()

        self.db.refresh(progress)

        return progress

    def remove(
        self,
        progress: StudentProgress,
        activity: str,
    ):

        amount = self.XP.get(
            activity,
            0,
        )

        progress.total_score = max(
            0,
            progress.total_score - amount,
        )

        self.db.commit()

        self.db.refresh(progress)

        return progress

    def current(
        self,
        progress: StudentProgress,
    ):

        return progress.total_score