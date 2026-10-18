"""Lösung (answer-key management): fingerprint, verification state and the
publish validation report — pure logic, no database."""

import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from app.services.lesson_skills import loesung

T0 = datetime(2026, 1, 1)


def opt(text, ok, n):
    return SimpleNamespace(option_text=text, is_correct=ok, order_index=n, created_at=T0, id=f"o{n}")


def mc(correct: int | None, text="Wer?"):
    return SimpleNamespace(id="q1", question=text, question_type="MULTIPLE_CHOICE", points=1, explanation=None, config=None,
                           options=[opt("A", correct == 0, 1), opt("B", correct == 1, 2), opt("C", correct == 2, 3)])


def gap(accepted):
    return SimpleNamespace(id="q2", question="Lücke", question_type="GAP_FILL", points=1, explanation=None, options=[],
                           config={"text": "Ich [[1]] hier.", "gaps": {"1": {"accepted": accepted}}, "case_sensitive": False,
                                   **({} if accepted else {"pending": True})})


def review(status, fp):
    return SimpleNamespace(status=status, key_fingerprint=fp, note="geprüft", reviewed_at=T0)


class TestFingerprint(unittest.TestCase):
    def test_changes_with_key_not_with_ids(self):
        a, b = mc(1), mc(1)
        b.options[0].id = "other"
        self.assertEqual(loesung.fingerprint(a), loesung.fingerprint(b))
        self.assertNotEqual(loesung.fingerprint(mc(1)), loesung.fingerprint(mc(2)))
        self.assertNotEqual(loesung.fingerprint(mc(1)), loesung.fingerprint(mc(1, text="Wo?")))
        self.assertNotEqual(loesung.fingerprint(gap(["bin"])), loesung.fingerprint(gap(["ist"])))


class TestQuestionState(unittest.TestCase):
    def test_missing_key(self):
        st = loesung.question_state(mc(None), None)
        self.assertEqual((st["has_key"], st["verified"]), (False, False))
        self.assertFalse(loesung.question_state(gap([]), None)["has_key"])

    def test_key_without_review_is_not_verified(self):
        st = loesung.question_state(mc(1), None)
        self.assertEqual((st["has_key"], st["verified"]), (True, False))

    def test_verified_only_while_fingerprint_matches(self):
        q = mc(1)
        r = review("verified", loesung.fingerprint(q))
        self.assertTrue(loesung.question_state(q, r)["verified"])
        changed = mc(2)  # key edited after the verification
        st = loesung.question_state(changed, r)
        self.assertEqual((st["verified"], st["verification_outdated"]), (False, True))

    def test_needs_review_flag(self):
        st = loesung.question_state(mc(1), review("needs_review", None))
        self.assertEqual((st["needs_review"], st["verified"]), (True, False))


class TestValidation(unittest.TestCase):
    def states(self, *qs_reviews):
        return [loesung.question_state(q, r) for q, r in qs_reviews]

    def test_ready_only_when_all_verified(self):
        q = mc(1)
        task = SimpleNamespace()
        ok = loesung.validation("lesen", task, self.states((q, review("verified", loesung.fingerprint(q)))))
        self.assertTrue(ok["ready"])
        bad = loesung.validation("lesen", task, self.states((q, None)))
        self.assertEqual([p["code"] for p in bad["problems"]], ["NOT_VERIFIED"])

    def test_missing_key_and_no_questions_block(self):
        self.assertEqual([p["code"] for p in loesung.validation("lesen", SimpleNamespace(), [])["problems"]], ["NO_QUESTIONS"])
        rep = loesung.validation("lesen", SimpleNamespace(), self.states((mc(None), None)))
        self.assertEqual(rep["problems"][0]["code"], "KEY_MISSING")

    def test_hoeren_audio_required(self):
        q = mc(1)
        st = self.states((q, review("verified", loesung.fingerprint(q))))
        for audio, code in (("none", "AUDIO_MISSING"), ("file_missing", "AUDIO_FILE_MISSING")):
            with self.subTest(audio=audio), patch.object(loesung, "audio_state", return_value=audio):
                rep = loesung.validation("hoeren", SimpleNamespace(), st)
                self.assertFalse(rep["ready"])
                self.assertIn(code, [p["code"] for p in rep["problems"]])
        with patch.object(loesung, "audio_state", return_value="ok"):
            self.assertTrue(loesung.validation("hoeren", SimpleNamespace(), st)["ready"])


class TestImportNotes(unittest.TestCase):
    def test_a2_lesson5_hoeren_note_is_found(self):
        note = loesung.import_notes().get("vizu-a2-l05-hoeren-01")
        self.assertIsNotNone(note)
        self.assertIn("Schwimmen im Meer", note["note"])
        self.assertTrue(note["key_pending"])


if __name__ == "__main__":
    unittest.main()
