from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.exam import Exam


class VorbereitungService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # =====================================
    # Unlock Vorbereitung
    # =====================================

    def unlock(
        self,
        course_id: str,
    ):

        course = (
            self.db.query(Course)
            .filter(
                Course.id == course_id,
            )
            .first()
        )

        if not course:
            return None

        if not course.completed:
            return None

        exams = (
            self.db.query(Exam)
            .filter(
                Exam.level == course.level,
            )
            .all()
        )

        return exams