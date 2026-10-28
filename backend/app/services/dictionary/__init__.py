"""Wörterbuch: search, word card, Random 5 and the student's own word state.

Search runs in the database on normalized keys (case, umlauts, ß and Uzbek
apostrophes folded the same way for the stored text and the query), ranked
exact > prefix > contains, paginated — the client never downloads the list.
Random 5 always returns distinct words, unseen ones first; once a pool is
exhausted the least recently seen words come back."""

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import case, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.dictionary import STATUS_KNOWN, STATUS_UNKNOWN, DictionaryEntry, DictionaryRandomSession, DictionaryUserWord
from app.models.user import User
from app.scripts.woerterbuch.source import ARTICLES, LEVELS, canonical_uz, search_key

RANDOM_SIZE = 5
ALL_LEVELS = "ALL"
MAX_PAGE_SIZE = 50
ATTRIBUTION = {"name": "Wiktionary", "license": "CC BY-SA 4.0", "url": "https://kaikki.org/dictionary/German/"}


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


def brief(entry: DictionaryEntry) -> dict:
    return {"id": entry.stable_id, "german": entry.german, "lemma": entry.lemma, "article": entry.article,
            "part_of_speech": entry.part_of_speech, "cefr_level": entry.cefr_level, "levels": entry.levels,
            "translation": entry.translation}


def card(entry: DictionaryEntry, state: DictionaryUserWord | None = None) -> dict:
    grammar = dict(entry.grammar or {})
    grammar.pop("gloss_en", None)
    return {
        **brief(entry),
        "reflexive": entry.reflexive,
        "translations_extra": entry.translations_extra,
        "definition_de": entry.definition_de,
        "grammar": grammar or None,
        "grammar_source": entry.grammar_source,
        "ipa": entry.ipa,
        "example_de": entry.example_de,
        "example_uz": entry.example_uz,
        "audio_url": entry.audio_url,
        "status": {"translation": entry.translation_status, "grammar": entry.grammar_status, "example": entry.example_status},
        "attribution": ATTRIBUTION if entry.grammar_source.startswith("wiktionary") else None,
        "me": {"saved": bool(state and state.saved), "status": state.status if state else None,
               "seen_count": state.seen_count if state else 0},
    }


def _published():
    return select(DictionaryEntry).where(DictionaryEntry.is_published.is_(True))


def _check_level(level: str | None) -> str | None:
    if level in (None, "", ALL_LEVELS):
        return None
    if level not in LEVELS:
        raise HTTPException(status_code=422, detail="level: A1, A2, B1, B2, C1 or ALL")
    return level


def search(db: Session, q: str, level: str | None = None, pos: str | None = None, page: int = 1, page_size: int = 20) -> dict:
    q = (q or "").strip()
    if not q:
        return {"items": [], "total": 0, "page": 1, "page_size": page_size}
    if len(q) > 80:
        raise HTTPException(status_code=422, detail="query too long")
    page, page_size = max(page, 1), min(max(page_size, 1), MAX_PAGE_SIZE)
    de, uz = query_keys(q)
    de_e, uz_e = _escape_like(de), _escape_like(uz)
    E = DictionaryEntry
    match = or_(E.search_de.like(f"%{de_e}%", escape="\\"), E.search_uz.like(f"%{uz_e}%", escape="\\"))
    stmt = _published().where(match)
    if (level := _check_level(level)):
        stmt = stmt.where(E.levels.contains([level]))
    if pos:
        stmt = stmt.where(E.part_of_speech == pos)
    rank = case(
        (E.search_de == de, 0),
        (E.search_de.like(f"{de_e}%", escape="\\"), 1),
        (or_(E.search_uz == uz, E.search_uz.like(f"{uz_e}|%", escape="\\"), E.search_uz.like(f"%|{uz_e}|%", escape="\\"),
             E.search_uz.like(f"%|{uz_e}", escape="\\")), 2),
        (or_(E.search_uz.like(f"{uz_e}%", escape="\\"), E.search_uz.like(f"%|{uz_e}%", escape="\\")), 3),
        else_=4,
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(rank, func.length(E.lemma), E.lemma).offset((page - 1) * page_size).limit(page_size))
    return {"items": [brief(e) for e in rows], "total": total, "page": page, "page_size": page_size}


def get_entry(db: Session, stable_id: str) -> DictionaryEntry:
    entry = db.scalar(_published().where(DictionaryEntry.stable_id == stable_id))
    if entry is None:
        raise HTTPException(status_code=404, detail="Word not found")
    return entry


def user_state(db: Session, user: User, entry_ids: list) -> dict:
    if not entry_ids:
        return {}
    rows = db.scalars(select(DictionaryUserWord).where(DictionaryUserWord.user_id == user.id, DictionaryUserWord.entry_id.in_(entry_ids)))
    return {r.entry_id: r for r in rows}


def entry_card(db: Session, user: User, stable_id: str) -> dict:
    entry = get_entry(db, stable_id)
    return card(entry, user_state(db, user, [entry.id]).get(entry.id))


def meta(db: Session) -> dict:
    E = DictionaryEntry
    levels = {lv: db.scalar(select(func.count()).select_from(E).where(E.is_published.is_(True), E.levels.contains([lv]))) for lv in LEVELS}
    pos = [p for (p,) in db.execute(select(E.part_of_speech).where(E.is_published.is_(True), E.part_of_speech.is_not(None))
                                     .group_by(E.part_of_speech).order_by(func.count().desc()))]
    total = db.scalar(select(func.count()).select_from(E).where(E.is_published.is_(True)))
    return {"total": total, "levels": levels, "parts_of_speech": pos, "attribution": ATTRIBUTION}


