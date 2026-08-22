"""Verifies the video-completion threshold is 70% (changed from 95%) —
watch_percent < 70 must be rejected, >= 70 (and 100) must be accepted.
Uses stdlib unittest + MagicMock (no real DB), matching this session's
established pattern."""

import unittest
from unittest.mock import MagicMock

from fastapi import HTTPException

from app.services.video_progress.service import COMPLETION_THRESHOLD_PERCENT, VideoProgressService


class TestVideoCompletionThreshold(unittest.TestCase):
    def setUp(self):
        self.service = VideoProgressService.__new__(VideoProgressService)
        self.service.db = MagicMock()
        self.service.repository = MagicMock()
        self.service.videos = MagicMock()
        self.service.student_progress = MagicMock()
        self.service.video_service = MagicMock()

        self.user = MagicMock(id="user-1")
        self.video = MagicMock(id="video-1", lesson_id="lesson-1", duration_seconds=100)
        self.service.videos.get.return_value = self.video

    def _progress_at(self, watch_percent: int, last_position: int | None = None):
        progress = MagicMock(watch_percent=watch_percent, last_position=last_position if last_position is not None else watch_percent)
        self.service.repository.get_by_user_and_video.return_value = progress
        return progress

    def test_threshold_constant_is_70(self):
        self.assertEqual(COMPLETION_THRESHOLD_PERCENT, 70)

    def test_69_percent_is_not_completed(self):
        self._progress_at(69, last_position=69)
        with self.assertRaises(HTTPException) as ctx:
            self.service.complete_progress(self.user, self.video.id, ended=False)
        self.assertEqual(ctx.exception.status_code, 400)
        self.service.repository.update.assert_not_called()

    def test_70_percent_is_completed(self):
        self._progress_at(70, last_position=70)
        result = self.service.complete_progress(self.user, self.video.id, ended=False)
        self.service.repository.update.assert_called_once()
        self.assertIsNotNone(result)

    def test_100_percent_is_completed(self):
        self._progress_at(100, last_position=100)
        self.service.complete_progress(self.user, self.video.id, ended=False)
        self.service.repository.update.assert_called_once()

    def test_ended_event_completes_regardless_of_percent(self):
        # A native <video> 'ended' event completes even if watch_percent
        # somehow under-reports (e.g. a duration mismatch) — unchanged
        # behavior, still valid after the threshold change.
        self._progress_at(50, last_position=50)
        self.service.complete_progress(self.user, self.video.id, ended=True)
        self.service.repository.update.assert_called_once()

    def test_marks_student_progress_video_completed_once(self):
        self._progress_at(70, last_position=70)
        student_progress = MagicMock(video_completed=False)
        self.service.student_progress.get_or_create.return_value = student_progress
        self.service.complete_progress(self.user, self.video.id, ended=False)
        self.service.student_progress.mark_video_completed.assert_called_once_with(student_progress)

    def test_does_not_re_mark_already_completed_student_progress(self):
        # Idempotency: a duplicate complete-request on an already-
        # completed video doesn't call mark_video_completed again.
        self._progress_at(70, last_position=70)
        student_progress = MagicMock(video_completed=True)
        self.service.student_progress.get_or_create.return_value = student_progress
        self.service.complete_progress(self.user, self.video.id, ended=False)
        self.service.student_progress.mark_video_completed.assert_not_called()


if __name__ == "__main__":
    unittest.main()
