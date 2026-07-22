from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.certificate import Certificate
from app.models.student_progress import StudentProgress


class DashboardStatisticsService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # =====================================
    # Dashboard Statistics
    # =====================================

    def overview(
        self,
        user_id: str,
    ):

        total_courses = (
            self.db.query(Course)
            .count()
        )

        completed_lessons = (
            self.db.query(StudentProgress)
            .filter(
                StudentProgress.user_id == user_id,
                StudentProgress.lesson_completed.is_(True),
            )
            .count()
        )

        total_minutes = (
            self.db.query(StudentProgress)
            .filter(
                StudentProgress.user_id == user_id,
            )
            .with_entities(
                StudentProgress.study_minutes,
            )
            .all()
        )

        study_minutes = sum(
            minute[0]
            for minute in total_minutes
        )

        certificates = (
            self.db.query(Certificate)
            .filter(
                Certificate.user_id == user_id,
            )
            .count()
        )

        total_xp = (
            self.db.query(StudentProgress)
            .filter(
                StudentProgress.user_id == user_id,
            )
            .with_entities(
                StudentProgress.experience,
            )
            .all()
        )

        experience = sum(
            xp[0]
            for xp in total_xp
        )

        return {
            "courses": total_courses,
            "completed_lessons": completed_lessons,
            "study_minutes": study_minutes,
            "certificates": certificates,
            "experience": experience,
        }