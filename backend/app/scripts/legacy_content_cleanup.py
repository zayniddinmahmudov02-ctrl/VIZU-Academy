"""Controlled cleanup of OLD course-system content that the VIZU LMS no longer
uses. DRY RUN by default — prints what each category would remove, how much
student history it touches, which files it owns and what the LMS would lose.

Categories (deletable, each root row cascades through the real foreign keys):
  homeworks           Hausaufgaben (removed from the student flow) + submissions
  lesson_assessments  lesson-bound Assessment Engine content (the old Lesen /
                      Hören / Schreiben / Sprechen engine; the LMS uses the
                      readings / listenings / writings / speakings tables)
  legacy_quizzes      GRAMMAR / VOCABULARY / LESSON quizzes (the LMS still
                      shows VOCABULARY / LESSON ones as a fallback where a
                      lesson has no exercise sets — see "lms_content_lost")
  orphan_video_files  files under protected video storage no row points at
  non_lms_video_files video + subtitle files of videos on A1–C1 lessons that
                      are OUTSIDE the LMS structure (old modules, numbers
                      beyond the level's range) — the old Courses system.
                      Videos of LMS lessons are never touched. The files are
                      MOVED into the archive (not copied — videos are large),
                      the video rows are kept (video_progress is student
                      history) and only unpublished. Restore: move the files
                      back to the storage key the row still carries, republish.
Report only (never deleted here): lessons outside the LMS structure, stale
video upload sessions (cleaned automatically by the upload flow).

Student history (attempts, submissions, grades) is NEVER deleted unless
--include-student-history is given; roots with history are skipped otherwise.

Executing requires ALL of:
  --execute --categories <list> --confirm <plan code printed by the dry run>
  --archive-dir <new dir>  (every affected row as JSON + a copy of every file)
  --i-have-a-verified-backup
The plan code covers exactly the rows of that dry run — if anything changed in
between, the code no longer matches and nothing is deleted.

    python -m app.scripts.legacy_content_cleanup
    python -m app.scripts.legacy_content_cleanup --categories homeworks orphan_video_files
    python -m app.scripts.legacy_content_cleanup --categories non_lms_video_files orphan_video_files
    python -m app.scripts.legacy_content_cleanup --categories homeworks --execute \\
        --confirm 1a2b3c4d5e6f --archive-dir /var/backups/vizu/legacy-2026-10-13 --i-have-a-verified-backup
"""

import argparse
import hashlib
import json
import shutil
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from sqlalchemy import text

from app.core.storage.local import LocalStorage
from app.core.storage.protected_local import ProtectedLegacySpeakingStorage, ProtectedLocalStorage, ProtectedVideoStorage
from app.db.session import SessionLocal
from app.scripts.course_content_audit import fk_edges, ids_where
from app.services.lms import structure

CATEGORIES = ("homeworks", "lesson_assessments", "legacy_quizzes", "orphan_video_files", "non_lms_video_files")
MOVED_FILE_CATEGORIES = {"non_lms_video_files"}
HISTORY_TABLES = {
    "homework_submissions", "assessment_attempts", "task_attempts", "answers", "section_results", "assessment_results",
    "speaking_submissions", "writing_submissions", "speaking_evaluations", "writing_evaluations", "student_quizzes",
}
ROOT_QUERIES = {
    "homeworks": ("homeworks", "SELECT id FROM homeworks ORDER BY id"),
    "lesson_assessments": ("assessments", "SELECT id FROM assessments WHERE lesson_id IS NOT NULL AND model_test_id IS NULL ORDER BY id"),
    "legacy_quizzes": ("quizzes", "SELECT id FROM quizzes WHERE lesson_id IS NOT NULL ORDER BY id"),
}
FILE_COLUMNS = {
    ("task_audio", "storage_path"): ProtectedLocalStorage.ROOT,
    ("speaking_submissions", "storage_path"): ProtectedLocalStorage.ROOT,
    ("speaking_evaluations", "feedback_audio_path"): ProtectedLocalStorage.ROOT,
    ("student_speakings", "storage_path"): ProtectedLegacySpeakingStorage.ROOT,
}


def cascade(db, edges, table: str, ids: list) -> dict[str, set]:
    affected: dict[str, set] = defaultdict(set)
    affected[table] = set(ids)
    changed = True
    while changed:
        changed = False
        for child, col, parent, rule in edges:
            if rule != "CASCADE" or not affected.get(parent) or child == parent:
                continue
            new = ids_where(db, child, col, list(affected[parent])) - affected[child]
            if new:
                affected[child] |= new
                changed = True
    return {t: ids for t, ids in affected.items() if ids}


