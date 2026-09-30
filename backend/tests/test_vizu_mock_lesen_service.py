"""VIZU-Mock Lesen grading — the cascade level-confirmation rule
(app/services/vizu_mock/lesen_service.py). The DB-facing parts
(_level_breakdown/submit_lesen's grading + idempotent-resubmit behavior)
were verified against a real, isolated Postgres instance over real HTTP
in this session (26/26 checks, including the spec's own worked example:
A1 4/4, A2 4/4, B1 3/4, B2 2/4, C1 1/4 -> lesen_level=B1, 14/20) rather
than mocked here, since mocking SQLAlchemy's join/aggregate query would
mostly test the mock. This file covers the pure cascade logic directly."""

import unittest

from app.services.vizu_mock.lesen_service import _confirmed_level


def scores(**by_level: tuple[int, int]) -> list[dict]:
    """scores(A1=(4, 4), A2=(3, 4), ...) -> the level_scores shape
    _level_breakdown produces, with `passed` derived the same way it is."""
    return [
        {
            "level": level,
            "points": points,
            "max_points": max_points,
            "passed": max_points > 0 and points * 4 >= 3 * max_points,
        }
        for level, (points, max_points) in by_level.items()
    ]


class TestConfirmedLevelCascade(unittest.TestCase):
    def test_spec_example_a1_a2_full_b1_partial_b2_low_c1_low_is_b1(self):
        level_scores = scores(A1=(4, 4), A2=(4, 4), B1=(3, 4), B2=(2, 4), C1=(1, 4))
        self.assertEqual(_confirmed_level(level_scores), "B1")

    def test_all_levels_passed_is_c1(self):
        level_scores = scores(A1=(4, 4), A2=(3, 4), B1=(3, 4), B2=(3, 4), C1=(4, 4))
        self.assertEqual(_confirmed_level(level_scores), "C1")

    def test_a1_below_threshold_confirms_nothing(self):
        level_scores = scores(A1=(2, 4), A2=(4, 4), B1=(4, 4), B2=(4, 4), C1=(4, 4))
        self.assertIsNone(_confirmed_level(level_scores))

    def test_gap_in_the_middle_stops_the_cascade_even_if_later_levels_pass(self):
        # A2 fails (2/4) even though B1 alone would technically pass (3/4)
        # — the result must still be A1, never "B1 because B1 passed".
        level_scores = scores(A1=(4, 4), A2=(2, 4), B1=(3, 4), B2=(4, 4), C1=(4, 4))
        self.assertEqual(_confirmed_level(level_scores), "A1")

    def test_exact_threshold_3_of_4_counts_as_passed(self):
        level_scores = scores(A1=(3, 4))
        self.assertEqual(_confirmed_level(level_scores), "A1")

    def test_below_threshold_2_of_4_does_not_count(self):
        level_scores = scores(A1=(2, 4))
        self.assertIsNone(_confirmed_level(level_scores))

    def test_all_zero_confirms_nothing(self):
        level_scores = scores(A1=(0, 4), A2=(0, 4), B1=(0, 4), B2=(0, 4), C1=(0, 4))
        self.assertIsNone(_confirmed_level(level_scores))


if __name__ == "__main__":
    unittest.main()
