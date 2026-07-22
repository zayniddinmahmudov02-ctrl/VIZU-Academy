from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enrollment import Enrollment


class ExamPreparationService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def unlock(
        self,
        user_id: str,
        course_id: str,
    ):

        enrollment = (
            self.db.query(Enrollment)
            .filter(
                Enrollment.user_id == user_id,
                Enrollment.course_id == course_id,
            )
            .first()
        )

        if not enrollment:
            return None

        if enrollment.progress < 100:
            return None

        enrollment.exam_preparation_unlocked = True

        self.db.commit()

        self.db.refresh(enrollment)

        return enrollment