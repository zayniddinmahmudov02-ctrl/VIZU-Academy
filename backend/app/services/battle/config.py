"""Battle rules in one place: CEFR stages, ranks, timing, scoring, Battle Points, avatars, achievements.

Ranks: every stage (A1 … C1, C1+) has three ranks of RANK_STEP points each, so the rank (and with it the
arena stage) follows from Battle Points alone. Questions come from the stage's words and every stage below
it; a stage without enough published picture words plays with the stages below (A2 players get A1 words
until A2 words are published). C1+ has no source words of its own."""

STAGES = ("A1", "A2", "B1", "B2", "C1", "C1+")
WORD_LEVELS = ("A1", "A2", "B1", "B2", "C1")
RANK_TITLES = ("Einsteiger", "Kämpfer", "Meister")
LEGEND_TITLES = ("Herausforderer", "Elite", "Legende")
# 2026-11-05: points now come in +1 per correct word (+3 win bonus) ≈ 4–13 per match, so a rank is 50 BP
# (was 150 with ±25 per match). Stored Battle Points are unchanged; ranks follow from them.
RANK_STEP = 50
STAGE_SUBTITLES = {
    "A1": "Der Anfang", "A2": "Der Aufstieg", "B1": "Die Freiheit", "B2": "Die Stärke", "C1": "Die Meisterschaft",
    "C1+": "Die Legende",
}

ROUNDS = 10
OPTIONS = 4
COUNTDOWN_S = 4
ROUND_S = 12
REVEAL_S = 3
ANSWER_GRACE_MS = 300
# 2026-11-05 owner rule: +1 per correct word, 0 for wrong / no answer (no speed bonus)
POINTS_PER_CORRECT = 1
# a player who has not polled for this long during a match loses it (reconnection window)
AFK_S = 20
# a waiting ranked match whose player stopped polling is dropped
QUEUE_STALE_S = 12
# point windows for ranked matchmaking by waiting time (seconds → max points difference)
MATCH_WINDOWS = ((10, 10), (20, 25), (None, None))
MIN_POOL = ROUNDS + OPTIONS

# Battle Points of a finished ranked or bot match = own match score + WIN_BONUS for the winner (draw / loss: own
# score only, never negative). Private rooms give no Battle Points.
WIN_BONUS = 3
POINT_MODES = ("ranked", "bot")

# Bot per stage: probability of a correct answer (random inside the range) and answer time window in ms.
# Gets faster and more accurate from A1 to C1+, but never perfect — a player who knows the words can win.
BOT_LEVELS = {
    "A1": {"accuracy": (0.55, 0.65), "time_ms": (5200, 10500)},
    "A2": {"accuracy": (0.63, 0.73), "time_ms": (4400, 9500)},
    "B1": {"accuracy": (0.70, 0.80), "time_ms": (3600, 8500)},
    "B2": {"accuracy": (0.77, 0.86), "time_ms": (2900, 7500)},
    "C1": {"accuracy": (0.83, 0.91), "time_ms": (2300, 6500)},
    "C1+": {"accuracy": (0.85, 0.92), "time_ms": (2000, 6000)},
}
BOT_NAME = "VIZU Bot"

# avatar key → (title, min rank index)
AVATARS = {
    "student": ("Student", 0),
    "explorer": ("Explorer", 1),
    "scholar": ("German Scholar", 3),
    "adventurer": ("Adventurer", 6),
    "professor": ("Professor", 9),
    "champion": ("Champion", 12),
    "legend": ("Legendary Player", 15),
}

# key → (title de, title uz, kind, threshold)
ACHIEVEMENTS = (
    ("first_match", "Erster Kampf", "Birinchi jang", "matches", 1),
    ("first_win", "Erster Sieg", "Birinchi g‘alaba", "wins", 1),
    ("wins_10", "Zehn Siege", "10 ta g‘alaba", "wins", 10),
    ("wins_50", "Fünfzig Siege", "50 ta g‘alaba", "wins", 50),
    ("streak_3", "Serie ×3", "Ketma-ket 3 g‘alaba", "best_streak", 3),
    ("streak_5", "Serie ×5", "Ketma-ket 5 g‘alaba", "best_streak", 5),
    ("matches_25", "Stammspieler", "25 ta jang", "matches", 25),
    ("a1_meister", "A1-Meister", "A1 ustasi", "rank", 2),
    ("a2_meister", "A2-Meister", "A2 ustasi", "rank", 5),
    ("b1_meister", "B1-Meister", "B1 ustasi", "rank", 8),
    ("legend", "Legende", "Afsona", "rank", 17),
)


def rank_index(points: int) -> int:
    return max(0, min(len(STAGES) * 3 - 1, points // RANK_STEP))


def rank_info(points: int) -> dict:
    i = rank_index(points)
    stage = STAGES[i // 3]
    titles = LEGEND_TITLES if stage == "C1+" else RANK_TITLES
    floor = i * RANK_STEP
    last = i == len(STAGES) * 3 - 1
    nxt = None if last else rank_title(i + 1)
    return {
        "index": i, "stage": stage, "tier": i % 3, "title": f"{stage}-{titles[i % 3]}", "stage_subtitle": STAGE_SUBTITLES[stage],
        "floor": floor, "next_at": None if last else floor + RANK_STEP, "next_title": nxt,
        "remaining": None if last else floor + RANK_STEP - points,
        "progress": 1.0 if last else round((points - floor) / RANK_STEP, 3),
    }


def rank_title(i: int) -> str:
    stage = STAGES[i // 3]
    return f"{stage}-{(LEGEND_TITLES if stage == 'C1+' else RANK_TITLES)[i % 3]}"


def stage_for_points(points: int) -> str:
    return STAGES[rank_index(points) // 3]


def word_levels_up_to(stage: str) -> list[str]:
    i = STAGES.index(stage)
    return list(WORD_LEVELS[: min(i + 1, len(WORD_LEVELS))])


def match_window(waited_s: float) -> int | None:
    for limit, window in MATCH_WINDOWS:
        if limit is None or waited_s < limit:
            return window
    return None


def round_score(correct: bool, time_ms: int) -> int:
    """+1 per correct word; wrong or no answer 0 (time_ms kept for the call sites, it no longer scores)."""
    return POINTS_PER_CORRECT if correct else 0


def win_bonus(result: str) -> int:
    return WIN_BONUS if result == "win" else 0


def points_delta(result: str, match_score: int) -> int:
    """Battle Points of one finished match: the player's own score (+1 per correct word) + 3 for the winner."""
    return max(0, match_score) + win_bonus(result)


def bot_plan(stage: str, rng) -> tuple[float, int, int]:
    """(accuracy for this match, earliest answer ms, latest answer ms) — random inside the stage's limits."""
    lvl = BOT_LEVELS.get(stage, BOT_LEVELS["A1"])
    lo, hi = lvl["accuracy"]
    return lo + (hi - lo) * rng.random(), lvl["time_ms"][0], lvl["time_ms"][1]
