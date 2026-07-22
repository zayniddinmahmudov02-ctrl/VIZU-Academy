from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.student_progress import StudentProgress

from app.services.learning.experience import (
    ExperienceService,
)


class CourseCompletionService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.experience = ExperienceService(db)

    # =====================================
    # Complete Course
    # =====================================

    def complete(
        self,
        course_id: str,
        user_id: str,
    ):

        modules = (
            self.db.query(Module)
            .filter(
                Module.course_id == course_id,
            )
            .all()
        )

        if not modules:
            return None

        for module in modules:

            lessons = (
                self.db.query(Lesson)
                .filter(
                    Lesson.module_id == module.id,
                )
                .all()
            )

            lesson_ids = [
                lesson.id
                for lesson in lessons
            ]

            completed = (
                self.db.query(StudentProgress)
                .filter(
                    StudentProgress.user_id == user_id,
                    StudentProgress.lesson_id.in_(lesson_ids),
                    StudentProgress.lesson_completed.is_(True),
                )
                .count()
            )

            if completed != len(lesson_ids):
                return None

        course = (
            self.db.query(Course)
            .filter(
                Course.id == course_id,
            )
            .first()
        )

        if not course:
            return None

        course.completed = True

        self.db.commit()

        self.db.refresh(course)

        return course