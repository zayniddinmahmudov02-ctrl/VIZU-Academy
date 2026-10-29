"""Cleanup of the OLD A2 audio archive — in reversible stages.

What counts as "old A2 audio" (and nothing else):
  * the main audio and extra tracks of A2 Hören tasks that are no longer
    current: first-edition copies titled "[Archiv] …" and the legacy
    A2-mapped tasks (a2_material_key, e.g. a2-l01-audio-01);
  * archived earlier versions (listening_audio_archives) of A2 tasks.

A file is only "ready to clean" when EVERY database reference to it is old
A2 audio and it exists on disk. It is kept ("blocked") when any reference is
another level, a current A2 task, or an A2 Audio Manager entry. Files in the
storage that no row references are listed for review but never attributed
to A2 and never touched. Database rows are never changed or deleted here.

Stages (app/scripts/a2_audio_cleanup.py):
  plan        read-only report, with a plan id (hash of the eligible set)
  quarantine  moves exactly the planned files (same plan id, else refused)
              into a quarantine folder, SHA-256 checked, manifest written
              after every file -> interruptible and fully reversible
  restore     moves quarantined files back (SHA-256 checked)
  purge       deletes quarantined copies only — needs the plan id again,
              re-checks that nothing current references them. Irreversible:
              only after the new A2 Audio Manager is verified and a
              separate approval (docs/a2-media-cleanup-plan.md)."""

import hashlib
import json
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.a2_audio_asset import A2AudioAsset
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.listening import Listening
from app.models.listening_audio_archive import ListeningAudioArchive
from app.models.listening_audio_track import ListeningAudioTrack
from app.models.module import Module
from app.services.a2_audio.assets import is_current_task
from app.services.lesson_skills.admin import listening_storage

LEVEL = "A2"
QUARANTINE_ROOT = Path("app/protected_storage/a2-audio-quarantine")
MANIFEST = "manifest.json"


class CleanupError(Exception):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def _references(db: Session) -> dict[str, list[dict]]:
    """storage path -> every row pointing at it, with level and old/current."""
    levels: dict = {}

    def where(lesson_id):
        if lesson_id not in levels:
            row = db.execute(select(Course.level, Lesson.number).join(Module, Module.course_id == Course.id)
                             .join(Lesson, Lesson.module_id == Module.id).where(Lesson.id == lesson_id)).first()
            levels[lesson_id] = (row[0], row[1]) if row else (None, None)
        return levels[lesson_id]

    refs: dict[str, list[dict]] = defaultdict(list)
    tasks = {t.id: t for t in db.scalars(select(Listening))}
    for t in tasks.values():
        if t.audio_storage_path:
            level, lesson = where(t.lesson_id)
            refs[t.audio_storage_path].append({"kind": "task_audio", "id": str(t.id), "level": level, "lesson": lesson, "title": t.title,
                                               "material_key": t.a2_material_key, "old": level == LEVEL and not is_current_task(t)})
    for tr in db.scalars(select(ListeningAudioTrack)):
        if tr.storage_path:
            parent = tasks.get(tr.listening_id)
            level, lesson = where(parent.lesson_id) if parent else (None, None)
            refs[tr.storage_path].append({"kind": "task_track", "id": str(tr.id), "level": level, "lesson": lesson,
                                          "title": parent.title if parent else None, "material_key": None,
                                          "old": parent is not None and level == LEVEL and not is_current_task(parent)})
    for a in db.scalars(select(ListeningAudioArchive)):
        parent = tasks.get(a.listening_id)
        level, lesson = where(parent.lesson_id) if parent else (None, None)
        refs[a.storage_path].append({"kind": "archived_version", "id": str(a.id), "level": level, "lesson": lesson,
                                     "title": parent.title if parent else None, "material_key": parent.a2_material_key if parent else None,
                                     "old": level == LEVEL})
    for asset in db.scalars(select(A2AudioAsset)):
        refs[asset.storage_path].append({"kind": "a2_audio_manager", "id": str(asset.id), "level": LEVEL, "lesson": asset.unterricht,
                                         "title": asset.title, "material_key": None, "old": False})
    return refs