def files_of(db, affected: dict[str, set]) -> list[dict]:
    out = []
    for (table, col), root in FILE_COLUMNS.items():
        ids = affected.get(table)
        if not ids:
            continue
        for row_id, key in db.execute(text(f'SELECT id, "{col}" FROM "{table}" WHERE id = ANY(:v) AND "{col}" IS NOT NULL AND "{col}" <> \'\''), {"v": list(ids)}):
            shared = db.scalar(text(f'SELECT count(*) FROM "{table}" WHERE "{col}" = :k AND NOT (id = ANY(:v))'), {"k": key, "v": list(ids)})
            path = root / key
            out.append({"table": table, "row": str(row_id), "path": str(path), "exists": path.is_file(),
                        "bytes": path.stat().st_size if path.is_file() else 0, "shared": shared > 0})
    return out


def orphan_video_files(db) -> list[dict]:
    keys = {k for (k,) in db.execute(text("SELECT storage_key FROM videos WHERE storage_key IS NOT NULL"))}
    keys |= {k for (k,) in db.execute(text("SELECT subtitle_key FROM videos WHERE subtitle_key IS NOT NULL"))}
    root = ProtectedVideoStorage.ROOT / "videos"
    out = []
    if root.is_dir():
        for p in sorted(root.rglob("*")):
            rel = p.relative_to(ProtectedVideoStorage.ROOT).as_posix()
            if p.is_file() and rel not in keys:
                out.append({"path": str(p), "key": rel, "exists": True, "bytes": p.stat().st_size, "shared": False})
    return out


def lessons_outside_lms(db) -> list[dict]:
    """A1–C1 lessons the LMS does not show: not in the level's main module or
    numbered outside 1..N."""
    outside = []
    for level in structure.LEVELS:
        course = structure.level_course(db, level)
        if course is None:
            continue
        main = structure.main_module(db, course)
        for lid, num, mid in db.execute(text(
            "SELECT le.id, le.number, le.module_id FROM lessons le JOIN modules m ON m.id = le.module_id WHERE m.course_id = :c"), {"c": course.id}):
            if main is None or mid != main.id or not 1 <= num <= structure.LEVEL_LESSON_COUNTS[level]:
                outside.append({"level": level, "lesson_id": str(lid), "number": num})
    return outside


def non_lms_video_files(db) -> tuple[list, list[dict]]:
    """Video rows of lessons outside the LMS structure and the files they own
    under protected video storage. A file another (out of scope) row also
    points at — e.g. an LMS lesson's video — is marked shared and left alone."""
    lesson_ids = [o["lesson_id"] for o in lessons_outside_lms(db)]
    ids = [r[0] for r in db.execute(text("SELECT id FROM videos WHERE lesson_id = ANY(CAST(:l AS uuid[])) ORDER BY id"), {"l": lesson_ids})] if lesson_ids else []
    files = []
    for col in ("storage_key", "subtitle_key"):
        for row_id, key in db.execute(text(f'SELECT id, "{col}" FROM videos WHERE id = ANY(:v) AND "{col}" IS NOT NULL AND "{col}" <> \'\''), {"v": ids}):
            shared = db.scalar(text('SELECT count(*) FROM videos WHERE (storage_key = :k OR subtitle_key = :k) AND NOT (id = ANY(:v))'), {"k": key, "v": ids})
            path = ProtectedVideoStorage.ROOT / key
            files.append({"table": "videos", "row": str(row_id), "key": key, "path": str(path), "exists": path.is_file(),
                          "bytes": path.stat().st_size if path.is_file() else 0, "shared": shared > 0})
    return ids, files


def lms_content_lost(db, quiz_ids: set) -> list[dict]:
    """Lessons whose only Wortschatz / Abschlusstest content is a legacy quiz."""
    if not quiz_ids:
        return []
    rows = db.execute(text("""
        SELECT q.lesson_id, q.quiz_type FROM quizzes q
        WHERE q.id = ANY(:v) AND q.is_published AND q.quiz_type IN ('VOCABULARY', 'LESSON')
          AND NOT EXISTS (SELECT 1 FROM skill_exercises e WHERE e.lesson_id = q.lesson_id AND e.is_published
                          AND e.skill = CASE q.quiz_type WHEN 'VOCABULARY' THEN 'WORTSCHATZ' ELSE 'YAKUNIY' END)
    """), {"v": list(quiz_ids)}).all()
    return [{"lesson_id": str(lid), "competency": "WORTSCHATZ" if qt == "VOCABULARY" else "ABSCHLUSSTEST"} for lid, qt in rows]


