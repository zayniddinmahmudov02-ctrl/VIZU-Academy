"""Reads the Wörterbuch source files in docs/ — the source of truth for the site.

  {A1..C1}-words.csv              22 columns, one row per word-list row
  worterbuch-extra-data.csv       level, id, lemma, kind, value — data the
                                  22 columns have no place for (other
                                  translations, quiz distractors, genitive …)
  worterbuch-needs-review.csv     level, id, …, priority, reasons, suggestion
  worterbuch-original-counts.csv  expected row counts per level

Everything is validated before anything is written: a file with a wrong
header, a broken row, a duplicate id or an unknown status stops the import
with a list of errors. Nothing is guessed or filled in here."""

import csv
import io
import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from app.scripts.woerterbuch.source import LEVELS, canonical_uz, clean, search_key

DOCS_DIR = Path(__file__).resolve().parents[4] / "docs"
COLUMNS = ("id", "level", "lemma", "word_type", "article", "plural", "translation", "verb_praeteritum", "verb_partizip_ii",
           "verb_auxiliary", "presens_ich", "presens_du", "presens_er_sie_es", "presens_wir", "presens_ihr", "presens_sie_Sie",
           "adjective_komparativ", "adjective_superlativ", "example_de", "example_uz", "audio_text", "status")
PRESENS = ("presens_ich", "presens_du", "presens_er_sie_es", "presens_wir", "presens_ihr", "presens_sie_Sie")
FORM_COLUMNS = ("plural", "verb_praeteritum", "verb_partizip_ii", *PRESENS, "adjective_komparativ", "adjective_superlativ")
STATUSES = ("verified", "needs_review")
ARTICLES = ("", "der", "die", "das")
# review reasons saying the headword itself is not correct German: kept, never shown
HIDDEN_REASONS = ("invalid_lemma:", "misspelling:", "wrong_article:")
# extra-data kinds whose value was written as JSON (list / dict / bool)
JSON_KINDS = ("noun_plural_variants", "verb_separable", "conjunction_word_order", "preposition_cases")
LIST_KINDS = ("other_translation",)


@dataclass
class WordRow:
    level: str
    source_id: int
    values: dict
    extra: dict = field(default_factory=dict)
    review: dict | None = None

    @property
    def key(self) -> tuple[str, int]:
        return self.level, self.source_id

    @property
    def group_key(self) -> str:
        """Same headword + word type = a repeat of the same word (never across word types)."""
        v = self.values
        return f"{clean(' '.join(p for p in (v['article'], v['lemma']) if p)).casefold()}|{v['word_type']}"

    @property
    def hidden(self) -> bool:
        return any(r.startswith(HIDDEN_REASONS) for r in (self.review or {}).get("reasons", []))


@dataclass
class Loaded:
    rows: list[WordRow]
    errors: list[str]
    warnings: list[str]


def _read(path: Path, errors: list[str]) -> list[list[str]] | None:
    try:
        text = path.read_bytes().decode("utf-8")
    except FileNotFoundError:
        errors.append(f"{path.name}: file not found")
        return None
    except UnicodeDecodeError as exc:
        errors.append(f"{path.name}: not UTF-8 ({exc})")
        return None
    return list(csv.reader(io.StringIO(text.lstrip("﻿"))))


def read_level(path: Path, level: str, errors: list[str]) -> list[WordRow]:
    raw = _read(path, errors)
    if raw is None:
        return []
    if not raw or tuple(raw[0]) != COLUMNS:
        errors.append(f"{path.name}: header is not the 22-column Wörterbuch format")
        return []
    rows, seen = [], set()
    for n, r in enumerate(raw[1:], start=2):
        if not r:
            continue
        where = f"{path.name} line {n}"
        if len(r) != len(COLUMNS):
            errors.append(f"{where}: {len(r)} columns, expected {len(COLUMNS)}")
            continue
        v = dict(zip(COLUMNS, (clean(c) for c in r)))
        try:
            source_id = int(v["id"])
        except ValueError:
            errors.append(f"{where}: id {v['id']!r} is not a number")
            continue
        if v["level"] != level:
            errors.append(f"{where}: level {v['level']!r} in the {level} file")
        if source_id in seen:
            errors.append(f"{where}: duplicate id {source_id}")
        if not v["lemma"] or not v["translation"]:
            errors.append(f"{where}: lemma and translation are required")
        if v["status"] not in STATUSES:
            errors.append(f"{where}: status {v['status']!r} (verified or needs_review)")
        if v["article"] not in ARTICLES:
            errors.append(f"{where}: article {v['article']!r}")
        seen.add(source_id)
        rows.append(WordRow(level, source_id, v))
    return rows