def _upsert_state(db: Session, user: User, entry_id, **values) -> None:
    """Insert-or-update one (user, word) row — safe under parallel requests."""
    now = _now()
    increments = {k: v for k, v in values.items() if k.endswith("_count")}
    sets = {k: v for k, v in values.items() if not k.endswith("_count")}
    stmt = insert(DictionaryUserWord).values(user_id=user.id, entry_id=entry_id, created_at=now, updated_at=now,
                                             **sets, **{k: v for k, v in increments.items()})
    T = DictionaryUserWord.__table__.c
    stmt = stmt.on_conflict_do_update(
        constraint="uq_dictionary_user_word",
        set_={**sets, "updated_at": now, **{k: getattr(T, k) + v for k, v in increments.items()}},
    )
    db.execute(stmt)


def random_five(db: Session, user: User, level: str | None) -> dict:
    lv = _check_level(level)
    E, W = DictionaryEntry, DictionaryUserWord
    pool = select(E.id).where(E.is_published.is_(True))
    if lv:
        pool = pool.where(E.levels.contains([lv]))
    seen = select(W.entry_id).where(W.user_id == user.id, W.seen_count > 0)
    pool_size = db.scalar(select(func.count()).select_from(pool.subquery()))
    unseen_before = db.scalar(select(func.count()).select_from(pool.where(E.id.not_in(seen)).subquery()))
    chosen = list(db.scalars(pool.where(E.id.not_in(seen)).order_by(func.random()).limit(RANDOM_SIZE)))
    if len(chosen) < RANDOM_SIZE:
        # pool exhausted: refill with the least recently seen words, never one twice
        refill = db.scalars(
            select(W.entry_id).join(E, E.id == W.entry_id)
            .where(W.user_id == user.id, W.seen_count > 0, E.id.in_(pool), W.entry_id.not_in(chosen or [None]))
            .order_by(W.last_seen_at.asc().nulls_first(), func.random()).limit(RANDOM_SIZE - len(chosen)))
        chosen += [i for i in refill if i not in chosen]
    entries = {e.id: e for e in db.scalars(select(E).where(E.id.in_(chosen)))} if chosen else {}
    now = _now()
    for entry_id in chosen:
        _upsert_state(db, user, entry_id, last_seen_at=now, seen_count=1)
    db.add(DictionaryRandomSession(user_id=user.id, level=lv or ALL_LEVELS, entry_ids=[entries[i].stable_id for i in chosen],
                                   pool_size=pool_size, unseen_before=unseen_before))
    db.commit()
    states = user_state(db, user, chosen)
    return {"level": lv or ALL_LEVELS, "pool_size": pool_size, "unseen_before": unseen_before,
            "complete": len(chosen) == RANDOM_SIZE, "items": [card(entries[i], states.get(i)) for i in chosen]}


def mark(db: Session, user: User, stable_id: str, status: str) -> dict:
    if status not in (STATUS_KNOWN, STATUS_UNKNOWN):
        raise HTTPException(status_code=422, detail="status: known or unknown")
    entry = get_entry(db, stable_id)
    _upsert_state(db, user, entry.id, status=status, last_marked_at=_now(),
                  **{"known_count" if status == STATUS_KNOWN else "unknown_count": 1})
    db.commit()
    return card(entry, user_state(db, user, [entry.id]).get(entry.id))


def set_saved(db: Session, user: User, stable_id: str, saved: bool) -> dict:
    entry = get_entry(db, stable_id)
    _upsert_state(db, user, entry.id, saved=bool(saved))
    db.commit()
    return card(entry, user_state(db, user, [entry.id]).get(entry.id))


def my_words(db: Session, user: User, kind: str, page: int = 1, page_size: int = 20) -> dict:
    E, W = DictionaryEntry, DictionaryUserWord
    stmt = select(W).join(E, E.id == W.entry_id).where(W.user_id == user.id, E.is_published.is_(True))
    if kind == "saved":
        stmt = stmt.where(W.saved.is_(True))
    elif kind in (STATUS_KNOWN, STATUS_UNKNOWN):
        stmt = stmt.where(W.status == kind)
    else:
        raise HTTPException(status_code=422, detail="kind: saved, known or unknown")
    page, page_size = max(page, 1), min(max(page_size, 1), MAX_PAGE_SIZE)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(W.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)).unique()
    counts = dict(db.execute(select(W.status, func.count()).where(W.user_id == user.id, W.status.is_not(None)).group_by(W.status)).all())
    return {"items": [{**brief(r.entry), "me": {"saved": r.saved, "status": r.status, "seen_count": r.seen_count}} for r in rows],
            "total": total, "page": page, "page_size": page_size,
            "summary": {"saved": db.scalar(select(func.count()).select_from(W).where(W.user_id == user.id, W.saved.is_(True))),
                        "known": counts.get(STATUS_KNOWN, 0), "unknown": counts.get(STATUS_UNKNOWN, 0),
                        "seen": db.scalar(select(func.count()).select_from(W).where(W.user_id == user.id, W.seen_count > 0))}}
