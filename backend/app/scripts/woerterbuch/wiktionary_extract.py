"""One-off: reduce the kaikki.org German Wiktionary extract (English
Wiktionary, CC BY-SA 4.0, https://kaikki.org/dictionary/German/) to the
headwords of our word lists.

    python -I -m app.scripts.woerterbuch.wiktionary_extract DUMP.jsonl.gz OUT.json

Only JSON is parsed; the dump is data, never executed. The output (committed
as app/data/woerterbuch/wiktionary_subset.json) keeps word, part of speech,
inflected forms with their tags, head line, IPA and the first English
glosses — what wiktionary.py needs, nothing else."""

import gzip
import json
import sys
from pathlib import Path

from app.scripts.woerterbuch import source

KEEP_POS = {"noun", "verb", "adj", "adv", "prep", "conj", "pron", "particle", "intj", "num", "det", "article",
            "phrase", "prep_phrase", "adv_phrase", "contraction", "name"}


def wanted_words() -> set[str]:
    words = set()
    for e in source.load_entries():
        words.add(e.lemma)
        words.add(e.german)
        if e.reflexive:
            words.add("sich " + e.lemma)
    return words


def reduce(entry: dict) -> dict:
    forms = [{"form": f.get("form", ""), "tags": f.get("tags", [])} for f in entry.get("forms", [])
             if f.get("form") and "table-tags" not in f.get("tags", []) and "inflection-template" not in f.get("tags", [])]
    heads = [h.get("expansion", "") for h in entry.get("head_templates", [])]
    ipa = next((s["ipa"] for s in entry.get("sounds", []) if s.get("ipa")), None)
    glosses = []
    senses = entry.get("senses", []) or [{}]
    for sense in senses[:4]:
        glosses.extend(sense.get("glosses", [])[:1])
    # a tag counts only when EVERY sense has it ("Apfel" has one alt-of sense
    # among normal ones and is still a normal noun)
    tags = sorted(t for t in ("form-of", "alt-of", "plural-only", "uncountable")
                  if all(t in s.get("tags", []) for s in senses))
    return {"word": entry["word"], "pos": entry.get("pos"), "forms": forms[:120], "head": heads[:2], "ipa": ipa,
            "glosses": glosses, "sense_tags": tags}


def noun_row(entry: dict) -> tuple[str, str] | None:
    """Head line of every German noun — for the gender / plural of a compound's
    last part (Fahrradhelm -> Helm)."""
    heads = [h.get("expansion", "") for h in entry.get("head_templates", [])]
    plural = next((f["form"] for f in entry.get("forms", []) if f.get("tags") == ["plural"]), None)
    return (heads[0] if heads else "", plural or "") if heads else None


def main() -> int:
    dump, out = Path(sys.argv[1]), Path(sys.argv[2])
    want = wanted_words()
    found: dict[str, list[dict]] = {}
    nouns: dict[str, list] = {}
    with gzip.open(dump, "rt", encoding="utf-8") as fh:
        for line in fh:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            word = entry.get("word")
            if entry.get("lang_code") != "de" or not word:
                continue
            if word in want and entry.get("pos") in KEEP_POS:
                found.setdefault(word, []).append(reduce(entry))
            if entry.get("pos") == "noun" and word[:1].isupper() and " " not in word:
                # agent nouns ("Lehrer" of "lehren") are tagged form-of too, so
                # form-of rows are kept; a normal row replaces a form-of one
                senses = entry.get("senses", []) or [{}]
                form_of = all("form-of" in s.get("tags", []) for s in senses)
                row = noun_row(entry)
                if row and (word not in nouns or (nouns[word][2] and not form_of)):
                    nouns[word] = [*row, form_of]
    out.write_text(json.dumps({"source": "kaikki.org German extract of English Wiktionary",
                               "license": "CC BY-SA 4.0", "url": "https://kaikki.org/dictionary/German/",
                               "entries": found, "nouns": nouns}, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(f"wanted {len(want)}, found {len(found)}, noun heads {len(nouns)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
