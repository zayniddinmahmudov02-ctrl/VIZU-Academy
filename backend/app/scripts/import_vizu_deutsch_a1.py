"""Import the VIZU-DEUTSCH A1 course book into the A1 course (lessons 1-14).

Reads app/data/vizu_deutsch_a1/modul_NN.json (built by
`python -m app.scripts.vizu_deutsch_a1.build`) and runs every document
through the regular content import (app/services/content_import): the same
validation, per-item report and batch record as the admin "Inhalte
importieren" page.

* Lessons are never created: book Modul N must already exist as
  A1 -> module 1 -> lesson N (`python -m app.scripts.ensure_lms_structure`).
* Re-runnable: content that already exists (same content_id, same title in
  the lesson, same word) is skipped — never duplicated.
* Everything is created UNPUBLISHED. Review it in the admin panel and publish
  per batch (LMS A1–C1 -> Inhalte importieren -> Importe), or pass --publish.
  Hören tasks stay hidden until their audio is uploaded (and, where the book
  has no reliable key, until an admin has set the answers).

Options for rebuilding a lesson from the book (explicit, per module):
  --replace --archive-dir DIR   the lesson's existing Lesen / Hören / Schreiben /
                                Sprechen / Frage / Grammatik / Wortschatz /
                                exercise content and the competency texts the
                                module provides are written to DIR as JSON and
                                removed. Content with student history
                                (attempts, submissions) is never deleted: it is
                                hidden and renamed "[Archiv] …" instead.
  --lesson-meta                 set the lesson title / description from the book
  --images                      attach the book's page images as (draft) image
                                resources of the matching competencies
  --remove-grammar-images --archive-dir DIR
                                only archive + remove the outdated Grammatik
                                images (image resources, retired book pages,
                                images in the Grammatik text); nothing else

Without --replace an existing lesson keeps its old content (new items are
skipped by content_id) — to rebuild lessons from the book always use --replace.

    python -m app.scripts.import_vizu_deutsch_a1 --modules 1 2 3 4 5 6 7 8 9 10 11 12 13 14 --replace \\
        --archive-dir /var/backups/vizu/a1 --lesson-meta --images --publish --dry-run
    python -m app.scripts.import_vizu_deutsch_a1 --remove-grammar-images --archive-dir /var/backups/vizu/a1-grammar --dry-run
"""

import argparse
import asyncio
import importlib
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from sqlalchemy import select, text

from app.db.session import SessionLocal
from app.models.grammar import Grammar
from app.models.lesson import Lesson
from app.models.lesson_skill import SkillExercise
from app.models.listening import Listening
from app.models.lms import LearningResource, LessonCompetency
from app.models.reading import Reading
from app.models.speaking import Speaking
from app.models.vocabulary import Vocabulary
from app.models.writing import Writing
from app.services.content_import import service as importer
from app.services.lms import grammar_text_only

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "vizu_deutsch_a1"
IMAGE_DIR = DATA_DIR / "images"
LEVEL, MODULE = "A1", 1
# --level A2 / B1: the VIZU-DEUTSCH A2 / B1 book (app/scripts/vizu_deutsch_a2|b1, files unterricht_NN)
PACKAGE, FILE_PREFIX = "vizu_deutsch_a1", "modul"
LEVELS = {"A1": ("vizu_deutsch_a1", "modul"), "A2": ("vizu_deutsch_a2", "unterricht"), "B1": ("vizu_deutsch_b1", "unterricht")}


def set_level(level: str) -> None:
    global LEVEL, PACKAGE, FILE_PREFIX, DATA_DIR, IMAGE_DIR
    LEVEL = level
    PACKAGE, FILE_PREFIX = LEVELS[level]
    DATA_DIR = Path(__file__).resolve().parents[1] / "data" / PACKAGE
    IMAGE_DIR = DATA_DIR / "images"


# lesson content replaced by --replace (table, model)
CONTENT = (("readings", Reading), ("listenings", Listening), ("writings", Writing), ("speakings", Speaking),
           ("grammars", Grammar), ("vocabularies", Vocabulary), ("skill_exercises", SkillExercise))
