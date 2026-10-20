"""A2 key audit (app/scripts/a2_keys*): data completeness, option-label fixes,
and the A1 / A2 rule that a Hören task is published only with verified keys
— pure logic, no database."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.models.answer_key_review import REVIEW_NEEDS_REVIEW, REVIEW_VERIFIED
from app.scripts import a1_hoeren_keys as planner
from app.scripts.a2_keys_data import HOEREN, LESEN
from tests.test_a1_hoeren_keys import gapq, mcq


class TestData(unittest.TestCase):
    def test_every_hoeren_entry_names_its_source(self):
        for cid, spec in HOEREN.items():
            with self.subTest(cid):
                self.assertTrue(cid.startswith("vizu-a2-l"))
                self.assertTrue(spec["keys"])
                review = spec.get("review", {})
                # verified keys name their check; a task left for the admin says why per question
                self.assertTrue(spec["evidence"].startswith("Geprüft") or len(review) == len(spec["keys"]))
                for n in list(review) + list(spec.get("option_fixes", {})):
                    self.assertTrue(1 <= n <= len(spec["keys"]))
                for note in review.values():
                    self.assertTrue(note.startswith("Prüfung nötig"))

    def test_l5_drops_the_two_imported_lesen_questions_and_fixes_munich(self):
        spec = HOEREN["vizu-a2-l05-hoeren-01"]
        self.assertEqual(len(spec["remove_questions"]), 2)
        self.assertEqual(len(spec["keys"]), 8)
        self.assertEqual(spec["keys"][3], "1500–2100 Euro")

    def test_l13_has_no_key_without_its_audio(self):
        # the delivered "A2 13.Unterricht" files are byte-identical to lesson 12 — nothing can be checked
        self.assertFalse([cid for cid in HOEREN if cid.startswith("vizu-a2-l13-")])

    def test_every_a2_lesen_text_is_covered_with_its_question_count(self):
        self.assertEqual(len(LESEN), 33)
        for cid, spec in LESEN.items():
            with self.subTest(cid):
                self.assertTrue(cid.startswith("vizu-a2-l") and "-lesen-" in cid)
                self.assertGreaterEqual(spec["questions"], 1)
                self.assertTrue(spec["evidence"].startswith("Geprüft"))


class TestOptionFix(unittest.TestCase):
    def test_label_contradicting_the_audio_is_renamed_and_keyed(self):
        lst = SimpleNamespace(questions=[mcq("q", "Wie verkleidet sich Rolf?", ["a) als Cowboy", "b) als Arzt", "c) als Pirat"])])
        spec = {"evidence": "Geprüft: x", "keys": ["b) als Krankenschwester"], "option_fixes": {1: [("b) als Arzt", "b) als Krankenschwester")]}}
        c = planner.plan_task(lst, spec)["questions"][0]
        self.assertEqual([(o["text"], o["is_correct"]) for o in c["clean"]["options"]],
                         [("a) als Cowboy", False), ("b) als Krankenschwester", True), ("c) als Pirat", False)])
        self.assertEqual(c["status"], REVIEW_VERIFIED)

    def test_option_fix_is_idempotent_and_strict(self):
        done = SimpleNamespace(questions=[mcq("q", "?", ["a) x", "b) neu"])])
        spec = {"evidence": "Geprüft: x", "keys": ["b) neu"], "option_fixes": {1: [("b) alt", "b) neu")]}}
        self.assertTrue(planner.plan_task(done, spec)["questions"][0]["clean"]["options"][1]["is_correct"])
        missing = SimpleNamespace(questions=[mcq("q", "?", ["a) x", "b) y"])])
        with self.assertRaises(ValueError):
            planner.plan_task(missing, spec)

    def test_picture_choice_gap_key_must_be_one_of_the_options(self):
        lst = SimpleNamespace(questions=[gapq("q", "6 Anne: [[1]]", options=["c) Tischdecke", "f) Puppen"])])
        ok = planner.plan_task(lst, {"evidence": "Geprüft: x", "keys": [{"1": ["c) Tischdecke"]}]})["questions"][0]
        self.assertEqual(ok["clean"]["config"]["gaps"]["1"]["accepted"], ["c) Tischdecke"])
        with self.assertRaises(ValueError):
            planner.plan_task(lst, {"evidence": "Geprüft: x", "keys": [{"1": ["Tischdecke"]}]})

    def test_gap_choice_label_is_renamed_for_every_question(self):
        opts = ["d) Hamburger", "f) Waffeln"]
        lst = SimpleNamespace(questions=[gapq("q1", "9 Marie: [[1]]", 1, options=list(opts)), gapq("q2", "10 Jakob: [[1]]", 2, options=list(opts))])
        spec = {"evidence": "Geprüft: x", "gap_option_renames": [("f) Waffeln", "f) Gebäck (Kuchen)")],
                "keys": [{"1": ["d) Hamburger"]}, {"1": ["f) Gebäck (Kuchen)"]}]}
        plan = planner.plan_task(lst, spec)["questions"]
        for c in plan:
            self.assertEqual(c["clean"]["config"]["gaps"]["1"]["options"], ["d) Hamburger", "f) Gebäck (Kuchen)"])
        self.assertEqual(plan[1]["clean"]["config"]["gaps"]["1"]["accepted"], ["f) Gebäck (Kuchen)"])

    def test_review_marks_needs_review(self):
        lst = SimpleNamespace(questions=[mcq("q", "?", ["a", "b"])])
        c = planner.plan_task(lst, {"evidence": "Geprüft: x", "keys": ["a"], "review": {1: "Bild unklar"}})["questions"][0]
        self.assertEqual((c["status"], c["note"]), (REVIEW_NEEDS_REVIEW, "Bild unklar"))


class TestRemovals(unittest.TestCase):
    def _lst(self):
        return SimpleNamespace(id="L", questions=[mcq("q1", "Worum geht es?", ["a", "b"], 1), mcq("q2", "Wie viele Tage?", ["3", "5"], 2)])

    def test_named_question_is_planned_for_removal_when_there_are_no_attempts(self):
        from app.scripts import a2_keys

        db = MagicMock(scalar=MagicMock(return_value=0))
        out = a2_keys.plan_removals(db, self._lst(), ["Wie viele Tage?"])
        self.assertEqual([q.id for q in out], ["q2"])
        self.assertEqual(a2_keys.plan_removals(db, self._lst(), ["schon entfernt"]), [])  # re-run

    def test_removal_refused_once_students_have_attempts(self):
        from app.scripts import a2_keys

        with self.assertRaises(ValueError):
            a2_keys.plan_removals(MagicMock(scalar=MagicMock(return_value=3)), self._lst(), ["Wie viele Tage?"])


class TestHoerenPublishRule(unittest.TestCase):
    """ListeningService.update refuses to publish an A1 / A2 Hören task whose
    keys are not all verified; other levels keep the old rule (key + audio)."""

    def _update(self, level: str, unverified: int):
        from app.schemas.listening import ListeningUpdate
        from app.services.listening.service import ListeningService

        service = ListeningService(MagicMock())
        listening = SimpleNamespace(is_published=False, audio_storage_path="a.mp3", audio_url=None, questions=[])
        service.repository = MagicMock(get=MagicMock(return_value=listening))
        state = {"level": level, "key_unverified": unverified}
        with patch("app.services.lesson_skills.hoeren_pdf_import.readiness", return_value=state):
            return service.update("id", ListeningUpdate(is_published=True))

    def test_a2_unverified_refused(self):
        with self.assertRaises(HTTPException) as ctx:
            self._update("A2", 3)
        self.assertEqual((ctx.exception.status_code, ctx.exception.detail), (409, "ANSWER_KEY_NOT_VERIFIED"))

    def test_a1_unverified_refused_a2_verified_allowed_b1_unchanged(self):
        with self.assertRaises(HTTPException):
            self._update("A1", 1)
        self._update("A2", 0)
        self._update("B1", 5)  # B1+ only need a key + audio (not changed here)


if __name__ == "__main__":
    unittest.main()
