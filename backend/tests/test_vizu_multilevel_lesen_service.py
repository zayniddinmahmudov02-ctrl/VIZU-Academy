"""VIZU-Multilevel Lesen: score -> level thresholds, and the integrity of
the seeded content (5 texts x 4 questions, 5 points each = 100)."""

import unittest

from app.scripts.seed_vizu_multilevel_lesen import POINTS_PER_QUESTION, TEXTS
from app.services.vizu_multilevel.lesen_service import level_for_score


class TestLevelThresholds(unittest.TestCase):
    def test_boundaries(self):
        cases = {
            0: None,
            19: None,
            20: "A1",
            39: "A1",
            40: "A2",
            59: "A2",
            60: "B1",
            74: "B1",
            75: "B2",
            89: "B2",
            90: "C1",
            100: "C1",
        }
        for score, expected in cases.items():
            with self.subTest(score=score):
                self.assertEqual(level_for_score(score, 100), expected)

    def test_score_is_five_points_per_correct_answer(self):
        # 20 correct = 100, 18 = 90, 16 = 80, 14 = 70, 12 = 60, 10 = 50
        self.assertEqual([n * 5 for n in (20, 18, 16, 14, 12, 10)], [100, 90, 80, 70, 60, 50])
        self.assertEqual(level_for_score(18 * 5, 100), "C1")
        self.assertEqual(level_for_score(16 * 5, 100), "B2")
        self.assertEqual(level_for_score(14 * 5, 100), "B1")
        self.assertEqual(level_for_score(10 * 5, 100), "A2")

    def test_no_content_never_yields_a_level(self):
        self.assertIsNone(level_for_score(0, 0))

    def test_threshold_scales_with_a_different_max(self):
        # Normalised to a percentage if an admin deactivates a question.
        self.assertEqual(level_for_score(95, 95), "C1")
        self.assertIsNone(level_for_score(0, 95))


class TestSeedContent(unittest.TestCase):
    def test_five_texts_levels_in_order(self):
        self.assertEqual([t["level"] for t in TEXTS], ["A1", "A2", "B1", "B2", "C1"])
        self.assertEqual([t["order"] for t in TEXTS], [1, 2, 3, 4, 5])

    def test_each_text_has_four_questions_twenty_in_total(self):
        self.assertTrue(all(len(t["questions"]) == 4 for t in TEXTS))
        self.assertEqual(sum(len(t["questions"]) for t in TEXTS), 20)

    def test_max_score_is_100(self):
        self.assertEqual(POINTS_PER_QUESTION, 5)
        self.assertEqual(sum(len(t["questions"]) for t in TEXTS) * POINTS_PER_QUESTION, 100)

    def test_every_question_has_exactly_one_valid_correct_option(self):
        for text in TEXTS:
            for item in text["questions"]:
                with self.subTest(prompt=item["prompt"]):
                    self.assertGreaterEqual(len(item["options"]), 2)
                    self.assertIn(item["correct"], range(len(item["options"])))
                    self.assertEqual(len(set(item["options"])), len(item["options"]))

    def test_question_formats_vary_within_a_level(self):
        for text in TEXTS:
            types = {item["type"] for item in text["questions"]}
            self.assertGreaterEqual(len(types), 3, text["level"])

    def test_texts_are_not_trivially_short(self):
        for text in TEXTS:
            self.assertGreater(len(text["passage"].split()), 40, text["level"])


if __name__ == "__main__":
    unittest.main()
