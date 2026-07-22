from sqlalchemy.orm import Session

from app.models.lesson import Lesson
from app.models.student_progress import StudentProgress


class LessonFlowService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # ======================================
    # Lesson Status
    # ======================================

    def is_completed(
        self,
        progress: StudentProgress,
    ):

        return all(
            [
                progress.video_completed,
                progress.grammar_completed,
                progress.reading_completed,
                progress.listening_completed,
                progress.writing_completed,
                progress.speaking_completed,
                progress.quiz_completed,
            ]
        )

    # ======================================
    # Complete Lesson
    # ======================================

    def complete(
        self,
        progress: StudentProgress,
    ):

        progress.lesson_completed = self.is_completed(
            progress,
        )

        if progress.lesson_completed:

            progress.experience += 100

        self.db.commit()

        self.db.refresh(progress)

        return progress

    # ======================================
    # Unlock Next Lesson
    # ======================================

    def unlock_next(
        self,
        progress: StudentProgress,
    ):

        lesson = (
            self.db.query(Lesson)
            .filter(
                Lesson.id == progress.lesson_id,
            )
            .first()
        )

        if not lesson:
            return None

        next_lesson = (
            self.db.query(Lesson)
            .filter(
                Lesson.module_id == lesson.module_id,
                Lesson.number == lesson.number + 1,
            )
            .first()
        )

        if not next_lesson:
            return None

        next_progress = (
            self.db.query(StudentProgress)
            .filter(
                StudentProgress.user_id == progress.user_id,
                StudentProgress.lesson_id == next_lesson.id,
            )
            .first()
        )

        if next_progress:

            next_progress.unlocked = True

            self.db.commit()

            self.db.refresh(next_progress)

        return next_progress