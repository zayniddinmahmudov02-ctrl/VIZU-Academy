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
    # Current lesson ("Weiter lernen")
    # ==================================================

    def _find_current_lesson(self, user_id: str) -> Lesson | None:
        """The lesson the student is actually working on right now.

        Was: the first StudentProgress row (any lesson, any order) with
        lesson_completed=False and NO ordering at all — `.first()` on an
        unordered query returns whatever row the database happens to
        scan first, unrelated to what the student is actually working
        on. That's the real bug behind "Weiter lernen" showing an
        unrelated module/lesson (e.g. a module title instead of the
        actual current lesson's title).

        Now, in priority order:
          1. The most recently touched (updated_at DESC) incomplete
             lesson — "oxirgi ishlangan/aktiv dars": if the student
             started a lesson, this is exactly that lesson, every time,
             until it's completed.
          2. Once there's no incomplete lesson left to resume (nothing
             started yet, or everything touched so far is completed),
             the first lesson in the real curriculum order (course/
             module order_index, then lesson number) that this student
             has no StudentProgress row for at all — the next lesson to
             start, or A1 lesson 1 for a brand-new student with zero
             progress (no row anywhere).

        Both branches reuse the exact same StudentProgress/Lesson/
        Module/Course tables this endpoint already queried — no parallel
        progress system.
        """

        in_progress = (
            self.db.query(Lesson)
            .join(
                StudentProgress,
                StudentProgress.lesson_id == Lesson.id,
            )
            .filter(
                StudentProgress.user_id == user_id,
                StudentProgress.lesson_completed.is_(False),
            )
            .order_by(StudentProgress.updated_at.desc())
            .first()
        )
        if in_progress is not None:
            return in_progress

        return (
            self.db.query(Lesson)
            .join(
                Module,
                Module.id == Lesson.module_id,
            )
            .join(
                Course,
                Course.id == Module.course_id,
            )
            .outerjoin(
                StudentProgress,
                (StudentProgress.lesson_id == Lesson.id)
                & (StudentProgress.user_id == user_id),
            )
            .filter(StudentProgress.id.is_(None))
            .order_by(
                Course.order_index.asc(),
                Module.order_index.asc(),
                Lesson.number.asc(),
            )
            .first()
        )

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
        # Current Lesson — the "Weiter lernen" dashboard card's single
        # source of truth for which lesson to show. See
        # _find_current_lesson's own docstring for what changed and why.
        # ----------------------------------------------

        current_lesson_row = self._find_current_lesson(user_id)

        current_course = None
        current_module = None
        current_lesson = None
        current_lesson_id = None
        current_lesson_number = None
        current_lesson_score = None
        current_lesson_max_score = None

        if current_lesson_row:

            current_course = current_lesson_row.module.course.title
            current_module = current_lesson_row.module.title
            current_lesson = current_lesson_row.title
            current_lesson_id = str(current_lesson_row.id)
            current_lesson_number = current_lesson_row.number

            lesson_score = LessonScoringService(self.db).compute(UUID(str(user_id)), current_lesson_row.id)
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
            "current_lesson_number": current_lesson_number,
            "current_lesson_score": current_lesson_score,
            "current_lesson_max_score": current_lesson_max_score,
            "vorbereitung": vorbereitung,
            "ai_teacher": True,
            "translator": True,
        }