def plan(db, categories: list[str], include_history: bool) -> dict:
    edges = fk_edges(db)
    result = {"categories": {}, "include_student_history": include_history}
    for cat in categories:
        if cat == "orphan_video_files":
            files = orphan_video_files(db)
            result["categories"][cat] = {"roots": [], "rows": {}, "history_rows": 0, "skipped_roots_with_history": 0,
                                         "files": files, "file_bytes": sum(f["bytes"] for f in files)}
            continue
        if cat == "non_lms_video_files":
            ids, files = non_lms_video_files(db)
            files = [f for f in files if not f["shared"]]
            result["categories"][cat] = {"roots": [], "rows": {"videos (kept, unpublished)": len(ids)}, "history_rows": 0,
                                         "skipped_roots_with_history": 0, "files": files, "file_bytes": sum(f["bytes"] for f in files),
                                         "files_missing": sum(1 for f in files if not f["exists"]),
                                         "unpublish": [str(i) for i in ids], "_archive_rows": {"videos": set(ids)}}
            continue
        table, sql = ROOT_QUERIES[cat]
        roots = [r[0] for r in db.execute(text(sql))]
        keep, skipped = [], 0
        for root in roots:
            aff = cascade(db, edges, table, [root])
            has_history = any(aff.get(t) for t in HISTORY_TABLES)
            if has_history and not include_history:
                skipped += 1
            else:
                keep.append(root)
        affected = cascade(db, edges, table, keep) if keep else {}
        files = [f for f in files_of(db, affected) if not f["shared"]]
        entry = {
            "root_table": table,
            "roots": [str(r) for r in keep],
            "rows": {t: len(ids) for t, ids in sorted(affected.items())},
            "history_rows": sum(len(affected.get(t, ())) for t in HISTORY_TABLES),
            "skipped_roots_with_history": skipped,
            "files": files,
            "file_bytes": sum(f["bytes"] for f in files),
            "_affected": affected,
        }
        if cat == "legacy_quizzes":
            entry["lms_content_lost"] = lms_content_lost(db, set(keep))
        result["categories"][cat] = entry

    # report-only
    result["report_only"] = {
        "lessons_outside_lms_structure": lessons_outside_lms(db),
        "stale_video_upload_sessions": db.scalar(text("SELECT count(*) FROM video_upload_sessions WHERE created_at < now() - interval '24 hours'")),
    }
    token = sorted(f"{c}:{t}:{i}" for c, e in result["categories"].items() for t, ids in e.get("_affected", {}).items() for i in ids)
    token += sorted(f"{c}:keep:{t}:{i}" for c, e in result["categories"].items() for t, ids in e.get("_archive_rows", {}).items() for i in ids)
    token += sorted(f"{c}:file:{f['path']}" for c, e in result["categories"].items() for f in e["files"])
    result["plan_code"] = hashlib.sha256("\n".join(token).encode()).hexdigest()[:12]
    return result


def _json_default(v):
    if isinstance(v, (UUID, Decimal)):
        return str(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, (bytes, memoryview)):
        return bytes(v).hex()
    return str(v)


def _check_space(p: dict, archive_dir: Path) -> None:
    """Moving across filesystems is a copy: make sure it fits."""
    need = 0
    for cat in MOVED_FILE_CATEGORIES & p["categories"].keys():
        for f in p["categories"][cat]["files"]:
            if f["exists"] and Path(f["path"]).stat().st_dev != archive_dir.parent.stat().st_dev:
                need += f["bytes"]
    if need and shutil.disk_usage(archive_dir.parent).free < need * 1.05:
        sys.exit(f"Refusing to execute: the archive needs {need} bytes on another filesystem, not enough free space there.")


def archive(db, p: dict, archive_dir: Path) -> None:
    archive_dir.parent.mkdir(parents=True, exist_ok=True)
    _check_space(p, archive_dir)
    archive_dir.mkdir(exist_ok=False)
    for cat, entry in p["categories"].items():
        for table, ids in {**entry.get("_affected", {}), **entry.get("_archive_rows", {})}.items():
            rows = db.execute(text(f'SELECT * FROM "{table}" WHERE id = ANY(:v)'), {"v": list(ids)}).mappings().all()
            with open(archive_dir / f"{cat}__{table}.jsonl", "w", encoding="utf-8") as fh:
                for row in rows:
                    fh.write(json.dumps(dict(row), default=_json_default, ensure_ascii=False) + "\n")
        if cat in MOVED_FILE_CATEGORIES:
            continue  # moved by execute(), after the rows are archived
        for f in entry["files"]:
            if f["exists"]:
                target = archive_dir / "files" / cat / Path(f["path"]).name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f["path"], target)
    report = {k: v for k, v in p.items() if k != "categories"}
    report["categories"] = {c: _public(e) for c, e in p["categories"].items()}
    (archive_dir / "plan.json").write_text(json.dumps(report, default=_json_default, indent=2, ensure_ascii=False), encoding="utf-8")


def _public(entry: dict) -> dict:
    return {k: v for k, v in entry.items() if not k.startswith("_")}