def _blocker(rows: list[dict]) -> str | None:
    for r in rows:
        if r["level"] != LEVEL:
            return f"also used by {r['level'] or 'unknown level'} ({r['kind']})"
    for r in rows:
        if not r["old"]:
            return "used by the A2 Audio Manager" if r["kind"] == "a2_audio_manager" else f"used by a current A2 task ({r['kind']})"
    return None


def build_plan(db: Session, root: Path | None = None) -> dict:
    """Read-only. Every file a row links to an A2 task, classified."""
    root = (root or listening_storage.ROOT).resolve()
    refs = _references(db)
    files = []
    for rel, rows in sorted(refs.items()):
        if not any(r["level"] == LEVEL for r in rows):
            continue
        path = (root / rel).resolve()
        inside = root in path.parents
        on_disk = inside and path.is_file()
        blocker = "path outside the storage folder" if not inside else _blocker(rows)
        files.append({"storage_path": rel, "on_disk": on_disk, "size_bytes": path.stat().st_size if on_disk else None,
                      "sha256": _sha256(path) if on_disk and blocker is None else None,
                      "eligible": on_disk and blocker is None, "blocked_by": blocker,
                      "missing_on_disk": not on_disk, "references": rows})
    referenced = {str((root / p).resolve()) for p in refs}
    unreferenced = [{"storage_path": str(f.relative_to(root)), "size_bytes": f.stat().st_size}
                    for f in sorted(root.rglob("*")) if f.is_file() and str(f.resolve()) not in referenced] if root.is_dir() else []
    eligible = [f for f in files if f["eligible"]]
    plan_id = hashlib.sha256("\n".join(f"{f['storage_path']}:{f['sha256']}" for f in eligible).encode()).hexdigest()[:12]
    old_rows = [r for f in files for r in f["references"] if r["old"]]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(), "storage_root": str(root), "plan_id": plan_id,
        "summary": {
            "a2_files": len(files), "eligible_files": len(eligible), "eligible_bytes": sum(f["size_bytes"] for f in eligible),
            "blocked_files": sum(1 for f in files if f["blocked_by"]), "missing_on_disk": sum(1 for f in files if f["missing_on_disk"]),
            "old_db_rows": len(old_rows),
            "old_db_rows_by_kind": {k: sum(1 for r in old_rows if r["kind"] == k) for k in ("task_audio", "task_track", "archived_version")},
            "unreferenced_files_not_touched": len(unreferenced),
        },
        "files": files, "unreferenced_files": unreferenced,
    }


def _write(manifest_path: Path, data: dict) -> None:
    tmp = manifest_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(manifest_path)


