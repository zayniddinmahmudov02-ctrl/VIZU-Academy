"""Multilevel Modelltest scoring tables (owner, 2026-11-28) — pure functions, no database. Every section is 0–75, the total 0–300.

* Lesen / Hören (35-question scale): the owner's bands — C1 28–35 → 65–75, B2 18–27 → 51–64, B1 10–17 → 38–50, below B1 0–9 → 0–37.
  The default table gives every raw count 0–35 one score: linear inside its band, rounded half up (deterministic, 35 → 75). The table is
  admin-configurable (app_settings["multilevel_scoring"]["lesen_table"], 36 non-decreasing values ending in 75).
* Any other question count (Hören with 30, or a test where keys are missing) is put on the 35 scale first:
  equivalent = round_half_up(correct × 35 / questions), then the same table — 30 / 30 = 75, the same rounding everywhere.
* Schreiben: the AI gives Teil 1.1 (0–5), Teil 1.2 (0–7) and Teil 2 (0–24) in steps of 0.5 → raw 0–36 → the official conversion table
  (rows "from–to → score"). The rows the owner could read are the default; 16.6–22.0 and 0–5.5 were not readable and are NOT invented: a
  raw score there has no converted score (the section waits for the Super Admin — score by hand or complete the table in the settings).
* Sprechen: no official table was given. The AI scores six criteria per Teil (0–5 each); the raw sum is put on 0–75 linearly (rounded half up).
  Aussprache / Flüssigkeit count only when a model listened to the audio — otherwise they are left out of raw and maximum.
* Level bands (same source as the Lesen table): below B1 0–37, B1 38–50, B2 51–64, C1 65–75 — admin-configurable lower bounds."""

import math
import re

SECTION_MAX = 75
LESEN_SCALE = 35  # the Lesen table is defined for 35 questions
LESEN_BANDS = ((0, 9, 0, 37), (10, 17, 38, 50), (18, 27, 51, 64), (28, 35, 65, 75))  # (raw from, raw to, score from, score to)
DEFAULT_BANDS = {"B1": 38, "B2": 51, "C1": 65}
NICHT_BESTANDEN = "NICHT_BESTANDEN"

SCHREIBEN_TEIL_MAX = {"1.1": 5.0, "1.2": 7.0, "2": 24.0}
SCHREIBEN_RAW_MAX = 36.0
# the official 36 → 75 table as far as it was readable (owner's upload, 2026-11-28): [from, to, score]
DEFAULT_SCHREIBEN_TABLE = [
    [35.1, 36.0, 75], [34.1, 35.0, 74], [33.1, 34.0, 73], [32.6, 33.0, 72], [32.1, 32.5, 71], [31.6, 32.0, 70], [31.1, 31.5, 69],
    [30.6, 31.0, 68], [30.1, 30.5, 67], [29.1, 30.0, 66], [28.1, 29.0, 65], [27.1, 28.0, 64], [26.6, 27.0, 63], [26.1, 26.5, 62],
    [25.6, 26.0, 61], [25.1, 25.5, 60], [24.6, 25.0, 59], [24.1, 24.5, 58], [23.6, 24.0, 57], [23.1, 23.5, 56], [22.6, 23.0, 55],
    [22.1, 22.5, 54],
    # 16.6–22.0: not readable in the upload — left out on purpose
    [16.1, 16.5, 42], [15.6, 16.0, 41], [15.1, 15.5, 40], [14.6, 15.0, 39], [14.1, 14.5, 38], [13.6, 14.0, 37], [13.1, 13.5, 36],
    [12.6, 13.0, 35], [12.1, 12.5, 34], [11.6, 12.0, 33], [11.1, 11.5, 32], [10.6, 11.0, 31], [10.1, 10.5, 30], [9.6, 10.0, 29],
    [9.1, 9.5, 28], [8.6, 9.0, 27], [8.1, 8.5, 26], [7.6, 8.0, 25], [7.1, 7.5, 24], [6.6, 7.0, 23], [6.1, 6.5, 22], [5.6, 6.0, 21],
    # 0–5.5: not readable in the upload — left out on purpose
]

SPRECHEN_CRITERIA = (
    ("aufgabe", "Aufgabenbewältigung"), ("fluessigkeit", "Flüssigkeit"), ("wortschatz", "Wortschatz"), ("grammatik", "Grammatik"),
    ("aussprache", "Aussprache"), ("kohaerenz", "Kohärenz und Interaktion"),
)
SPRECHEN_CRITERION_MAX = 5
AUDIO_ONLY = {"aussprache", "fluessigkeit"}  # never from the transcript alone

EPS = 1e-6


def round_half_up(value: float) -> int:
    return int(math.floor(value + 0.5 + EPS))


# ---------------------------------------------------------------- Lesen / Hören


def default_lesen_table() -> list[int]:
    table = [0] * (LESEN_SCALE + 1)
    for raw_from, raw_to, s_from, s_to in LESEN_BANDS:
        for raw in range(raw_from, raw_to + 1):
            table[raw] = s_from if raw_to == raw_from else round_half_up(s_from + (raw - raw_from) * (s_to - s_from) / (raw_to - raw_from))
    return table


