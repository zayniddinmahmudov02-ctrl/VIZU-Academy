"""Reads the original word lists {A1,A2,B1,B2,C1}-words.csv without changing them.

They are frozen byte copies in app/data/woerterbuch/source/ (docs/ now holds
the converted 22-column files written by export_csv.py; the originals are
also in docs/backup/). The files have no header; every row is
    id, German, correct Uzbek answer, wrong answer 1, wrong answer 2
— the last two are the word game's distractors, NOT translations. They are
kept per source row for the audit trail and never shown as a meaning.

Deduplication: one entry per normalized German headword (article kept, so
"der See" / "die See" stay apart; umlauts kept, so "Bar" / "Bär" stay apart).
A headword found in several levels gets the lowest level as its CEFR level
and keeps every level it was listed in. Different Uzbek answers for the same
headword become one primary translation (most frequent) + alternatives, and
the translation is flagged for review."""

import csv
import hashlib
import io
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

LEVELS = ("A1", "A2", "B1", "B2", "C1")
SOURCE_DIR = Path(__file__).resolve().parents[2] / "data" / "woerterbuch" / "source"
ARTICLES = ("der", "die", "das")

# Malformed rows (wrong column count), repaired explicitly — every repair is
# recorded on the source row and flags the entry for review.
REPAIRS = {
    ("A1", 420): ("weich", "yumshoq", "qattiq", "baland",
                  "6 columns: a stray 'lang' before 'weich'; yumshoq = weich"),
    ("A2", 279): ("leiden", "aziyat chekmoq", "yashirmoq", "qochmoq",
                  "4 columns: German and Uzbek joined without a comma"),
    ("B2", 664): ("auswirken", "ta'sir qilmoq", "natija bermoq", "aks etmoq",
                  "4 columns: German and Uzbek joined without a comma"),
    ("C1", 28): ("unter der Voraussetzung, dass", "sharti bilan", "faqat ma’lum holatda", "oldindan belgilangan asosda",
                 "6 columns: the comma inside the conjunction split the German column"),
}

_APOSTROPHES = "'`´ʻʼ‘’"


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def canonical_uz(text: str) -> str:
    """One spelling for the Uzbek o‘/g‘ letters and the tutuq belgisi, so
    "to'lamoq" and "to‘lamoq" are the same translation."""
    text = clean(text)
    text = re.sub(rf"([oOgG])[{_APOSTROPHES}]", lambda m: m.group(1) + "‘", text)
    return re.sub(rf"(?<![oOgG])[{_APOSTROPHES}]", "’", text)


def headword_key(german: str) -> str:
    """Deduplication key: case-insensitive, umlauts and ß kept."""
    return clean(german).casefold()


def search_key(text: str) -> str:
    """Search key used for both the stored value and the query: case-folded,
    umlauts / ß folded (ä, ae -> a ...), Uzbek apostrophes removed."""
    t = clean(text).casefold()
    t = t.replace("ß", "ss")
    for src, dst in (("ä", "a"), ("ö", "o"), ("ü", "u"), ("ae", "a"), ("oe", "o"), ("ue", "u")):
        t = t.replace(src, dst)
    t = re.sub(rf"[{_APOSTROPHES}]", "", t)
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode() or t


def stable_id(key: str) -> str:
    return "wb-" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def split_headword(german: str) -> tuple[str | None, str, bool]:
    """(article, bare lemma, reflexive) — 'die Entscheidung' -> ('die', 'Entscheidung', False)."""
    g = clean(german)
    first, _, rest = g.partition(" ")
    # "die politische Legitimation hinterfragen" ends in a verb: a phrase,
    # not a noun with an article
    if first.lower() in ARTICLES and rest and rest.split(" ")[-1][:1].isupper():
        return first.lower(), rest, False
    if first.lower() == "sich" and rest:
        return None, rest, True
    return None, g, False


@dataclass
class SourceRow:
    level: str
    row_id: int
    german: str
    correct: str
    wrong: tuple[str, str]
    repaired: str | None = None


@dataclass
class Entry:
    key: str
    german: str
    article: str | None
    lemma: str
    reflexive: bool
    levels: list[str] = field(default_factory=list)
    rows: list[SourceRow] = field(default_factory=list)

    @property
    def cefr_level(self) -> str:
        return min(self.levels, key=LEVELS.index)

    @property
    def stable_id(self) -> str:
        return stable_id(self.key)

    def translations(self) -> list[str]:
        """Most frequent answer first; ties keep the order of first appearance
        (lowest level, lowest row id)."""
        counts = Counter(canonical_uz(r.correct) for r in self.rows)
        first = {}
        for i, r in enumerate(self.rows):
            first.setdefault(canonical_uz(r.correct), i)
        return sorted(counts, key=lambda t: (-counts[t], first[t]))

    def review_reasons(self) -> list[str]:
        reasons = []
        if len(self.translations()) > 1:
            reasons.append("translation:variants")
        if len(set(self.levels)) > 1:
            reasons.append("level:listed_in_" + "+".join(sorted(set(self.levels), key=LEVELS.index)))
        if any(r.repaired for r in self.rows):
            reasons.append("source:repaired_row")
        return reasons


def read_rows(level: str, path: Path | None = None) -> list[SourceRow]:
    path = path or SOURCE_DIR / f"{level}-words.csv"
    rows = []
    for raw in csv.reader(io.StringIO(path.read_bytes().decode("utf-8"))):
        if not raw:
            continue
        row_id = int(raw[0])
        if (level, row_id) in REPAIRS:
            de, ok, w1, w2, why = REPAIRS[(level, row_id)]
            rows.append(SourceRow(level, row_id, clean(de), clean(ok), (clean(w1), clean(w2)), repaired=why))
            continue
        if len(raw) != 5:
            raise ValueError(f"{path.name} row {row_id}: {len(raw)} columns and no repair rule")
        rows.append(SourceRow(level, row_id, clean(raw[1]), clean(raw[2]), (clean(raw[3]), clean(raw[4]))))
    return rows


def load_entries(docs_dir: Path | None = None) -> list[Entry]:
    entries: dict[str, Entry] = {}
    for level in LEVELS:
        path = (docs_dir / f"{level}-words.csv") if docs_dir else None
        for row in read_rows(level, path):
            key = headword_key(row.german)
            if key not in entries:
                article, lemma, reflexive = split_headword(row.german)
                entries[key] = Entry(key, row.german, article, lemma, reflexive)
            entry = entries[key]
            entry.rows.append(row)
            if level not in entry.levels:
                entry.levels.append(level)
    return list(entries.values())
