"""Wortschatz tests built from a lesson's own words (pure, deterministic).

Seven test types, each one exercise set (skill WORTSCHATZ, source "vizu"),
graded on the server like every other set — the key lives in the option rows
/ `config`, never in the student view:

  1 bedeutung   German word -> Uzbek translation      (multiple choice)
  2 uebersetzung Uzbek translation -> German word     (multiple choice)
  3 artikel     der / die / das                       (multiple choice)
  4 plural      the plural form                       (short answer)
  5 verbformen  Präteritum + Perfekt (Hilfsverb, Partizip II) (gap text)
  6 luecke      the word in its example sentence       (gap text, typed)
  7 kontext     the word in its example sentence       (gap text, 3 options)

Rules:
* Only stored data is used: the book's word / article / translation and the
  fields filled from VERIFIED Wörterbuch entries. A word without the data a
  type needs is simply not asked in that type — nothing is invented.
* Distractors are other words of the same lesson (same word type for 2 and 7,
  a different translation), so the options are plausible and unambiguous;
  a word whose translation is shared by another word is not asked in 1 / 2.
* No repetition inside a set: every word at most once, no duplicate question
  text. Types 1 / 2 and 6 / 7 split the words between them, so one example
  sentence is never asked twice.
* At most MAX_QUESTIONS per set; the words are taken evenly across the list.
* Gap sentences show the Uzbek translation of the sentence as the hint."""

import hashlib
import re

MAX_QUESTIONS = 15
MIN_QUESTIONS = 3
ARTICLES = ("der", "die", "das")
AUX = {"haben": "hat", "sein": "ist"}

TYPES = {
    # the book's own meaning of the word — Uzbek, or a German explanation where the book gives one (A2 L9)
    "bedeutung": ("Wortschatz-Test: Bedeutung", "Nemischa so'zning ma'nosini (tarjimasini) tanlang."),
    "uebersetzung": ("Wortschatz-Test: Übersetzung", "Ma'noga (tarjimaga) mos nemischa so'zni tanlang."),
    "artikel": ("Wortschatz-Test: Artikel", "To'g'ri artiklni tanlang: der, die yoki das."),
    "plural": ("Wortschatz-Test: Plural", "Otning ko'plik shaklini yozing (artiklsiz)."),
    "verbformen": ("Wortschatz-Test: Verbformen", "Fe'lning Präteritum va Perfekt shakllarini yozing (er/sie/es)."),
    "luecke": ("Wortschatz-Test: Lückentext", "Gapdagi bo'sh joyni darsdagi so'z bilan to'ldiring. Qavsda — gapning tarjimasi."),
    "kontext": ("Wortschatz-Test: Kontext", "Gapga mos so'zni tanlang. Qavsda — gapning tarjimasi."),
}
ORDER = tuple(TYPES)


def _norm(value) -> str:
    return " ".join(str(value or "").split()).casefold()


def _h(*parts) -> str:
    return hashlib.sha256(":".join(str(p) for p in parts).encode()).hexdigest()


def _get(w, key):
    return w.get(key) if isinstance(w, dict) else getattr(w, key, None)


def _label(w) -> str:
    article = _get(w, "article")
    return f"{article} {_get(w, 'german_word')}" if article else _get(w, "german_word")


def _spread(items: list, n: int = MAX_QUESTIONS) -> list:
    """n items taken evenly across the list (all of them if fewer)."""
    if len(items) <= n:
        return list(items)
    step = len(items) / n
    return [items[int(i * step)] for i in range(n)]


def _mc(question: str, correct: str, distractors: list[str], explanation: str, seed: str) -> dict:
    options = [correct, *distractors]
    options.sort(key=lambda o: _h(seed, o))
    return {
        "question": question,
        "question_type": "MULTIPLE_CHOICE",
        "points": 1,
        "explanation": explanation,
        "options": [{"text": o, "is_correct": _norm(o) == _norm(correct)} for o in options],
        "config": None,
    }


def _pick(pool: list[str], exclude: set[str], seed: str, n: int) -> list[str]:
    seen, out = set(exclude), []
    for value in sorted(pool, key=lambda v: _h(seed, v)):
        if _norm(value) not in seen:
            seen.add(_norm(value))
            out.append(value)
        if len(out) == n:
            break
    return out


