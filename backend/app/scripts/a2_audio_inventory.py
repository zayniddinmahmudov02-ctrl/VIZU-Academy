"""Audit an A2 MP3/M4A source directory without changing files or the database.

    python -m app.scripts.a2_audio_inventory --audio-dir C:\\path\\to\\A2
"""

import argparse
from pathlib import Path
import sys

from app.services.lesson_skills.a2_audio_manifest import A2_AUDIO_MATERIALS, audit_audio_files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-dir", required=True, type=Path)
    args = parser.parse_args()
    if not args.audio_dir.is_dir():
        print(f"ERROR: audio directory does not exist: {args.audio_dir}", file=sys.stderr)
        return 2

    report = audit_audio_files(list(args.audio_dir.rglob("*")))
    print(f"Expected: {report['expected_count']} audio files across 13 lessons")
    print(f"Discovered: {report['discovered_count']} MP3/M4A files; matched: {report['matched_count']}")
    for material in report["missing"]:
        print(f"MISSING L{material.lesson_number:02d}: {material.source_name}.{material.extension}")
    for item in report["wrong_format"]:
        print(
            f"WRONG FORMAT L{item['material'].lesson_number:02d}: {item['file'].name}; "
            f"expected .{item['expected_extension']}"
        )
    for item in report["ambiguous"]:
        print(f"AMBIGUOUS: {item['material'].source_name}: {', '.join(p.name for p in item['files'])}")
    for path in report["unexpected"]:
        print(f"UNEXPECTED: {path.name}")
    if not report["ok"]:
        print("ERROR: inventory differs from the declared 28-file list; no material was changed.")
        return 1

    print(f"OK: all {len(A2_AUDIO_MATERIALS)} expected files match their declared format.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
