"""One-time conversion (2026-10-28) of the word lists to the 22-column format.

Since then docs/{A1..C1}-words.csv are the source of truth (edited by hand,
imported by app.scripts.import_woerterbuch), so this refuses to overwrite
files that are already converted unless --force is given — it would undo
every edit made in docs/ since.

    python -m app.scripts.woerterbuch.build
    python -m app.scripts.woerterbuch.export_csv --out /tmp/x   # compare
    python -m app.scripts.woerterbuch.export_csv --force         # overwrite docs/

One output row per original row: docs/{A1..C1}-words.csv keep every row,
its id (1..N per file) and its order; duplicates are reported, never dropped.
Values come from dictionary.json (Wiktionary grammar, VIZU examples); the
translation is the row's own answer. Nothing is guessed: a value that is not
known stays empty and the row is needs_review.

Also written to docs/:
  worterbuch-needs-review.csv     every needs_review row with its reasons
  worterbuch-duplicates.csv       every headword listed more than once
  worterbuch-original-counts.csv  the original files (rows, columns, sha256)
  worterbuch-extra-data.csv       source data the 22 columns have no place for
                                  (other translations, quiz distractors, extra grammar)"""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from app.scripts.woerterbuch import source
from app.scripts.woerterbuch.build import FLAGS_FILE, OUT
from app.scripts.woerterbuch.docs_csv import COLUMNS, DOCS_DIR as DOCS
WORD_TYPE = {"Präposition": "Praeposition"}
PERSON_COLUMN = {"ich": "presens_ich", "du": "presens_du", "er/sie/es": "presens_er_sie_es", "wir": "presens_wir",
                 "ihr": "presens_ihr", "sie/Sie": "presens_sie_Sie"}
# review notes that only describe the entry and need no action
INFO_NOTES = ("level:listed_in_",)


def _without_article(form: str | None) -> str:
    return form.split(" ", 1)[1] if form and form.startswith(("der ", "die ", "das ")) else (form or "")


def convert_row(row: source.SourceRow, entry: dict) -> tuple[dict, list[str]]:
    """(csv values, review reasons) for one original row."""
    article, lemma, reflexive = source.split_headword(row.german)
    word_type = WORD_TYPE.get(entry["part_of_speech"], entry["part_of_speech"] or "")
    grammar = entry["grammar"] or {}
    reasons = [n for n in entry["review_notes"] if not n.startswith(INFO_NOTES)]
    values = dict.fromkeys(COLUMNS, "")
    values.update(id=row.row_id, level=row.level, lemma=("sich " if reflexive else "") + lemma, word_type=word_type,
                  translation=source.canonical_uz(row.correct),
                  example_de=entry["example_de"] or "", example_uz=entry["example_uz"] or "")
    if not word_type:
        reasons.append("word_type:unknown")
    if word_type == "Nomen":
        values["article"] = article or grammar.get("article") or ""
        values["plural"] = _without_article(grammar.get("plural"))
        if grammar.get("number") == "Pluraletantum":
            reasons.append("noun:pluraletantum_no_singular")
        if not values["article"]:
            reasons.append("noun:article_missing")
        if not values["plural"] and grammar.get("number") != "Pluraletantum":
            reasons.append("noun:plural_missing")
    elif word_type == "Verb":
        values["verb_praeteritum"] = grammar.get("praeteritum") or ""
        values["verb_partizip_ii"] = grammar.get("partizip_ii") or ""
        aux = grammar.get("auxiliary") or []
        values["verb_auxiliary"] = "/".join(aux)
        for form in grammar.get("praesens") or []:
            values[PERSON_COLUMN[form["person"]]] = form["form"]
        if not all(values[c] for c in ("verb_praeteritum", "verb_partizip_ii", "verb_auxiliary", *PERSON_COLUMN.values())):
            reasons.append("verb:forms_incomplete")
    elif word_type == "Adjektiv":
        values["adjective_komparativ"] = grammar.get("komparativ") or ""
        values["adjective_superlativ"] = grammar.get("superlativ") or ""
        if grammar.get("note") == "nicht steigerbar":
            reasons.append("adjective:not_comparable")
        elif not (values["adjective_komparativ"] and values["adjective_superlativ"]):
            reasons.append("adjective:degrees_missing")
    # a headword that is not correct German is not given to TTS
    if entry["is_published"]:
        values["audio_text"] = " ".join(p for p in (values["article"], values["lemma"]) if p)
    if values["translation"] != row.correct:
        reasons.append("translation:apostrophes_normalized")
    if entry["example_status"] == "none":
        reasons.append("example:missing")
    elif entry["example_status"] != "reviewed":
        reasons.append("example:not_reviewed")
    if row.repaired and "source:repaired_row" not in reasons:
        reasons.append("source:repaired_row")
    verified = (entry["translation_status"] == "reviewed" and entry["example_status"] == "reviewed"
                and entry["grammar_status"] in ("reviewed", "none") and entry["is_published"])
    values["status"] = "verified" if verified else "needs_review"
    return values, reasons


def priority(reasons: list[str], word_type: str) -> str:
    """'example_only': nothing is wrong except that nobody has reviewed the example yet."""
    harmless = {"example:not_reviewed", "translation:apostrophes_normalized", "adjective:not_comparable"}
    if word_type not in ("Nomen", "Verb", "Adjektiv"):
        harmless.add("grammar:not_in_wiktionary")  # no grammar columns to fill for a phrase or particle
    actionable = [r for r in reasons if r not in harmless]
    return "high" if actionable else "example_only"