# rows referencing these are student history: never deleted
STUDENT_HISTORY = {"lesson_skill_attempts", "student_writings", "student_speakings", "ai_evaluations"}
def load(n: int) -> dict:
    return json.loads((DATA_DIR / f"{FILE_PREFIX}_{n:02d}.json").read_text(encoding="utf-8"))


def book_module(n: int):
    return importlib.import_module(f"app.scripts.{PACKAGE}.{FILE_PREFIX}_{n:02d}")


def lesson_of(db, n: int) -> Lesson | None:
    target = importer._resolve_target(db, "de", type("T", (), {"level": LEVEL, "module": MODULE, "lesson": n})(), False, {})
    return db.get(Lesson, UUID(target["lesson_id"])) if target.get("lesson_id") else None


def print_report(n: int, report: dict) -> None:
    print(f"\nModul {n}: {report['total']} items · {report['valid']} to import · {report.get('skipped', 0)} skipped · {report['invalid']} invalid")
    for e in report["errors"]:
        print(f"  ERROR {e}")
    for r in report["items"]:
        state = "OK  " if r["valid"] else ("SKIP" if r.get("skip") and not r["errors"] else "FAIL")
        print(f"  {state} {r['skill']:<18} {r['content_id']}  {r['title']}")
        if r.get("skip") and not r["errors"]:
            print(f"         {r['skip']}")
        for e in r["errors"]:
            print(f"         error: {e}")
        for w in r["warnings"]:
            print(f"         note: {w}")


# ============================================================
# --replace
# ============================================================