def validate_lesen_table(table) -> list[int]:
    if not isinstance(table, list) or len(table) != LESEN_SCALE + 1:
        raise ValueError(f"lesen_table needs {LESEN_SCALE + 1} values (0–{LESEN_SCALE} correct)")
    out = []
    for v in table:
        if isinstance(v, bool) or not isinstance(v, (int, float)) or float(v) != int(v) or not 0 <= int(v) <= SECTION_MAX:
            raise ValueError("lesen_table values are whole numbers 0–75")
        out.append(int(v))
    if any(b < a for a, b in zip(out, out[1:])):
        raise ValueError("lesen_table must not go down")
    if out[-1] != SECTION_MAX:
        raise ValueError("35 correct must be 75")
    return out


def equivalent_correct(raw: int, raw_max: int) -> int:
    """Correct answers on the 35-question scale (30 → × 35 / 30), rounded half up."""
    if raw_max == LESEN_SCALE:
        return max(0, min(LESEN_SCALE, raw))
    return max(0, min(LESEN_SCALE, round_half_up(max(0, min(raw, raw_max)) * LESEN_SCALE / raw_max)))


def auto_score(raw: int, raw_max: int, table: list[int]) -> int | None:
    if not raw_max or raw_max <= 0:
        return None
    return table[equivalent_correct(raw, raw_max)]


# ---------------------------------------------------------------- Schreiben


def schreiben_teil_key(title: str | None) -> str | None:
    """"Teil 1.1" → "1.1", "Teil 2" → "2" (None for anything else)."""
    m = re.search(r"teil\s*(\d+(?:[.,]\d+)?)", title or "", re.IGNORECASE)
    if not m:
        return None
    key = m.group(1).replace(",", ".")
    return key if key in SCHREIBEN_TEIL_MAX else None


def validate_schreiben_table(rows) -> list[list]:
    if not isinstance(rows, list) or not 1 <= len(rows) <= 200:
        raise ValueError("schreiben_table needs 1–200 rows")
    out = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) != 3:
            raise ValueError("each row is [from, to, score]")
        lo, hi, score = row
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in row):
            raise ValueError("rows are numbers")
        lo, hi = round(float(lo), 1), round(float(hi), 1)
        if not 0 <= lo <= hi <= SCHREIBEN_RAW_MAX or float(score) != int(score) or not 0 <= int(score) <= SECTION_MAX:
            raise ValueError("from ≤ to within 0–36, score a whole number 0–75")
        out.append([lo, hi, int(score)])
    out.sort(key=lambda r: r[0], reverse=True)
    for upper, lower in zip(out, out[1:]):
        if lower[1] >= upper[0] - EPS:
            raise ValueError(f"rows overlap: {lower[0]}–{lower[1]} and {upper[0]}–{upper[1]}")
        if lower[2] > upper[2]:
            raise ValueError("a higher raw score must not give a lower score")
    return out


def schreiben_score(raw: float, rows: list[list]) -> int | None:
    """Converted 0–75, or None when the table has no row for this raw score (the Super Admin decides)."""
    raw = round(float(raw), 1)
    for lo, hi, score in rows:
        if lo - 0.05 - EPS <= raw <= hi + EPS:
            return int(score)
    return None


def missing_schreiben_ranges(rows: list[list]) -> list[list[float]]:
    """Raw scores 0–36 (steps of 0.5) the table does not convert, merged into ranges — shown to the admin as "missing"."""
    gaps, start, prev = [], None, None
    for i in range(int(SCHREIBEN_RAW_MAX * 2) + 1):
        raw = i / 2
        if schreiben_score(raw, rows) is None:
            start = raw if start is None else start
            prev = raw
        elif start is not None:
            gaps.append([start, prev])
            start = None
    if start is not None:
        gaps.append([start, prev])
    return gaps


# ---------------------------------------------------------------- Sprechen


def sprechen_score(raw: float, raw_max: float) -> int | None:
    if not raw_max or raw_max <= 0:
        return None
    return max(0, min(SECTION_MAX, round_half_up(max(0.0, min(raw, raw_max)) * SECTION_MAX / raw_max)))


# ---------------------------------------------------------------- levels


def validate_bands(bands) -> dict:
    if not isinstance(bands, dict):
        raise ValueError("bands: {B1, B2, C1}")
    try:
        out = {k: int(bands[k]) for k in ("B1", "B2", "C1")}
    except (KeyError, TypeError, ValueError):
        raise ValueError("bands: whole numbers for B1, B2, C1") from None
    if not 0 < out["B1"] < out["B2"] < out["C1"] <= SECTION_MAX:
        raise ValueError("bands: 0 < B1 < B2 < C1 ≤ 75")
    return out


def band_level(score: int | None, bands: dict) -> str | None:
    if score is None:
        return None
    if not 0 <= score <= SECTION_MAX:
        raise ValueError("score must be 0–75")
    if score >= bands["C1"]:
        return "C1"
    if score >= bands["B2"]:
        return "B2"
    if score >= bands["B1"]:
        return "B1"
    return NICHT_BESTANDEN
