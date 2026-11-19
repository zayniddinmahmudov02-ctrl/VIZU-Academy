"""SHA-256 of songs uploaded before the bulk upload's duplicate check existed (`songs.sha256`, migration e8a3c5f1b7d2).

    python -m app.scripts.medien_song_hashes plan
    python -m app.scripts.medien_song_hashes apply --confirm <plan id>

plan (nothing is written): the songs without a hash, how many of them have their stored file, how many do not (they keep NULL), and the same
file stored twice (shown, never changed). apply: exactly the songs of the plan (refused when the plan changed) get the hash of their stored file;
nothing else is touched (no file, no other column); one audit entry. Take a DB backup first."""

import argparse
import hashlib
import json
import sys
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.db.session import SessionLocal
from app.models.medien import Song
from app.services.medien import common as c


def _sha256(path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_plan(db: Session) -> dict:
    rows = db.scalars(select(Song).where(Song.sha256.is_(None)).order_by(Song.created_at, Song.id)).all()
    items, missing = [], []
    for s in rows:
        path = c.file_path(s.file_key)
        if path is None:
            missing.append(str(s.id))
        else:
            items.append({"id": str(s.id), "size": path.stat().st_size})
    plan_id = hashlib.sha256(json.dumps({"items": items, "missing": missing}, sort_keys=True).encode()).hexdigest()[:12]
    return {"plan_id": plan_id, "items": items, "missing": missing, "with_hash": db.query(Song).filter(Song.sha256.is_not(None)).count()}


def apply_plan(db: Session, confirm: str) -> dict:
    plan = build_plan(db)
    if plan["plan_id"] != confirm:
        raise SystemExit(f"STOP: the plan changed (now {plan['plan_id']}); run plan again.")
    hashes = {}
    for item in plan["items"]:
        song = db.get(Song, item["id"])
        path = c.file_path(song.file_key) if song else None
        if song is None or path is None or song.sha256 is not None:
            continue
        song.sha256 = hashes[item["id"]] = _sha256(path)
    db.commit()
    same = sum(1 for n in Counter(hashes.values()).values() if n > 1)
    write_audit(db, actor_id=None, action="medien_song_hashes", details=f"plan {confirm}: {len(hashes)} songs hashed, {len(plan['missing'])} without file, {same} identical files")
    return {"plan_id": confirm, "hashed": len(hashes), "without_file": len(plan["missing"]), "identical_files": same}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    sub.add_parser("apply").add_argument("--confirm", required=True)
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.cmd == "plan":
            plan = build_plan(db)
            print(f"song hashes — plan id {plan['plan_id']}: {len(plan['items'])} songs to hash ({sum(i['size'] for i in plan['items']) // 1048576} MB), "
                  f"{len(plan['missing'])} without a stored file (stay empty), {plan['with_hash']} already have one")
            print("READ-ONLY: nothing was changed.")
        else:
            print(json.dumps(apply_plan(db, args.confirm)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
