"""Import the book-faithful VIZU-DEUTSCH A2 edition into the existing A2
lessons 1-14, next to the archived first edition — nothing is deleted.

    python -m app.scripts.vizu_deutsch_a2_buch.build
    python -m app.scripts.import_vizu_deutsch_a2_buch --archive-dir DIR --dry-run
    python -m app.scripts.import_vizu_deutsch_a2_buch --archive-dir DIR
    python -m app.scripts.import_vizu_deutsch_a2_buch --archive-dir DIR --publish

Per lesson:
1. lesson title / description from the book (lesson 14 -> "Wiederholung";
   is_published is not touched here);
2. the Einführung / Zusammenfassung texts of the first edition (VIZU-written,
   not in the book) are written to DIR/a2buch_competency_texts.jsonl and
   cleared — the competency row itself and its publish state stay;
3. the lesson's document goes through the regular content import
   (skip_existing: re-running never duplicates; archived rows keep their own
   content ids "vizu-a2-…" and "[Archiv] …" titles and are not touched);
4. book page images (lesson 1: S. 15) attached as draft resources;
5. the book's track numbers set as the audio label of the Hören tasks;
6. the lesson videos lose their "[Archiv] IMG_…" title (see rename_videos).

--publish additionally publishes what the import created (Hören only with
audio + key, so every keyless Hören stays a draft), the page images, the
lessons 1-13 and their competencies that have book content. Lesson 14 stays
unpublished. A2 sales (app_settings "angebote") are never touched.
"""

import argparse
import asyncio
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.content_import import ContentImport
from app.models.listening import Listening
from app.models.video import Video
from app.scripts import import_vizu_deutsch_a1 as base
from app.scripts import vizu_deutsch_a2_buch as book
from app.services.content_import import service as importer
from app.services.lms import structure

LESSONS = range(1, 15)
VIZU_TEXT_KINDS = ("EINFUEHRUNG", "ZUSAMMENFASSUNG")
# competencies shown once the lesson is published (only those with book content count)
PUBLISH_KINDS = ("EINFUEHRUNG", "WORTSCHATZ", "GRAMMATIK", "LESEN", "HOEREN", "SPRECHEN", "SCHREIBEN", "ZUSAMMENFASSUNG")


def _use_edition() -> None:
    """The A1 importer's helpers, pointed at this edition (target level A2).
    Words of the archived first edition ("vizu-a2-…", hidden) do not count
    as already present, so the edition gets its own word rows."""
    base.LEVEL = "A2"
    base.PACKAGE, base.FILE_PREFIX = "vizu_deutsch_a2_buch", "unterricht"
    base.DATA_DIR = Path(__file__).resolve().parents[1] / "data" / base.PACKAGE
    base.IMAGE_DIR = base.DATA_DIR / "images"
    importer.ARCHIVED_CONTENT_PREFIXES = ("vizu-a2-",)


def batch_file(n: int) -> str:
    return f"vizu-deutsch-a2-buch/unterricht_{n:02d}.json"


def publish_lesson_batches(db, n: int) -> list[str]:
    """Every import batch of this lesson's document (also those of earlier
    runs) through the regular publish: Hören only with audio + key, exercises
    only with keys — the rest is reported as waiting."""
    waiting = []
    for batch in db.scalars(select(ContentImport).where(ContentImport.filename == batch_file(n)).order_by(ContentImport.created_at)):
        batch = importer.publish_batch(db, batch.id)
        waiting += [f"{i['title']} ({i['publish_problem']})" for i in batch.items if i.get("publish_problem")]
    return waiting


