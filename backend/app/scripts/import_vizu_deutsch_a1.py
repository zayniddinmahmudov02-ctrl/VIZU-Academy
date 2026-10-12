"""Import the VIZU-DEUTSCH A1 course book into the A1 course (lessons 1-14).

Reads app/data/vizu_deutsch_a1/modul_NN.json (built by
`python -m app.scripts.vizu_deutsch_a1.build`) and runs every document
through the regular content import (app/services/content_import): the same
validation, per-item report and batch record as the admin "Inhalte
importieren" page.

* Lessons are never created or renamed: book Modul N must already exist as
  A1 -> module 1 -> lesson N (production has all 14).
* Re-runnable: content that already exists (same content_id, same title in
  the lesson, same word) is skipped — never duplicated.
* Everything is created UNPUBLISHED. Review it in the admin panel and publish
  per batch (LMS A1–C1 -> Inhalte importieren -> Importe), or pass --publish.
  Hören tasks stay hidden until their audio is uploaded (and, where the book
  has no reliable key, until an admin has set the answers).

    python -m app.scripts.import_vizu_deutsch_a1 --dry-run
    python -m app.scripts.import_vizu_deutsch_a1
    python -m app.scripts.import_vizu_deutsch_a1 --modules 1 2 --publish
"""

import argparse
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.services.content_import import service as importer

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "vizu_deutsch_a1"


def load(n: int) -> dict:
    return json.loads((DATA_DIR / f"modul_{n:02d}.json").read_text(encoding="utf-8"))


def print_report(n: int, report: dict) -> None:
    print(f"\nModul {n}: {report['total']} items · {report['valid']} to import · {report.get('skipped', 0)} skipped · {report['invalid']} invalid")
    for e in report["errors"]:
        print(f"  ERROR {e}")
    for r in report["items"]:
        state = "OK  " if r["valid"] else ("SKIP" if r.get("skip") and not r["errors"] else "FAIL")
        print(f"  {state} {r['skill']:<10} {r['content_id']}  {r['title']}")
        if r.get("skip") and not r["errors"]:
            print(f"         {r['skip']}")
        for e in r["errors"]:
            print(f"         error: {e}")
        for w in r["warnings"]:
            print(f"         note: {w}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modules", type=int, nargs="*", help="book modules (default: all available)")
    parser.add_argument("--dry-run", action="store_true", help="validate and report only, write nothing")
    parser.add_argument("--publish", action="store_true", help="publish what was created (Hören without audio/key stays hidden)")
    args = parser.parse_args()

    modules = args.modules or sorted(int(p.stem.split("_")[1]) for p in DATA_DIR.glob("modul_*.json"))
    failed = 0
    db = SessionLocal()
    try:
        for n in modules:
            document = load(n)
            report = importer.validate_document(db, document, create_missing=False, skip_existing=True)
            print_report(n, report)
            failed += report["invalid"]
            if args.dry_run or report["errors"] or not report["valid"]:
                continue
            batch = importer.commit_document(db, document, None, f"vizu-deutsch-a1/modul_{n:02d}.json", skip_existing=True)
            summary = importer.batch_summary(batch)
            print(f"  -> batch {batch.id}: {summary['created_items']} created, {summary['skipped_items']} skipped, {summary['failed_items']} failed")
            if args.publish:
                batch = importer.publish_batch(db, batch.id)
                waiting = [i for i in batch.items if i.get("publish_problem")]
                print(f"  -> published; waiting: " + (", ".join(f"{i['title']} ({i['publish_problem']})" for i in waiting) or "none"))
    finally:
        db.close()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
