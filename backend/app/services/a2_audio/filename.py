"""Reads Unterricht number, audio kind and part from an A2 audio file name.

The names the A2 audio was delivered with (docs/a2-media-manifest.md):

    A2 1.Unterricht Hören.m4a      -> 1, HOEREN
    A2 4.Unterricht Text 2.mp3     -> 4, TEXT, part 2
    A2 6.Unterricht.mp3            -> 6, UNTERRICHT
    A2 11.Unterricht Teil_3.m4a    -> 11, UNTERRICHT, part 3

The result is only a suggestion the admin confirms or corrects; it never
links a file to a lesson by itself. A name that does not follow the pattern
is "not recognised" (all fields None). A name that names another level
(A1, B1, ...) is flagged so it cannot slip into A2 by mistake."""

import re
import unicodedata
from pathlib import PurePath

from app.models.a2_audio_asset import KIND_HOEREN, KIND_OTHER, KIND_TEXT, KIND_UNTERRICHT

# "Unterricht" also as printed in the book ("UNTERICHT") and the course's Uzbek "dars"
_LESSON_WORD = r"(?:unterricht|unterrich|untericht|lektion|lesson|dars)"
_PATTERN = re.compile(rf"^\s*(?P<level>[abc])\s*(?P<lvl>[12])\b[\s.\-]*(?P<n>\d{{1,2}})\s*[.\-]?\s*{_LESSON_WORD}\b(?P<rest>.*)$", re.I)
_PART = re.compile(r"\b(?P<word>teil|text|part)\s*[.\-#]?\s*(?P<n>\d{1,2})\b", re.I)  # a book "Track 27" is not a part
_HOEREN = re.compile(r"\b(?:hören|horen|hoeren|hörverstehen|hörtext)\b", re.I)


def _normalise(name: str) -> str:
    stem = PurePath(name or "").name
    if "." in stem:
        stem = stem.rsplit(".", 1)[0]  # the extension is checked separately (content decides the format)
    stem = unicodedata.normalize("NFC", stem)  # macOS uploads "Hören" decomposed
    return re.sub(r"\s+", " ", stem.replace("_", " ")).strip()


def parse(name: str) -> dict:
    """{"recognized", "unterricht", "audio_kind", "part", "title", "other_level"}"""
    title = _normalise(name)
    out = {"recognized": False, "unterricht": None, "audio_kind": None, "part": None, "title": title or "Audio", "other_level": None}
    m = _PATTERN.match(title)
    if not m:
        return out
    level = f"{m['level'].upper()}{m['lvl']}"
    if level != "A2":
        out["other_level"] = level
        return out
    rest = m["rest"].strip(" .-")
    part = _PART.search(rest)
    if part:
        kind = KIND_TEXT if part["word"].lower() == "text" else (KIND_HOEREN if _HOEREN.search(rest) else KIND_UNTERRICHT)
    elif _HOEREN.search(rest):
        kind = KIND_HOEREN
    elif not rest:
        kind = KIND_UNTERRICHT
    else:
        kind = KIND_OTHER
    out.update(recognized=True, unterricht=int(m["n"]), audio_kind=kind, part=int(part["n"]) if part else None)
    return out
