"""READ-ONLY: the A2 audio manifest from the database and storage as Markdown
(or JSON) — the same data as GET /admin/media-management/a2-audio/manifest.

    python -m app.scripts.a2_audio_manifest [--json] > a2-media-manifest.md
"""

import argparse
import json
import sys

from app.db.session import SessionLocal
from app.services.a2_audio import assets


def to_markdown(m: dict) -> str:
    c = m["counts"]
    out = [f"Generated {m['generated_at']:%Y-%m-%d %H:%M} UTC from the database (nothing assumed).", "",
           "| | |", "|---|---|",
           f"| files in the A2 Audio Manager | {c['files']} ({c['size_bytes']} bytes) · {c['by_format']} |",
           f"| by kind | {c['by_kind']} |",
           f"| verified / pending / problem | {c['verified']} / {c['pending']} / {c['problem']} |",
           f"| linked / not linked / no Unterricht | {c['linked']} / {c['unlinked']} / {c['no_unterricht']} |",
           f"| file missing in storage | {c['missing_file']} |",
           f"| current Hören tasks with / without audio | {c['tasks_with_audio']} / {c['tasks_without_audio']} (of {c['tasks']}) |", ""]
    for lesson in m["lessons"]:
        out.append(f"## {lesson['number']}. Unterricht — {lesson['title']}{'' if lesson['is_published'] else ' (Entwurf)'}")
        out += ["", "| file | kind | part | format | size | verified | linked to |", "|---|---|---|---|---|---|---|"]
        for a in lesson["assets"] or []:
            linked = a["linked"]["title"] if a["linked"] else "—"
            out.append(f"| {a['original_filename']} | {a['audio_kind'] or '—'} | {a['part'] or '—'} | {a['audio_format']} | {a['size_bytes']} "
                       f"| {a['verification']} | {linked} |")
        if not lesson["assets"]:
            out.append("| — | | | | | | |")
        out += ["", "Hören tasks: " + ("; ".join(f"{t['title']} ({'audio' if t['has_audio'] else 'NO AUDIO'})" for t in lesson["tasks"]) or "none"), ""]
    if m["unassigned"]:
        out += ["## Without Unterricht", ""] + [f"- {a['original_filename']}" for a in m["unassigned"]] + [""]
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    with SessionLocal() as db:
        m = assets.manifest(db)
    print(json.dumps(m, indent=2, default=str, ensure_ascii=False) if args.json else to_markdown(m))
    return 0


if __name__ == "__main__":
    sys.exit(main())
