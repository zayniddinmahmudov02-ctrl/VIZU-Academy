"""VIZU LMS — pure rules: structure constants, competency order, status
aggregation, resource file detection and the lesson unlock rules."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.models.lms import COMPETENCY_ORDER, COMPETENCY_POSITION
from app.services.lms import access, progress, resources, structure


class TestStructure(unittest.TestCase):
    def test_levels_and_lesson_counts(self):
        self.assertEqual(structure.LEVELS, ("A1", "A2", "B1", "B2", "C1"))
        self.assertEqual(structure.LEVEL_LESSON_COUNTS, {"A1": 14, "A2": 14, "B1": 20, "B2": 30, "C1": 22})
        self.assertEqual(structure.TOTAL_LESSONS, 100)

    def test_competency_order_is_fixed(self):
        self.assertEqual(
            COMPETENCY_ORDER,
            ("EINFUEHRUNG", "WORTSCHATZ", "GRAMMATIK", "LESEN", "HOEREN", "SPRECHEN", "SCHREIBEN", "UEBUNGEN", "ABSCHLUSSTEST", "ZUSAMMENFASSUNG"),
        )
        self.assertEqual([COMPETENCY_POSITION[k] for k in COMPETENCY_ORDER], list(range(1, 11)))

    def test_unknown_level_is_404(self):
        with self.assertRaises(HTTPException) as ctx:
            structure.normalize_level("D1")
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(structure.normalize_level(" b2 "), "B2")


class TestAggregate(unittest.TestCase):
    def test_all_completed(self):
        self.assertEqual(progress.aggregate(["completed", "completed"]), "completed")

    def test_nothing_started(self):
        self.assertEqual(progress.aggregate(["not_started", "not_started"]), "not_started")

    def test_mixed_is_in_progress(self):
        self.assertEqual(progress.aggregate(["completed", "not_started"]), "in_progress")
        self.assertEqual(progress.aggregate(["in_progress"]), "in_progress")

    def test_pending_evaluation_is_in_progress_with_detail(self):
        part = progress._skill_part({"available": True, "status": "pending_evaluation", "score": None})
        self.assertEqual((part["status"], part["detail"]), ("in_progress", "pending_evaluation"))

    def test_unavailable_skill_is_not_a_part(self):
        self.assertIsNone(progress._skill_part({"available": False, "status": "not_available"}))

    def test_frage_counts_once_submitted(self):
        self.assertEqual(progress._frage_part({"available": True, "submitted": True, "status": "pending_evaluation"})["status"], "completed")
        self.assertEqual(progress._frage_part({"available": True, "submitted": False, "status": "not_started"})["status"], "not_started")

    def test_a1_student_competency_order_omits_only_einfuehrung(self):
        self.assertEqual(
            progress.competency_order_for_level("A1"),
            ("WORTSCHATZ", "GRAMMATIK", "LESEN", "HOEREN", "SPRECHEN", "SCHREIBEN", "UEBUNGEN", "ABSCHLUSSTEST", "ZUSAMMENFASSUNG"),
        )

    def test_other_levels_keep_the_shared_competency_order(self):
        for level in ("A2", "B1", "B2", "C1", None):
            with self.subTest(level=level):
                self.assertEqual(progress.competency_order_for_level(level), COMPETENCY_ORDER)


class TestResourceDetection(unittest.TestCase):
    def test_magic_bytes(self):
        self.assertEqual(resources._detect("PDF", b"%PDF-1.7\n", "a.pdf"), "pdf")
        self.assertEqual(resources._detect("AUDIO", b"ID3\x04\x00", "a.mp3"), "mp3")
        self.assertEqual(resources._detect("AUDIO", b"OggS\x00", "a.ogg"), "ogg")
        self.assertEqual(resources._detect("IMAGE", b"\x89PNG\r\n\x1a\n", "a.png"), "png")
        self.assertEqual(resources._detect("DOCUMENT", b"PK\x03\x04", "a.docx"), "docx")

    def test_wrong_content_is_rejected(self):
        self.assertIsNone(resources._detect("PDF", b"<html>", "a.pdf"))
        self.assertIsNone(resources._detect("AUDIO", b"%PDF-1.7", "a.mp3"))
        self.assertIsNone(resources._detect("DOCUMENT", b"PK\x03\x04", "a.exe"))

    def test_competency_and_type_validation(self):
        self.assertEqual(resources.validate_competency("hoeren"), "HOEREN")
        self.assertIsNone(resources.validate_competency(""))
        with self.assertRaises(HTTPException):
            resources.validate_competency("MATHE")
        with self.assertRaises(HTTPException):
            resources.validate_type("VIDEO")

    def test_links_must_be_https(self):
        self.assertTrue(resources.URL_RE.match("https://www.goethe.de/de/spr/ueb.html"))
        self.assertFalse(resources.URL_RE.match("http://example.com/x"))
        self.assertFalse(resources.URL_RE.match("javascript:alert(1)"))


class TestLessonAccess(unittest.TestCase):
    """Order: staff -> draft -> admin lock -> Premium -> sequential."""

    def lesson(self, **kw):
        return SimpleNamespace(**{"is_published": True, "access_override": None, "id": "l2", "module_id": "m", "number": 2, **kw})

    def run_access(self, lesson, *, staff=False, premium_ok=True, sequential=False, prev_done=True, has_prev=True):
        user = SimpleNamespace(id="u")
        with patch.object(access, "has_premium_bypass", return_value=staff), \
             patch.object(access, "can_access_lesson", return_value=premium_ok), \
             patch.object(access, "_sequential", return_value=sequential), \
             patch.object(access, "previous_published_lesson", return_value=SimpleNamespace(id="l1") if has_prev else None), \
             patch.object(access, "lesson_completed", return_value=prev_done):
            return access.lesson_access(None, user, lesson)

    def test_defaults_only_apply_the_premium_rule(self):
        self.assertTrue(self.run_access(self.lesson()).unlocked)
        a = self.run_access(self.lesson(), premium_ok=False)
        self.assertEqual((a.unlocked, a.reason, a.http_detail), (False, "PREMIUM_REQUIRED", "PREMIUM_REQUIRED"))

    def test_draft_is_invisible_to_students_but_not_staff(self):
        self.assertFalse(self.run_access(self.lesson(is_published=False)).visible)
        self.assertTrue(self.run_access(self.lesson(is_published=False), staff=True).unlocked)

    def test_admin_lock_beats_premium(self):
        a = self.run_access(self.lesson(access_override="LOCKED"))
        self.assertEqual((a.unlocked, a.reason, a.http_detail), (False, "ADMIN_LOCKED", "LESSON_LOCKED"))

    def test_sequential_unlock(self):
        self.assertTrue(self.run_access(self.lesson(), sequential=True, prev_done=True).unlocked)
        a = self.run_access(self.lesson(), sequential=True, prev_done=False)
        self.assertEqual((a.unlocked, a.reason), (False, "PREVIOUS_LESSON_NOT_COMPLETED"))
        self.assertTrue(self.run_access(self.lesson(), sequential=True, prev_done=False, has_prev=False).unlocked)

    def test_open_override_skips_sequential_but_not_premium(self):
        self.assertTrue(self.run_access(self.lesson(access_override="OPEN"), sequential=True, prev_done=False).unlocked)
        self.assertFalse(self.run_access(self.lesson(access_override="OPEN"), premium_ok=False).unlocked)


class TestPresent(unittest.TestCase):
    def state(self):
        comps = [
            {"kind": "EINFUEHRUNG", "is_published": True, "status": "completed", "progress_status": "completed"},
            {"kind": "WORTSCHATZ", "is_published": False, "status": "not_started", "progress_status": "not_started"},
            {"kind": "LESEN", "is_published": True, "status": "not_available", "progress_status": "not_available"},
        ]
        return {"lesson_id": "l", "progress_status": "in_progress", "completed": False, "competencies": comps}

    def test_hidden_competencies_are_removed_for_students(self):
        view = progress.present(self.state(), access.LessonAccess(visible=True, unlocked=True))
        self.assertEqual([c["kind"] for c in view["competencies"]], ["EINFUEHRUNG", "LESEN"])
        self.assertEqual(view["status"], "in_progress")

    def test_locked_lesson_overlays_locked_but_keeps_real_state(self):
        view = progress.present(self.state(), access.LessonAccess(visible=True, unlocked=False, reason="ADMIN_LOCKED"))
        first = view["competencies"][0]
        self.assertEqual((first["status"], first["progress_status"]), ("locked", "completed"))
        self.assertEqual(view["competencies"][1]["status"], "not_available")
        self.assertEqual(view["status"], "locked")


if __name__ == "__main__":
    unittest.main()
