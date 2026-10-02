"""VIZU-Multilevel Lesen: score -> level thresholds, and the integrity of
the seeded content (5 texts x 4 questions, 5 points each = 100)."""

import copy
import unittest

from app.services.vizu_multilevel.lesen_json_import_service import LesenImportError, _parse, load_default
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


class TestLesenJson(unittest.TestCase):
    def setUp(self):
        self.data = load_default()
        self.parsed = _parse(self.data)

    def test_20_aufgaben_20_questions_100_points(self):
        self.assertEqual(len(self.parsed), 20)
        self.assertEqual(sum(len(a["questions"]) for a in self.parsed), 20)
        self.assertEqual(self.data["max_score"], 100)
        self.assertTrue(all(q["points"] == 5 for a in self.parsed for q in a["questions"]))

    def test_orders_are_1_to_20(self):
        self.assertEqual([a["order"] for a in self.parsed], list(range(1, 21)))
        self.assertEqual([q["order"] for a in self.parsed for q in a["questions"]], list(range(1, 21)))

    def test_four_options_and_exactly_one_correct(self):
        for a in self.parsed:
            for q in a["questions"]:
                self.assertEqual(len(q["options"]), 4)
                self.assertEqual(sum(1 for _, ok in q["options"] if ok), 1)

    def test_internal_levels_by_position(self):
        levels = [a["level"] for a in self.parsed]
        self.assertEqual(levels, ["A1"] * 4 + ["A2"] * 4 + ["B1"] * 4 + ["B2"] * 4 + ["C1"] * 4)

    def test_source_answers_preserved(self):
        keys = "".join(a["questions"][0]["correct_answer"] for a in self.data["aufgaben"])
        self.assertEqual(keys, "CBACBCBBBCBCCBCCACCC")

    def test_text_is_verbatim(self):
        self.assertTrue(self.parsed[0]["text"].startswith("Hallo! Ich heiße Maria. Ich bin 22 Jahre alt"))
        self.assertIn("Der Einsatz künstlicher Intelligenz", self.parsed[17]["text"])

    def test_invalid_datasets_are_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["aufgaben"][0]["questions"][0]["correct_answer"] = "E"
        with self.assertRaises(LesenImportError):
            _parse(bad)
        bad = copy.deepcopy(self.data)
        bad["aufgaben"][1]["questions"][0]["options"].pop()
        with self.assertRaises(LesenImportError):
            _parse(bad)
        bad = copy.deepcopy(self.data)
        bad["aufgaben"][2]["questions"][0]["points"] = 4
        with self.assertRaises(LesenImportError):
            _parse(bad)
        bad = copy.deepcopy(self.data)
        bad["aufgaben"][3]["order"] = 1  # duplicate order
        with self.assertRaises(LesenImportError):
            _parse(bad)


if __name__ == "__main__":
    unittest.main()
