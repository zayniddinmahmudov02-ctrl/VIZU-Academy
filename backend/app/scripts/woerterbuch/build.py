"""Builds app/data/woerterbuch/dictionary.json from

  * source/{A1..C1}-words.csv          (original word lists, frozen: headwords, Uzbek answers, levels — source.py)
  * wiktionary_grammar.json            (resolved grammar, CC BY-SA 4.0 — wiktionary.py)
  * examples/{A1..C1}-n.json           (example sentences written for VIZU, all needs_review)
  * review_flags.json                  (source problems found by hand; become review notes)

    python -m app.scripts.woerterbuch.build                       # rebuild from the committed files
    python -m app.scripts.woerterbuch.build --wiktionary SUBSET   # re-resolve grammar first
    python -m app.scripts.woerterbuch.build --report              # print the audit numbers

The original CSV files are only read. docs/{A1..C1}-words.csv are the converted
22-column lists written from dictionary.json by export_csv.py."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from app.scripts.woerterbuch import source, wiktionary

DATA = Path(__file__).resolve().parents[2] / "data" / "woerterbuch"
GRAMMAR_FILE = DATA / "wiktionary_grammar.json"
EXAMPLES_DIR = DATA / "examples"
FLAGS_FILE = DATA / "review_flags.json"
OUT = DATA / "dictionary.json"
ATTRIBUTION = {"name": "Wiktionary (English edition), via kaikki.org", "license": "CC BY-SA 4.0",
               "url": "https://kaikki.org/dictionary/German/"}


def resolve_grammar(subset_path: Path) -> None:
    raw = json.loads(subset_path.read_text(encoding="utf-8"))
    out = {}
    for e in source.load_entries():
        pos, grammar, ipa, src, reasons = wiktionary.resolve(e, raw["entries"], raw["nouns"])
        out[e.stable_id] = {"german": e.german, "pos": pos, "grammar": grammar, "ipa": ipa, "source": src, "reasons": reasons}
    GRAMMAR_FILE.write_text(json.dumps({"attribution": ATTRIBUTION, "entries": out}, ensure_ascii=False, indent=0, sort_keys=True),
                            encoding="utf-8")


def load_examples() -> dict[str, dict]:
    examples = {}
    for path in sorted(EXAMPLES_DIR.glob("*.json")):
        for german, ex in json.loads(path.read_text(encoding="utf-8")).items():
            examples[source.headword_key(german)] = ex
    return examples


LEMMA_PROBLEMS = {"invalid_lemma", "misspelling", "wrong_article"}


def load_review_flags(known: set[str]) -> dict[str, dict]:
    raw = json.loads(FLAGS_FILE.read_text(encoding="utf-8")) if FLAGS_FILE.exists() else {}
    flags = {source.headword_key(german): flag for german, flag in raw.items() if not german.startswith("_")}
    unknown = sorted(set(flags) - known)
    if unknown:
        raise SystemExit(f"review_flags.json: unknown headwords {unknown}")
    return flags


def source_files() -> list[dict]:
    return [{"file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in (source.SOURCE_DIR / f"{level}-words.csv" for level in source.LEVELS)]


def build() -> dict:
    grammar = json.loads(GRAMMAR_FILE.read_text(encoding="utf-8"))["entries"] if GRAMMAR_FILE.exists() else {}
    examples = load_examples()
    source_entries = source.load_entries()
    flags = load_review_flags({e.key for e in source_entries})
    entries = []
    for e in source_entries:
        g = grammar.get(e.stable_id, {})
        translations = e.translations()
        ex = examples.get(e.key)
        reasons = e.review_reasons() + list(g.get("reasons", []))
        flag = flags.get(e.key)
        if flag:
            reasons.append(f"{flag['kind']}:{flag['note']}")
            if flag["kind"] == "translation":
                reasons.append("translation:flagged")
            if flag["kind"] in LEMMA_PROBLEMS:
                reasons.append("grammar:lemma_flagged")
            if flag["kind"] == "pos":
                reasons.append("pos:flagged")
        entries.append({
            "stable_id": e.stable_id,
            "german": e.german,
            "lemma": e.lemma,
            "article": e.article,
            "reflexive": e.reflexive,
            "part_of_speech": g.get("pos") or ("Nomen" if e.article else None),
            "cefr_level": e.cefr_level,
            "levels": sorted(e.levels, key=source.LEVELS.index),
            "translation": translations[0],
            "translations_extra": translations[1:],
            "grammar": g.get("grammar"),
            "grammar_source": g.get("source", "none"),
            "ipa": g.get("ipa"),
            "example_de": ex.get("de") if ex else None,
            "example_uz": ex.get("uz") if ex else None,
            # translation: the word list's answer; "source" = one consistent answer
            "translation_status": "needs_review" if {"translation:variants", "translation:flagged", "source:repaired_row"} & set(reasons) else "source",
            "grammar_status": "none" if not g.get("grammar") else ("needs_review" if any(r.startswith(("grammar:", "pos:")) for r in reasons) else "sourced"),
            # every example is written for VIZU and waits for a teacher's review
            "example_status": "needs_review" if ex else "none",
            "review_notes": reasons,
            # a headword that is not a correct German word stays hidden until a teacher fixes it
            "is_published": not (flag and flag["kind"] in LEMMA_PROBLEMS),
            "sources": [{"level": r.level, "row": r.row_id, "german": r.german, "answer": r.correct,
                         "distractors": list(r.wrong), "repaired": r.repaired} for r in e.rows],
        })
    return {"attribution": ATTRIBUTION, "source_files": source_files(), "entries": entries}


def report(doc: dict) -> None:
    entries = doc["entries"]
    print(f"entries {len(entries)}, source rows {sum(len(e['sources']) for e in entries)}")
    print("cefr_level", dict(Counter(e["cefr_level"] for e in entries)))
    print("listed in", {lv: sum(lv in e["levels"] for e in entries) for lv in source.LEVELS})
    print("part_of_speech", dict(Counter(e["part_of_speech"] for e in entries).most_common()))
    for key in ("translation_status", "grammar_status", "example_status", "grammar_source", "is_published"):
        print(key, dict(Counter(e[key] for e in entries)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wiktionary", type=Path, help="kaikki subset from wiktionary_extract.py: re-resolve grammar")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.wiktionary:
        resolve_grammar(args.wiktionary)
    doc = build()
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    if args.report:
        report(doc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
