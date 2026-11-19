"""Question pool and distractor engine.

Picture rounds: battle_words that are `published`, have a `published` image and belong to the stage's level or a
level below (own level first). Distractors: same category first, then the same word type from the rest
of the pool; never the same lemma, display text or translation, never a pair listed in `conflicts`
(app/data/battle/words.json: one picture could show both). The correct option's position is balanced
over the match (each of the four positions used 2–3 times in ten rounds).

Text rounds (2026-11-19, question_bank): when the stage's own level has at least ROUNDS published text questions, a match plays
them — mixed with PICTURE_ROUNDS picture rounds when the level has its own picture words (A1 today), so every round fits the
player's level; a word never appears twice in one match, the players' recent questions are avoided, A2+ matches carry at least
MIN_GRAMMAR grammar questions. Without text questions the stage plays picture rounds exactly as before."""

import json
import random
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.battle import BattleImage, BattleWord
from app.services.battle import config, question_bank

DATA = Path(__file__).resolve().parents[2] / "data" / "battle" / "words.json"


@lru_cache(maxsize=1)
def word_data() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def categories() -> dict:
    return word_data()["categories"]


@lru_cache(maxsize=1)
def conflict_pairs() -> frozenset:
    return frozenset(frozenset(pair) for pair in word_data()["conflicts"])


def in_conflict(a: str, b: str) -> bool:
    return frozenset((a, b)) in conflict_pairs()


def pool(db: Session, stage: str) -> list[BattleWord]:
    levels = config.word_levels_up_to(stage)
    return list(db.execute(
        select(BattleWord).join(BattleImage, BattleImage.id == BattleWord.image_id)
        .where(BattleWord.status == "published", BattleImage.status == "published", BattleWord.level.in_(levels))
    ).scalars())


def pool_size(db: Session, stage: str) -> int:
    """Picture words a stage can play (its own level and the levels below)."""
    return len(pool(db, stage))


def readiness(db: Session, stage: str) -> dict:
    """What a stage can play: picture words (own level + below), text questions of its own level, playable or not."""
    pictures = pool_size(db, stage)
    text = question_bank.pool_size(db, question_bank.text_level(stage))
    return {"pictures": pictures, "text": text, "pool": pictures + text,
            "ready": text >= config.ROUNDS or pictures >= config.MIN_POOL}


def _distractors(target: BattleWord, words: list[BattleWord], rng: random.Random, n: int) -> list[BattleWord]:
    def ok(w: BattleWord, chosen: list[BattleWord]) -> bool:
        if w.id == target.id or w.lemma == target.lemma or w.display == target.display or w.translation.strip() == target.translation.strip():
            return False
        if in_conflict(w.lemma, target.lemma):
            return False
        return all(w.lemma != c.lemma and w.display != c.display and not in_conflict(w.lemma, c.lemma) for c in chosen)

    same = [w for w in words if w.category == target.category]
    rest = [w for w in words if w.category != target.category]
    rng.shuffle(same)
    rng.shuffle(rest)
    chosen: list[BattleWord] = []
    for w in same + rest:
        if len(chosen) == n:
            break
        if ok(w, chosen):
            chosen.append(w)
    return chosen


def balanced_positions(rounds: int, rng: random.Random) -> list[int]:
    positions = [i % config.OPTIONS for i in range(rounds)]
    rng.shuffle(positions)
    return positions


def _picture_round(target: BattleWord, words: list[BattleWord], pos: int, rng: random.Random) -> dict:
    wrong = _distractors(target, words, rng, config.OPTIONS - 1)
    if len(wrong) < config.OPTIONS - 1:
        raise HTTPException(409, "BATTLE_NOT_ENOUGH_WORDS")
    opts = [str(w.id) for w in wrong]
    opts.insert(pos, str(target.id))
    return {"w": str(target.id), "img": str(target.image_id), "opts": opts, "c": pos}


def build(db: Session, stage: str, rounds: int = config.ROUNDS, rng: random.Random | None = None, bot: bool = False,
          avoid: set[str] | None = None) -> list[dict]:
    """The rounds of a new match. `avoid` = question ids the players saw in their last matches (used only when nothing else is left)."""
    rng = rng or random.SystemRandom()
    words = pool(db, stage)
    own_level = config.word_levels_up_to(stage)[-1]
    own = [w for w in words if w.level == own_level]
    text_pool = question_bank.pool(db, question_bank.text_level(stage))
    if len(text_pool) >= rounds:
        n_pic = min(config.PICTURE_ROUNDS, rounds) if len(own) >= config.MIN_POOL else 0
        rng.shuffle(own)
        pictures = own[:n_pic]
        min_grammar = 0 if question_bank.text_level(stage) == "A1" else config.MIN_GRAMMAR
        texts = question_bank.pick(text_pool, rounds - n_pic, rng, avoid_ids=avoid or set(), avoid_refs={w.lemma for w in pictures},
                                   min_grammar=min_grammar)
        if len(texts) < rounds - n_pic:
            raise HTTPException(409, "BATTLE_NOT_ENOUGH_WORDS")
        plan: list = [("pic", w) for w in pictures] + [("text", q) for q in texts]
        rng.shuffle(plan)
    else:  # no (or too few) text questions for this level: picture rounds as before
        if len(words) < config.MIN_POOL:
            raise HTTPException(409, "BATTLE_NOT_ENOUGH_WORDS: Bu bosqich uchun hali yetarli rasmli so‘z yo‘q")
        lower = [w for w in words if w.level != own_level]
        rng.shuffle(own)
        rng.shuffle(lower)
        targets = (own + lower)[:rounds]
        rng.shuffle(targets)
        plan = [("pic", w) for w in targets]
    out = []
    accuracy, t_min, t_max = config.bot_plan(stage, rng) if bot else (0.0, 0, 0)
    for (kind, item), pos in zip(plan, balanced_positions(rounds, rng)):
        q = _picture_round(item, words, pos, rng) if kind == "pic" else question_bank.round_entry(item, pos, rng)
        if bot:
            n_opts = len(q["opts"])
            right = rng.random() < accuracy  # per-stage strength (config.BOT_LEVELS); the plan never leaves the server
            q["bot"] = {"at": rng.randint(t_min, t_max), "choice": q["c"] if right else rng.choice([i for i in range(n_opts) if i != q["c"]])}
        out.append(q)
    return out
