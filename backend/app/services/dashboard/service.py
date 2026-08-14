from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.certificate import Certificate
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.student_progress import StudentProgress
from app.services.lesson_scoring import LessonScoringService


class DashboardService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # ==================================================
    # Dashboard
    # ==================================================

    def get_dashboard(
        self,
        user_id: str,
    ):

        # ----------------------------------------------
        # Enrolled Courses
        # ----------------------------------------------

        enrolled_courses = (
            self.db.query(Enrollment)
            .filter(
                Enrollment.user_id == user_id,
            )
            .count()
        )

        # ----------------------------------------------
        # Completed Lessons
        # ----------------------------------------------

        completed_lessons = (
            self.db.query(StudentProgress)
            .filter(
                StudentProgress.user_id == user_id,
                StudentProgress.lesson_completed.is_(True),
            )
            .count()
        )

        # ----------------------------------------------
        # Completed Modules
        # ----------------------------------------------

        completed_modules = (
            self.db.query(StudentProgress)
            .filter(
                StudentProgress.user_id == user_id,
                StudentProgress.module_completed.is_(True),
            )
            .count()
        )

        # ----------------------------------------------
        # Completed Courses
        # ----------------------------------------------

        completed_courses = (
            self.db.query(StudentProgress)
            .filter(
                StudentProgress.user_id == user_id,
                StudentProgress.course_completed.is_(True),
            )
            .count()
        )

        # ----------------------------------------------
        # Certificates
        # ----------------------------------------------

        certificates = (
            self.db.query(Certificate)
            .filter(
                Certificate.user_id == user_id,
            )
            .count()
        )

        # ----------------------------------------------
        # Study Minutes
        # ----------------------------------------------

        study_minutes = (
            self.db.query(
                func.coalesce(
                    func.sum(
                        StudentProgress.study_minutes,
                    ),
                    0,
                )
            )
            .filter(
                StudentProgress.user_id == user_id,
            )
            .scalar()
        )

        # ----------------------------------------------
        # Experience
        # ----------------------------------------------

        experience = (
            self.db.query(
                func.coalesce(
                    func.sum(
                        StudentProgress.experience,
                    ),
                    0,
                )
            )
            .filter(
                StudentProgress.user_id == user_id,
            )
            .scalar()
        )

        # ----------------------------------------------
        # Overall Progress
        # ----------------------------------------------

        total_lessons = (
            self.db.query(Lesson)
            .count()
        )

        progress = 0

        if total_lessons:

            progress = round(
                (
                    completed_lessons
                    / total_lessons
                )
                * 100,
                1,
            )

        # ----------------------------------------------
        # Current Lesson
        # ----------------------------------------------

        current = (
            self.db.query(StudentProgress)
            .join(
                Lesson,
                Lesson.id == StudentProgress.lesson_id,
            )
            .join(
                Module,
                Module.id == Lesson.module_id,
            )
            .join(
                Course,
                Course.id == Module.course_id,
            )
            .filter(
                StudentProgress.user_id == user_id,
                StudentProgress.lesson_completed.is_(False),
            )
            .first()
        )

        current_course = None
        current_module = None
        current_lesson = None
        current_lesson_id = None
        current_lesson_score = None
        current_lesson_max_score = None

        if current:

            current_course = current.lesson.module.course.title
            current_module = current.lesson.module.title
            current_lesson = current.lesson.title
            current_lesson_id = str(current.lesson.id)

            lesson_score = LessonScoringService(self.db).compute(UUID(str(user_id)), current.lesson.id)
            current_lesson_score = lesson_score["total_score"]
            current_lesson_max_score = lesson_score["max_score"]

        # ----------------------------------------------
        # Vorbereitung
        # ----------------------------------------------

        vorbereitung = completed_courses > 0

        # ----------------------------------------------
        # Dashboard Response
        # ----------------------------------------------

        return {
            "enrolled_courses": enrolled_courses,
            "completed_lessons": completed_lessons,
            "completed_modules": completed_modules,
            "completed_courses": completed_courses,
            "study_minutes": study_minutes,
            "experience": experience,
            "certificates": certificates,
            "progress": progress,
            "current_course": current_course,
            "current_module": current_module,
            "current_lesson": current_lesson,
            "current_lesson_id": current_lesson_id,
            "current_lesson_score": current_lesson_score,
            "current_lesson_max_score": current_lesson_max_score,
            "vorbereitung": vorbereitung,
            "ai_teacher": True,
            "translator": True,
        }