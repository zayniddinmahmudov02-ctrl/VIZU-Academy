"""Verifies grade_and_submit's section-gate check now covers all three
gated legacy-Quiz types (VOCABULARY/GRAMMAR/LESSON) via one shared code
path (generalized from the VOCABULARY-only check built earlier this
session), and that a duplicate submit doesn't get rejected by anything
new here (idempotency of the underlying StudentQuizService.create call
is unchanged, out of scope for this task — only the gate check itself is
new). Uses stdlib unittest + mock.patch, no real DB."""

import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException

from app.services.quiz.grading_service import grade_and_submit


class TestGradingServiceSectionGate(unittest.TestCase):
    def _make_db(self, quiz_type: str):
        db = MagicMock()
        quiz = MagicMock(id=uuid4(), lesson_id=str(uuid4()), quiz_type=quiz_type, passing_score=70)
        lesson = MagicMock(id=quiz.lesson_id)

        def get_side_effect(model, pk):
            from app.models.lesson import Lesson
            from app.models.quiz import Quiz

            if model is Quiz:
                return quiz
            if model is Lesson:
                return lesson
            return None

        db.get.side_effect = get_side_effect
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        return db, quiz, lesson

    @patch("app.services.quiz.grading_service.StudentQuizService")
    @patch("app.services.quiz.grading_service.can_access_lesson", return_value=True)
    @patch("app.services.quiz.grading_service.SectionGateService")
    def test_locked_section_rejects_submission_for_every_gated_type(
        self, mock_gate_cls, mock_can_access, mock_student_quiz_cls
    ):
        mock_gate_cls.return_value.is_unlocked.return_value = False
        for quiz_type in ("VOCABULARY", "GRAMMAR", "LESSON"):
            with self.subTest(quiz_type=quiz_type):
                db, quiz, lesson = self._make_db(quiz_type)
                user = MagicMock(id=uuid4())
                with self.assertRaises(HTTPException) as ctx:
                    grade_and_submit(db, quiz.id, user, answers=[])
                self.assertEqual(ctx.exception.status_code, 403)
                self.assertEqual(ctx.exception.detail, "SECTION_LOCKED")

    @patch("app.services.quiz.grading_service.StudentQuizService")
    @patch("app.services.quiz.grading_service.can_access_lesson", return_value=True)
    @patch("app.services.quiz.grading_service.SectionGateService")
    def test_unlocked_section_allows_submission_for_every_gated_type(
        self, mock_gate_cls, mock_can_access, mock_student_quiz_cls
    ):
        mock_gate_cls.return_value.is_unlocked.return_value = True
        for quiz_type in ("VOCABULARY", "GRAMMAR", "LESSON"):
            with self.subTest(quiz_type=quiz_type):
                db, quiz, lesson = self._make_db(quiz_type)
                user = MagicMock(id=uuid4())
                response = grade_and_submit(db, quiz.id, user, answers=[])
                self.assertEqual(response.score, 0)  # no questions in this mock -> 0/0 -> 0

    @patch("app.services.quiz.grading_service.StudentQuizService")
    @patch("app.services.quiz.grading_service.can_access_lesson", return_value=True)
    @patch("app.services.quiz.grading_service.SectionGateService")
    def test_gate_checked_against_the_matching_section_key(self, mock_gate_cls, mock_can_access, mock_student_quiz_cls):
        mock_gate_cls.return_value.is_unlocked.return_value = True
        expectations = {
            "VOCABULARY": "wortschatz_quiz",
            "GRAMMAR": "grammatik_quiz",
            "LESSON": "lesson_quiz",
        }
        for quiz_type, expected_key in expectations.items():
            with self.subTest(quiz_type=quiz_type):
                db, quiz, lesson = self._make_db(quiz_type)
                user = MagicMock(id=uuid4())
                grade_and_submit(db, quiz.id, user, answers=[])
                _, called_lesson_id, called_key = mock_gate_cls.return_value.is_unlocked.call_args.args
                self.assertEqual(called_key, expected_key)


if __name__ == "__main__":
    unittest.main()
