"""Wörterbuch: search (autocomplete), word card, Random 5 and saved words.

Search runs in the database on folded keys (case, umlauts, ß and Uzbek
apostrophes folded the same way for the stored text and the query), over
the German lemma, the Uzbek translations and the grammatical forms, ranked
exact > prefix > contains — the client never downloads the list. Only the
first row of a same-word group per level (is_primary) and only published
rows are offered.

Random 5 returns five different words, one per level where it can, words
seen in the last days only when nothing else is left."""

import random
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import case, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.dictionary import DictionaryEntry, DictionaryUserWord
from app.models.user import User
from app.scripts.woerterbuch.source import ARTICLES, LEVELS, canonical_uz, search_key

RANDOM_SIZE = 5
ALL_LEVELS = "ALL"
MAX_PAGE_SIZE = 50
# a word seen in Random 5 within this window comes back only when nothing unseen is left
RECENT = timedelta(days=7)
# candidates read per level for one draw
RANDOM_CANDIDATES = 12
ATTRIBUTION = {"name": "Wiktionary", "license": "CC BY-SA 4.0", "url": "https://kaikki.org/dictionary/German/"}
PERSONS = (("ich", "presens_ich"), ("du", "presens_du"), ("er/sie/es", "presens_er_sie_es"), ("wir", "presens_wir"),
           ("ihr", "presens_ihr"), ("sie/Sie", "presens_sie_Sie"))
# extra-data kinds shown on the card (quiz distractors are not meanings and are never shown)
CARD_EXTRA = ("noun_genitive", "noun_plural_variants", "verb_perfekt", "verb_separable", "verb_conjugation_type",
              "conjunction_word_order", "preposition_cases", "grammar_note", "ipa")
GRAMMAR_FROM_WIKTIONARY = ("Nomen", "Verb", "Adjektiv", "Praeposition")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def query_keys(q: str) -> tuple[str, str]:
    """(German key, Uzbek key) of a query — a leading article or "sich" is
    ignored for the German side, so "die Entscheidung" finds Entscheidung."""
    q = q.strip()
    first, _, rest = q.partition(" ")
    de = rest if first.lower() in (*ARTICLES, "sich") and rest else q
    return search_key(de), search_key(canonical_uz(q))


def parse_word_id(word_id: str) -> tuple[str, int]:
    level, _, sid = (word_id or "").partition("-")
    if level not in LEVELS or not sid.isdigit():
        raise HTTPException(status_code=404, detail="Word not found")
    return level, int(sid)


def _check_level(level: str | None) -> str | None:
    if level in (None, "", ALL_LEVELS):
        return None
    if level not in LEVELS:
        raise HTTPException(status_code=422, detail="level: A1, A2, B1, B2, C1 or ALL")
    return level


def _visible():
    E = DictionaryEntry
    return select(E).where(E.is_published.is_(True), E.is_primary.is_(True))


def brief(e: DictionaryEntry, saved: bool = False) -> dict:
    return {"id": e.word_id, "level": e.level, "lemma": e.lemma, "article": e.article, "word_type": e.word_type,
            "translation": e.translation, "status": e.status, "saved": saved}


def card(e: DictionaryEntry, saved: bool = False, also_in: list[str] | None = None) -> dict:
    extra = e.extra or {}
    verb = None
    if e.word_type == "Verb":
        verb = {"infinitive": e.lemma, "praeteritum": e.verb_praeteritum, "partizip_ii": e.verb_partizip_ii,
                "auxiliary": e.verb_auxiliary,
                "praesens": [{"person": p, "form": getattr(e, col)} for p, col in PERSONS if getattr(e, col)] or None}
    adjective = None
    if e.word_type == "Adjektiv":
        adjective = {"positiv": e.lemma, "komparativ": e.adjective_komparativ, "superlativ": e.adjective_superlativ}
    return {
        **brief(e, saved),
        "plural": e.plural,
        "other_translations": extra.get("other_translation", []),
        "verb": verb,
        "adjective": adjective,
        "details": {k: extra[k] for k in CARD_EXTRA if extra.get(k) not in (None, "", [])},
        "example_de": e.example_de,
        "example_uz": e.example_uz,
        "audio_text": e.audio_text,
        "review_note": (e.review or {}).get("suggestion"),
        "also_in": also_in or [],
        "attribution": ATTRIBUTION if e.word_type in GRAMMAR_FROM_WIKTIONARY else None,
    }


