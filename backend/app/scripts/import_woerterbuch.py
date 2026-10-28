"""Import app/data/woerterbuch/dictionary.json into dictionary_entries.

    python -m app.scripts.woerterbuch.build
    python -m app.scripts.import_woerterbuch --dry-run
    python -m app.scripts.import_woerterbuch

Idempotent: rows are matched by stable_id; an unchanged entry (same content
hash) is skipped, a changed one updated in place (its id, and so every
student's saved / known state, stays). Nothing is ever deleted — an entry
that is no longer in the file is only reported. Entries a teacher has
reviewed (any status "reviewed") are never overwritten by the import."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.dictionary import DictionaryEntry
from app.scripts.woerterbuch.build import OUT
from app.scripts.woerterbuch.source import canonical_uz, search_key

FIELDS = ("german", "lemma", "article", "reflexive", "part_of_speech", "cefr_level", "levels", "translation",
          "translations_extra", "grammar", "grammar_source", "ipa", "example_de", "example_uz", "translation_status",
          "grammar_status", "example_status", "review_notes", "sources", "is_published")


def row_values(item: dict) -> dict:
    values = {f: item.get(f) for f in FIELDS}
    values["translations_extra"] = values["translations_extra"] or []
    values["review_notes"] = values["review_notes"] or []
    values["is_published"] = item.get("is_published", True)
    values["search_de"] = search_key(item["lemma"])[:255]
    values["search_uz"] = "|".join(search_key(canonical_uz(t)) for t in [item["translation"], *values["translations_extra"]])[:1000]
    values["content_hash"] = hashlib.sha256(json.dumps(values, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return values


def reviewed(entry: DictionaryEntry) -> bool:
    return "reviewed" in (entry.translation_status, entry.grammar_status, entry.example_status)


def run(db, items: list[dict], dry_run: bool) -> dict:
    existing = {e.stable_id: e for e in db.scalars(select(DictionaryEntry))}
    stats = {"in_file": len(items), "create": 0, "update": 0, "unchanged": 0, "kept_reviewed": 0, "not_in_file": 0}
    seen = set()
    for item in items:
        sid = item["stable_id"]
        if sid in seen:
            raise ValueError(f"duplicate stable_id in file: {sid}")
        seen.add(sid)
        values = row_values(item)
        entry = existing.get(sid)
        if entry is None:
            stats["create"] += 1
            if not dry_run:
                db.add(DictionaryEntry(stable_id=sid, **values))
        elif entry.content_hash == values["content_hash"]:
            stats["unchanged"] += 1
        elif reviewed(entry):
            stats["kept_reviewed"] += 1
        else:
            stats["update"] += 1
            if not dry_run:
                for key, value in values.items():
                    setattr(entry, key, value)
    stats["not_in_file"] = len(set(existing) - seen)
    if dry_run:
        db.rollback()
    else:
        db.commit()
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", type=Path, default=OUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    items = json.loads(args.file.read_text(encoding="utf-8"))["entries"]
    db = SessionLocal()
    try:
        stats = run(db, items, args.dry_run)
    finally:
        db.close()
    print(("DRY RUN " if args.dry_run else "") + json.dumps(stats))
    return 0


if __name__ == "__main__":
    sys.exit(main())
