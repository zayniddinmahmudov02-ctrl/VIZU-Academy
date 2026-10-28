"""Applies a review file (app/data/woerterbuch/review_*.json) to the source of
truth in docs/: the five 22-column word lists, worterbuch-extra-data.csv and
worterbuch-needs-review.csv.

    python -m app.scripts.woerterbuch.apply_review --dry-run
    python -m app.scripts.woerterbuch.apply_review

What it does, in this order — every change is written to
docs/worterbuch-review-log.csv (level, id, field, old, new, reason):

1. word corrections by headword (lemma / article / word type / translation /
   grammar / example; "delete" removes the word);
2. one primary translation per word: the same headword + word type gets the
   same translation in every level, the other answers become
   other_translation (wrong ones listed under "drop" are removed);
3. plurals of uncountable nouns that only the compound rule produced are emptied;
4. repeats of the same word inside one level file are removed — the first
   row stays, docs/worterbuch-merges.csv maps every removed row to it (the
   importer moves students' saved words along before deleting);
5. status: verified unless the review keeps the word needs_review or the row
   has no example.

Running it again changes nothing."""

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from app.scripts.woerterbuch import docs_csv
from app.scripts.woerterbuch.source import LEVELS, canonical_uz, clean

REVIEW = Path(__file__).resolve().parents[2] / "data" / "woerterbuch" / "review_2026-10-28.json"
PERSONS = docs_csv.PRESENS
LIST_KINDS = ("other_translation",)


def head(v: dict) -> str:
    return " ".join(p for p in (v["article"], v["lemma"]) if p)


def key_of(text: str) -> str:
    return clean(text).casefold()


def group_key(v: dict) -> str:
    return f"{key_of(head(v))}|{v['word_type']}"


class Log:
    def __init__(self):
        self.rows: list[tuple] = []

    def set(self, row: dict, field: str, new, reason: str) -> None:
        old = row[field]
        if old != new:
            self.rows.append((row["level"], row["id"], field, old if not isinstance(old, (list, dict)) else json.dumps(old, ensure_ascii=False),
                              new if not isinstance(new, (list, dict)) else json.dumps(new, ensure_ascii=False), reason))
            row[field] = new


def load_rows(docs: Path) -> tuple[list[dict], dict, dict]:
    errors: list[str] = []
    rows = []
    for level in LEVELS:
        for r in docs_csv.read_level(docs / f"{level}-words.csv", level, errors):
            rows.append(dict(r.values, id=r.source_id))
    extra = docs_csv.read_extra(docs / "worterbuch-extra-data.csv", errors)
    review = docs_csv.read_review(docs / "worterbuch-needs-review.csv", errors)
    if errors:
        raise SystemExit("source files invalid:\n" + "\n".join(errors[:50]))
    for r in rows:
        r["_extra"] = dict(extra.get((r["level"], r["id"]), {}))
        r["_review"] = review.get((r["level"], r["id"]))
    return rows, extra, review


