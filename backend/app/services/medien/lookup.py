"""Word look-up for the clickable film subtitles: the German word (or short phrase) a student clicked, answered from the
existing Wörterbuch (`dictionary_entries`) — nothing is translated or invented here.

  exact    the word is a dictionary headword (lemma)          -> entries (translation, article, word type, example)
  form     the word is a known inflected form of a headword    -> entries of that headword (the answer says it is a form)
  similar  neither: headwords that start like it / contain it  -> suggestions only (never shown as a translation)
  none     nothing found                                       -> the player offers the Wörterbuch search

Saving a word uses the Wörterbuch's own `PUT /dictionary/entries/{id}/saved` (the star = the student's saved words)."""

from __future__ import annotations

import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.dictionary import DictionaryEntry
from app.models.user import User
from app.scripts.woerterbuch.source import search_key
from app.services import dictionary as dic

MAX_WORD = 60
MAX_ENTRIES = 4
_EDGE = re.compile(r"^[^\w]+|[^\w]+$")


def clean_word(raw: str) -> str:
    """The word without surrounding punctuation / quotes; inner letters, digits, hyphen, apostrophe and single spaces stay."""
    word = _EDGE.sub("", (raw or "").strip().replace("’", "'").replace("‘", "'"))
    word = re.sub(r"[^\w' \-]", "", word)
    return re.sub(r"\s+", " ", word)[:MAX_WORD]


def _like(key: str) -> str:
    return key.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def lookup(db: Session, user: User, raw: str) -> dict:
    word = clean_word(raw)
    out = {"word": word, "status": "none", "entries": [], "suggestions": []}
    if not word:
        return out
    key = search_key(word)
    if not key:
        return out
    E = DictionaryEntry
    visible = select(E).where(E.is_published.is_(True), E.is_primary.is_(True))
    rows = list(db.scalars(visible.where(E.search_de == key).order_by(E.level, E.source_id).limit(MAX_ENTRIES)))
    status = "exact"
    if not rows:
        status = "form"
        rows = list(db.scalars(visible.where(E.search_forms.like(f"%|{_like(key)}|%", escape="\\"))
                               .order_by(func.length(E.lemma), E.level, E.source_id).limit(MAX_ENTRIES)))
    if rows:
        out["status"] = status
        out["entries"] = [dic.entry_card(db, user, e.word_id) for e in rows]
        return out
    similar = dic.search(db, user, word, None, None, 1, 5)["items"]
    if similar:
        out["status"] = "similar"
        out["suggestions"] = similar
    return out
