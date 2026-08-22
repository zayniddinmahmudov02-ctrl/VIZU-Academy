"""Verifies QuizService.update()'s GRAMMAR-only publish cascade — the
backward-repair for the exact bug this whole fix addresses: a quiz
shown as published while some of its questions are still drafts.
Re-saving an already-published (or newly-published) GRAMMAR quiz
through the existing update endpoint publishes every straggler
question; other quiz types (LESSON/VOCABULARY) and an unpublished quiz
are left untouched. Uses stdlib unittest + MagicMock, no real DB."""

import unittest
from unittest.mock import MagicMock

from app.schemas.quiz import QuizUpdate
from app.services.quiz.service import QuizService


def make_quiz(quiz_type: str, is_published: bool):
    quiz = MagicMock()
    quiz.quiz_type = quiz_type
    quiz.is_published = is_published
    return quiz


class TestQuizServicePublishCascade(unittest.TestCase):
    def _service_with(self, quiz):
        db = MagicMock()
        service = QuizService(db)
        service.repository.get = MagicMock(return_value=quiz)
        service.repository.update = MagicMock(return_value=quiz)
        return service, db

    def test_publishing_a_grammar_quiz_cascades_to_its_questions(self):
        quiz = make_quiz("GRAMMAR", is_published=True)
        service, db = self._service_with(quiz)
        service.update("quiz-1", QuizUpdate(is_published=True))
        db.query.assert_called_once()
        # .update(...) is the actual bulk-flip call in the built query chain.
        db.query.return_value.filter.return_value.update.assert_called_once_with(
            {"is_published": True}, synchronize_session=False
        )
        db.commit.assert_called_once()

    def test_unpublished_grammar_quiz_does_not_cascade(self):
        quiz = make_quiz("GRAMMAR", is_published=False)
        service, db = self._service_with(quiz)
        service.update("quiz-1", QuizUpdate(title="renamed"))
        db.query.assert_not_called()

    def test_lesson_type_quiz_never_cascades(self):
        quiz = make_quiz("LESSON", is_published=True)
        service, db = self._service_with(quiz)
        service.update("quiz-1", QuizUpdate(is_published=True))
        db.query.assert_not_called()

    def test_vocabulary_type_quiz_never_cascades(self):
        quiz = make_quiz("VOCABULARY", is_published=True)
        service, db = self._service_with(quiz)
        service.update("quiz-1", QuizUpdate(is_published=True))
        db.query.assert_not_called()

    def test_missing_quiz_returns_none_without_error(self):
        service, db = self._service_with(None)
        result = service.update("missing", QuizUpdate(is_published=True))
        self.assertIsNone(result)
        db.query.assert_not_called()


if __name__ == "__main__":
    unittest.main()
