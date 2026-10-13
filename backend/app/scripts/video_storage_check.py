"""Read-only check of lesson video files: for each video (or the given ids)
the DB row, the absolute path its storage_key resolves to, whether the file
is there — and, for a missing file, where a file with the same name exists
instead (other storage roots, another working directory). Changes nothing.

Run it exactly like the service runs (same user, same working directory —
`systemctl show vizu-backend -p WorkingDirectory`), because the storage
roots are relative to the working directory:

    cd /opt/vizu/VIZU-Academy/backend
    .venv/bin/python -m app.scripts.video_storage_check c0703df1-2f04-435d-a76f-054d107e3f2e
    .venv/bin/python -m app.scripts.video_storage_check --published --missing-only
"""

import argparse
import os
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.core.storage.local import LocalStorage
from app.core.storage.protected_local import ProtectedVideoStorage
from app.db.session import SessionLocal
from app.models.video import Video
from app.services.video.service import stored_file_path

MAX_SEARCH_FILES = 200_000


def candidate_roots() -> list[Path]:
    """Where a misplaced video file could be: the current root, the public
    uploads root (where videos lived before protected storage), and the
    same roots relative to the repository / backend directory."""
    backend = Path(__file__).resolve().parents[2]
    roots = [ProtectedVideoStorage.ROOT, LocalStorage.ROOT, backend / "app" / "protected_storage", backend / "uploads",
             backend.parent / "app" / "protected_storage", backend.parent / "uploads"]
    out, seen = [], set()
    for r in roots:
        r = r.resolve()
        if r not in seen and r.is_dir():
            seen.add(r)
            out.append(r)
    return out


def find_by_name(name: str, roots: list[Path]) -> list[str]:
    hits, scanned = [], 0
    for root in roots:
        for dirpath, _, files in os.walk(root):
            scanned += len(files)
            if name in files:
                hits.append(str(Path(dirpath) / name))
            if scanned > MAX_SEARCH_FILES:
                return hits + ["(search stopped: too many files)"]
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", help="video ids (default: all videos)")
    ap.add_argument("--published", action="store_true", help="only published videos")
    ap.add_argument("--missing-only", action="store_true", help="print only videos whose file is missing")
    args = ap.parse_args()

    roots = candidate_roots()
    print(f"working directory : {Path.cwd()}")
    print(f"video storage root: {ProtectedVideoStorage.ROOT.resolve()} (exists: {ProtectedVideoStorage.ROOT.is_dir()})")
    print("search roots      : " + ", ".join(str(r) for r in roots))
    db = SessionLocal()
    try:
        q = select(Video).order_by(Video.created_at)
        if args.ids:
            q = q.where(Video.id.in_([UUID(i) for i in args.ids]))
        if args.published:
            q = q.where(Video.is_published.is_(True))
        rows = list(db.scalars(q))
        found_ids = {str(v.id) for v in rows}
        for i in args.ids:
            if i not in found_ids:
                print(f"\n{i}: NO ROW in the videos table -> the stream answers 404 'Video not found'")
        missing = 0
        for v in rows:
            path = stored_file_path(v.storage_key)
            if path is None:
                missing += 1
            elif args.missing_only:
                continue
            print(f"\n{v.id}  lesson={v.lesson_id}  published={v.is_published}  title={v.title!r}")
            print(f"  storage_key : {v.storage_key!r}")
            if not v.storage_key:
                print("  -> no storage_key: the stream answers 404 'Video not found'")
                continue
            expected = (ProtectedVideoStorage.ROOT / v.storage_key).resolve()
            print(f"  expected at : {expected}")
            if path is not None:
                print(f"  file        : OK ({path.stat().st_size} bytes)")
                continue
            print("  file        : MISSING -> the stream answers 404 'VIDEO_FILE_MISSING'")
            hits = find_by_name(Path(v.storage_key).name, roots)
            print("  same name at: " + ("; ".join(hits) if hits else "nowhere under the search roots"))
        print(f"\n{len(rows)} video(s) checked, {missing} without a readable file. Nothing was changed.")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
