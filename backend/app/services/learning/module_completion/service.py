from sqlalchemy.orm import Session

from app.models.lesson import Lesson
from app.models.module import Module
from app.models.student_progress import StudentProgress

from app.services.learning.experience import (
    ExperienceService,
)


class ModuleCompletionService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

        self.experience = ExperienceService(db)

    def complete(
        self,
        module_id: str,
        user_id: str,
    ):

        lessons = (
            self.db.query(Lesson)
            .filter(
                Lesson.module_id == module_id,
            )
            .all()
        )

        if not lessons:
            return None

        completed = (
            self.db.query(StudentProgress)
            .filter(
                StudentProgress.user_id == user_id,
                StudentProgress.module_id == module_id,
                StudentProgress.lesson_completed == True,
            )
            .count()
        )

        if completed != len(lessons):
            return None

        module = (
            self.db.query(Module)
            .filter(
                Module.id == module_id,
            )
            .first()
        )

        if not module:
            return None

        module.completed = True

        progress = (
            self.db.query(StudentProgress)
            .filter(
                StudentProgress.user_id == user_id,
                StudentProgress.module_id == module_id,
            )
            .first()
        )

        if progress:
            self.experience.add(
                progress,
                "module",
            )

        self.db.commit()

        self.unlock_next(
            module,
        )

        return module

    def unlock_next(
        self,
        module: Module,
    ):

        next_module = (
            self.db.query(Module)
            .filter(
                Module.course_id == module.course_id,
                Module.number == module.number + 1,
            )
            .first()
        )

        if next_module:

            next_module.locked = False

            self.db.commit()