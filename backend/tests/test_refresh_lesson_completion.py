"""refresh_lesson_completion persists the lesson snapshot through the VIZU LMS
progress service (app.services.lms.progress.sync_lesson) — the one place
that decides lesson completion."""

import unittest
from unittest.mock import MagicMock, patch

from app.services.learning.lesson_progress import LessonProgressService, refresh_lesson_completion

UID = "00000000-0000-0000-0000-000000000001"
LID = "00000000-0000-0000-0000-000000000002"


class TestRefreshLessonCompletion(unittest.TestCase):
    def test_delegates_to_update_completion_with_string_ids(self):
        db = MagicMock()
        with patch.object(LessonProgressService, "update_completion") as update:
            refresh_lesson_completion(db, 123, 456)
        update.assert_called_once_with("123", "456")

    def test_update_completion_syncs_the_lms_snapshot(self):
        db = MagicMock()
        with patch("app.services.learning.lesson_progress.lms_progress") as lms:
            LessonProgressService(db).update_completion(UID, LID)
        args = lms.sync_lesson.call_args.args
        self.assertIs(args[0], db)
        self.assertEqual((str(args[1]), str(args[2])), (UID, LID))

    def test_lesson_completed_follows_the_lms_rule(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = MagicMock()
        service = LessonProgressService(db)
        with patch("app.services.learning.lesson_progress.lms_progress") as lms:
            lms.is_lesson_completed.return_value = True
            self.assertTrue(service.lesson_completed(UID, LID))
            lms.is_lesson_completed.return_value = False
            self.assertFalse(service.lesson_completed(UID, LID))

    def test_no_progress_row_is_not_completed(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with patch("app.services.learning.lesson_progress.lms_progress") as lms:
            self.assertFalse(LessonProgressService(db).lesson_completed(UID, LID))
            lms.is_lesson_completed.assert_not_called()


if __name__ == "__main__":
    unittest.main()
