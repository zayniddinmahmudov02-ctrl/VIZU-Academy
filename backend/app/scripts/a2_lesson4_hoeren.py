"""A2 4. Unterricht Hören: remove the old "Familie Mannsberg" task and set up
Text 1 / Text 2 / Text 3 — see app/services/a2_audio/lesson4_hoeren.py and
docs/a2-lesson-4-hoeren-update.md. Default is the read-only plan.

    python -m app.scripts.a2_lesson4_hoeren plan [--json out.json]
    python -m app.scripts.a2_lesson4_hoeren apply --backup-dir DIR --confirm <plan id>

apply writes every row and audio file of the old tasks to DIR first (SHA-256
checked), deletes a task without learner history, archives one with history
("[Archiv]", unpublished), removes audio files nothing references any more
and creates the missing Text tasks (drafts). Take a DB backup before."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.db.session import SessionLocal
from app.services.a2_audio import lesson4_hoeren


def _print_plan(result: dict) -> None:
    print(f"A2 {result['lesson_number']}. Unterricht — plan id {result['plan_id']}")
    for t in result["tasks"]:
        print(f"  {t['action'].upper():8} {t['title']} ({t['listening_id']}) — {t['questions']} questions, {t['options']} options, "
              f"published={t['is_published']}, attempts={t['attempts']}, key reviews={t['answer_key_reviews']}")
        for f in t["files"]:
            print(f"           file {f['storage_path']} on_disk={f['on_disk']} size={f['size_bytes']} references={f['references']}")
    if not result["tasks"]:
        print("  no 'Familie Mannsberg' task left in this lesson")
    print(f"  Text tasks to create: {', '.join(f'Text {n}' for n in result['slots_missing']) or 'none'}")


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
                result = lesson4_hoeren.plan(db)
                if getattr(args, "json", None):
                    Path(args.json).write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
                _print_plan(result)
                print("READ-ONLY: nothing was changed.")
            else:
                report = asyncio.run(lesson4_hoeren.remove_legacy(db, Path(args.backup_dir), args.confirm))
                print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    except RuntimeError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
