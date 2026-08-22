from uuid import UUID

from sqlalchemy.orm import Session

from app.models.lesson import Lesson
from app.models.student_progress import StudentProgress
from app.services.lesson_progress.section_gate import SectionGateService


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
        # Delegates to the single canonical, content-aware completion
        # check (SectionGateService) instead of re-deriving it from a
        # fixed flag list — a lesson missing a section type is no longer
        # incorrectly required to have it, and this stays in sync with
        # section_gate.py automatically instead of drifting.
        return SectionGateService(self.db).is_lesson_completed(
            UUID(progress.user_id),
            UUID(progress.lesson_id),
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