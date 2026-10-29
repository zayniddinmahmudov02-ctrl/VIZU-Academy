"""READ-ONLY dry-run inventory of A2 Hören audio: database vs. storage.

    python -m app.scripts.a2_audio_inventory [--json]

Lists every audio file the database links to an A2 lesson (main audio, extra
tracks, archived versions) with its media/task ID, lesson, size, on-disk
status, and whether any non-A2 row references the same storage path. Then
lists files in the listening storage directory that no database row
references at all ("unlinked - needs review"). It never writes to the
database or the storage directory, and never deletes, moves or archives
anything: it is only the report that a later, separately approved cleanup
must be based on.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.a2_audio_asset import A2AudioAsset
from app.models.course import Course
from app.models.language import Language
from app.models.lesson import Lesson
from app.models.listening import Listening
from app.models.listening_audio_archive import ListeningAudioArchive
from app.models.listening_audio_track import ListeningAudioTrack
from app.models.module import Module
from app.services.lesson_skills.admin import listening_storage


def _size(root: Path, rel: str | None) -> tuple[bool, int | None]:
    if not rel:
        return False, None
    path = (root / rel).resolve()
    if root not in path.parents or not path.is_file():
        return False, None
    return True, path.stat().st_size


def build_report(db) -> dict:
    root = listening_storage.ROOT.resolve()
    # every (path -> [(level, lesson_number, kind, id)]) reference, all levels
    refs: dict[str, list[dict]] = defaultdict(list)

    def lesson_of(lesson_id):
        row = db.execute(
            select(Course.level, Lesson.number)
            .join(Module, Module.course_id == Course.id)
            .join(Lesson, Lesson.module_id == Module.id)
            .join(Language, Language.id == Course.language_id)
            .where(Lesson.id == lesson_id)
        ).first()
        return (row[0], row[1]) if row else (None, None)

    cache: dict = {}

    def where(lesson_id):
        if lesson_id not in cache:
            cache[lesson_id] = lesson_of(lesson_id)
        return cache[lesson_id]

    for l in db.scalars(select(Listening)):
        if l.audio_storage_path:
            level, num = where(l.lesson_id)
            refs[l.audio_storage_path].append(
                {"kind": "main", "id": str(l.id), "task": l.title, "level": level, "lesson": num,
                 "material_key": l.a2_material_key}
            )
    for t in db.scalars(select(ListeningAudioTrack)):
        if t.storage_path:
            parent = db.get(Listening, t.listening_id)
            level, num = where(parent.lesson_id) if parent else (None, None)
            refs[t.storage_path].append({"kind": "track", "id": str(t.id), "task": parent.title if parent else None,
                                         "level": level, "lesson": num, "material_key": None})
    for a in db.scalars(select(ListeningAudioArchive)):
        parent = db.get(Listening, a.listening_id)
        level, num = where(parent.lesson_id) if parent else (None, None)
        refs[a.storage_path].append({"kind": "archive", "id": str(a.id), "task": parent.title if parent else None,
                                     "level": level, "lesson": num, "material_key": None})
    for asset in db.scalars(select(A2AudioAsset)):  # A2 Audio Manager library
        refs[asset.storage_path].append({"kind": "a2_library", "id": str(asset.id), "task": asset.title,
                                         "level": "A2", "lesson": asset.unterricht, "material_key": None})

    a2_files = []
    for path, rows in sorted(refs.items()):
        if not any(r["level"] == "A2" for r in rows):
            continue
        on_disk, size = _size(root, path)
        a2_files.append({
            "storage_path": str(root / path), "on_disk": on_disk, "size_bytes": size,
            "references": rows,
            "shared_with_other_levels": sorted({r["level"] or "?" for r in rows if r["level"] != "A2"}),
            "references_count": len(rows),
        })

    referenced = {str((root / p).resolve()) for p in refs}
    unlinked = []
    if root.is_dir():
        for f in sorted(root.rglob("*")):
            if f.is_file() and str(f.resolve()) not in referenced:
                unlinked.append({"storage_path": str(f), "size_bytes": f.stat().st_size})
    return {"storage_root": str(root), "a2_files": a2_files, "unlinked_files": unlinked}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    with SessionLocal() as db:
        report = build_report(db)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    print(f"Storage root: {report['storage_root']}  (READ-ONLY dry run, nothing was changed)")
    print(f"A2-linked audio files: {len(report['a2_files'])}")
    for f in report["a2_files"]:
        flag = "" if f["on_disk"] else "  [MISSING ON DISK]"
        shared = f"  [ALSO USED BY: {', '.join(f['shared_with_other_levels'])}]" if f["shared_with_other_levels"] else ""
        print(f"- {f['storage_path']} ({f['size_bytes']} B){flag}{shared}")
        for r in f["references"]:
            print(f"    {r['kind']} id={r['id']} lesson=A2/{r['lesson']} task={r['task']!r} key={r['material_key']}")
    print(f"Unlinked files (no DB row, needs review, NOT A2-attributed): {len(report['unlinked_files'])}")
    for f in report["unlinked_files"]:
        print(f"- {f['storage_path']} ({f['size_bytes']} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
