"""Make a SUPER_ADMIN account also a teacher (Admin → Team row "Admin + Lehrkraft" + My Teacher catalog) — the owner's request of
2026-11-25. The account keeps its role and every admin right; only `teacher_profiles.teaches` is set (row made if missing).

    python -m app.scripts.team_admin_teaches plan [--user-id <uuid>]
    python -m app.scripts.team_admin_teaches apply --confirm <plan id> --backup-dir <dir> [--user-id <uuid>]

Without --user-id the target is the only active SUPER_ADMIN (more than one → STOP, name it). `plan` is read-only and prints the
account only as id + masked username (no e-mail / name). `apply` checks the plan id again, writes a JSON copy of the account's
teacher_profiles row (or "none") to --backup-dir, sets the flag through app.services.teacher.team.set_admin_teaches (audit
`team_staff_teacher_added`) and one more audit entry with the plan id. Idempotent: a second plan says "nothing to do"."""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.core.audit import write_audit
from app.core.security.roles import UserRole
from app.db.session import SessionLocal
from app.models.study_group import GROUP_ARCHIVED, StudyGroup
from app.models.teacher_profile import TeacherProfile
from app.models.user import User


def _mask(name: str) -> str:
    return (name[:2] + "***") if name else "***"


def _target(db: Session, user_id: str | None) -> User:
    if user_id:
        user = db.get(User, UUID(user_id))
        if user is None or user.role != UserRole.SUPER_ADMIN:
            raise RuntimeError("the given account is not a SUPER_ADMIN — nothing was changed")
        return user
    admins = list(db.scalars(select(User).where(User.role == UserRole.SUPER_ADMIN, User.is_active.is_(True), User.is_banned.is_(False))))
    if len(admins) != 1:
        raise RuntimeError(f"{len(admins)} active SUPER_ADMIN accounts — name one with --user-id")
    return admins[0]


def build_plan(db: Session, user_id: str | None = None) -> dict:
    user = _target(db, user_id)
    row = db.scalar(select(TeacherProfile).where(TeacherProfile.user_id == user.id))
    groups = db.scalar(select(func.count()).select_from(StudyGroup).where(StudyGroup.teacher_id == user.id, StudyGroup.status != GROUP_ARCHIVED)) or 0
    state = {"user": str(user.id), "profile": bool(row), "teaches": bool(row and row.teaches)}
    return {"plan_id": hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()[:12], "user_id": str(user.id),
            "username": _mask(user.username), "profile_row": bool(row), "teaches": state["teaches"], "groups_led": int(groups),
            "action": "nothing to do" if state["teaches"] else ("SET teaches=true" if row else "CREATE profile row + SET teaches=true")}


def apply_plan(db: Session, confirm: str, backup_dir: Path, user_id: str | None = None) -> dict:
    from app.services.teacher import team

    plan = build_plan(db, user_id)
    if confirm != plan["plan_id"]:
        raise RuntimeError(f"plan changed or wrong id: current plan id is {plan['plan_id']} — nothing was changed")
    if plan["teaches"]:
        return {"plan_id": plan["plan_id"], "changed": False}
    user = db.get(User, UUID(plan["user_id"]))
    row = db.scalar(select(TeacherProfile).where(TeacherProfile.user_id == user.id))
    backup_dir.mkdir(parents=True, exist_ok=True)
    snap = backup_dir / f"teacher-profile-before-{plan['plan_id']}.json"
    copy = {c.name: getattr(row, c.key) for c in TeacherProfile.__table__.columns} if row else "none"
    snap.write_text(json.dumps(copy, indent=1, default=str), encoding="utf-8")
    team.set_admin_teaches(db, user, user.id, True, None)
    write_audit(db, actor_id=None, action="team_admin_teaches_script", target_user_id=user.id,
                details=f"plan={plan['plan_id']}; teaches=true via app.scripts.team_admin_teaches (owner request)")
    return {"plan_id": plan["plan_id"], "changed": True, "backup": str(snap)}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="stage")
    p = sub.add_parser("plan")
    p.add_argument("--user-id")
    a = sub.add_parser("apply")
    a.add_argument("--confirm", required=True)
    a.add_argument("--backup-dir", required=True)
    a.add_argument("--user-id")
    args = parser.parse_args()
    try:
        with SessionLocal() as db:
            if (args.stage or "plan") == "plan":
                plan = build_plan(db, getattr(args, "user_id", None))
                print(f"Admin also teaches — plan id {plan['plan_id']}")
                print(f"  account {plan['user_id'][:8]}… ({plan['username']}), SUPER_ADMIN, groups led: {plan['groups_led']}, "
                      f"profile row: {'yes' if plan['profile_row'] else 'no'}, teaches: {plan['teaches']} -> {plan['action']}")
                print("READ-ONLY: nothing was changed.")
            else:
                print(json.dumps(apply_plan(db, args.confirm, Path(args.backup_dir), args.user_id), ensure_ascii=False, indent=1))
    except RuntimeError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