def saved_ids(db: Session, user: User, entry_ids: list) -> set:
    if not entry_ids:
        return set()
    W = DictionaryUserWord
    return set(db.scalars(select(W.entry_id).where(W.user_id == user.id, W.saved.is_(True), W.entry_id.in_(entry_ids))))


def _rank_and_match(q: str):
    de, uz = query_keys(q)
    de_e, uz_e = _escape_like(de), _escape_like(uz)
    E = DictionaryEntry
    match = or_(E.search_de.like(f"%{de_e}%", escape="\\"), E.search_uz.like(f"%{uz_e}%", escape="\\"),
                E.search_forms.like(f"%{de_e}%", escape="\\"))
    rank = case(
        (E.search_de == de, 0),
        (E.search_de.like(f"{de_e}%", escape="\\"), 1),
        (E.search_uz.like(f"%|{uz_e}|%", escape="\\"), 2),
        (E.search_forms.like(f"%|{de_e}|%", escape="\\"), 3),
        (or_(E.search_uz.like(f"%|{uz_e}%", escape="\\"), E.search_uz.like(f"% {uz_e}%", escape="\\")), 4),
        (E.search_forms.like(f"%|{de_e}%", escape="\\"), 5),
        (E.search_de.like(f"%{de_e}%", escape="\\"), 6),
        else_=7,
    )
    return match, rank


def _page(page: int, page_size: int) -> tuple[int, int]:
    return max(page, 1), min(max(page_size, 1), MAX_PAGE_SIZE)


def search(db: Session, user: User, q: str, level: str | None = None, word_type: str | None = None,
           page: int = 1, page_size: int = 10) -> dict:
    q = (q or "").strip()
    page, page_size = _page(page, page_size)
    if not q:
        return {"items": [], "total": 0, "page": 1, "page_size": page_size}
    if len(q) > 80:
        raise HTTPException(status_code=422, detail="query too long")
    E = DictionaryEntry
    match, rank = _rank_and_match(q)
    stmt = _visible().where(match)
    if (lv := _check_level(level)):
        stmt = stmt.where(E.level == lv)
    if word_type:
        stmt = stmt.where(E.word_type == word_type)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = list(db.scalars(stmt.order_by(rank, func.length(E.lemma), E.lemma, E.level, E.source_id)
                           .offset((page - 1) * page_size).limit(page_size)))
    saved = saved_ids(db, user, [e.id for e in rows])
    return {"items": [brief(e, e.id in saved) for e in rows], "total": total, "page": page, "page_size": page_size}


def get_entry(db: Session, word_id: str) -> DictionaryEntry:
    level, sid = parse_word_id(word_id)
    E = DictionaryEntry
    entry = db.scalar(select(E).where(E.level == level, E.source_id == sid, E.is_published.is_(True)))
    if entry is None:
        raise HTTPException(status_code=404, detail="Word not found")
    return entry


def _also_in(db: Session, entry: DictionaryEntry) -> list[str]:
    E = DictionaryEntry
    levels = db.scalars(select(E.level).where(E.group_key == entry.group_key, E.level != entry.level,
                                              E.is_published.is_(True)).distinct())
    return sorted(levels, key=LEVELS.index)


def entry_card(db: Session, user: User, word_id: str) -> dict:
    entry = get_entry(db, word_id)
    return card(entry, entry.id in saved_ids(db, user, [entry.id]), _also_in(db, entry))


def meta(db: Session) -> dict:
    E = DictionaryEntry
    rows = dict(db.execute(select(E.level, func.count()).group_by(E.level)).all())
    words = dict(db.execute(select(E.level, func.count()).where(E.is_published.is_(True), E.is_primary.is_(True)).group_by(E.level)).all())
    types = [t for (t,) in db.execute(select(E.word_type).where(E.is_published.is_(True), E.is_primary.is_(True), E.word_type.is_not(None))
                                       .group_by(E.word_type).order_by(func.count().desc()))]
    return {"rows": {lv: rows.get(lv, 0) for lv in LEVELS}, "levels": {lv: words.get(lv, 0) for lv in LEVELS},
            "total": sum(words.values()), "word_types": types, "attribution": ATTRIBUTION}


