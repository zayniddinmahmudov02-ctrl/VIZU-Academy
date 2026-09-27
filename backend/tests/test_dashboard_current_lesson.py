"""Regression tests for the "Weiter lernen" dashboard card bug:
DashboardService._find_current_lesson() used to run an unordered query
(`.first()` with no `.order_by()` at all), so it could return an
unrelated lesson instead of whatever the student was actually working
on. Real end-to-end behavior (brand-new user -> lesson 1, in-progress
lesson keeps showing, completing it advances to the next untouched
lesson, two users never see each other's lesson) was verified against a
real, throwaway local PostgreSQL instance during development (not part
of this suite — no DB fixture infra exists here, see conftest.py). These
tests instead pin the two query SHAPES themselves — in particular that
each one carries a real `.order_by(...)` — so a future edit can't
silently reintroduce the exact original bug (removing the ordering)
without a test failing.
"""

import unittest
from unittest.mock import MagicMock

from app.services.dashboard.service import DashboardService


class TestFindCurrentLesson(unittest.TestCase):
    def _service_with_mock_query(self):
        service = DashboardService(db=MagicMock())
        return service

    def test_returns_in_progress_lesson_ordered_by_most_recently_updated(self):
        service = self._service_with_mock_query()
        expected_lesson = MagicMock()

        # First call: the "in progress" query — .query(Lesson).join(...)
        # .filter(...).order_by(...).first()
        query_chain = service.db.query.return_value
        query_chain.join.return_value = query_chain
        query_chain.filter.return_value = query_chain
        query_chain.order_by.return_value = query_chain
        query_chain.first.return_value = expected_lesson

        result = service._find_current_lesson("user-1")

        self.assertIs(result, expected_lesson)
        # The literal bug: no order_by at all. Must always be called
        # before .first() on this query.
        query_chain.order_by.assert_called_once()

    def test_falls_back_to_next_untouched_lesson_in_curriculum_order(self):
        service = self._service_with_mock_query()
        expected_lesson = MagicMock()

        query_chain = service.db.query.return_value
        query_chain.join.return_value = query_chain
        query_chain.outerjoin.return_value = query_chain
        query_chain.filter.return_value = query_chain
        query_chain.order_by.return_value = query_chain

        # First .first() call (the in-progress lookup) finds nothing;
        # the second (next-untouched lookup) finds the fallback lesson.
        query_chain.first.side_effect = [None, expected_lesson]

        result = service._find_current_lesson("user-1")

        self.assertIs(result, expected_lesson)
        self.assertEqual(query_chain.outerjoin.call_count, 1)
        # Both queries must be ordered — this is the fallback path that
        # decides curriculum order (course -> module -> lesson number).
        self.assertEqual(query_chain.order_by.call_count, 2)

    def test_returns_none_when_nothing_in_progress_and_nothing_untouched(self):
        # Every lesson in the whole platform already completed — an
        # unlikely but real edge case; must not raise.
        service = self._service_with_mock_query()

        query_chain = service.db.query.return_value
        query_chain.join.return_value = query_chain
        query_chain.outerjoin.return_value = query_chain
        query_chain.filter.return_value = query_chain
        query_chain.order_by.return_value = query_chain
        query_chain.first.side_effect = [None, None]

        result = service._find_current_lesson("user-1")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
