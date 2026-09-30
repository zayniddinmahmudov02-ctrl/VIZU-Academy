"""VIZU-Mock service — framework only (see app/models/vizu_mock_attempt.py):
verifies attempt creation stays IN_PROGRESS with every level null, owner
scoping never leaks another user's attempt, and complete() is idempotent
and never invents a level."""

import unittest
from unittest.mock import MagicMock

from app.models.vizu_mock_attempt import STATUS_COMPLETED, STATUS_IN_PROGRESS, VizuMockAttempt
from app.services.vizu_mock import service


class TestCreateAttempt(unittest.TestCase):
    def test_new_attempt_is_in_progress_with_no_levels(self):
        db = MagicMock()
        db.refresh.side_effect = lambda obj: None
        attempt = service.create_attempt(db, user_id="u1")
        self.assertEqual(attempt.status, STATUS_IN_PROGRESS)
        self.assertIsNone(attempt.overall_level)
        self.assertIsNone(attempt.lesen_level)
        db.add.assert_called_once_with(attempt)
        db.commit.assert_called_once()


class TestOwnerScoping(unittest.TestCase):
    def test_get_own_attempt_scopes_by_user_id(self):
        db = MagicMock()
        db.scalar.return_value = None
        result = service.get_own_attempt(db, user_id="u1", attempt_id="a1")
        self.assertIsNone(result)
        db.scalar.assert_called_once()

    def test_complete_returns_none_for_someone_elses_attempt(self):
        db = MagicMock()
        db.scalar.return_value = None  # get_own_attempt finds nothing for this user
        result = service.complete_attempt(db, user_id="attacker", attempt_id="victim-attempt")
        self.assertIsNone(result)
        db.commit.assert_not_called()


class TestCompleteAttempt(unittest.TestCase):
    def test_completing_sets_status_and_timestamp_never_a_level(self):
        db = MagicMock()
        attempt = VizuMockAttempt(user_id="u1", status=STATUS_IN_PROGRESS)
        db.scalar.return_value = attempt
        result = service.complete_attempt(db, user_id="u1", attempt_id="a1")
        self.assertIs(result, attempt)
        self.assertEqual(attempt.status, STATUS_COMPLETED)
        self.assertIsNotNone(attempt.completed_at)
        self.assertIsNone(attempt.overall_level)
        db.commit.assert_called_once()

    def test_completing_an_already_completed_attempt_is_a_noop(self):
        db = MagicMock()
        attempt = VizuMockAttempt(user_id="u1", status=STATUS_COMPLETED)
        db.scalar.return_value = attempt
        service.complete_attempt(db, user_id="u1", attempt_id="a1")
        db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