def _extra_value(kind: str, value: str):
    if kind in JSON_KINDS:
        try:
            return json.loads(value)
        except ValueError:
            return value
    if kind == "quiz_distractors":
        return [p.strip() for p in value.split(" | ") if p.strip()]
    return value


def read_extra(path: Path, errors: list[str]) -> dict[tuple[str, int], dict]:
    raw = _read(path, errors)
    out: dict[tuple[str, int], dict] = defaultdict(dict)
    if raw is None:
        return out
    if not raw or raw[0] != ["level", "id", "lemma", "kind", "value"]:
        errors.append(f"{path.name}: unexpected header")
        return out
    for n, r in enumerate(raw[1:], start=2):
        if len(r) != 5 or not r[1].isdigit():
            errors.append(f"{path.name} line {n}: malformed row")
            continue
        level, sid, _, kind, value = r
        extra = out[(level, int(sid))]
        if kind in LIST_KINDS:
            extra.setdefault(kind, []).append(value)
        else:
            extra[kind] = _extra_value(kind, value)
    return out


def read_review(path: Path, errors: list[str]) -> dict[tuple[str, int], dict]:
    raw = _read(path, errors)
    if raw is None:
        return {}
    header = ["level", "id", "lemma", "word_type", "translation", "priority", "reasons", "suggestion"]
    if not raw or raw[0] != header:
        errors.append(f"{path.name}: unexpected header")
        return {}
    out = {}
    for n, r in enumerate(raw[1:], start=2):
        if len(r) != len(header) or not r[1].isdigit():
            errors.append(f"{path.name} line {n}: malformed row")
            continue
        out[(r[0], int(r[1]))] = {"priority": r[5], "reasons": [x for x in r[6].split("; ") if x], "suggestion": r[7] or None}
    return out


def read_expected_counts(path: Path) -> dict[str, int]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        return {r["level"]: int(r["new_rows"]) for r in csv.DictReader(f)}


def load(docs: Path = DOCS_DIR) -> Loaded:
    errors: list[str] = []
    warnings: list[str] = []
    rows = [row for level in LEVELS for row in read_level(docs / f"{level}-words.csv", level, errors)]
    extra = read_extra(docs / "worterbuch-extra-data.csv", errors)
    review = read_review(docs / "worterbuch-needs-review.csv", errors)
    by_key = {r.key: r for r in rows}
    for key, data in extra.items():
        if key in by_key:
            by_key[key].extra = data
    for key, data in review.items():
        if key in by_key:
            by_key[key].review = data
    if missing := [k for k in extra if k not in by_key]:
        warnings.append(f"worterbuch-extra-data.csv: {len(missing)} rows point to no word, e.g. {missing[:3]}")
    if missing := [k for k in review if k not in by_key]:
        warnings.append(f"worterbuch-needs-review.csv: {len(missing)} rows point to no word, e.g. {missing[:3]}")
    if unlisted := [r.key for r in rows if r.values["status"] == "needs_review" and r.review is None]:
        warnings.append(f"{len(unlisted)} needs_review rows have no reasons in worterbuch-needs-review.csv")
    expected = read_expected_counts(docs / "worterbuch-original-counts.csv")
    for level, n in expected.items():
        found = sum(r.level == level for r in rows)
        if found != n:
            warnings.append(f"{level}: {found} rows, worterbuch-original-counts.csv says {n}")
    return Loaded(rows, errors, warnings)


def search_fields(row: WordRow) -> dict:
    """Folded search keys; Uzbek and form keys are '|'-delimited tokens (|a|b|)."""
    v = row.values
    lemma = v["lemma"][5:] if v["lemma"].startswith("sich ") else v["lemma"]
    translations = [v["translation"], *row.extra.get("other_translation", [])]
    forms = [v[c] for c in FORM_COLUMNS if v[c]]
    return {
        "search_de": search_key(lemma)[:255],
        "search_uz": ("|" + "|".join(search_key(canonical_uz(t)) for t in translations) + "|")[:2000],
        "search_forms": ("|" + "|".join(dict.fromkeys(search_key(f) for f in forms)) + "|")[:2000] if forms else "",
    }
