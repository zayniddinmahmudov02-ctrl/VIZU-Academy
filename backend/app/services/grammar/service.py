from sqlalchemy.orm import Session

from app.repositories.grammar import GrammarRepository
from app.schemas.grammar import (
    GrammarCreate,
    GrammarUpdate,
)


class GrammarService:

    def __init__(self, db: Session):
        self.repository = GrammarRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def get(self, grammar_id: str):
        return self.repository.get(grammar_id)

    def get_by_lesson(self, lesson_id: str, published_only: bool = False):
        return self.repository.get_by_lesson(lesson_id, published_only=published_only)

    def create(self, data: GrammarCreate):
        return self.repository.create(data)

    def update(
        self,
        grammar_id: str,
        data: GrammarUpdate,
    ):
        grammar = self.repository.get(grammar_id)

        if not grammar:
            return None

        return self.repository.update(grammar, data)

    def delete(self, grammar_id: str):
        grammar = self.repository.get(grammar_id)

        if not grammar:
            return False

        self.repository.delete(grammar)

        return True