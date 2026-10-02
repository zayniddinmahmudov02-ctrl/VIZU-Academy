"""VIZU-Multilevel Hören grading — same cascade level-confirmation rule as
Lesen (see test_vizu_multilevel_lesen_service.py), duplicated here against
hoeren_service's own copy of the pure function since each skill module
is independently self-contained (see hoeren_service.py's docstring).
The DB-facing parts (grading + idempotent-resubmit) were verified
against a real, isolated Postgres instance over real HTTP in this
session rather than mocked here."""

import unittest

from app.services.vizu_multilevel.hoeren_service import _confirmed_level


def scores(**by_level: tuple[int, int]) -> list[dict]:
    return [
        {
            "level": level,
            "points": points,
            "max_points": max_points,
            "passed": max_points > 0 and points * 4 >= 3 * max_points,
        }
        for level, (points, max_points) in by_level.items()
    ]


class TestHoerenConfirmedLevelCascade(unittest.TestCase):
    def test_all_levels_passed_is_c1(self):
        level_scores = scores(A1=(4, 4), A2=(3, 4), B1=(3, 4), B2=(3, 4), C1=(4, 4))
        self.assertEqual(_confirmed_level(level_scores), "C1")

    def test_a1_below_threshold_confirms_nothing(self):
        level_scores = scores(A1=(2, 4), A2=(4, 4), B1=(4, 4), B2=(4, 4), C1=(4, 4))
        self.assertIsNone(_confirmed_level(level_scores))

    def test_gap_in_the_middle_stops_the_cascade(self):
        level_scores = scores(A1=(4, 4), A2=(2, 4), B1=(3, 4), B2=(4, 4), C1=(4, 4))
        self.assertEqual(_confirmed_level(level_scores), "A1")

    def test_exact_threshold_3_of_4_counts_as_passed(self):
        level_scores = scores(A1=(3, 4))
        self.assertEqual(_confirmed_level(level_scores), "A1")

    def test_below_threshold_2_of_4_does_not_count(self):
        level_scores = scores(A1=(2, 4))
        self.assertIsNone(_confirmed_level(level_scores))


if __name__ == "__main__":
    unittest.main()