def _meaning_words(words: list) -> list:
    """Words whose translation is unique in the lesson (else 1 / 2 would be ambiguous)."""
    counts: dict[str, int] = {}
    for w in words:
        counts[_norm(_get(w, "translation"))] = counts.get(_norm(_get(w, "translation")), 0) + 1
    return [w for w in words if _norm(_get(w, "translation")) and counts[_norm(_get(w, "translation"))] == 1]


def _bedeutung(words: list, all_words: list) -> list[dict]:
    translations = [_get(w, "translation") for w in all_words]
    out = []
    for w in words:
        d = _pick(translations, {_norm(_get(w, "translation"))}, f"b:{_get(w, 'german_word')}", 3)
        if len(d) < 2:
            continue
        out.append(_mc(f"„{_label(w)}“ — ma'nosi qaysi?", _get(w, "translation"), d, f"{_label(w)} — {_get(w, 'translation')}",
                       f"b:{_get(w, 'german_word')}"))
    return out


def _uebersetzung(words: list, all_words: list) -> list[dict]:
    out = []
    for w in words:
        same_type = [_label(x) for x in all_words if _get(x, "word_type") == _get(w, "word_type")] if _get(w, "word_type") else []
        pool = same_type if len(same_type) >= 4 else [_label(x) for x in all_words]
        d = _pick(pool, {_norm(_label(w))}, f"u:{_get(w, 'german_word')}", 3)
        if len(d) < 2:
            continue
        out.append(_mc(f"„{_get(w, 'translation')}“ — qaysi nemischa so'z?", _label(w), d, f"{_get(w, 'translation')} — {_label(w)}",
                       f"u:{_get(w, 'german_word')}"))
    return out


def _plural_only(w) -> bool:
    """The listed form is already the plural (die Medien): no gender to ask, no
    plural to form. Masculine / neuter nouns with an unchanged plural (der
    Lehrer, das Unternehmen) are ordinary words; a feminine noun never has an
    unchanged plural, so "die" + plural == word means a plural form."""
    return _get(w, "article") == "die" and _norm(_get(w, "plural")) == _norm(_get(w, "german_word"))


def _artikel(words: list) -> list[dict]:
    out = []
    for w in words:
        article, word = _get(w, "article"), _get(w, "german_word") or ""
        if article not in ARTICLES or "/" in word or _plural_only(w):
            continue
        out.append({
            "question": f"___ {word}",
            "question_type": "MULTIPLE_CHOICE",
            "points": 1,
            "explanation": f"{article} {word} — {_get(w, 'translation')}",
            "options": [{"text": a, "is_correct": a == article} for a in ARTICLES],
            "config": None,
        })
    return out


def _plural(words: list) -> list[dict]:
    out = []
    for w in words:
        plural, word = (_get(w, "plural") or "").strip(), _get(w, "german_word") or ""
        if _get(w, "word_type") != "Nomen" or not plural or plural in ("-", "—") or "/" in word or _plural_only(w):
            continue
        accepted = [plural, f"die {plural}"]
        out.append({
            "question": f"{_label(w)} → die ___",
            "question_type": "SHORT_ANSWER",
            "points": 1,
            "explanation": f"{_label(w)} — die {plural}",
            "options": [],
            "config": {"accepted": accepted, "case_sensitive": False, "max_length": 80},
        })
    return out


def _verbformen(words: list) -> list[dict]:
    out = []
    for w in words:
        prt, p2, aux = (_get(w, "verb_praeteritum") or "").strip(), (_get(w, "verb_partizip_ii") or "").strip(), AUX.get((_get(w, "verb_auxiliary") or "").strip())
        if _get(w, "word_type") != "Verb" or not prt or not p2 or not aux:
            continue
        inf = _get(w, "german_word")
        out.append({
            "question": f"{inf} — {_get(w, 'translation')}",
            "question_type": "GAP_FILL",
            "points": 1,
            "explanation": f"{inf} — er {prt} — er {aux} {p2}",
            "options": [],
            "config": {
                "text": f"Präteritum: er [[prt]]\nPerfekt: er [[aux]] [[p2]]",
                "gaps": {"prt": {"accepted": [prt]}, "aux": {"accepted": [aux], "options": ["hat", "ist"]}, "p2": {"accepted": [p2]}},
                "case_sensitive": False,
            },
        })
    return out