def _json_default(v):
    if isinstance(v, (UUID, Decimal)):
        return str(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return str(v)


def replace_plan(db, lesson: Lesson, document: dict, mod=None) -> dict:
    """What --replace would do: per content row 'delete' or 'archive'
    (student history), the competency texts the module brings, and the
    lesson's image resources that are outdated: every image of the
    Grammatik competency (grammar is taught as text / tables) and the book
    page images an earlier import attached that the module retired; images
    embedded in the Grammatik competency text are stripped from it.
    Videos, audio, PDFs and other resources are never touched."""
    from app.scripts.course_content_audit import fk_edges
    from app.scripts.legacy_content_cleanup import HISTORY_TABLES, cascade

    edges = fk_edges(db)
    history_tables = HISTORY_TABLES | STUDENT_HISTORY
    rows = []
    for table, model in CONTENT:
        for row in db.scalars(select(model).where(model.lesson_id == lesson.id)):
            affected = cascade(db, edges, table, [row.id])
            history = sum(len(affected.get(t, ())) for t in history_tables)
            rows.append({"table": table, "model": model, "id": row.id, "title": getattr(row, "title", None) or getattr(row, "german_word", None),
                         "content_id": row.content_id, "action": "archive" if history else "delete", "history_rows": history,
                         "affected": {t: sorted(str(i) for i in ids) for t, ids in affected.items()}})
    kinds = {i["competency"] for i in document["items"] if i.get("skill") == "kompetenz"}
    competencies = [c for c in db.scalars(select(LessonCompetency).where(LessonCompetency.lesson_id == lesson.id, LessonCompetency.kind.in_(kinds)))
                    if (c.body or "").strip()]
    retired = set(getattr(mod, "RETIRED_IMAGE_TITLES", []))
    images = [r for r in db.scalars(select(LearningResource).where(LearningResource.lesson_id == lesson.id, LearningResource.resource_type == "IMAGE"))
              if r.competency == "GRAMMATIK" or r.title in retired]
    grammar_texts = [c for c in db.scalars(select(LessonCompetency).where(LessonCompetency.lesson_id == lesson.id, LessonCompetency.kind == "GRAMMATIK"))
                     if c not in competencies and grammar_text_only.has_images(c.body)]
    return {"rows": rows, "competencies": competencies, "images": images, "grammar_texts": grammar_texts}


def grammar_image_plan(db, lesson: Lesson, mod=None) -> dict:
    """--remove-grammar-images: only the outdated images (Grammatik image
    resources, retired book pages, images in the Grammatik text); the
    lesson's content stays as it is."""
    retired = set(getattr(mod, "RETIRED_IMAGE_TITLES", []))
    images = [r for r in db.scalars(select(LearningResource).where(LearningResource.lesson_id == lesson.id, LearningResource.resource_type == "IMAGE"))
              if r.competency == "GRAMMATIK" or r.title in retired]
    grammar_texts = [c for c in db.scalars(select(LessonCompetency).where(LessonCompetency.lesson_id == lesson.id, LessonCompetency.kind == "GRAMMATIK"))
                     if grammar_text_only.has_images(c.body)]
    return {"rows": [], "competencies": [], "images": images, "grammar_texts": grammar_texts}


def print_replace_plan(plan: dict) -> None:
    deletes = [r for r in plan["rows"] if r["action"] == "delete"]
    archives = [r for r in plan["rows"] if r["action"] == "archive"]
    print(f"  replace: {len(deletes)} row(s) to delete, {len(archives)} with student history to hide as [Archiv], "
          f"{len(plan['competencies'])} competency text(s) to clear, {len(plan['images'])} outdated image(s) to remove, "
          f"{len(plan.get('grammar_texts', []))} Grammatik text(s) with embedded images to strip")
    for r in plan["images"]:
        print(f"    remove  image ({r.competency or 'Lektion'}) {r.title!s:.60}")
    for r in plan["rows"]:
        print(f"    {r['action']:<7} {r['table']:<16} {r['title']!s:.60}" + (f"  ({r['history_rows']} history rows kept)" if r["history_rows"] else ""))


def execute_replace(db, plan: dict, archive_dir: Path, stamp: str) -> dict:
    archive_dir.mkdir(parents=True, exist_ok=True)
    with open(archive_dir / "content.jsonl", "a", encoding="utf-8") as fh:
        for r in plan["rows"]:
            for table, ids in r["affected"].items():
                for row in db.execute(text(f'SELECT * FROM "{table}" WHERE id = ANY(CAST(:v AS uuid[]))'), {"v": ids}).mappings():
                    fh.write(json.dumps({"root": f"{r['table']}:{r['id']}", "table": table, "row": dict(row)}, default=_json_default, ensure_ascii=False) + "\n")
        for c in [*plan["competencies"], *plan.get("grammar_texts", [])]:
            fh.write(json.dumps({"root": f"lesson_competencies:{c.id}", "table": "lesson_competencies",
                                 "row": {"id": c.id, "lesson_id": c.lesson_id, "kind": c.kind, "body": c.body}}, default=_json_default, ensure_ascii=False) + "\n")
    deleted = archived = 0
    for r in plan["rows"]:
        row = db.get(r["model"], r["id"])
        if row is None:
            continue
        if r["action"] == "delete":
            savepoint = db.begin_nested()
            try:
                db.delete(row)
                db.flush()
                savepoint.commit()
                deleted += 1
                continue
            except Exception:  # noqa: BLE001 — a non-cascading reference: keep the row, archive it
                savepoint.rollback()
                row = db.get(r["model"], r["id"])
        row.is_published = False
        if hasattr(row, "title") and row.title and not row.title.startswith("[Archiv]"):
            row.title = f"[Archiv] {row.title}"[:255]
        row.content_id = f"archiv-{stamp}-{row.content_id or row.id}"[:120]
        archived += 1
    for c in plan["competencies"]:
        c.body = None
    for c in plan.get("grammar_texts", []):
        c.body = grammar_text_only.strip_images(c.body or "") or None
    db.commit()
    images = asyncio.run(_remove_images(db, plan["images"], archive_dir))
    return {"deleted": deleted, "archived": archived, "competency_texts_cleared": len(plan["competencies"]),
            "grammar_text_images_stripped": len(plan.get("grammar_texts", [])), "images_removed": images}


async def _remove_images(db, images: list, archive_dir: Path) -> int:
    """Each image: its row to images.jsonl and a copy of the file to
    archive_dir/images/, then the regular resource delete (the file goes
    only when no other resource uses it)."""
    import shutil

    from app.services.lms import resources

    if not images:
        return 0
    (archive_dir / "images").mkdir(parents=True, exist_ok=True)
    with open(archive_dir / "images.jsonl", "a", encoding="utf-8") as fh:
        for r in images:
            fh.write(json.dumps({c.name: getattr(r, c.name) for c in r.__table__.columns}, default=_json_default, ensure_ascii=False) + "\n")
            path = resources.file_path(r)
            if path is not None:
                shutil.copy2(path, archive_dir / "images" / f"{r.id}{path.suffix}")
    for r in images:
        await resources.delete_resource(db, r)
    return len(images)


# ============================================================
# --lesson-meta / --images
# ============================================================


def set_lesson_meta(db, lesson: Lesson, mod) -> bool:
    title, description = getattr(mod, "LESSON_TITLE", None), getattr(mod, "LESSON_DESCRIPTION", None)
    changed = False
    if title and lesson.title != title:
        lesson.title, changed = title, True
    if description and lesson.description != description:
        lesson.description, changed = description, True
    db.commit()
    return changed


async def attach_images(db, lesson: Lesson, n: int, mod) -> list[str]:
    from starlette.datastructures import Headers, UploadFile

    from app.services.lms import resources

    have = {t for (t,) in db.execute(select(LearningResource.title).where(LearningResource.lesson_id == lesson.id))}
    created = []
    for filename, competency, title in getattr(mod, "IMAGES", []):
        if title in have:
            continue
        path = IMAGE_DIR / f"{FILE_PREFIX}_{n:02d}" / filename
        with open(path, "rb") as fh:
            upload = UploadFile(fh, filename=filename, headers=Headers({"content-type": "image/jpeg"}))
            await resources.create_file_resource(db, lesson, resource_type="IMAGE", file=upload, title=title, competency=competency,
                                                 description=f"VIZU-DEUTSCH {LEVEL}", duration_seconds=None, actor_id=None)
        created.append(title)
    return created


def _audio_duration(path: Path) -> int | None:
    import subprocess

    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                             capture_output=True, text=True, timeout=60)
        return round(float(out.stdout.strip()))
    except Exception:  # noqa: BLE001 — duration is optional
        return None