def _upsert_state(db: Session, user: User, entry_id, seen: bool = False, **sets) -> None:
    """Insert-or-update one (user, word) row — one row per pair, safe under parallel requests."""
    now = _now()
    W = DictionaryUserWord
    stmt = insert(W).values(user_id=user.id, entry_id=entry_id, created_at=now, updated_at=now,
                            seen_count=1 if seen else 0, **sets)
    update = {**sets, "updated_at": now}
    if seen:
        update["seen_count"] = W.__table__.c.seen_count + 1
    db.execute(stmt.on_conflict_do_update(constraint="uq_dictionary_user_word", set_=update))


def random_five(db: Session, user: User, level: str | None = None) -> dict:
    lv = _check_level(level)
    E, W = DictionaryEntry, DictionaryUserWord
    recent = case((W.last_seen_at > _now() - RECENT, 1), else_=0)
    ranked = (
        select(E.id.label("id"), E.level.label("level"), E.search_de.label("key"), recent.label("recent"),
               func.row_number().over(partition_by=E.level, order_by=(recent, func.random())).label("rn"))
        .select_from(E)
        .outerjoin(W, (W.entry_id == E.id) & (W.user_id == user.id))
        .where(E.is_published.is_(True), E.is_primary.is_(True), *([E.level == lv] if lv else []))
        .subquery()
    )
    limit = RANDOM_SIZE * 3 if lv else RANDOM_CANDIDATES
    candidates = db.execute(select(ranked).where(ranked.c.rn <= limit).order_by(ranked.c.level, ranked.c.rn)).all()
    by_level: dict[str, list] = {}
    for c in candidates:
        by_level.setdefault(c.level, []).append(c)

    chosen, keys = [], set()

    def take(c) -> bool:
        if c.id in {x.id for x in chosen} or c.key in keys or len(chosen) >= RANDOM_SIZE:
            return False
        chosen.append(c)
        keys.add(c.key)
        return True

    levels = list(by_level)
    random.shuffle(levels)
    # one word per level first (the same German word never twice in a set) …
    for level_name in levels:
        for c in by_level[level_name]:
            if take(c):
                break
    # … then fill from all levels, not recently seen words first
    rest = [c for cs in by_level.values() for c in cs]
    random.shuffle(rest)
    for c in sorted(rest, key=lambda c: c.recent):
        take(c)

    random.shuffle(chosen)
    ids = [c.id for c in chosen]
    now = _now()
    for entry_id in ids:
        _upsert_state(db, user, entry_id, seen=True, last_seen_at=now)
    db.commit()
    entries = {e.id: e for e in db.scalars(select(E).where(E.id.in_(ids)))} if ids else {}
    saved = saved_ids(db, user, ids)
    return {"level": lv or ALL_LEVELS, "complete": len(ids) == RANDOM_SIZE,
            "items": [card(entries[i], i in saved) for i in ids]}


def set_saved(db: Session, user: User, word_id: str, saved: bool) -> dict:
    entry = get_entry(db, word_id)
    _upsert_state(db, user, entry.id, saved=bool(saved), saved_at=_now() if saved else None)
    db.commit()
    return {"id": entry.word_id, "saved": bool(saved)}


def saved_words(db: Session, user: User, q: str = "", level: str | None = None, page: int = 1, page_size: int = 20) -> dict:
    E, W = DictionaryEntry, DictionaryUserWord
    page, page_size = _page(page, page_size)
    stmt = (select(E, W.saved_at).join(W, W.entry_id == E.id)
            .where(W.user_id == user.id, W.saved.is_(True), E.is_published.is_(True)))
    if (lv := _check_level(level)):
        stmt = stmt.where(E.level == lv)
    order = [W.saved_at.desc().nulls_last(), E.lemma]
    if (q := (q or "").strip()):
        if len(q) > 80:
            raise HTTPException(status_code=422, detail="query too long")
        match, rank = _rank_and_match(q)
        stmt = stmt.where(match)
        order = [rank, *order]
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.execute(stmt.order_by(*order).offset((page - 1) * page_size).limit(page_size)).all()
    counts = dict(db.execute(select(E.level, func.count()).join(W, W.entry_id == E.id)
                             .where(W.user_id == user.id, W.saved.is_(True), E.is_published.is_(True)).group_by(E.level)).all())
    return {"items": [brief(e, True) for e, _ in rows], "total": total, "page": page, "page_size": page_size,
            "by_level": {lv: counts.get(lv, 0) for lv in LEVELS}}
