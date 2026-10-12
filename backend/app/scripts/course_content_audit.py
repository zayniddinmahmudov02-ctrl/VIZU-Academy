"""READ-ONLY dry run for the A1–C1 course content reset.

Answers "what exactly would be deleted if the lessons of these levels were
deleted?" without changing anything:

  * every row, per table, that the database's own ON DELETE CASCADE chain
    would remove (walked from the real foreign keys in information_schema,
    so a table added later is picked up automatically), plus SET NULL
    effects and RESTRICT blockers;
  * rows with no foreign key that would be orphaned (ai_evaluations);
  * every file those rows own (protected storage + public /uploads), its
    size, whether it exists, and whether anything OUTSIDE the deletion set
    still references it (such a file must be kept);
  * guards: courses, modules, payments, certificates, enrollments, users,
    VIZU-Multilevel, Vorbereitung model tests, books and media library are
    never part of the set — the run fails loudly if they would be.

Courses and modules are deliberately NOT targets: deleting a course
cascades to payments, certificates, enrollments and teacher assignments.

The whole run is one READ ONLY transaction. Run from backend/ (the storage
roots are relative to the working directory, exactly like the service):

    python -m app.scripts.course_content_audit
    python -m app.scripts.course_content_audit --levels A1 A2 --json /root/course-audit.json
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from sqlalchemy import text

from app.core.storage.local import LocalStorage
from app.core.storage.protected_local import (
    ProtectedLegacySpeakingStorage,
    ProtectedLessonListeningStorage,
    ProtectedLocalStorage,
    ProtectedVideoStorage,
    ProtectedVideoUploadTempStorage,
)
from app.db.session import SessionLocal

LEVELS = ["A1", "A2", "B1", "B2", "C1"]

# Tables that must never be touched by the course content reset.
PROTECTED_TABLES = {
    "users", "courses", "modules", "languages", "payments", "certificates", "enrollments",
    "teacher_assignments", "subscription_orders", "promo_codes", "promo_code_redemptions",
    "model_tests", "kompetenzen", "books", "media_assets", "advertisements", "content_imports",
    "audit_logs", "refresh_tokens", "login_history", "notifications",
}
PROTECTED_PREFIXES = ("vizu_mock_", "vizu_multilevel_", "mock_", "exam")

# (table, column) -> storage root of a file owned by that row (relative key).
KEY_FILES = {
    ("videos", "storage_key"): ProtectedVideoStorage.ROOT,
    ("videos", "thumbnail_key"): LocalStorage.ROOT,
    ("listenings", "audio_storage_path"): ProtectedLessonListeningStorage.ROOT,
    ("task_audio", "storage_path"): ProtectedLocalStorage.ROOT,
    ("speaking_submissions", "storage_path"): ProtectedLocalStorage.ROOT,
    ("speaking_evaluations", "feedback_audio_path"): ProtectedLocalStorage.ROOT,
    ("student_speakings", "storage_path"): ProtectedLegacySpeakingStorage.ROOT,
}
# URL columns: "/uploads/<path>" is a local public file, http(s) is external
# (never deleted), "/api/..." is served from a key column above.
URL_COLUMNS = [
    ("videos", "thumbnail_url"), ("videos", "video_url"), ("lessons", "video_url"), ("grammars", "video_url"),
    ("readings", "image_url"), ("writings", "image_url"), ("assessment_tasks", "image_url"),
    ("vocabularies", "image_url"), ("vocabularies", "audio_url"), ("listenings", "audio_url"),
    ("student_speakings", "audio_url"),
]
# Columns elsewhere that may point at the same /uploads file (shared use).
SHARED_URL_COLUMNS = URL_COLUMNS + [("media_assets", "url"), ("notifications", "audio_url"), ("books", "cover_url"),
                                    ("advertisements", "image_url")]


def is_protected(table: str) -> bool:
    return table in PROTECTED_TABLES or table.startswith(PROTECTED_PREFIXES)


def fk_edges(db):
    rows = db.execute(text("""
        SELECT tc.table_name, kcu.column_name, ccu.table_name, rc.delete_rule
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
        JOIN information_schema.referential_constraints rc ON rc.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
    """)).all()
    return [tuple(r) for r in rows]


def existing_columns(db) -> set[tuple[str, str]]:
    rows = db.execute(text("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public'")).all()
    return {(t, c) for t, c in rows}


def ids_where(db, table: str, column: str, values: list) -> set:
    if not values:
        return set()
    rows = db.execute(text(f'SELECT id FROM "{table}" WHERE "{column}" = ANY(:v)'), {"v": list(values)}).all()
    return {r[0] for r in rows}


def file_info(path: Path) -> dict:
    exists = path.is_file()
    return {"path": str(path), "exists": exists, "bytes": path.stat().st_size if exists else 0}


def dir_bytes(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) if path.is_dir() else 0


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def run(levels: list[str]) -> dict:
    if not Path("app").is_dir():
        sys.exit("Run from the backend/ directory (storage roots are relative to it).")

    db = SessionLocal()
    try:
        db.execute(text("SET TRANSACTION READ ONLY"))
        cols = existing_columns(db)

        courses = db.execute(text("""
            SELECT c.id, c.level, l.code, c.title FROM courses c JOIN languages l ON l.id = c.language_id
            WHERE c.level = ANY(:levels) ORDER BY l.code, c.level
        """), {"levels": levels}).all()
        per_course = []
        lesson_ids: set = set()
        for course_id, level, lang, title in courses:
            ids = {r[0] for r in db.execute(text(
                "SELECT le.id FROM lessons le JOIN modules m ON m.id = le.module_id WHERE m.course_id = :c"), {"c": course_id}).all()}
            modules = db.execute(text("SELECT count(*) FROM modules WHERE course_id = :c"), {"c": course_id}).scalar()
            per_course.append({"course_id": str(course_id), "language": lang, "level": level, "title": title,
                               "modules_kept": modules, "lessons": len(ids)})
            lesson_ids |= ids

        # --- cascade walk over the real foreign keys -------------------------
        edges = fk_edges(db)
        affected: dict[str, set] = defaultdict(set)
        affected["lessons"] = set(lesson_ids)
        changed = True
        while changed:
            changed = False
            for child, col, parent, rule in edges:
                if rule != "CASCADE" or parent not in affected or not affected[parent] or child == parent:
                    continue
                new = ids_where(db, child, col, list(affected[parent])) - affected[child]
                if new:
                    affected[child] |= new
                    changed = True

        set_null = []
        blockers = []
        for child, col, parent, rule in edges:
            if parent in affected and affected[parent] and rule != "CASCADE":
                rows = ids_where(db, child, col, list(affected[parent])) - affected.get(child, set())
                if rows:
                    entry = {"table": child, "column": col, "parent": parent, "rule": rule, "rows": len(rows)}
                    (set_null if rule == "SET NULL" else blockers).append(entry)

        # --- guards ------------------------------------------------------------
        violations = sorted(t for t, ids in affected.items() if ids and is_protected(t))
        model_test_assessments = 0
        if affected.get("assessments"):
            model_test_assessments = db.execute(text(
                "SELECT count(*) FROM assessments WHERE id = ANY(:v) AND model_test_id IS NOT NULL"),
                {"v": list(affected["assessments"])}).scalar()

        # --- rows without a foreign key that would be orphaned ---------------
        orphans = {}
        for kind, table in (("WRITING", "student_writings"), ("SPEAKING", "student_speakings")):
            ids = list(affected.get(table, set()))
            orphans[f"ai_evaluations[{kind}]"] = db.execute(text(
                "SELECT count(*) FROM ai_evaluations WHERE kind = :k AND submission_id = ANY(:v)"),
                {"k": kind, "v": ids}).scalar() if ids else 0

        # --- files ----------------------------------------------------------------
        files = []
        for (table, col), root in KEY_FILES.items():
            ids = affected.get(table)
            if not ids or (table, col) not in cols:
                continue
            for row_id, key in db.execute(text(
                    f'SELECT id, "{col}" FROM "{table}" WHERE id = ANY(:v) AND "{col}" IS NOT NULL AND "{col}" <> \'\''),
                    {"v": list(ids)}).all():
                shared = db.execute(text(f'SELECT count(*) FROM "{table}" WHERE "{col}" = :k AND id <> ALL(:v)'),
                                    {"k": key, "v": list(ids)}).scalar()
                files.append({"table": table, "column": col, "row": str(row_id), "storage": "protected" if root != LocalStorage.ROOT else "uploads",
                              **file_info(root / key), "shared_refs": shared})

        external_urls = defaultdict(int)
        for table, col in URL_COLUMNS:
            ids = affected.get(table)
            if not ids or (table, col) not in cols:
                continue
            for row_id, url in db.execute(text(
                    f'SELECT id, "{col}" FROM "{table}" WHERE id = ANY(:v) AND "{col}" IS NOT NULL AND "{col}" <> \'\''),
                    {"v": list(ids)}).all():
                if url.startswith(("http://", "https://")):
                    external_urls[f"{table}.{col}"] += 1
                    continue
                if not url.startswith("/uploads/"):
                    continue  # /api/... = served from a key column above
                shared = 0
                for st, sc in SHARED_URL_COLUMNS:
                    if (st, sc) not in cols:
                        continue
                    exclude = list(affected.get(st, set()))
                    shared += db.execute(text(f'SELECT count(*) FROM "{st}" WHERE "{sc}" = :u AND NOT (id = ANY(:v))'),
                                         {"u": url, "v": exclude}).scalar()
                files.append({"table": table, "column": col, "row": str(row_id), "storage": "uploads",
                              **file_info(LocalStorage.ROOT / url.removeprefix("/uploads/")), "shared_refs": shared})

        upload_dirs = []
        for (sid,) in db.execute(text("SELECT id FROM video_upload_sessions WHERE id = ANY(:v)"),
                                 {"v": list(affected.get("video_upload_sessions", set()))}).all():
            d = ProtectedVideoUploadTempStorage.ROOT / str(sid)
            upload_dirs.append({"path": str(d), "exists": d.is_dir(), "bytes": dir_bytes(d)})

        # Files on disk under the video / lesson-audio roots that no row references at all.
        referenced = {Path(f["path"]).resolve() for f in files}
        all_keys = set()
        for (table, col), root in KEY_FILES.items():
            if (table, col) in cols:
                all_keys |= {(root / k).resolve() for (k,) in db.execute(text(
                    f'SELECT "{col}" FROM "{table}" WHERE "{col}" IS NOT NULL AND "{col}" <> \'\'')).all()}
        unreferenced = []
        for root in (ProtectedVideoStorage.ROOT / "videos", ProtectedLessonListeningStorage.ROOT):
            if root.is_dir():
                for p in root.rglob("*"):
                    if p.is_file() and p.resolve() not in all_keys and "thumbnails" not in p.parts:
                        unreferenced.append({"path": str(p), "bytes": p.stat().st_size})

        db.rollback()
    finally:
        db.close()

    deletable = [f for f in files if f["exists"] and f["shared_refs"] == 0]
    return {
        "levels": levels,
        "cwd": os.getcwd(),
        "storage_roots": {name: str(r.resolve()) for name, r in (
            ("videos", ProtectedVideoStorage.ROOT), ("uploads", LocalStorage.ROOT),
            ("lesson_listening", ProtectedLessonListeningStorage.ROOT), ("assessment_audio", ProtectedLocalStorage.ROOT),
            ("legacy_speaking", ProtectedLegacySpeakingStorage.ROOT), ("video_uploads", ProtectedVideoUploadTempStorage.ROOT))},
        "courses": per_course,
        "rows": {t: len(ids) for t, ids in sorted(affected.items()) if ids},
        "set_null": set_null,
        "blockers": blockers,
        "orphans_without_fk": orphans,
        "guard_violations": violations,
        "model_test_assessments_in_set": model_test_assessments,
        "files": files,
        "files_summary": {
            "referenced": len(files),
            "existing": sum(f["exists"] for f in files),
            "missing_on_disk": sum(not f["exists"] for f in files),
            "shared_keep": sum(f["shared_refs"] > 0 for f in files),
            "deletable": len(deletable),
            "deletable_bytes": sum(f["bytes"] for f in deletable),
        },
        "external_urls_not_deleted": dict(external_urls),
        "upload_session_dirs": upload_dirs,
        "unreferenced_files_on_disk": unreferenced,
    }


def print_report(r: dict) -> None:
    print(f"COURSE CONTENT AUDIT (read-only) — levels {', '.join(r['levels'])}")
    print(f"working directory: {r['cwd']}")
    for name, path in r["storage_roots"].items():
        print(f"  root {name:17} {path}  {'(exists)' if Path(path).exists() else '(MISSING)'}")
    print("\nCourses (kept) / modules (kept) / lessons (would be deleted):")
    for c in r["courses"]:
        print(f"  {c['language']} {c['level']:3} {c['title'][:40]:40} modules={c['modules_kept']:3} lessons={c['lessons']}")
    print("\nRows removed by ON DELETE CASCADE:")
    for t, n in r["rows"].items():
        print(f"  {t:32} {n}")
    print(f"  {'TOTAL':32} {sum(r['rows'].values())}")
    for e in r["set_null"]:
        print(f"SET NULL: {e['table']}.{e['column']} -> {e['parent']}: {e['rows']} rows keep, column nulled")
    for e in r["blockers"]:
        print(f"BLOCKER ({e['rule']}): {e['table']}.{e['column']} -> {e['parent']}: {e['rows']} rows")
    for k, n in r["orphans_without_fk"].items():
        print(f"orphaned without FK (must be deleted explicitly): {k}: {n}")
    s = r["files_summary"]
    print(f"\nFiles referenced: {s['referenced']} · on disk: {s['existing']} · missing: {s['missing_on_disk']} · "
          f"shared (keep): {s['shared_keep']} · deletable: {s['deletable']} ({human(s['deletable_bytes'])})")
    by_kind = defaultdict(lambda: [0, 0])
    for f in r["files"]:
        if f["exists"] and f["shared_refs"] == 0:
            by_kind[f"{f['table']}.{f['column']}"][0] += 1
            by_kind[f"{f['table']}.{f['column']}"][1] += f["bytes"]
    for k, (n, b) in sorted(by_kind.items()):
        print(f"  {k:36} {n:5} files  {human(b)}")
    if r["external_urls_not_deleted"]:
        print(f"external URLs (not deleted): {r['external_urls_not_deleted']}")
    if r["upload_session_dirs"]:
        print(f"unfinished upload dirs: {len(r['upload_session_dirs'])} ({human(sum(d['bytes'] for d in r['upload_session_dirs']))})")
    if r["unreferenced_files_on_disk"]:
        print(f"files on disk referenced by NO row (pre-existing orphans): {len(r['unreferenced_files_on_disk'])} "
              f"({human(sum(f['bytes'] for f in r['unreferenced_files_on_disk']))})")
    print("\nGUARDS:")
    print(f"  protected tables in delete set: {r['guard_violations'] or 'none'}")
    print(f"  Vorbereitung (model test) assessments in delete set: {r['model_test_assessments_in_set']}")
    ok = not r["guard_violations"] and not r["blockers"] and not r["model_test_assessments_in_set"]
    print(f"  RESULT: {'OK — nothing outside the course content would be touched' if ok else 'STOP — see above'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--levels", nargs="+", default=LEVELS, choices=LEVELS)
    parser.add_argument("--json", help="write the full report (incl. every file path) to this file")
    args = parser.parse_args()
    report = run(args.levels)
    print_report(report)
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print(f"\nfull report: {args.json}")
    if report["guard_violations"] or report["blockers"] or report["model_test_assessments_in_set"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
