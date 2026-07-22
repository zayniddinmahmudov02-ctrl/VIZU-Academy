from datetime import date
from datetime import timedelta

from sqlalchemy.orm import Session

from app.models.student_progress import StudentProgress


class DailyStreakService:

    BONUS_XP = 25

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def update(
        self,
        progress: StudentProgress,
    ):

        today = date.today()

        if progress.last_activity is None:

            progress.last_activity = today
            progress.streak = 1

        else:

            diff = (
                today -
                progress.last_activity
            ).days

            if diff == 0:

                return progress

            if diff == 1:

                progress.streak += 1

            else:

                progress.streak = 1

            progress.last_activity = today

        progress.total_score += self.BONUS_XP

        self.db.commit()

        self.db.refresh(progress)

        return progress

    def reset(
        self,
        progress: StudentProgress,
    ):

        progress.streak = 0

        self.db.commit()

        self.db.refresh(progress)

        return progress

    def current(
        self,
        progress: StudentProgress,
    ):

        return progress.streak