def quarantine(db: Session, confirm_plan_id: str, root: Path | None = None, quarantine_root: Path | None = None) -> dict:
    """Moves exactly the planned files into quarantine. Refused if the plan
    changed since it was reviewed (different plan id)."""
    root = (root or listening_storage.ROOT).resolve()
    plan = build_plan(db, root)
    if plan["plan_id"] != confirm_plan_id:
        raise CleanupError(f"plan changed: current plan id {plan['plan_id']}, confirmed {confirm_plan_id} — review the new plan")
    eligible = [f for f in plan["files"] if f["eligible"]]
    if not eligible:
        raise CleanupError("nothing to quarantine")
    # microseconds: quarantine -> restore -> quarantine of the same plan must never reuse a folder
    batch = (quarantine_root or QUARANTINE_ROOT).resolve() / f"{datetime.now(timezone.utc):%Y%m%d-%H%M%S-%f}-{plan['plan_id']}"
    batch.mkdir(parents=True, exist_ok=False)
    manifest_path = batch / MANIFEST
    data = {"plan_id": plan["plan_id"], "storage_root": str(root), "created_at": datetime.now(timezone.utc).isoformat(),
            "state": "quarantining", "files": []}
    _write(manifest_path, data)
    for f in eligible:
        src = root / f["storage_path"]
        dst = batch / "files" / f["storage_path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if _sha256(dst) != f["sha256"]:
            dst.unlink(missing_ok=True)
            data["state"] = "stopped"
            _write(manifest_path, data)
            raise CleanupError(f"copy of {f['storage_path']} does not match its SHA-256 — stopped, the original is untouched")
        src.unlink()
        data["files"].append({"storage_path": f["storage_path"], "sha256": f["sha256"], "size_bytes": f["size_bytes"],
                              "references": f["references"], "state": "quarantined"})
        _write(manifest_path, data)
    data["state"] = "quarantined"
    _write(manifest_path, data)
    return {"manifest": str(manifest_path), **data}


def _load(manifest_path: Path) -> dict:
    if not manifest_path.is_file():
        raise CleanupError(f"no manifest at {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def restore(manifest_path: Path) -> dict:
    """Moves every quarantined file back to where it was (never overwrites)."""
    data = _load(manifest_path)
    root, batch = Path(data["storage_root"]), manifest_path.parent
    for entry in data["files"]:
        if entry["state"] != "quarantined":
            continue
        src, dst = batch / "files" / entry["storage_path"], root / entry["storage_path"]
        if dst.exists():
            entry["state"] = "conflict_original_exists"
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if _sha256(dst) != entry["sha256"]:
            dst.unlink(missing_ok=True)
            raise CleanupError(f"restored copy of {entry['storage_path']} does not match — the quarantined file is kept")
        src.unlink()
        entry["state"] = "restored"
        _write(manifest_path, data)
    data["state"] = "restored" if all(e["state"] == "restored" for e in data["files"]) else "partially_restored"
    _write(manifest_path, data)
    return data


def purge(db: Session, manifest_path: Path, confirm_plan_id: str) -> dict:
    """Irreversible: deletes the quarantined copies. Needs the plan id again and
    re-checks the database — a file that something current points at again
    is kept."""
    data = _load(manifest_path)
    if confirm_plan_id != data["plan_id"]:
        raise CleanupError("confirmation does not match this quarantine batch")
    if data["state"] not in ("quarantined", "partially_purged"):
        raise CleanupError(f"batch state is {data['state']}, nothing to purge")
    refs = _references(db)
    batch = manifest_path.parent
    for entry in data["files"]:
        if entry["state"] != "quarantined":
            continue
        blocker = _blocker(refs.get(entry["storage_path"], []))
        if blocker:
            entry["state"] = f"kept: {blocker}"
            continue
        path = batch / "files" / entry["storage_path"]
        if not path.is_file() or _sha256(path) != entry["sha256"]:
            entry["state"] = "kept: quarantined copy missing or changed"
            continue
        path.unlink()
        entry["state"] = "purged"
        _write(manifest_path, data)
    data["state"] = "purged" if all(e["state"] == "purged" for e in data["files"]) else "partially_purged"
    data["purged_at"] = datetime.now(timezone.utc).isoformat()
    _write(manifest_path, data)
    return data


def plan_markdown(plan: dict) -> str:
    s = plan["summary"]
    lines = [f"Plan id `{plan['plan_id']}` · generated {plan['generated_at']} · storage `{plan['storage_root']}`", "",
             "| | |", "|---|---|",
             f"| A2-linked files | {s['a2_files']} |", f"| ready to clean (all references old A2) | {s['eligible_files']} ({s['eligible_bytes']} bytes) |",
             f"| kept (blocked) | {s['blocked_files']} |", f"| DB says file exists, storage has none | {s['missing_on_disk']} |",
             f"| old DB rows (unchanged) | {s['old_db_rows']} {s['old_db_rows_by_kind']} |",
             f"| unreferenced files (not attributed to A2, not touched) | {s['unreferenced_files_not_touched']} |", "",
             "| file | size | status | references |", "|---|---|---|---|"]
    for f in plan["files"]:
        status = "ready" if f["eligible"] else ("missing on disk" if f["missing_on_disk"] else f"kept: {f['blocked_by']}")
        refs = "; ".join(f"{r['kind']} {r['level']}/{r['lesson']} {r['title']!r}" + (f" key={r['material_key']}" if r["material_key"] else "")
                         for r in f["references"])
        lines.append(f"| `{f['storage_path']}` | {f['size_bytes'] or '—'} | {status} | {refs} |")
    return "\n".join(lines) + "\n"
