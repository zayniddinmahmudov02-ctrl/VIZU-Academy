"""A2 module separation (Wortschatz / Lesen / Schreiben) — the data step, see
app/services/lms/a2_module_separation.py. Default is the read-only plan.

    python -m app.scripts.a2_module_separation plan [--json out.json]
    python -m app.scripts.a2_module_separation apply --backup-dir DIR --confirm <plan id>

apply writes the affected rows to DIR first. Take a DB backup before."""

import argparse
import json
import sys
from pathlib import Path

from app.db.session import SessionLocal
from app.services.lms import a2_module_separation as separation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="stage")
    p = sub.add_parser("plan")
    p.add_argument("--json")
    a = sub.add_parser("apply")
    a.add_argument("--backup-dir", required=True)
    a.add_argument("--confirm", required=True)
    args = parser.parse_args()
    try:
        with SessionLocal() as db:
            if (args.stage or "plan") == "plan":
                result = separation.plan(db)
                if getattr(args, "json", None):
                    Path(args.json).write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
                print(json.dumps(separation.summary(result), indent=1, ensure_ascii=False))
                print("READ-ONLY: nothing was changed.")
            else:
                print(json.dumps(separation.apply(db, Path(args.backup_dir), args.confirm), indent=1, ensure_ascii=False, default=str))
    except RuntimeError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
