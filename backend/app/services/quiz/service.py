from sqlalchemy.orm import Session

from app.models.quiz import QUIZ_TYPE_GRAMMAR
from app.models.quiz_question import QuizQuestion
from app.repositories.quiz import QuizRepository

from app.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
)


class QuizService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = QuizRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def get(self, quiz_id: str):
        return self.repository.get(quiz_id)

    def create(
        self,
        data: QuizCreate,
    ):
        return self.repository.create(data)

    def update(
        self,
        quiz_id: str,
        data: QuizUpdate,
    ):
        quiz = self.repository.get(quiz_id)

        if not quiz:
            return None

        updated = self.repository.update(
            quiz,
            data,
        )

        # GRAMMAR only, and only when the quiz ends up published: repairs
        # the exact bug class this was built for — a quiz shown as
        # "Veröffentlicht" while some of its questions are still drafts
        # (e.g. generated before questions defaulted to published, or
        # added manually and never individually published). Re-saving
        # an already-published quiz through this same endpoint is what
        # an admin already does to "fix" a quiz, so no new UI/endpoint
        # is needed — just makes that action complete. Idempotent: only
        # ever flips rows that are still draft.
        if updated.quiz_type == QUIZ_TYPE_GRAMMAR and updated.is_published:
            self._publish_all_questions(updated)

        return updated

    def _publish_all_questions(self, quiz) -> None:
        self.db.query(QuizQuestion).filter(
            QuizQuestion.quiz_id == quiz.id,
            QuizQuestion.is_published.is_(False),
        ).update({"is_published": True}, synchronize_session=False)
        self.db.commit()

    def delete(
        self,
        quiz_id: str,
    ):
        quiz = self.repository.get(quiz_id)

        if not quiz:
            return False

        self.repository.delete(quiz)

        return True