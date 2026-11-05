"""Import Multilevel Modelltests 1–10 (app/data/multilevel) into provider NATIONAL, level "Multilevel B1–C1".
Rules: app/services/mock_exam/multilevel_service.py. Default is the read-only plan.

    python -m app.scripts.multilevel_import plan [--pdf-dir DIR]
    python -m app.scripts.multilevel_import apply --confirm <plan id> [--pdf-dir DIR]

Idempotent: existing tests are skipped (never changed or deleted), new ones are created as DRAFT. --pdf-dir holds the
original "Multilevel Mock Variant N.pdf" files, copied into private storage. Take a DB backup before apply."""

import argparse
import json
import sys
from pathlib import Path

from app.db.session import SessionLocal
from app.services.mock_exam import multilevel_service


def _print_plan(p: dict) -> None:
    print(f"Multilevel import — plan id {p['plan_id']} — provider {p['provider']}, level {p['level']}"
          f"{' (new)' if p['create_level'] else ''}")
    for i in p["items"]:
        counts = ", ".join(f"{k} {v['teile']}T/{v['questions']}Q/{v['keys']}K" for k, v in i["counts"].items())
        print(f"  {i['action'].upper():6} MT{i['number']:02} {i['origin']:4} {counts}; review={i['review']}; "
              f"pdf={'ok' if i['pdf_found'] else ('-' if not i['source_pdf'] else 'MISSING')}{'; ' + i['warning'] if i.get('warning') else ''}")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="stage")
    p = sub.add_parser("plan")
    p.add_argument("--pdf-dir")
    a = sub.add_parser("apply")
    a.add_argument("--confirm", required=True)
    a.add_argument("--pdf-dir")
    args = parser.parse_args()
    pdf_dir = Path(args.pdf_dir) if getattr(args, "pdf_dir", None) else None
    try:
        with SessionLocal() as db:
            if (args.stage or "plan") == "plan":
                _print_plan(multilevel_service.plan(db, pdf_dir))
                print("READ-ONLY: nothing was changed.")
            else:
                print(json.dumps(multilevel_service.apply(db, args.confirm, pdf_dir), ensure_ascii=False, indent=1))
    except RuntimeError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