def apply(docs: Path, review_file: Path = REVIEW, dry_run: bool = False, allow_unused: bool = False) -> dict:
    spec = json.loads(review_file.read_text(encoding="utf-8"))
    words = {key_of(k): v for k, v in spec["words"].items()}
    plural_blank = {key_of(k) for k in spec.get("plural_blank", [])}
    rows, _, _ = load_rows(docs)
    log = Log()
    stats = Counter()
    keep_review: dict[tuple, list[str]] = {}

    # 1. word corrections
    used = set()
    for r in rows:
        fix = words.get(key_of(head(r)))
        if not fix:
            continue
        used.add(key_of(head(r)))
        reason = "review: " + fix.get("note", "corrected")
        if fix.get("delete"):
            r["_delete"] = reason
            continue
        for field in ("article", "lemma", "word_type", "translation", "plural", "example_de", "example_uz"):
            if field in fix:
                log.set(r, field, fix[field] or "", reason)
        if "verb" in fix:
            vf = fix["verb"]
            if vf is None:
                for c in ("verb_praeteritum", "verb_partizip_ii", "verb_auxiliary", *PERSONS):
                    log.set(r, c, "", reason)
            else:
                for src, col in (("praeteritum", "verb_praeteritum"), ("partizip_ii", "verb_partizip_ii"), ("auxiliary", "verb_auxiliary")):
                    if src in vf:
                        log.set(r, col, vf[src], reason)
                if "presens" in vf:
                    for col, form in zip(PERSONS, vf["presens"]):
                        log.set(r, col, form, reason)
        if "adjective" in fix:
            log.set(r, "adjective_komparativ", fix["adjective"][0], reason)
            log.set(r, "adjective_superlativ", fix["adjective"][1], reason)
        if "grammar_note" in fix:
            r["_extra"]["grammar_note"] = fix["grammar_note"]
        for k, v in (fix.get("extra") or {}).items():
            if v is None:
                r["_extra"].pop(k, None)
            else:
                r["_extra"][k] = v
        if "lemma" in fix or "article" in fix:
            # stale data of the old (wrong) headword
            for k in ("ipa", "noun_genitive", "noun_plural_variants"):
                r["_extra"].pop(k, None)
        if fix.get("status") == "needs_review":
            keep_review[(r["level"], r["id"])] = [f"review:{fix.get('note', 'needs review')}"]
        r["_fixed"] = fix
        stats["rows_corrected"] += 1

    unused = sorted((set(words) - used) | (plural_blank - {key_of(head(r)) for r in rows}))
    if unused and not dry_run and not allow_unused:
        raise SystemExit(f"review entries that match no word (typo?): {unused}")
    stats["unused_review_keys"] = len(unused)
    if unused:
        print("unused review keys:", unused)
    deleted = [r for r in rows if r.get("_delete")]
    for r in deleted:
        log.rows.append((r["level"], r["id"], "row", head(r), "", r["_delete"]))
    rows = [r for r in rows if not r.get("_delete")]
    stats["rows_deleted"] = len(deleted)

    # word-type specific columns must stay empty for other types
    for r in rows:
        wt = r["word_type"]
        if wt != "Nomen":
            for c in ("article", "plural"):
                log.set(r, c, "", "review: column only for Nomen")
        if wt != "Verb":
            for c in ("verb_praeteritum", "verb_partizip_ii", "verb_auxiliary", *PERSONS):
                log.set(r, c, "", "review: column only for Verb")
        if wt != "Adjektiv":
            for c in ("adjective_komparativ", "adjective_superlativ"):
                log.set(r, c, "", "review: column only for Adjektiv")
        # standard 1st person of -ern verbs: ich wandere (not wandre)
        if wt == "Verb" and re.search(r"ern$", r["lemma"]) and re.match(r"^\S*[^e]re\b", r["presens_ich"]):
            log.set(r, "presens_ich", re.sub(r"^(\S*?)([^e])re\b", r"\1\2ere", r["presens_ich"]), "review: ich-form of -ern verb")
        if wt == "Verb" and r["verb_partizip_ii"] and r["verb_auxiliary"] in ("haben", "sein"):
            refl = " sich" if r["lemma"].startswith("sich ") else ""
            r["_extra"]["verb_perfekt"] = ("hat" if r["verb_auxiliary"] == "haben" else "ist") + refl + " " + r["verb_partizip_ii"]
        if wt == "Verb" and "/" in r["verb_auxiliary"]:
            keep_review[(r["level"], r["id"])] = ["verb:auxiliary_not_decided"]
        # every headword is now correct German, so TTS may read it
        log.set(r, "audio_text", head(r), "review: audio text = headword")

    # 2. one primary translation per word (all levels)
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[group_key(r)].append(r)
    for gk, rs in groups.items():
        fix = next((r["_fixed"] for r in rs if r.get("_fixed")), {}) or words.get(key_of(head(rs[0])), {})
        counts = Counter(canonical_uz(r["translation"]) for r in rs)
        others_src = [canonical_uz(t) for r in rs for t in r["_extra"].get("other_translation", [])]
        drop = {canonical_uz(t) for t in fix.get("drop", [])}
        primary = canonical_uz(fix["translation"]) if fix.get("translation") else counts.most_common(1)[0][0]
        others = []
        for t in [*fix.get("others", []), *(t for t, _ in counts.most_common()), *others_src]:
            t = canonical_uz(t)
            if t and t != primary and t not in drop and t not in others:
                others.append(t)
        for r in rs:
            if canonical_uz(r["translation"]) != primary:
                log.set(r, "translation", primary, "review: one primary translation per word")
            old = r["_extra"].get("other_translation", [])
            if old != others:
                log.rows.append((r["level"], r["id"], "other_translation", " | ".join(old), " | ".join(others), "review: other meanings"))
                if others:
                    r["_extra"]["other_translation"] = others
                else:
                    r["_extra"].pop("other_translation", None)

    # 3. plurals that only the compound rule produced
    for r in rows:
        if r["word_type"] == "Nomen" and key_of(head(r)) in plural_blank and r["plural"]:
            log.set(r, "plural", "", "review: uncountable noun, no plural")
            r["_extra"].setdefault("grammar_note", "kein Plural")

    # 4. repeats inside one level file
    first: dict[tuple, dict] = {}
    merges = []
    kept_rows = []
    for r in sorted(rows, key=lambda r: (LEVELS.index(r["level"]), r["id"])):
        k = (r["level"], group_key(r))
        if k in first:
            keep = first[k]
            if not keep["example_de"] and r["example_de"]:
                keep["example_de"], keep["example_uz"] = r["example_de"], r["example_uz"]
            merges.append((r["level"], r["id"], keep["level"], keep["id"], head(r)))
            log.rows.append((r["level"], r["id"], "row", head(r), f"{keep['level']}-{keep['id']}", "review: repeat in the same level, merged"))
            continue
        first[k] = r
        kept_rows.append(r)
    stats["rows_merged"] = len(merges)
    rows = kept_rows

    # 5. status
    for r in rows:
        k = (r["level"], r["id"])
        reasons = list(keep_review.get(k, []))
        if not (r["example_de"] and r["example_uz"]):
            reasons.append("example:missing")
        r["_reasons"] = reasons
        log.set(r, "status", "needs_review" if reasons else "verified", "review: " + ("; ".join(reasons) if reasons else "checked"))
    stats.update(Counter(r["status"] for r in rows))
    stats["rows_after"] = len(rows)
    stats["changes_logged"] = len(log.rows)

    if not dry_run:
        write(docs, rows, merges, log)
    return dict(stats)


