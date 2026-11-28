"""Multilevel scoring tables (app/services/mock_exam/multilevel_scoring.py, owner 2026-11-28) — pure, no database.

Lesen bands → a deterministic 0–35 → 0–75 table; Hören 30 put on the 35 scale (30/30 = 75); the official Schreiben 36 → 75 rows with the two
unreadable ranges left open (never invented); Sprechen linear; level bands; validation of admin-edited tables."""

import unittest

from app.services.mock_exam import multilevel_scoring as s


class TestLesenTable(unittest.TestCase):
    def test_default_table_follows_the_owners_bands(self):
        t = s.default_lesen_table()
        self.assertEqual(len(t), 36)
        self.assertEqual(t, sorted(t))  # never goes down
        # band ends exactly as given: below B1 0–9 → 0–37, B1 10–17 → 38–50, B2 18–27 → 51–64, C1 28–35 → 65–75
        self.assertEqual([t[0], t[9], t[10], t[17], t[18], t[27], t[28], t[35]], [0, 37, 38, 50, 51, 64, 65, 75])
        # inside a band: linear, rounded half up — e.g. 23 → 51 + 5 × 13/9 = 58.2 → 58; 31 → 65 + 3 × 10/7 = 69.3 → 69
        self.assertEqual((t[23], t[31], t[5], t[14]), (58, 69, 21, 45))
        self.assertEqual(t, s.default_lesen_table())  # deterministic
        for raw, level in ((9, "NICHT_BESTANDEN"), (10, "B1"), (17, "B1"), (18, "B2"), (27, "B2"), (28, "C1"), (35, "C1")):
            self.assertEqual(s.band_level(t[raw], s.DEFAULT_BANDS), level, raw)

    def test_hoeren_30_on_the_35_scale(self):
        t = s.default_lesen_table()
        self.assertEqual(s.equivalent_correct(30, 30), 35)
        self.assertEqual(s.auto_score(30, 30, t), 75)  # 30 / 30 = 75
        self.assertEqual(s.equivalent_correct(15, 30), 18)  # 17.5 → 18 (half up)
        self.assertEqual(s.equivalent_correct(24, 30), 28)
        self.assertEqual(s.auto_score(24, 30, t), 65)  # same level threshold as 28 / 35
        self.assertEqual(s.auto_score(0, 30, t), 0)
        self.assertEqual(s.auto_score(35, 35, t), 75)
        self.assertEqual(s.auto_score(40, 35, t), 75)  # never above
        self.assertIsNone(s.auto_score(3, 0, t))  # no key at all: not scored

    def test_table_validation(self):
        good = s.default_lesen_table()
        self.assertEqual(s.validate_lesen_table(good), good)
        for bad in (good[:-1], good[:-1] + [74], [5] + good[1:3] + [1] + good[4:], good[:-1] + [76], good[:-1] + ["75"]):
            with self.subTest(bad=bad[-3:]), self.assertRaises(ValueError):
                s.validate_lesen_table(bad)


class TestSchreibenTable(unittest.TestCase):
    def test_official_rows(self):
        rows = s.validate_schreiben_table(s.DEFAULT_SCHREIBEN_TABLE)
        cases = {36.0: 75, 35.5: 75, 35.0: 74, 34.0: 73, 33.5: 73, 33.0: 72, 32.5: 71, 30.0: 66, 29.0: 65, 27.0: 63, 25.5: 60,
                 22.5: 54, 16.5: 42, 16.0: 41, 12.0: 33, 8.5: 26, 6.0: 21}
        for raw, score in cases.items():
            self.assertEqual(s.schreiben_score(raw, rows), score, raw)

    def test_unreadable_ranges_are_not_invented(self):
        rows = s.validate_schreiben_table(s.DEFAULT_SCHREIBEN_TABLE)
        for raw in (22.0, 20.0, 17.0, 5.5, 3.0, 0.0):
            self.assertIsNone(s.schreiben_score(raw, rows), raw)
        self.assertEqual(s.missing_schreiben_ranges(rows), [[0.0, 5.5], [17.0, 22.0]])
        # once the Super Admin completes the table, the gap closes
        filled = s.validate_schreiben_table(rows + [[19.6, 20.0, 47]])
        self.assertEqual(s.schreiben_score(20.0, filled), 47)
        self.assertEqual(s.missing_schreiben_ranges(filled), [[0.0, 5.5], [17.0, 19.5], [20.5, 22.0]])

    def test_validation(self):
        for bad in ([[10, 12, 30], [11, 13, 31]],  # overlap
                    [[10, 12, 40], [12.1, 14, 30]],  # higher raw, lower score
                    [[0, 37, 75]], [[5, 4, 10]], [[1, 2, 76]], [[1, 2]], "x", []):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                s.validate_schreiben_table(bad)

    def test_teil_keys(self):
        self.assertEqual([s.schreiben_teil_key(t) for t in ("Teil 1.1", "Teil 1,2", "teil 2", "Teil 3", None)], ["1.1", "1.2", "2", None, None])
        self.assertEqual(sum(s.SCHREIBEN_TEIL_MAX.values()), 36)


class TestSprechenAndBands(unittest.TestCase):
    def test_sprechen_linear(self):
        self.assertEqual(s.sprechen_score(120, 120), 75)
        self.assertEqual(s.sprechen_score(60, 120), 38)  # 37.5 → 38
        self.assertEqual(s.sprechen_score(0, 120), 0)
        self.assertEqual(s.sprechen_score(80, 80), 75)  # a maximum without the audio-only criteria
        self.assertIsNone(s.sprechen_score(3, 0))

    def test_bands(self):
        self.assertEqual(s.validate_bands({"B1": 38, "B2": 51, "C1": 65}), s.DEFAULT_BANDS)
        for bad in ({"B1": 51, "B2": 51, "C1": 65}, {"B1": 0, "B2": 51, "C1": 65}, {"B1": 38, "B2": 51, "C1": 76}, {"B1": 38}, None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                s.validate_bands(bad)
        self.assertEqual([s.band_level(x, s.DEFAULT_BANDS) for x in (0, 37, 38, 50, 51, 64, 65, 75)],
                         ["NICHT_BESTANDEN", "NICHT_BESTANDEN", "B1", "B1", "B2", "B2", "C1", "C1"])
        self.assertIsNone(s.band_level(None, s.DEFAULT_BANDS))


if __name__ == "__main__":
    unittest.main()
