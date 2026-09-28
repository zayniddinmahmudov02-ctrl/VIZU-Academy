"""New 100-point lesson scoring (Video 10, Lesen 15, Hören 15,
Schreiben 20, Sprechen 20, Wortschatz 10, Yakuniy Test 10 — no
Grammatik) and the Schreiben/Sprechen "pending until a teacher grades"
rule. Pure-logic tests on the parts that need no DB; the DB-facing
queries are exercised through the shared helper with plain dicts."""

import unittest
from unittest.mock import MagicMock

from app.services.lesson_scoring import service as scoring
from app.services.lesson_scoring.service import LessonScoringService


class TestWeights(unittest.TestCase):
    def test_weights_match_the_new_distribution_and_sum_to_100(self):
        self.assertEqual(scoring.MAX_VIDEO, 10)
        self.assertEqual(scoring.MAX_LESEN, 15)
        self.assertEqual(scoring.MAX_HOEREN, 15)
        self.assertEqual(scoring.MAX_SCHREIBEN, 20)
        self.assertEqual(scoring.MAX_SPRECHEN, 20)
        self.assertEqual(scoring.MAX_WORTSCHATZ, 10)
        self.assertEqual(scoring.MAX_YAKUNIY_TEST, 10)
        self.assertEqual(scoring.MAX_TOTAL, 100)

    def test_grammar_is_gone(self):
        self.assertFalse(hasattr(scoring, "MAX_GRAMMATIK_QUIZ"))


class TestGradedTaskPercentage(unittest.TestCase):
    def setUp(self):
        self.service = LessonScoringService(db=MagicMock())

    def test_no_tasks_is_zero_and_final(self):
        self.assertEqual(self.service._graded_task_percentage({}, []), (0, "final"))

    def test_submitted_only_gives_no_points_and_is_pending(self):
        result = self.service._graded_task_percentage({"a": ("SUBMITTED", None)}, ["a"])
        self.assertEqual(result, (0, "pending"))

    def test_graded_uses_the_teacher_score(self):
        result = self.service._graded_task_percentage({"a": ("GRADED", 80)}, ["a"])
        self.assertEqual(result, (80, "final"))

    def test_mean_over_all_published_tasks_with_one_pending(self):
        result = self.service._graded_task_percentage(
            {"a": ("GRADED", 100), "b": ("SUBMITTED", None)}, ["a", "b"]
        )
        self.assertEqual(result, (50, "pending"))

    def test_needs_revision_and_untouched_tasks_are_zero_but_not_pending(self):
        result = self.service._graded_task_percentage({"a": ("NEEDS_REVISION", None)}, ["a", "b"])
        self.assertEqual(result, (0, "final"))

    def test_score_is_clamped_to_0_100(self):
        result = self.service._graded_task_percentage({"a": ("GRADED", 250)}, ["a"])
        self.assertEqual(result, (100, "final"))


if __name__ == "__main__":
    unittest.main()
