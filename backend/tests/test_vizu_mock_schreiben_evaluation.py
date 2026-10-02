"""VIZU-Mock Schreiben: the server-side guarantees of the AI evaluation —
invented errors are dropped, scores are clamped and summed
deterministically, and the 5-task / 100-point content is exact."""

import unittest
from types import SimpleNamespace

from app.scripts.seed_vizu_mock_schreiben import POINTS_PER_TASK, TASKS
from app.services.vizu_multilevel.schreiben_evaluation_service import (
    DONE,
    FAILED,
    PENDING,
    RUNNING,
    confirm_errors,
    evaluation_status,
    score_criteria,
    verify_errors,
)

TEXT = "Hallo Anna! Ich habe am Samstag Zeit. Wir konnen uns im Park treffen und Eis essen."


class TestVerifyErrors(unittest.TestCase):
    def test_keeps_only_errors_that_really_occur_in_the_text(self):
        raw = [
            {"original": "Wir konnen", "correction": "Wir können", "explanation": "Umlaut", "category": "rechtschreibung"},
            {"original": "Ich gehe gestern", "correction": "Ich ging gestern", "explanation": "erfunden", "category": "grammatik"},
        ]
        kept = verify_errors(TEXT, raw)
        self.assertEqual([e["original"] for e in kept], ["Wir konnen"])

    def test_drops_non_corrections_duplicates_and_garbage(self):
        raw = [
            {"original": "im Park", "correction": "im Park", "explanation": "keine Änderung"},
            {"original": "Wir konnen", "correction": "Wir können"},
            {"original": "Wir konnen", "correction": "Wir können"},
            "kein Objekt",
            {"original": "", "correction": "x"},
        ]
        self.assertEqual(len(verify_errors(TEXT, raw)), 1)

    def test_whitespace_differences_are_tolerated(self):
        kept = verify_errors("Ich  habe\\nam Samstag Zeit.".replace("\\\\n", "\\n"), [{"original": "Ich habe", "correction": "Ich hab"}])
        self.assertEqual(len(kept), 1)

    def test_not_a_list_yields_no_errors(self):
        self.assertEqual(verify_errors(TEXT, None), [])

    def test_overlapping_quotes_of_the_same_spot_are_merged(self):
        raw = [
            {"original": "Wir konnen", "correction": "Wir können"},
            {"original": "konnen", "correction": "können"},
            {"original": "Wir konnen uns", "correction": "Wir können uns"},
        ]
        self.assertEqual([e["original"] for e in verify_errors(TEXT, raw)], ["Wir konnen"])


class TestConfirmErrors(unittest.TestCase):
    errors = [{"original": "a"}, {"original": "b"}, {"original": "c"}]

    def test_keeps_only_confirmed_numbers(self):
        self.assertEqual([e["original"] for e in confirm_errors(self.errors, [1, "3"])], ["a", "c"])

    def test_malformed_verdict_confirms_nothing(self):
        self.assertEqual(confirm_errors(self.errors, None), [])
        self.assertEqual(confirm_errors(self.errors, ["x", 9]), [])


def rubric(*pairs):
    return [SimpleNamespace(id=i, name=n, max_score=m) for i, (n, m) in enumerate(pairs)]


class TestScoreCriteria(unittest.TestCase):
    def test_scores_are_clamped_to_each_criterion_and_total_never_exceeds_20(self):
        criteria = rubric(("Aufgabenbearbeitung", 6), ("Wortschatz", 4), ("Grammatik", 4), ("Verständlichkeit", 3), ("Rechtschreibung", 3))
        ai = [
            {"name": "Aufgabenbearbeitung", "score": 9},
            {"name": "wortschatz", "score": 3.6},
            {"name": "Grammatik", "score": -2},
            {"name": "Verständlichkeit", "score": "3"},
            {"name": "Rechtschreibung", "score": 100},
        ]
        scored = score_criteria(criteria, ai)
        self.assertEqual([c["score"] for c in scored], [6, 4, 0, 3, 3])
        self.assertLessEqual(sum(c["score"] for c in scored), 20)

    def test_missing_criterion_gets_zero_not_a_guess(self):
        scored = score_criteria(rubric(("Grammatik", 4), ("Wortschatz", 4)), [{"name": "Grammatik", "score": 3}])
        self.assertEqual([c["score"] for c in scored], [3, 0])

    def test_same_input_same_result(self):
        criteria = rubric(("Grammatik", 4))
        ai = [{"name": "Grammatik", "score": 2.5}]
        self.assertEqual(score_criteria(criteria, ai), score_criteria(criteria, ai))


class TestStatus(unittest.TestCase):
    def test_status_aggregation(self):
        sub = lambda s: SimpleNamespace(evaluation_status=s)  # noqa: E731
        self.assertEqual(evaluation_status([sub(DONE)] * 5), DONE)
        self.assertEqual(evaluation_status([sub(DONE), sub(RUNNING)]), PENDING)
        self.assertEqual(evaluation_status([sub(DONE), sub(FAILED)]), FAILED)
        self.assertEqual(evaluation_status([sub(FAILED), sub(PENDING)]), PENDING)


class TestSchreibenContent(unittest.TestCase):
    def test_five_tasks_twenty_points_each_hundred_total(self):
        self.assertEqual([t["order"] for t in TASKS], [1, 2, 3, 4, 5])
        self.assertTrue(all(sum(m for _, m in t["rubric"]) == POINTS_PER_TASK == 20 for t in TASKS))
        self.assertEqual(len(TASKS) * POINTS_PER_TASK, 100)

    def test_word_limits_and_titles(self):
        self.assertEqual([(t["min_words"], t["max_words"]) for t in TASKS], [(30, 40), (50, 70), (80, 100), (120, 150), (180, 220)])
        self.assertEqual(TASKS[3]["title"], "Beitrag für ein Online-Forum")

    def test_rubrics_match_the_specification(self):
        self.assertEqual(TASKS[0]["rubric"][0], ("Aufgabenbearbeitung", 6))
        self.assertEqual(TASKS[4]["rubric"][3], ("Textaufbau, Kohärenz und Verknüpfungen", 4))


if __name__ == "__main__":
    unittest.main()