def execute(db, p: dict, archive_dir: Path) -> dict:
    deleted, unpublished = {}, {}
    for cat, entry in p["categories"].items():
        if entry.get("roots"):
            res = db.execute(text(f'DELETE FROM "{entry["root_table"]}" WHERE id = ANY(:v)'), {"v": entry["roots"]})
            deleted[cat] = res.rowcount
        if entry.get("unpublish"):
            res = db.execute(text("UPDATE videos SET is_published = false WHERE id = ANY(:v)"), {"v": entry["unpublish"]})
            unpublished[cat] = res.rowcount
    db.execute(
        text("INSERT INTO audit_logs (id, action, details, created_at, updated_at) VALUES (gen_random_uuid(), 'legacy_content_cleanup', :d, now(), now())"),
        {"d": json.dumps({"plan_code": p["plan_code"], "deleted_roots": deleted, "unpublished": unpublished, "archive_dir": str(archive_dir)}, ensure_ascii=False)},
    )
    db.commit()
    moved = moved_bytes = 0
    for cat in MOVED_FILE_CATEGORIES & p["categories"].keys():
        for f in p["categories"][cat]["files"]:
            src = Path(f["path"])
            if f["exists"] and src.is_file():
                # keep the storage key as the relative path: restore = move back
                target = archive_dir / "files" / cat / f["key"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(target))
                moved += 1
                moved_bytes += f["bytes"]
    removed = 0
    for cat, entry in p["categories"].items():
        if cat in MOVED_FILE_CATEGORIES:
            continue
        for f in entry["files"]:
            path = Path(f["path"])
            if f["exists"] and not f["shared"] and path.is_file():
                path.unlink()
                removed += 1
    return {"deleted_roots": deleted, "unpublished": unpublished, "files_removed": removed, "files_moved_to_archive": moved, "bytes_moved": moved_bytes}


def print_plan(p: dict) -> None:
    print("LEGACY CONTENT CLEANUP — plan")
    for cat, e in p["categories"].items():
        rows = sum(e["rows"].values())
        print(f"\n[{cat}] roots: {len(e['roots'])} · rows (cascade): {rows} · student-history rows: {e['history_rows']}"
              f" · skipped roots with history: {e['skipped_roots_with_history']} · files: {len(e['files'])} ({e['file_bytes']} bytes)")
        for t, n in e["rows"].items():
            print(f"    {t:28} {n}{'   <- student history' if t in HISTORY_TABLES else ''}")
        if e.get("files_missing"):
            print(f"    {e['files_missing']} referenced file(s) already missing on disk")
        if e.get("lms_content_lost"):
            print(f"    !! LMS would lose its only Wortschatz / Abschlusstest content in {len(e['lms_content_lost'])} lesson(s)")
    r = p["report_only"]
    print(f"\nreport only: {len(r['lessons_outside_lms_structure'])} lessons outside the LMS structure · "
          f"{r['stale_video_upload_sessions']} stale upload sessions (auto-cleaned by the upload flow)")
    print(f"\nPLAN CODE: {p['plan_code']}   (pass with --confirm to execute exactly this plan)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Controlled cleanup of old course content (dry run by default).")
    ap.add_argument("--categories", nargs="+", default=list(CATEGORIES), choices=CATEGORIES)
    ap.add_argument("--include-student-history", action="store_true")
    ap.add_argument("--json", help="write the dry-run plan to this file")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--confirm")
    ap.add_argument("--archive-dir")
    ap.add_argument("--i-have-a-verified-backup", action="store_true")
    args = ap.parse_args()
    if not Path("app").is_dir():
        sys.exit("Run from the backend/ directory (storage roots are relative to it).")

    db = SessionLocal()
    try:
        p = plan(db, args.categories, args.include_student_history)
        print_plan(p)
        if args.json:
            report = {k: v for k, v in p.items() if k != "categories"}
            report["categories"] = {c: _public(e) for c, e in p["categories"].items()}
            Path(args.json).write_text(json.dumps(report, default=_json_default, indent=2, ensure_ascii=False), encoding="utf-8")
        if not args.execute:
            db.rollback()
            print("\nDRY RUN — nothing changed.")
            return
        missing = [n for n, ok in (("--confirm", args.confirm), ("--archive-dir", args.archive_dir), ("--i-have-a-verified-backup", args.i_have_a_verified_backup)) if not ok]
        sys.stdout.flush()
        if missing:
            sys.exit("Refusing to execute, missing: " + ", ".join(missing))
        if args.confirm != p["plan_code"]:
            sys.exit(f"Refusing to execute: --confirm {args.confirm} does not match the current plan code {p['plan_code']} (data changed or other categories).")
        archive(db, p, Path(args.archive_dir))
        print(f"\narchived to {args.archive_dir}")
        result = execute(db, p, Path(args.archive_dir))
        print(f"EXECUTED at {datetime.now(timezone.utc).isoformat()}: {result}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