def extra_data(row: source.SourceRow, entry: dict) -> list[tuple[str, str]]:
    grammar = entry["grammar"] or {}
    out = [("quiz_distractors", " | ".join(row.wrong))]
    out += [("other_translation", t) for t in [entry["translation"], *entry["translations_extra"]]
            if t != source.canonical_uz(row.correct)]
    for key, kind in (("genitive", "noun_genitive"), ("plural_variants", "noun_plural_variants"), ("conjugation_type", "verb_conjugation_type"),
                      ("separable", "verb_separable"), ("perfekt", "verb_perfekt"), ("cases", "preposition_cases"),
                      ("conjunction", "conjunction_word_order"), ("note", "grammar_note")):
        value = grammar.get(key)
        if value not in (None, [], ""):
            out.append((kind, json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict, bool)) else str(value)))
    if entry["ipa"]:
        out.append(("ipa", entry["ipa"]))
    return out


def write_csv(path: Path, header, rows) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\r\n")
        writer.writerow(header)
        writer.writerows(rows)


def export(docs: Path = DOCS) -> dict:
    entries = json.loads(OUT.read_text(encoding="utf-8"))["entries"]
    by_row = {(s["level"], s["row"]): e for e in entries for s in e["sources"]}
    flags = {source.headword_key(g): f for g, f in json.loads(FLAGS_FILE.read_text(encoding="utf-8")).items() if not g.startswith("_")}
    review, extra, occurrences = [], [], defaultdict(list)
    stats = {}
    for level in source.LEVELS:
        rows = source.read_rows(level)
        out = []
        st = Counter(old_rows=len(rows))
        for row in rows:
            entry = by_row[(level, row.row_id)]
            values, reasons = convert_row(row, entry)
            out.append([values[c] for c in COLUMNS])
            occurrences[source.headword_key(row.german)].append((level, row.row_id, row.german, values["translation"]))
            extra += [(level, row.row_id, values["lemma"], kind, value) for kind, value in extra_data(row, entry)]
            st["new_rows"] += 1
            st[values["status"]] += 1
            st["translation_source_consistent"] += entry["translation_status"] == "source"
            st["grammar_from_wiktionary"] += values["word_type"] in ("Nomen", "Verb", "Adjektiv") and entry["grammar_status"] == "sourced"
            st["grammar_applicable"] += values["word_type"] in ("Nomen", "Verb", "Adjektiv")
            st["with_example"] += bool(values["example_de"] and values["example_uz"])
            if values["status"] == "needs_review":
                flag = flags.get(source.headword_key(row.german))
                review.append((level, row.row_id, values["lemma"], values["word_type"], values["translation"],
                               priority(reasons, values["word_type"]), "; ".join(reasons), flag["note"] if flag else ""))
        write_csv(docs / f"{level}-words.csv", COLUMNS, out)
        stats[level] = st
    dup_rows = []
    for n, (key, occ) in enumerate(sorted(((k, o) for k, o in occurrences.items() if len(o) > 1), key=lambda x: x[1][0][:2]), 1):
        levels = Counter(o[0] for o in occ)
        answers = {o[3] for o in occ}
        for level, row_id, german, translation in occ:
            kind = "same_level" if levels[level] > 1 else "cross_level"
            dup_rows.append((f"D{n:04d}", german, level, row_id, translation, kind,
                             "same" if len(answers) == 1 else "different", len(occ), "kept"))
            if levels[level] > 1:
                stats[level]["same_level_duplicate_rows"] += 1
    for level, n in Counter(r[2] for r in dup_rows).items():
        stats[level]["rows_in_duplicate_groups"] = n
    write_csv(docs / "worterbuch-needs-review.csv",
              ("level", "id", "lemma", "word_type", "translation", "priority", "reasons", "suggestion"), review)
    write_csv(docs / "worterbuch-duplicates.csv",
              ("group", "headword", "level", "id", "translation", "duplicate_kind", "answers_in_group", "group_size", "action"), dup_rows)
    write_csv(docs / "worterbuch-extra-data.csv", ("level", "id", "lemma", "kind", "value"), extra)
    counts = []
    for level in source.LEVELS:
        path = source.SOURCE_DIR / f"{level}-words.csv"
        raw = path.read_bytes()
        widths = Counter(len(r) for r in csv.reader(raw.decode("utf-8").splitlines()) if r)
        counts.append((level, path.name, len(source.read_rows(level)), stats[level]["new_rows"],
                       " ".join(f"{w}:{c}" for w, c in sorted(widths.items())), "UTF-8", "CRLF" if b"\r\n" in raw else "LF",
                       "no", hashlib.sha256(raw).hexdigest()))
    write_csv(docs / "worterbuch-original-counts.csv",
              ("level", "file", "original_rows", "new_rows", "columns_per_row", "encoding", "line_endings", "header", "original_sha256"), counts)
    return {"levels": {lv: dict(st) for lv, st in stats.items()}, "needs_review": len(review),
            "priority": dict(Counter(r[5] for r in review)), "duplicate_groups": len({r[0] for r in dup_rows}),
            "extra_data": dict(Counter(r[3] for r in extra)),
            "reasons": dict(Counter(x for r in review for x in r[6].split("; ") if x).most_common(40))}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=DOCS)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    first = args.out / "A1-words.csv"
    if first.exists() and first.read_text(encoding="utf-8").startswith(",".join(COLUMNS)) and not args.force:
        print(f"{args.out} already holds the converted lists (source of truth) — not overwritten. Use --out or --force.")
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    print(json.dumps(export(args.out), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