def _json_default(v):
    if isinstance(v, (UUID, Decimal)):
        return str(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return str(v)


def clear_vizu_texts(db, lesson, archive: Path, dry_run: bool) -> int:
    rows = [c for c in structure.ensure_competencies(db, lesson) if c.kind in VIZU_TEXT_KINDS and (c.body or "").strip()]
    if dry_run or not rows:
        return len(rows)
    archive.parent.mkdir(parents=True, exist_ok=True)
    with open(archive, "a", encoding="utf-8") as fh:
        for c in rows:
            fh.write(json.dumps({"table": "lesson_competencies", "id": c.id, "lesson_id": c.lesson_id, "kind": c.kind,
                                 "is_published": c.is_published, "body": c.body, "archived_at": datetime.now(timezone.utc)},
                                default=_json_default, ensure_ascii=False) + "\n")
            c.body = None
    db.commit()
    return len(rows)


def set_audio_labels(db, lesson, dry_run: bool) -> list[str]:
    out = []
    for content_id, label in book.AUDIO_LABELS.items():
        row = db.scalar(select(Listening).where(Listening.lesson_id == lesson.id, Listening.content_id == content_id))
        if row is None or row.audio_label == label:
            continue
        out.append(f"{content_id}: {label}")
        if not dry_run:
            row.audio_label = label
    if not dry_run:
        db.commit()
    return out


def rename_videos(db, lesson, title: str, archive: Path, dry_run: bool) -> list[str]:
    """The lesson videos were renamed "[Archiv] IMG_…" when the first edition
    was archived — but a video belongs to the lesson, not to an edition (one
    row per file: uq_videos_storage_key), so it gets a lesson title back:
    "Video: <book lesson title>". Only the title changes — same row, file,
    publish state and video_progress; the old title is written to the
    archive file first (rollback = set it back)."""
    rows = [v for v in db.scalars(select(Video).where(Video.lesson_id == lesson.id).order_by(Video.order_index, Video.created_at))
            if (v.title or "").startswith("[Archiv]")]
    out = []
    for k, video in enumerate(rows, 1):
        new_title = f"Video: {title}" + (f" (Teil {k})" if len(rows) > 1 else "")
        out.append(f"„{video.title}“ -> „{new_title}“")
        if dry_run:
            continue
        archive.parent.mkdir(parents=True, exist_ok=True)
        with open(archive.with_name("a2buch_video_titles.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"table": "videos", "id": video.id, "lesson_id": video.lesson_id, "title": video.title,
                                 "archived_at": datetime.now(timezone.utc)}, default=_json_default, ensure_ascii=False) + "\n")
        video.title = new_title
    if not dry_run:
        db.commit()
    return out


def publish_structure(db, lesson) -> list[str]:
    lesson.is_published = True
    shown = []
    for c in structure.ensure_competencies(db, lesson):
        if c.kind in PUBLISH_KINDS and not c.is_published:
            c.is_published = True
            shown.append(c.kind)
    db.commit()
    return shown


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--archive-dir", required=True, help="where the cleared VIZU competency texts are written (JSON lines)")
    parser.add_argument("--lessons", type=int, nargs="*", help="default: 1-14")
    parser.add_argument("--dry-run", action="store_true", help="validate and report only, write nothing")
    parser.add_argument("--publish", action="store_true", help="publish created content, page images, lessons 1-13 and their book competencies")
    args = parser.parse_args()

    _use_edition()
    archive = Path(args.archive_dir) / "a2buch_competency_texts.jsonl"
    failed = 0
    db = SessionLocal()
    try:
        for n in args.lessons or LESSONS:
            mod = base.book_module(n)
            lesson = base.lesson_of(db, n)
            if lesson is None:
                print(f"\nLektion {n}: A2 -> module 1 -> lesson {n} does not exist — skipped")
                failed += 1
                continue
            print(f"\nLektion {n} — {lesson.id} ({lesson.title} -> {mod.LESSON_TITLE})")
            if not args.dry_run:
                base.set_lesson_meta(db, lesson, mod)
            cleared = clear_vizu_texts(db, lesson, archive, args.dry_run)
            print(f"  VIZU competency texts {'to clear' if args.dry_run else 'archived + cleared'}: {cleared}")
            videos = rename_videos(db, lesson, mod.LESSON_TITLE, archive, args.dry_run)
            print(f"  videos {'to rename' if args.dry_run else 'renamed'}: {'; '.join(videos) or 'none'}")
            if n == 14:
                print("  no book pages — no content; stays unpublished")
                continue
            document = base.load(n)
            report = importer.validate_document(db, document, create_missing=False, skip_existing=True)
            base.print_report(n, report)
            failed += report["invalid"]
            if report["errors"]:
                print("  -> document errors — lesson skipped")
                continue
            if args.dry_run:
                # Hören tasks of this edition may not exist yet; labels are set right after the import
                print(f"  audio labels (book tracks): {sum(1 for c in book.AUDIO_LABELS if c.startswith(f'vizu-a2buch-l{n:02d}-'))}")
                continue
            created = asyncio.run(base.attach_images(db, lesson, n, mod))
            if created:
                print(f"  -> {len(created)} page image(s) attached (draft)")
            if not (report["errors"] or not report["valid"]):
                batch = importer.commit_document(db, document, None, batch_file(n), skip_existing=True)
                summary = importer.batch_summary(batch)
                print(f"  -> batch {batch.id}: {summary['created_items']} created, {summary['skipped_items']} skipped, {summary['failed_items']} failed")
            else:
                print("  -> nothing new to import")
            if args.publish:
                waiting = publish_lesson_batches(db, n)
                print(f"  -> published; waiting ({len(waiting)}): " + ("; ".join(waiting) or "none"))
            labels = set_audio_labels(db, lesson, False)
            if labels:
                print(f"  -> audio labels: {', '.join(labels)}")
            if args.publish:
                print(f"  -> {base.publish_images(db, lesson, mod)} page image(s) published")
                print(f"  -> lesson published; competencies shown: {', '.join(publish_structure(db, lesson)) or 'already'}")
    finally:
        db.close()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