def _concat_audio(paths: list[Path], out: Path) -> None:
    """Several book tracks of ONE Hören task (Text 1, Text 2 …) -> one MP3,
    in the given order. The source files stay untouched."""
    import subprocess

    args = ["ffmpeg", "-y", "-loglevel", "error"]
    for p in paths:
        args += ["-i", str(p)]
    args += ["-filter_complex", f"concat=n={len(paths)}:v=0:a=1", "-c:a", "libmp3lame", "-q:a", "3", str(out)]
    subprocess.run(args, check=True, timeout=600)


def attach_audio(db, lesson: Lesson, mod, audio_dir: Path, publish: bool, dry_run: bool) -> list[str]:
    """--audio-dir: the module's AUDIO = {content_id: file | [files]} — each
    file is uploaded to the Hören task with that content_id of THIS lesson
    through the regular upload (type checked by content, stored privately).
    A task that already has audio is left alone (re-runnable). With --publish
    a task is published only when its audio file exists and every question
    has a key; otherwise it stays a draft."""
    import tempfile

    from starlette.datastructures import Headers, UploadFile

    from app.services.lesson_skills import admin as skill_admin
    from app.services.lesson_skills.hoeren_pdf_import import readiness

    import unicodedata

    # file names may be stored decomposed (NFD "ö" from macOS) — match on NFC
    on_disk = {unicodedata.normalize("NFC", p.name): p for p in audio_dir.iterdir() if p.is_file()} if audio_dir.is_dir() else {}
    holds = {i["content_id"]: (i.get("metadata") or {}).get("publish_hold") for i in mod.items()} if hasattr(mod, "items") else {}
    report = []
    for content_id, files in getattr(mod, "AUDIO", {}).items():
        listening = db.scalar(select(Listening).where(Listening.lesson_id == lesson.id, Listening.content_id == content_id))
        if listening is None:
            report.append(f"{content_id}: Hören-Aufgabe fehlt (erst importieren)")
            continue
        names = files if isinstance(files, list) else [files]
        paths = [on_disk.get(unicodedata.normalize("NFC", n), audio_dir / n) for n in names]
        missing = [p.name for p in paths if not p.is_file()]
        if listening.audio_storage_path:
            state = "hat schon Audio"
        elif missing:
            report.append(f"{content_id}: Datei fehlt: {', '.join(missing)}")
            continue
        elif dry_run:
            state = f"würde hochladen: {' + '.join(names)}"
        else:
            with tempfile.TemporaryDirectory() as tmp:
                if len(paths) > 1:
                    source = Path(tmp) / (Path(names[0]).stem.rsplit(" ", 1)[0] + f" 1-{len(paths)}.mp3")
                    try:
                        _concat_audio(paths, source)
                    except Exception as exc:  # noqa: BLE001 — e.g. ffmpeg not installed: report, do not stop the import
                        report.append(f"{content_id}: Zusammenfügen fehlgeschlagen ({type(exc).__name__}) — nichts hochgeladen")
                        continue
                else:
                    source = paths[0]
                ctype = "audio/mp4" if source.suffix.lower() == ".m4a" else "audio/mpeg"
                with open(source, "rb") as fh:
                    upload = UploadFile(fh, filename=source.name, headers=Headers({"content-type": ctype}))
                    asyncio.run(skill_admin.upload_listening_audio(db, listening.id, upload, _audio_duration(source)))
            db.refresh(listening)
            state = f"hochgeladen: {listening.audio_original_name}"
        if publish and not dry_run and not listening.is_published and holds.get(content_id):
            state += f" · Entwurf (HOLD: {holds[content_id]})"
        elif publish and not dry_run and not listening.is_published:
            ready = readiness(db, listening)
            if ready["ready"]:
                listening.is_published = True
                db.commit()
                state += " · veröffentlicht"
            else:
                state += " · Entwurf (" + ", ".join(ready["reasons"]) + ")"
        report.append(f"{content_id}: {state}")
    return report


