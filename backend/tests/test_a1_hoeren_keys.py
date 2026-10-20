"""A1 Hören key audit (app/scripts/a1_hoeren_keys*): data completeness and the
key planning against stand-in questions — pure logic, no database."""

import unittest
from datetime import datetime
from types import SimpleNamespace

from app.models.answer_key_review import REVIEW_NEEDS_REVIEW, REVIEW_VERIFIED
from app.scripts import a1_hoeren_keys as script
from app.scripts.a1_hoeren_keys_data import TASKS

T0 = datetime(2026, 1, 1)


def opt(text, n, ok=False):
    return SimpleNamespace(id=f"o{n}", option_text=text, is_correct=ok, order_index=n, created_at=T0)


def mcq(qid, text, options, order=1):
    return SimpleNamespace(id=qid, question=text, question_type="MULTIPLE_CHOICE", points=1, explanation=None, config=None,
                           order_index=order, created_at=T0, options=[opt(o, i) for i, o in enumerate(options, start=1)])


def gapq(qid, text, order=1, options=None):
    gaps = {g: ({"accepted": [], "options": options} if options else []) for g in __import__("re").findall(r"\[\[(\d+)\]\]", text)}
    return SimpleNamespace(id=qid, question="Ergänzen Sie.", question_type="GAP_FILL", points=1, explanation=None,
                           config={"text": text, "gaps": gaps, "case_sensitive": False, "pending": True}, order_index=order, created_at=T0, options=[])


class TestData(unittest.TestCase):
    def test_every_a1_hoeren_task_is_covered(self):
        expected = {f"vizu-a1-l{n:02d}-hoeren-01" for n in range(1, 15)} | {"vizu-a1-l10-hoeren-02", "vizu-a1-l12-hoeren-02"}
        self.assertEqual(set(TASKS), expected)

    def test_every_task_names_its_source(self):
        for cid, spec in TASKS.items():
            with self.subTest(cid):
                self.assertTrue(spec["evidence"].startswith("Geprüft:"))
                self.assertTrue(spec["keys"])
                for n in spec.get("review", {}):
                    self.assertTrue(1 <= n <= len(spec["keys"]))


class TestTimes(unittest.TestCase):
    def test_variants(self):
        self.assertEqual(script._time_variants("8"), ["8", "08", "8:00", "08:00", "8.00", "08.00"])
        self.assertEqual(script._time_variants("22:30"), ["22:30", "22.30"])


class TestPlan(unittest.TestCase):
    def test_choice_and_gap_keys_are_set_and_verified(self):
        lst = SimpleNamespace(questions=[mcq("q1", "Welcher Tag?", ["Sonntag", "Samstag"], 1), gapq("q2", "Es ist [[1]] und [[2]].", 2)])
        plan = script.plan_task(lst, {"evidence": "Geprüft: Test", "keys": ["Samstag", {"1": ["sonnig"], "2": ["warm"]}]})
        q1, q2 = plan["questions"]
        self.assertEqual([o["is_correct"] for o in q1["clean"]["options"]], [False, True])
        self.assertEqual(q2["clean"]["config"]["gaps"]["1"]["accepted"], ["sonnig"])
        self.assertNotIn("pending", q2["clean"]["config"])
        self.assertEqual({q1["status"], q2["status"]}, {REVIEW_VERIFIED})

    def test_review_note_marks_needs_review(self):
        lst = SimpleNamespace(questions=[mcq("q1", "Wer?", ["Alisa", "Alex"])])
        plan = script.plan_task(lst, {"evidence": "Geprüft: x", "keys": ["Alex"], "review": {1: "Audio unklar"}})
        self.assertEqual(plan["questions"][0]["status"], REVIEW_NEEDS_REVIEW)
        self.assertEqual(plan["questions"][0]["note"], "Audio unklar")

    def test_structure_mismatch_changes_nothing(self):
        lst = SimpleNamespace(questions=[mcq("q1", "Wer?", ["Alisa", "Alex"])])
        with self.assertRaises(ValueError):
            script.plan_task(lst, {"evidence": "Geprüft: x", "keys": ["Max"]})  # not an option
        with self.assertRaises(ValueError):
            script.plan_task(lst, {"evidence": "Geprüft: x", "keys": ["Alex", "Alex"]})  # question count
        gap_lst = SimpleNamespace(questions=[gapq("q", "[[1]] [[2]]")])
        with self.assertRaises(ValueError):
            script.plan_task(gap_lst, {"evidence": "Geprüft: x", "keys": [{"1": ["a"]}]})  # gap 2 missing

    def test_choice_gap_answer_must_be_an_option(self):
        lst = SimpleNamespace(questions=[gapq("q", "Es ist [[1]].", options=["sonnig", "kalt"])])
        with self.assertRaises(ValueError):
            script.plan_task(lst, {"evidence": "Geprüft: x", "keys": [{"1": ["warm"]}]})

    def test_text_fix_applies_to_gap_text(self):
        lst = SimpleNamespace(questions=[gapq("q", "Zum Frühstück esse ich [[1]].")])
        plan = script.plan_task(lst, {"evidence": "Geprüft: x", "keys": [{"1": ["Butter"]}],
                                      "text_fixes": {1: [("esse ich [[1]]", "nehme ich [[1]]")]}})
        self.assertEqual(plan["questions"][0]["clean"]["config"]["text"], "Zum Frühstück nehme ich [[1]].")

    def test_text_fix_is_applied_once(self):
        """A fix that extends a sentence keeps the old sentence as a prefix — a re-run must not add it again."""
        spec = {"evidence": "Geprüft: x", "keys": [{"1": ["8"]}], "text_fixes": {1: [("Am Mittag warm.", "Am Mittag warm. In Berlin 11 Grad.")]}}
        q = gapq("q", "In Berlin [[1]] Grad. Am Mittag warm.")
        first = script.plan_task(SimpleNamespace(questions=[q]), spec)["questions"][0]["clean"]["config"]["text"]
        q.config = {**q.config, "text": first}
        second = script.plan_task(SimpleNamespace(questions=[q]), spec)["questions"][0]["clean"]["config"]["text"]
        self.assertEqual(first, second)
        self.assertEqual(second.count("In Berlin 11 Grad."), 1)

    def test_track_plan_is_idempotent(self):
        from unittest.mock import patch

        done = SimpleNamespace(label="Audio von Alex", original_name="A1-14.2.mp3")
        with patch("app.services.lesson_skills.admin.track_audio_path", return_value="x"):
            self.assertEqual(script.plan_tracks(SimpleNamespace(audio_tracks=[done]), [("Audio von Alex", "A1-14.2.mp3")]), [])
            todo = script.plan_tracks(SimpleNamespace(audio_tracks=[]), [("Audio von Alex", "A1-14.2.mp3")])
        self.assertEqual([(lbl, f) for lbl, f, _ in todo], [("Audio von Alex", "A1-14.2.mp3")])

    def test_l14_has_two_separate_audios(self):
        spec = TASKS["vizu-a1-l14-hoeren-01"]
        self.assertEqual((spec["audio_parts"], spec["audio_label"], spec["audio_tracks"]),
                         (["A1-14.1.mp3"], "Audio von Alisa", [("Audio von Alex", "A1-14.2.mp3")]))

    def test_audio_name(self):
        self.assertEqual(script.audio_name(["A1-10.2.mp3"]), "A1-10.2.mp3")
        self.assertEqual(script.audio_name(["A1-14.1.mp3", "A1-14.2.mp3"]), "A1-14.mp3")


if __name__ == "__main__":
    unittest.main()
