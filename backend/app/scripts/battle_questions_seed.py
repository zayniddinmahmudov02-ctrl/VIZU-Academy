"""VIZU Battle text questions (vocabulary + grammar, A1–C1) from app/data/battle/questions — see
app/services/battle/question_seed.py. Default is the read-only plan.

    python -m app.scripts.battle_questions_seed plan [--json out.json]
    python -m app.scripts.battle_questions_seed apply --confirm <plan id>

Take a database backup first. Only adds rows to battle_questions; existing questions (also an admin's edits) are kept, nothing is
deleted, the picture words are not touched."""

import argparse
import json
import sys
from pathlib import Path

from app.db.session import SessionLocal
from app.services.battle import question_seed as seed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="stage")
    p = sub.add_parser("plan")
    p.add_argument("--json")
    a = sub.add_parser("apply")
    a.add_argument("--confirm", required=True)
    args = parser.parse_args()
    try:
        with SessionLocal() as db:
            if (args.stage or "plan") == "plan":
                plan = seed.build_plan(db)
                if getattr(args, "json", None):
                    Path(args.json).write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
                print(json.dumps({"plan_id": plan["plan_id"], "total_in_files": plan["total_in_files"], "counts": plan["counts"],
                                  "problems": plan["problems"][:20]}, ensure_ascii=False, indent=2))
                print("READ-ONLY: nothing was changed.")
            else:
                print(json.dumps(seed.apply(db, args.confirm), indent=2))
    except seed.SeedError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
