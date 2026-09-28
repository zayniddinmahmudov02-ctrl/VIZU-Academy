from uuid import UUID

from sqlalchemy.orm import Session

from app.models.student_progress import StudentProgress
from app.services.lesson_progress.section_gate import SectionGateService


class LessonProgressService:

    def __init__(self, db: Session):
        self.db = db

    def lesson_completed(
        self,
        user_id: str,
        lesson_id: str,
    ):
        # Delegates to the single canonical, content-aware completion
        # check (SectionGateService) — see LessonFlowService.is_completed
        # for the same consolidation, fixing the previous duplicate
        # fixed-flag-list logic that lived independently in both places.
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

        return SectionGateService(self.db).is_lesson_completed(UUID(user_id), UUID(lesson_id))

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


def refresh_lesson_completion(db: Session, user_id, lesson_id) -> None:
    """Persists StudentProgress.lesson_completed from the canonical
    SectionGateService check, right after any event that can change it
    (video finished, Wortschatz Test / Yakuniy Test submitted, a teacher
    graded a Schreiben/Sprechen submission). Nothing else ever wrote that
    flag, although the dashboard ("Weiter lernen"), lesson progress,
    unlocking and course completion all read it. A student with no
    progress row yet is left alone (update_completion returns None)."""
    LessonProgressService(db).update_completion(str(user_id), str(lesson_id))
