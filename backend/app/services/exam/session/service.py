from sqlalchemy.orm import Session

from app.models.exam import Exam
from app.models.exam_session import ExamSession


class ExamSessionService:

    def __init__(self, db: Session):
        self.db = db

    def start_exam(
        self,
        user_id: str,
        exam_id: str,
    ):

        exam = (
            self.db.query(Exam)
            .filter(Exam.id == exam_id)
            .first()
        )

        if not exam:
            return None

        session = ExamSession(
            user_id=user_id,
            exam_id=exam_id,
            status="started",
            score=0,
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def finish_exam(
        self,
        session_id: str,
        score: int,
    ):

        session = (
            self.db.query(ExamSession)
            .filter(
                ExamSession.id == session_id
            )
            .first()
        )

        if not session:
            return None

        session.score = score
        session.status = "finished"

        self.db.commit()
        self.db.refresh(session)

        return session