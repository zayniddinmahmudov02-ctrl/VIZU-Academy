"""Word filter for the Global Chat.

A hit never punishes anyone: the message is held ("pending") for a moderator,
who approves or hides it and decides about a mute / ban. Moderators' own
messages are not filtered.

Matching is per whole word, never a substring inside another word (no
"Scunthorpe" accidents): the text is NFKC-normalised, lowercased, look-alike
characters are mapped (0→o 1→i 3→e 4→a 5→s 7→t @→a $→s) and letter repeats
are collapsed ("fuuuck" → "fuck"); list entries get the same treatment. An entry ending in
"*" matches every word that starts with it ("хуй*" → "хуйня").

The list is admin-editable (app_settings key below); the code holds the
default list. It covers common insults/strong profanity in Uzbek (Latin and
Cyrillic), Russian (incl. Latin transliteration), German and English — mild
expletives ("Scheiße", "shit") and words that are also normal vocabulary or
names ("dick" is German for thick, "hui" a German interjection) are left out
on purpose. Letters typed apart ("f u c k") are not detected."""

import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.app_setting import AppSetting

SETTING_KEY = "global_chat_word_filter"
MAX_WORDS = 500
MAX_WORD_LENGTH = 40

DEFAULT_WORDS: tuple[str, ...] = (
    # Uzbek (Latin)
    "jalab", "jalap", "qanjiq", "dalbayob", "dalbayop", "skay", "sikay", "sikaman", "sikdim", "sikish", "sikib",
    "sikvoraman", "itvachcha", "haromi", "gandon", "pidaraz", "pidaras",
    # Uzbek (Cyrillic)
    "жалаб", "қанжиқ", "канжик", "далбаёб", "сикай", "сикаман", "итвачча", "ҳароми",
    # Russian (+ Latin transliteration)
    "бля", "блять", "бляд*", "сука", "суки", "хуй*", "хуе*", "хуё*", "пизд*", "ебат*", "ебан*", "ебал*", "ёб*", "еб*ть",
    "мудак*", "гандон*", "долбоёб*", "долбоеб*", "пидор*", "пидар*", "шлюх*", "нахуй", "похуй",
    "blyat", "blyad", "suka", "pizdec", "pizdets", "nahui", "nahuy", "ebat", "yebat", "mudak", "pidor",
    # German
    "arschloch", "hurensohn", "fotze", "wichser", "missgeburt", "schlampe", "hure", "fick*", "spast", "spasti",
    "drecksau", "bastard",
    # English
    "fuck*", "motherfucker*", "bitch*", "asshole*", "cunt*", "whore*", "slut*", "faggot*", "nigger*", "nigga*",
)

_LOOKALIKE = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})
# a word: letters, digits, look-alike symbols and the apostrophes of Uzbek Latin (oʻ, g‘)
_WORD = re.compile(r"[\w@$'ʻʼ‘’`]+")
_APOSTROPHES = re.compile(r"['ʻʼ‘’`]")
_REPEATS = re.compile(r"(.)\1+")


def normalize_word(word: str) -> str:
    word = unicodedata.normalize("NFKC", word).lower().translate(_LOOKALIKE)
    word = _APOSTROPHES.sub("", word).replace("_", "")
    return _REPEATS.sub(r"\1", word)


def _compile(words) -> tuple[set[str], tuple[str, ...]]:
    exact, prefixes = set(), []
    for raw in words:
        raw = (raw or "").strip()
        if not raw:
            continue
        if raw.endswith("*"):
            stem = normalize_word(raw[:-1])
            if len(stem) >= 2:
                prefixes.append(stem)
        elif "*" in raw:
            # "еб*ть": one wildcard in the middle — a stem plus a suffix
            stem, _, tail = raw.partition("*")
            prefixes.append(f"{normalize_word(stem)}\x00{normalize_word(tail)}")
        else:
            exact.add(normalize_word(raw))
    return exact, tuple(prefixes)


def _matches(token: str, exact: set[str], prefixes: tuple[str, ...]) -> bool:
    if token in exact:
        return True
    for p in prefixes:
        if "\x00" in p:
            stem, tail = p.split("\x00", 1)
            if token.startswith(stem) and token.endswith(tail) and len(token) >= len(stem) + len(tail):
                return True
        elif token.startswith(p):
            return True
    return False


def find(text: str, words) -> list[str]:
    """The distinct normalised words of `text` the list matches (empty = clean)."""
    exact, prefixes = _compile(words)
    hits: list[str] = []
    for raw in _WORD.findall(text or ""):
        token = normalize_word(raw)
        if token and token not in hits and _matches(token, exact, prefixes):
            hits.append(token)
    return hits


def settings_row(db: Session) -> AppSetting | None:
    return db.scalar(select(AppSetting).where(AppSetting.key == SETTING_KEY))


def current(db: Session) -> dict:
    row = settings_row(db)
    if row is None or not isinstance(row.value, dict):
        return {"enabled": True, "words": list(DEFAULT_WORDS), "is_default": True, "updated_at": None}
    words = row.value.get("words")
    return {"enabled": bool(row.value.get("enabled", True)),
            "words": [w for w in words if isinstance(w, str)] if isinstance(words, list) else list(DEFAULT_WORDS),
            "is_default": False, "updated_at": row.updated_at}


def check(db: Session, text: str) -> list[str]:
    config = current(db)
    return find(text, config["words"]) if config["enabled"] else []


def clean_list(words: list[str]) -> list[str]:
    out: list[str] = []
    for w in words:
        w = unicodedata.normalize("NFKC", (w or "")).strip().lower()
        if w and len(w) <= MAX_WORD_LENGTH and w not in out:
            out.append(w)
    return out[:MAX_WORDS]
