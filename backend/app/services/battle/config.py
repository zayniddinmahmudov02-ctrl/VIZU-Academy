"""Battle rules in one place: CEFR stages, ranks, timing, scoring, Battle Points, avatars, achievements.

Ranks: every stage (A1 … C1, C1+) has three ranks of RANK_STEP points each, so the rank (and with it the
arena stage) follows from Battle Points alone. Questions come from the stage's words and every stage below
it; a stage without enough published picture words plays with the stages below (A2 players get A1 words
until A2 words are published). C1+ has no source words of its own."""

STAGES = ("A1", "A2", "B1", "B2", "C1", "C1+")
WORD_LEVELS = ("A1", "A2", "B1", "B2", "C1")
RANK_TITLES = ("Einsteiger", "Kämpfer", "Meister")
LEGEND_TITLES = ("Herausforderer", "Elite", "Legende")
RANK_STEP = 150
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
BASE_SCORE = 100
SPEED_BONUS = 50
# a player who has not polled for this long during a match loses it (reconnection window)
AFK_S = 20
# a waiting ranked match whose player stopped polling is dropped
QUEUE_STALE_S = 12
# point windows for ranked matchmaking by waiting time (seconds → max points difference)
MATCH_WINDOWS = ((10, 10), (20, 25), (None, None))
MIN_POOL = ROUNDS + OPTIONS

WIN_POINTS = 25
DRAW_POINTS = 5
LOSS_POINTS = -15
STRENGTH_BONUS_MAX = 10
STREAK_BONUS = 2
STREAK_BONUS_MAX = 10

BOT_ACCURACY = {"A1": 0.6, "A2": 0.65, "B1": 0.7, "B2": 0.72, "C1": 0.75, "C1+": 0.8}
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
    if not correct:
        return 0
    left = max(0.0, 1 - time_ms / (ROUND_S * 1000))
    return BASE_SCORE + round(SPEED_BONUS * left)


def points_delta(result: str, my_points: int, opp_points: int, streak_after: int) -> int:
    """Ranked only. result = win | draw | loss; a stronger opponent gives more and costs less."""
    strength = max(-STRENGTH_BONUS_MAX, min(STRENGTH_BONUS_MAX, round((opp_points - my_points) / 20)))
    if result == "win":
        return WIN_POINTS + strength + min(STREAK_BONUS_MAX, STREAK_BONUS * max(0, streak_after - 1))
    if result == "draw":
        return DRAW_POINTS
    return min(-5, LOSS_POINTS + strength)
