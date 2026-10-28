"""Import the Wörterbuch from docs/ (the 22-column CSVs + extra data + review list).

    python -m app.scripts.import_woerterbuch --dry-run
    python -m app.scripts.import_woerterbuch
    python -m app.scripts.import_woerterbuch --docs /path/to/docs

Every file is validated first; any error stops the import before a single
row is written. Rows are matched by (level, id): an unchanged row (same
content hash) is skipped, a changed one is updated in place — its database
id, and so every student's saved word, stays. One transaction; nothing is
ever deleted (rows no longer in the CSV are only reported). The CSV status is
taken as it is: needs_review is never turned into verified here."""

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.dictionary import DictionaryEntry
from app.scripts.woerterbuch import docs_csv


class ImportRejected(Exception):
    def __init__(self, errors: list[str]):
        super().__init__(f"{len(errors)} errors in the source files")
        self.errors = errors


def primary_keys(rows: list[docs_csv.WordRow]) -> set[tuple[str, int]]:
    """The first row (lowest id) of each same-headword group within a level."""
    first: dict[tuple[str, str], tuple[str, int]] = {}
    for r in sorted(rows, key=lambda r: (r.level, r.source_id)):
        first.setdefault((r.level, r.group_key), r.key)
    return set(first.values())


def row_values(row: docs_csv.WordRow, primary: bool) -> dict:
    v = row.values
    values = {c: (v[c] or None) for c in docs_csv.COLUMNS if c not in ("id", "level", "presens_sie_Sie")}
    values.update(level=row.level, source_id=row.source_id, presens_sie_Sie=v["presens_sie_Sie"] or None,
                  translation=v["translation"], lemma=v["lemma"], status=v["status"],
                  extra=row.extra, review=row.review, group_key=row.group_key[:300],
                  is_primary=primary, is_published=not row.hidden, **docs_csv.search_fields(row))
    values["content_hash"] = hashlib.sha256(json.dumps(values, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return values


def run(db, docs: Path = docs_csv.DOCS_DIR, dry_run: bool = False) -> dict:
    loaded = docs_csv.load(docs)
    if loaded.errors:
        raise ImportRejected(loaded.errors)
    primary = primary_keys(loaded.rows)
    existing = {(e.level, e.source_id): e for e in db.scalars(select(DictionaryEntry))}
    per_level: dict[str, Counter] = defaultdict(Counter)
    try:
        for row in loaded.rows:
            values = row_values(row, row.key in primary)
            st = per_level[row.level]
            st["rows"] += 1
            st[values["status"]] += 1
            st["duplicate_rows_kept"] += not values["is_primary"]
            st["hidden"] += not values["is_published"]
            st["with_extra_data"] += bool(row.extra)
            entry = existing.get(row.key)
            if entry is None:
                st["created"] += 1
                if not dry_run:
                    db.add(DictionaryEntry(**values))
            elif entry.content_hash == values["content_hash"]:
                st["unchanged"] += 1
            else:
                st["updated"] += 1
                if not dry_run:
                    for key, value in values.items():
                        setattr(entry, key, value)
        stats = {
            "dry_run": dry_run,
            "rows": len(loaded.rows),
            "levels": {lv: dict(c) for lv, c in per_level.items()},
            "not_in_csv_kept": len(set(existing) - {r.key for r in loaded.rows}),
            "warnings": loaded.warnings,
        }
        if dry_run:
            db.rollback()
        else:
            db.commit()
        return stats
    except Exception:
        db.rollback()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--docs", type=Path, default=docs_csv.DOCS_DIR)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        stats = run(db, args.docs, args.dry_run)
    except ImportRejected as exc:
        print(f"REJECTED — nothing written. {exc}:", file=sys.stderr)
        for line in exc.errors[:200]:
            print("  " + line, file=sys.stderr)
        return 2
    finally:
        db.close()
    print(("DRY RUN " if args.dry_run else "") + json.dumps(stats, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