def _sentence_gap(w) -> tuple[str, str] | None:
    """(sentence with [[w]], the form that fills it) when the word itself —
    the lemma, or for a noun its plural — occurs as a whole word in the
    example sentence; otherwise None (inflected forms are not guessed)."""
    sentence, word = (_get(w, "example_sentence") or "").strip(), (_get(w, "german_word") or "").strip()
    if not sentence or not _get(w, "example_translation") or not word or "/" in word or " " in word:
        return None
    candidates = [word]
    if _get(w, "word_type") == "Nomen" and _get(w, "plural"):
        candidates.append(_get(w, "plural").strip())
    for form in candidates:
        m = re.search(rf"(?<![\wÄÖÜäöüß]){re.escape(form)}(?![\wÄÖÜäöüß])", sentence, flags=re.IGNORECASE)
        if m:
            return sentence[: m.start()] + "[[w]]" + sentence[m.end():], m.group(0)
    return None


def _luecke(words: list) -> list[dict]:
    out = []
    for w in words:
        gap = _sentence_gap(w)
        if gap is None:
            continue
        text, form = gap
        out.append({
            "question": f"({_get(w, 'example_translation')})",
            "question_type": "GAP_FILL",
            "points": 1,
            "explanation": _get(w, "example_sentence"),
            "options": [],
            "config": {"text": text, "gaps": {"w": {"accepted": [form]}}, "case_sensitive": False},
        })
    return out


def _kontext(words: list, all_words: list) -> list[dict]:
    out = []
    for w in words:
        gap = _sentence_gap(w)
        if gap is None:
            continue
        text, form = gap
        same = [x for x in all_words if _get(x, "word_type") == _get(w, "word_type") and " " not in (_get(x, "german_word") or "")
                and "/" not in (_get(x, "german_word") or "") and _norm(_get(x, "translation")) != _norm(_get(w, "translation"))]
        pool = [_get(x, "german_word") for x in same]
        if form != _get(w, "german_word") and _get(w, "word_type") == "Nomen":  # the sentence uses the plural
            pool = [_get(x, "plural") for x in same if _get(x, "plural")]
        d = _pick(pool, {_norm(form)}, f"k:{_get(w, 'german_word')}", 2)
        if len(d) < 2:
            continue
        options = sorted([form, *d], key=lambda o: _h(f"k:{_get(w, 'german_word')}", o))
        out.append({
            "question": f"({_get(w, 'example_translation')})",
            "question_type": "GAP_FILL",
            "points": 1,
            "explanation": _get(w, "example_sentence"),
            "options": [],
            "config": {"text": text, "gaps": {"w": {"accepted": [form], "options": options}}, "case_sensitive": False},
        })
    return out


def _dedupe(questions: list[dict]) -> list[dict]:
    seen, out = set(), []
    for q in questions:
        key = (_norm(q["question"]), _norm((q.get("config") or {}).get("text")))
        if key not in seen:
            seen.add(key)
            out.append(q)
    return out


def build_sets(words: list) -> list[dict]:
    """The lesson's Wortschatz test sets: [{"key", "title", "instruction",
    "source": "vizu", "questions": [...]}] — a type with fewer than
    MIN_QUESTIONS possible questions is left out."""
    words = [w for w in words if (_get(w, "german_word") or "").strip() and (_get(w, "translation") or "").strip()]
    meaning = _meaning_words(words)
    half_a, half_b = meaning[0::2], meaning[1::2]
    with_sentence = [w for w in words if _sentence_gap(w)]
    built = {
        "bedeutung": _bedeutung(_spread(half_a), words),
        "uebersetzung": _uebersetzung(_spread(half_b), words),
        "artikel": _spread(_artikel(words)),
        "plural": _spread(_plural(words)),
        "verbformen": _spread(_verbformen(words)),
        "luecke": _spread(_luecke(with_sentence[0::2])),
        "kontext": _spread(_kontext(with_sentence[1::2], words)),
    }
    out = []
    for key in ORDER:
        questions = _dedupe(built[key])
        if len(questions) < MIN_QUESTIONS:
            continue
        title, instruction = TYPES[key]
        out.append({"key": key, "title": title, "instruction": instruction, "source": "vizu", "questions": questions})
    return out
