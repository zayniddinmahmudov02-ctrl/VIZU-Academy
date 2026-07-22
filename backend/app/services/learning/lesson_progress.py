from sqlalchemy.orm import Session

from app.models.student_progress import StudentProgress


class LessonProgressService:

    def __init__(self, db: Session):
        self.db = db

    def lesson_completed(
        self,
        user_id: str,
        lesson_id: str,
    ):

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

        return (
            progress.video_completed
            and progress.grammar_completed
            and progress.reading_completed
            and progress.listening_completed
            and progress.writing_completed
            and progress.speaking_completed
            and progress.quiz_completed
        )

    def update_completion(
        self,
        user_id: str,
        lesson_id: str,
    ):

        progress = (
            self.db.query(StudentProgress)
            .filter(
                StudentProgress.user_id == user_id,
                StudentProgress.lesson_id == lesson_id,
            )
            .first()
        )

        if not progress:
            return None

        progress.lesson_completed = self.lesson_completed(
            user_id,
            lesson_id,
        )

        self.db.commit()

        self.db.refresh(progress)

        return progress