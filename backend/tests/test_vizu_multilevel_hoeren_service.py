"""VIZU-Multilevel Hören: content integrity (5 Aufgaben x 4 questions,
5 points each = 100) and score -> level mapping. The DB-facing parts (audio
upload/streaming, autosave, grading, immutability) are verified end to end
against a real Postgres over HTTP."""

import copy
import unittest

from app.services.vizu_multilevel.hoeren_audio_service import AUFGABE_NUMBERS
from app.services.vizu_multilevel.hoeren_json_import_service import HoerenImportError, _parse, load_default
from app.services.vizu_multilevel.lesen_service import level_for_score


class TestHoerenJson(unittest.TestCase):
    def setUp(self):
        self.data = load_default()
        self.parsed = _parse(self.data)

    def test_five_aufgaben_four_questions_each_twenty_points(self):
        self.assertEqual(len(self.parsed), 5)
        self.assertTrue(all(len(a["questions"]) == 4 for a in self.parsed))
        self.assertEqual(self.data["max_score"], 100)
        self.assertTrue(all(q["points"] == 5 for a in self.parsed for q in a["questions"]))

    def test_test_numbers_run_1_to_20_in_aufgabe_order(self):
        self.assertEqual([q["order"] for a in self.parsed for q in a["questions"]], list(range(1, 21)))
        self.assertEqual([[q["order"] for q in a["questions"]] for a in self.parsed][2], [9, 10, 11, 12])

    def test_four_options_exactly_one_correct_multiple_choice(self):
        for a in self.parsed:
            for q in a["questions"]:
                self.assertEqual(q["type"], "MULTIPLE_CHOICE")
                self.assertEqual(len(q["options"]), 4)
                self.assertEqual(sum(1 for _, ok in q["options"] if ok), 1)

    def test_source_answers_preserved(self):
        keys = "".join(q["correct_answer"] for a in self.data["aufgaben"] for q in a["questions"])
        self.assertEqual(keys, "CBDACCCBBCCCBBBCBABC")

    def test_audio_scripts_are_stored_verbatim(self):
        self.assertTrue(self.parsed[0]["script"].startswith("Daniel ist 23 Jahre alt. Er wohnt jetzt in Berlin."))
        self.assertIn("Nach dem Unterricht findet kein zusätzlicher Test statt.", self.parsed[1]["script"])

    def test_five_audio_slots(self):
        self.assertEqual(AUFGABE_NUMBERS, (1, 2, 3, 4, 5))

    def test_invalid_datasets_rejected(self):
        for mutate in (
            lambda d: d["aufgaben"][0]["questions"][0].__setitem__("correct_answer", "E"),
            lambda d: d["aufgaben"][1]["questions"][0]["options"].pop(),
            lambda d: d["aufgaben"][2]["questions"][0].__setitem__("points", 2),
            lambda d: d["aufgaben"][3].__setitem__("order", 1),
            lambda d: d["aufgaben"][4].__setitem__("audio_script", ""),
        ):
            bad = copy.deepcopy(self.data)
            mutate(bad)
            with self.assertRaises(HoerenImportError):
                _parse(bad)


class TestHoerenScoreToLevel(unittest.TestCase):
    def test_hundred_point_scale_uses_the_percentage_thresholds(self):
        cases = {0: None, 15: None, 20: "A1", 35: "A1", 40: "A2", 55: "A2", 60: "B1", 70: "B1", 75: "B2", 85: "B2", 90: "C1", 100: "C1"}
        for score, level in cases.items():
            with self.subTest(score=score):
                self.assertEqual(level_for_score(score, 100), level)


class TestVizuMockHoerenSeed(unittest.TestCase):
    """app/scripts/seed_vizu_mock_hoeren.py — the production seed."""

    def test_seed_dataset_is_5_aufgaben_20_tests_80_options_100_points(self):
        from app.scripts.seed_vizu_mock_hoeren import DATASET

        parsed = _parse(DATASET)
        self.assertEqual(len(parsed), 5)
        self.assertEqual([len(a["questions"]) for a in parsed], [4] * 5)
        self.assertEqual(sum(len(q["options"]) for a in parsed for q in a["questions"]), 80)
        self.assertEqual(sum(q["points"] for a in parsed for q in a["questions"]), 100)
        self.assertEqual([q["order"] for a in parsed for q in a["questions"]], list(range(1, 21)))
        keys = "".join(q["correct_answer"] for a in DATASET["aufgaben"] for q in a["questions"])
        self.assertEqual(keys, "CBDACCCBBCCCBBBCBABC")
        self.assertTrue(parsed[0]["script"].startswith("Daniel ist 23 Jahre alt."))


if __name__ == "__main__":
    unittest.main()
