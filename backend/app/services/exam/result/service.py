from sqlalchemy.orm import Session

from app.models.exam_session import ExamSession


class ExamResultService:

    def __init__(self, db: Session):
        self.db = db

    def get_result(
        self,
        session_id: str,
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

        return {
            "session_id": str(session.id),
            "user_id": str(session.user_id),
            "exam_id": str(session.exam_id),
            "score": session.score,
            "status": session.status,
            "passed": session.score >= 60,
        }