"""Question pool and distractor engine.

Pool: battle_words that are `published`, have a `published` image and belong to the stage's level or a
level below (own level first). Distractors: same category first, then the same word type from the rest
of the pool; never the same lemma, display text or translation, never a pair listed in `conflicts`
(app/data/battle/words.json: one picture could show both). The correct option's position is balanced
over the match (each of the four positions used 2–3 times in ten rounds)."""

import json
import random
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.battle import BattleImage, BattleWord
from app.services.battle import config

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
    return len(pool(db, stage))


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


def build(db: Session, stage: str, rounds: int = config.ROUNDS, rng: random.Random | None = None, bot: bool = False) -> list[dict]:
    rng = rng or random.SystemRandom()
    words = pool(db, stage)
    if len(words) < config.MIN_POOL:
        raise HTTPException(409, "BATTLE_NOT_ENOUGH_WORDS: Bu bosqich uchun hali yetarli rasmli so‘z yo‘q")
    own_level = config.word_levels_up_to(stage)[-1]
    own = [w for w in words if w.level == own_level]
    lower = [w for w in words if w.level != own_level]
    rng.shuffle(own)
    rng.shuffle(lower)
    targets = (own + lower)[:rounds]
    rng.shuffle(targets)
    out = []
    for target, pos in zip(targets, balanced_positions(rounds, rng)):
        wrong = _distractors(target, words, rng, config.OPTIONS - 1)
        if len(wrong) < config.OPTIONS - 1:
            raise HTTPException(409, "BATTLE_NOT_ENOUGH_WORDS")
        opts = [str(w.id) for w in wrong]
        opts.insert(pos, str(target.id))
        q = {"w": str(target.id), "img": str(target.image_id), "opts": opts, "c": pos}
        if bot:
            right = rng.random() < config.BOT_ACCURACY.get(stage, 0.65)
            q["bot"] = {"at": rng.randint(2600, 9500), "choice": pos if right else rng.choice([i for i in range(config.OPTIONS) if i != pos])}
        out.append(q)
    return out
