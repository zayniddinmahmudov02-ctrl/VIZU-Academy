"""Wortschatz of a lesson: the course book's word list (vocabularies) as a
student dictionary — search, topic (= lesson) filter, saved / learned state —
and the enrichment of the words from the Wörterbuch.

Data rules (docs/a2-module-separation-report.md):
* The book's word, article and translation are never overwritten.
* Empty grammar fields (word type, plural, Präteritum, Partizip II, Hilfsverb)
  and the example sentence are filled ONLY from a Wörterbuch entry with status
  "verified" and the same article + lemma; `data_sources` records the entry.
* A word the book lists with der / die / das is a noun ("book:article").
* Nothing else is guessed: what is still empty is reported as missing so an
  admin can fill it in.
* Pronunciation: the browser's speech synthesis reads `audio_text`
  (article + word); `audio_url` is played instead when an admin set one."""

import unicodedata
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dictionary import DictionaryEntry
from app.models.lesson import Lesson
from app.models.user import User
from app.models.vocabulary import Vocabulary, VocabularyUserWord

VERIFIED = "verified"
NOUN, VERB = "Nomen", "Verb"
SOURCE_BOOK_ARTICLE = "book:article"
# vocabulary column <- Wörterbuch column
ENTRY_FIELDS = {
    "word_type": "word_type",
    "plural": "plural",
    "verb_praeteritum": "verb_praeteritum",
    "verb_partizip_ii": "verb_partizip_ii",
    "verb_auxiliary": "verb_auxiliary",
    "example_sentence": "example_de",
    "example_translation": "example_uz",
}


def _norm(value: str | None) -> str:
    return unicodedata.normalize("NFC", (value or "").strip()).casefold()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# Enrichment from the Wörterbuch
# ============================================================


def entry_index(db: Session) -> dict[tuple[str, str], DictionaryEntry]:
    """Verified, published entries by (article, lemma); the A2 entry wins
    over other levels, the primary row over duplicates."""
    index: dict[tuple[str, str], DictionaryEntry] = {}
    rank = {"A2": 0, "A1": 1, "B1": 2, "B2": 3, "C1": 4}
    rows = db.scalars(
        select(DictionaryEntry).where(DictionaryEntry.status == VERIFIED, DictionaryEntry.is_published.is_(True))
    )
    for e in sorted(rows, key=lambda e: (rank.get(e.level, 9), not e.is_primary, e.source_id)):
        index.setdefault((_norm(e.article), _norm(e.lemma)), e)
    return index


def match_entry(index: dict, word: Vocabulary) -> DictionaryEntry | None:
    return index.get((_norm(word.article), _norm(word.german_word)))


def enrichment(word: Vocabulary, entry: DictionaryEntry | None) -> dict[str, tuple[str, str]]:
    """Fields to fill: {column: (value, source)} — only empty columns."""
    out: dict[str, tuple[str, str]] = {}
    if entry is not None:
        source = f"woerterbuch:{entry.word_id}"
        is_verb = entry.word_type == VERB
        for column, entry_column in ENTRY_FIELDS.items():
            if column.startswith("verb_") and not is_verb:
                continue
            if column == "plural" and entry.word_type != NOUN:
                continue
            value = (getattr(entry, entry_column) or "").strip()
            if value and not (getattr(word, column) or "").strip():
                out[column] = (value, source)
    if "word_type" not in out and not word.word_type and word.article:
        out["word_type"] = (NOUN, SOURCE_BOOK_ARTICLE)
    return out


def missing_fields(word: Vocabulary) -> list[str]:
    """What an admin still has to fill in (shown, never invented)."""
    missing = []
    if not word.word_type:
        missing.append("word_type")
    if word.word_type == NOUN and not word.plural:
        missing.append("plural")
    if word.word_type == VERB:
        missing += [c for c in ("verb_praeteritum", "verb_partizip_ii", "verb_auxiliary") if not getattr(word, c)]
    if not word.example_sentence:
        missing.append("example_sentence")
    elif not word.example_translation:
        missing.append("example_translation")
    return missing


# ============================================================
# Student
# ============================================================


def word_view(word: Vocabulary, lesson: Lesson, state: VocabularyUserWord | None) -> dict:
    label = f"{word.article} {word.german_word}" if word.article else word.german_word
    return {
        "id": word.id,
        "lesson_id": lesson.id,
        "lesson_number": lesson.number,
        "lesson_title": lesson.title,
        "german_word": word.german_word,
        "article": word.article,
        "plural": word.plural,
        "translation": word.translation,
        "word_type": word.word_type,
        "verb_praeteritum": word.verb_praeteritum,
        "verb_partizip_ii": word.verb_partizip_ii,
        "verb_auxiliary": word.verb_auxiliary,
        "example_sentence": word.example_sentence,
        "example_translation": word.example_translation,
        "audio_url": word.audio_url,
        "audio_text": label,
        "sources": word.data_sources or {},
        "missing": missing_fields(word),
        "saved": bool(state and state.saved),
        "learned": bool(state and state.learned),
    }


def _states(db: Session, user_id, word_ids: list) -> dict:
    if not word_ids:
        return {}
    return {
        s.vocabulary_id: s
        for s in db.scalars(select(VocabularyUserWord).where(VocabularyUserWord.user_id == user_id, VocabularyUserWord.vocabulary_id.in_(word_ids)))
    }


def words_of_lessons(db: Session, user: User, lessons: list[Lesson]) -> list[dict]:
    if not lessons:
        return []
    by_id = {lesson.id: lesson for lesson in lessons}
    words = list(
        db.scalars(
            select(Vocabulary)
            .where(Vocabulary.lesson_id.in_(list(by_id)), Vocabulary.is_published.is_(True))
            .order_by(Vocabulary.order_index, Vocabulary.created_at)
        )
    )
    states = _states(db, user.id, [w.id for w in words])
    words.sort(key=lambda w: (by_id[w.lesson_id].number or 0, w.order_index or 0))
    return [word_view(w, by_id[w.lesson_id], states.get(w.id)) for w in words]


def level_topics(db: Session, user: User, lesson: Lesson) -> list[Lesson]:
    """The lessons ("topics") of the lesson's level whose words the student
    may read: published and open for this student (same rule as the lesson
    itself — a paid lesson's words never leak through the level list)."""
    from app.services.lms import structure
    from app.services.lms.access import lesson_access

    module = lesson.module
    lessons = structure.level_lessons(db, module, published_only=True) if module is not None else [lesson]
    return [lsn for lsn in lessons if lsn.id == lesson.id or lesson_access(db, user, lsn).unlocked]


def set_state(db: Session, user: User, word_id: UUID, saved: bool | None, learned: bool | None) -> dict:
    from app.services.lms.access import ensure_lesson_open

    word = db.get(Vocabulary, word_id)
    if word is None or not word.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WORD_NOT_FOUND")
    lesson = db.get(Lesson, word.lesson_id)
    ensure_lesson_open(db, user, lesson)
    state = db.scalar(select(VocabularyUserWord).where(VocabularyUserWord.user_id == user.id, VocabularyUserWord.vocabulary_id == word.id))
    if state is None:
        state = VocabularyUserWord(user_id=user.id, vocabulary_id=word.id)
        db.add(state)
    now = _now()
    if saved is not None and bool(state.saved) != saved:
        state.saved, state.saved_at = saved, (now if saved else None)
    if learned is not None and bool(state.learned) != learned:
        state.learned, state.learned_at = learned, (now if learned else None)
    db.commit()
    db.refresh(state)
    return word_view(word, lesson, state)
