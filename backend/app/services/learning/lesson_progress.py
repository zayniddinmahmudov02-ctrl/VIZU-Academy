from uuid import UUID

from sqlalchemy.orm import Session

from app.models.student_progress import StudentProgress
from app.services.lms import progress as lms_progress


class LessonProgressService:

    def __init__(self, db: Session):
        self.db = db

    def lesson_completed(
        self,
        user_id: str,
        lesson_id: str,
    ):
        # Delegates to the single canonical completion rule — the VIZU LMS
        # progress service (app.services.lms.progress), which decides from
        # the lesson's published, tracked competencies.
        progress = (
            self.db.query(StudentProgress)
            .filter(
                StudentProgress.user_id == user_id,
                StudentProgress.lesson_id == lesson_id,
            )
            .first()
        )

        if not progress:
            return False

        return lms_progress.is_lesson_completed(self.db, UUID(user_id), UUID(lesson_id))

    def update_completion(
        self,
        user_id: str,
        lesson_id: str,
    ):
        """Recompute and persist the lesson + competency snapshot; returns
        the StudentProgress row (None while the student has no activity)."""
        lms_progress.sync_lesson(self.db, UUID(str(user_id)), UUID(str(lesson_id)))
        return (
            self.db.query(StudentProgress)
            .filter(
                StudentProgress.user_id == user_id,
                StudentProgress.lesson_id == lesson_id,
            )
            .first()
        )


def refresh_lesson_completion(db: Session, user_id, lesson_id) -> None:
    """Persists the student's lesson progress (competency snapshot,
    StudentProgress.lesson_completed / completed_at / last_activity_at)
    right after any event that can change it — video finished, an exercise /
    test / Lesen / Hören attempt submitted, a teacher or the AI graded a
    Schreiben / Sprechen submission. The dashboard ("Weiter lernen"),
    sequential unlocking and the level overview read that snapshot."""
    LessonProgressService(db).update_completion(str(user_id), str(lesson_id))
