"""Old A2 audio archive cleanup — see app/services/a2_audio/cleanup.py and
docs/a2-media-cleanup-plan.md. Default is the read-only plan.

    python -m app.scripts.a2_audio_cleanup plan [--json out.json] [--md out.md]
    python -m app.scripts.a2_audio_cleanup quarantine --confirm <plan id>
    python -m app.scripts.a2_audio_cleanup restore --manifest <batch>/manifest.json
    python -m app.scripts.a2_audio_cleanup purge --manifest <batch>/manifest.json --confirm <plan id>

Take a backup first (scripts/backup-course-content.sh). quarantine and
restore only move files (reversible); purge deletes quarantined copies and is
for after a separate approval. No stage changes or deletes database rows."""

import argparse
import json
import sys
from pathlib import Path

from app.db.session import SessionLocal
from app.services.a2_audio import cleanup


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="stage")
    p = sub.add_parser("plan")
    p.add_argument("--json")
    p.add_argument("--md")
    q = sub.add_parser("quarantine")
    q.add_argument("--confirm", required=True)
    r = sub.add_parser("restore")
    r.add_argument("--manifest", required=True)
    g = sub.add_parser("purge")
    g.add_argument("--manifest", required=True)
    g.add_argument("--confirm", required=True)
    args = parser.parse_args()
    stage = args.stage or "plan"
    try:
        with SessionLocal() as db:
            if stage == "plan":
                result = cleanup.build_plan(db)
                if getattr(args, "json", None):
                    Path(args.json).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
                if getattr(args, "md", None):
                    Path(args.md).write_text(cleanup.plan_markdown(result), encoding="utf-8")
                print(cleanup.plan_markdown(result))
                print("READ-ONLY: nothing was changed.")
            elif stage == "quarantine":
                result = cleanup.quarantine(db, args.confirm)
                print(f"quarantined {len(result['files'])} file(s); manifest: {result['manifest']}")
            elif stage == "restore":
                result = cleanup.restore(Path(args.manifest))
                print(f"restore: {result['state']}")
            else:
                result = cleanup.purge(db, Path(args.manifest), args.confirm)
                print(f"purge: {result['state']}")
    except cleanup.CleanupError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