def _write(path: Path, header, data) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\r\n")
        w.writerow(header)
        w.writerows(data)


def write(docs: Path, rows: list[dict], merges: list[tuple], log: Log) -> None:
    by_level = defaultdict(list)
    for r in rows:
        by_level[r["level"]].append(r)
    for level in LEVELS:
        _write(docs / f"{level}-words.csv", docs_csv.COLUMNS,
               [[r[c] for c in docs_csv.COLUMNS] for r in sorted(by_level[level], key=lambda r: r["id"])])
    extra_rows = []
    for r in sorted(rows, key=lambda r: (LEVELS.index(r["level"]), r["id"])):
        for kind, value in r["_extra"].items():
            values = value if kind in LIST_KINDS else [value]
            for v in values:
                if kind == "quiz_distractors":
                    v = " | ".join(v)
                elif isinstance(v, (list, dict, bool)):
                    v = json.dumps(v, ensure_ascii=False)
                extra_rows.append((r["level"], r["id"], r["lemma"], kind, v))
    _write(docs / "worterbuch-extra-data.csv", ("level", "id", "lemma", "kind", "value"), extra_rows)
    review_rows = [(r["level"], r["id"], r["lemma"], r["word_type"], r["translation"], "high", "; ".join(r["_reasons"]), "")
                   for r in rows if r["status"] == "needs_review"]
    _write(docs / "worterbuch-needs-review.csv", ("level", "id", "lemma", "word_type", "translation", "priority", "reasons", "suggestion"), review_rows)
    old_merges = []
    merges_path = docs / "worterbuch-merges.csv"
    if merges_path.exists():
        with merges_path.open(encoding="utf-8", newline="") as f:
            old_merges = [tuple(x) for x in list(csv.reader(f))[1:]]
    all_merges = {(m[0], str(m[1])): m for m in old_merges}
    for m in merges:
        all_merges[(m[0], str(m[1]))] = m
    _write(merges_path, ("level", "removed_id", "kept_level", "kept_id", "headword"), sorted(all_merges.values(), key=lambda m: (LEVELS.index(m[0]), int(m[1]))))
    log_path = docs / "worterbuch-review-log.csv"
    old_log = []
    if log_path.exists():
        with log_path.open(encoding="utf-8", newline="") as f:
            old_log = [tuple(x) for x in list(csv.reader(f))[1:]]
    _write(log_path, ("level", "id", "field", "old", "new", "reason"), old_log + log.rows)
    # duplicates report: what is left is the same word in several levels (kept on purpose)
    groups = defaultdict(list)
    for r in rows:
        groups[group_key(r)].append(r)
    dup = []
    for n, (gk, rs) in enumerate(sorted(((g, rs) for g, rs in groups.items() if len(rs) > 1), key=lambda x: (LEVELS.index(x[1][0]["level"]), x[1][0]["id"])), 1):
        for r in rs:
            dup.append((f"D{n:04d}", head(r), r["level"], r["id"], r["translation"], "cross_level", "same", len(rs), "kept"))
    _write(docs / "worterbuch-duplicates.csv", ("group", "headword", "level", "id", "translation", "duplicate_kind", "answers_in_group", "group_size", "action"), dup)
    counts_path = docs / "worterbuch-original-counts.csv"
    with counts_path.open(encoding="utf-8", newline="") as f:
        reader = list(csv.DictReader(f))
    for c in reader:
        c["new_rows"] = str(len(by_level[c["level"]]))
    _write(counts_path, list(reader[0].keys()), [list(c.values()) for c in reader])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--docs", type=Path, default=docs_csv.DOCS_DIR)
    parser.add_argument("--review", type=Path, default=REVIEW)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-unused", action="store_true", help="re-run: entries already applied match no word any more")
    args = parser.parse_args()
    print(json.dumps(apply(args.docs, args.review, args.dry_run, args.allow_unused), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
