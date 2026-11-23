"""Publish a signed Android APK as the current VIZU-DEUTSCH app release from a file on the server (the same rules as
Admin → App Management, app.services.app_releases.service.check_apk: package, not debug-signed, the same certificate as every
earlier release, a new and higher versionCode).

    python -m app.scripts.app_release_publish plan --apk /root/vizu-apk/VIZU-DEUTSCH-1.0.0.apk --notes-file notes.txt
    python -m app.scripts.app_release_publish apply --confirm <plan id> --apk … --notes-file … --backup-dir /var/backups/vizu/<dir>

`plan` only reads the APK and the database. `apply` re-checks the plan id (APK sha256 + notes + current latest release),
writes a JSON copy of the app_releases rows to the backup dir, copies the APK into the private release storage under a random
name, creates the release (draft) and publishes it (the previous latest stays as history), with audit entries APP_RELEASE_UPLOAD
and APP_RELEASE_PUBLISH. Nothing is deleted.
"""

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.app_release import AppRelease
from app.services.app_releases import service as releases
from app.services.app_releases.apk import ApkError


def build_plan(db: Session, apk: Path, notes: str) -> dict:
    if not apk.is_file() or apk.suffix.lower() != ".apk":
        raise RuntimeError(f"not an .apk file: {apk}")
    try:
        info = releases.check_apk(db, apk)
    except ApkError as e:
        raise RuntimeError(f"refused: {e.code}")
    current = releases.latest(db)
    if current is not None and info.version_code <= current.version_code:
        raise RuntimeError(f"refused: VERSION_CODE_NOT_NEWER (latest is {current.version_name} / {current.version_code})")
    state = [info.sha256, notes.strip(), str(current.id) if current else None]
    return {
        "plan_id": hashlib.sha256(json.dumps(state).encode()).hexdigest()[:12],
        "package": info.package, "version_name": info.version_name, "version_code": info.version_code, "min_sdk": info.min_sdk,
        "min_android": releases.android_version(info.min_sdk), "size_bytes": info.size_bytes, "sha256": info.sha256,
        "signer_sha256": info.signer_sha256, "current_latest": f"{current.version_name} ({current.version_code})" if current else None,
        "notes": notes.strip(),
    }


def apply_plan(db: Session, confirm: str, apk: Path, notes: str, backup_dir: Path) -> dict:
    plan = build_plan(db, apk, notes)
    if plan["plan_id"] != confirm:
        raise RuntimeError(f"plan id is {plan['plan_id']}, not {confirm} — run `plan` again")
    backup_dir.mkdir(parents=True, exist_ok=True)
    rows = [releases.admin_view(r) for r in db.scalars(select(AppRelease).order_by(AppRelease.version_code))]
    (backup_dir / f"app-releases-before-{plan['plan_id']}.json").write_text(
        json.dumps({"taken_at": datetime.now(timezone.utc).isoformat(), "rows": rows}, indent=1, default=str), encoding="utf-8")
    storage_name = f"{uuid4().hex}.apk"
    target = releases.storage._inside_root(storage_name)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(apk, target)
    if hashlib.sha256(target.read_bytes()).hexdigest() != plan["sha256"]:
        target.unlink(missing_ok=True)
        raise RuntimeError("the copied file differs from the planned one — nothing was published")
    try:
        info = releases.check_apk(db, target)
        release = releases.register(db, None, info, storage_name, f"VIZU-DEUTSCH-{info.version_name}.apk", notes)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    published = releases.publish(db, None, release.id)
    return {"plan_id": plan["plan_id"], "release_id": published["id"], "version": published["version_name"],
            "version_code": published["version_code"], "sha256": published["sha256"], "status": published["status"],
            "is_latest": published["is_latest"]}


def main(argv=None) -> int:
    from app.db.session import SessionLocal

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "apply"):
        p = sub.add_parser(name)
        p.add_argument("--apk", required=True)
        p.add_argument("--notes-file", required=True)
        if name == "apply":
            p.add_argument("--confirm", required=True)
            p.add_argument("--backup-dir", required=True)
    args = parser.parse_args(argv)
    notes = Path(args.notes_file).read_text(encoding="utf-8")
    db = SessionLocal()
    try:
        if args.cmd == "plan":
            print(json.dumps(build_plan(db, Path(args.apk), notes), ensure_ascii=False, indent=1))
            print("READ-ONLY: nothing was changed.")
        else:
            print(json.dumps(apply_plan(db, args.confirm, Path(args.apk), notes, Path(args.backup_dir)), ensure_ascii=False, indent=1))
    except RuntimeError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    finally:
        db.rollback()
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