def publish_images(db, lesson: Lesson, mod) -> int:
    titles = [t for _, _, t in getattr(mod, "IMAGES", [])]
    rows = list(db.scalars(select(LearningResource).where(LearningResource.lesson_id == lesson.id, LearningResource.title.in_(titles))))
    for r in rows:
        r.is_published = True
    db.commit()
    return len(rows)


# ============================================================


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--level", choices=sorted(LEVELS), default="A1", help="which VIZU-DEUTSCH book (default A1)")
    parser.add_argument("--modules", type=int, nargs="*", help="book modules (default: all available)")
    parser.add_argument("--dry-run", action="store_true", help="validate and report only, write nothing")
    parser.add_argument("--publish", action="store_true", help="publish what was created (Hören without audio/key stays hidden)")
    parser.add_argument("--replace", action="store_true", help="archive + remove the lesson's existing content first (needs --archive-dir)")
    parser.add_argument("--archive-dir", help="where --replace writes the removed content (JSON lines)")
    parser.add_argument("--lesson-meta", action="store_true", help="set the lesson title / description from the book")
    parser.add_argument("--images", action="store_true", help="attach the book's page images as image resources")
    parser.add_argument("--audio-dir", help="upload the module's AUDIO files from this folder to their Hören tasks (after the import)")
    parser.add_argument("--remove-grammar-images", action="store_true",
                        help="only archive + remove the outdated Grammatik images (needs --archive-dir; content untouched, nothing imported)")
    args = parser.parse_args()
    if (args.replace or args.remove_grammar_images) and not args.archive_dir:
        parser.error("--replace / --remove-grammar-images need --archive-dir")
    if (args.replace or args.lesson_meta or args.images or args.audio_dir) and not args.modules:
        parser.error("--replace / --lesson-meta / --images / --audio-dir need explicit --modules")

    set_level(args.level)
    modules = args.modules or sorted(int(p.stem.split("_")[1]) for p in DATA_DIR.glob(f"{FILE_PREFIX}_*.json"))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    failed = 0
    db = SessionLocal()
    try:
        for n in modules:
            document = load(n)
            mod = book_module(n)
            if args.remove_grammar_images:
                lesson = lesson_of(db, n)
                if lesson is None:
                    print(f"\nModul {n}: lesson {LEVEL} -> module {MODULE} -> lesson {n} does not exist — skipped")
                    failed += 1
                    continue
                plan = grammar_image_plan(db, lesson, mod)
                print(f"\nModul {n} — lesson {lesson.id} ({lesson.title}): {len(plan['images'])} outdated image(s), "
                      f"{len(plan['grammar_texts'])} Grammatik text(s) with images")
                for r in plan["images"]:
                    print(f"    remove  image ({r.competency or 'Lektion'}) {r.title!s:.60}")
                if not args.dry_run and (plan["images"] or plan["grammar_texts"]):
                    result = execute_replace(db, plan, Path(args.archive_dir) / f"modul_{n:02d}", stamp)
                    print(f"  -> {result}")
                continue
            needs_lesson = args.replace or args.lesson_meta or args.images or args.audio_dir
            lesson = lesson_of(db, n) if needs_lesson else None
            if needs_lesson and lesson is None:
                print(f"\nModul {n}: lesson {LEVEL} -> module {MODULE} -> lesson {n} does not exist — skipped")
                failed += 1
                continue
            if args.replace:
                plan = replace_plan(db, lesson, document, mod)
                print(f"\nModul {n} — lesson {lesson.id} ({lesson.title})")
                print_replace_plan(plan)
                if args.dry_run:
                    print("  (dry run: nothing replaced; the import report below still sees the old content)")
                else:
                    result = execute_replace(db, plan, Path(args.archive_dir) / f"modul_{n:02d}", stamp)
                    print(f"  -> replaced: {result}; archive {Path(args.archive_dir) / f'modul_{n:02d}'}")
            report = importer.validate_document(db, document, create_missing=False, skip_existing=True)
            print_report(n, report)
            failed += report["invalid"]
            if args.dry_run:
                if args.audio_dir:
                    for line in attach_audio(db, lesson, mod, Path(args.audio_dir), args.publish, True):
                        print(f"  -> audio {line}")
                continue
            if args.lesson_meta and set_lesson_meta(db, lesson, mod):
                print(f"  -> lesson title / description set: {lesson.title}")
            if args.images:
                created = asyncio.run(attach_images(db, lesson, n, mod))
                print(f"  -> {len(created)} page image(s) attached (draft)")
            if not (report["errors"] or not report["valid"]):
                batch = importer.commit_document(db, document, None, f"{PACKAGE.replace('_', '-')}/{FILE_PREFIX}_{n:02d}.json", skip_existing=True)
                summary = importer.batch_summary(batch)
                print(f"  -> batch {batch.id}: {summary['created_items']} created, {summary['skipped_items']} skipped, {summary['failed_items']} failed")
                if args.publish:
                    batch = importer.publish_batch(db, batch.id)
                    waiting = [i for i in batch.items if i.get("publish_problem")]
                    print("  -> published; waiting: " + (", ".join(f"{i['title']} ({i['publish_problem']})" for i in waiting) or "none"))
                    if args.images:
                        print(f"  -> {publish_images(db, lesson, mod)} page image(s) published")
            if args.audio_dir:
                for line in attach_audio(db, lesson, mod, Path(args.audio_dir), args.publish, args.dry_run):
                    print(f"  -> audio {line}")
    finally:
        db.close()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
