"""refresh_lesson_completion persists StudentProgress.lesson_completed via
the existing LessonProgressService.update_completion (canonical
SectionGateService check) — nothing else ever wrote that flag."""

import unittest
from unittest.mock import MagicMock, patch

from app.services.learning.lesson_progress import LessonProgressService, refresh_lesson_completion


class TestRefreshLessonCompletion(unittest.TestCase):
    def test_delegates_to_update_completion_with_string_ids(self):
        db = MagicMock()
        with patch.object(LessonProgressService, "update_completion") as update:
            refresh_lesson_completion(db, 123, 456)
        update.assert_called_once_with("123", "456")

    def test_lesson_completed_follows_the_gate(self):
        db = MagicMock()
        progress = MagicMock(lesson_completed=False)
        db.query.return_value.filter.return_value.first.return_value = progress
        service = LessonProgressService(db)
        uid, lid = "00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"
        with patch("app.services.learning.lesson_progress.SectionGateService") as gate:
            gate.return_value.is_lesson_completed.return_value = True
            result = service.update_completion(uid, lid)
        self.assertTrue(result.lesson_completed)
        with patch("app.services.learning.lesson_progress.SectionGateService") as gate:
            gate.return_value.is_lesson_completed.return_value = False
            result = service.update_completion(uid, lid)
        self.assertFalse(result.lesson_completed)


if __name__ == "__main__":
    unittest.main()
