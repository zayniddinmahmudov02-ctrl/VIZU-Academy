"""Link the Multilevel study groups to the Vorbereitung level "Multilevel B1–C1" and drop their C1 course link (owner, 2026-11-28: "Teacher
Panel Multilevel 1/2: C1 kursi o'rniga Multilevel Modelltestlar").

    python -m app.scripts.multilevel_groups_link plan [--name-prefix Multilevel]
    python -m app.scripts.multilevel_groups_link apply --confirm <plan id> --backup-dir <dir> [--name-prefix Multilevel]

Targets = groups whose name starts with --name-prefix (case-insensitive, default "Multilevel"), not blocked. For each: set
`study_groups.mock_exam_level_id` (members then open every Modelltest of the level without the Premium) and delete its `study_group_courses`
rows of level C1 (the "C1 Advanced" link; course links never granted lesson access — purchases do). Nothing else changes: members, chat,
tasks, video lessons, attempts and payments stay. `plan` is read-only and prints group names + counts only (no student data). `apply` checks the
plan id again, writes a JSON copy of the groups and the course-link rows it removes to --backup-dir, writes a group audit entry per group and
one audit log entry. Idempotent: a second plan says "nothing to do"."""

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
from app.db.session import SessionLocal
from app.models.course import Course
from app.models.mock_exam_level import MockExamLevel
from app.models.study_group import GROUP_BLOCKED, MEMBER_ACTIVE, MEMBER_STUDENT, StudyGroup, StudyGroupCourse, StudyGroupMember
from app.services.mock_exam.multilevel_service import LEVEL_TITLE
from app.services.study_groups.access import audit as group_audit

REMOVE_COURSE_LEVELS = ("C1",)


def _level(db: Session) -> MockExamLevel:
    levels = list(db.scalars(select(MockExamLevel).where(MockExamLevel.title == LEVEL_TITLE)))
    if len(levels) != 1:
        raise RuntimeError(f"{len(levels)} Vorbereitung levels titled {LEVEL_TITLE!r} — expected exactly one")
    return levels[0]


def _groups(db: Session, prefix: str) -> list[StudyGroup]:
    if len(prefix.strip()) < 4:
        raise RuntimeError("--name-prefix too short")
    return list(db.scalars(select(StudyGroup).where(func.lower(func.trim(StudyGroup.name)).like(prefix.strip().lower() + "%"),
                                                    StudyGroup.status != GROUP_BLOCKED).order_by(StudyGroup.name)))


def _links(db: Session, group: StudyGroup) -> list[tuple[StudyGroupCourse, Course]]:
    return list(db.execute(select(StudyGroupCourse, Course).join(Course, Course.id == StudyGroupCourse.course_id)
                           .where(StudyGroupCourse.group_id == group.id).order_by(Course.order_index)).all())


def build_plan(db: Session, prefix: str = "Multilevel") -> dict:
    level = _level(db)
    items, state = [], []
    for g in _groups(db, prefix):
        links = _links(db, g)
        drop = [(link, c) for link, c in links if (c.level or "").upper() in REMOVE_COURSE_LEVELS]
        students = db.scalar(select(func.count()).select_from(StudyGroupMember).where(
            StudyGroupMember.group_id == g.id, StudyGroupMember.role == MEMBER_STUDENT, StudyGroupMember.status == MEMBER_ACTIVE)) or 0
        set_link = g.mock_exam_level_id != level.id
        items.append({"group_id": str(g.id), "name": g.name.strip(), "status": g.status, "level": g.level, "students": int(students),
                      "linked_now": str(g.mock_exam_level_id) if g.mock_exam_level_id else None, "set_link": set_link,
                      "courses": [c.title for _, c in links], "remove_courses": [c.title for _, c in drop],
                      "remove_link_ids": [str(link.id) for link, _ in drop]})
        state.append([str(g.id), str(g.mock_exam_level_id), sorted(str(link.id) for link, _ in drop)])
    if not items:
        raise RuntimeError(f"no group name starts with {prefix!r}")
    plan_id = hashlib.sha256(json.dumps({"level": str(level.id), "groups": state}, sort_keys=True).encode()).hexdigest()[:12]
    todo = sum(1 for i in items if i["set_link"] or i["remove_link_ids"])
    return {"plan_id": plan_id, "level_id": str(level.id), "level": level.title, "groups": items, "changes": todo}


def apply_plan(db: Session, confirm: str, backup_dir: Path, prefix: str = "Multilevel") -> dict:
    plan = build_plan(db, prefix)
    if confirm != plan["plan_id"]:
        raise RuntimeError(f"plan changed or wrong id: current plan id is {plan['plan_id']} — nothing was changed")
    if not plan["changes"]:
        return {"plan_id": plan["plan_id"], "changed": 0}
    backup_dir.mkdir(parents=True, exist_ok=True)
    snap = backup_dir / f"multilevel-groups-before-{plan['plan_id']}.json"
    copy = {"groups": [{c.name: getattr(db.get(StudyGroup, UUID(i["group_id"])), c.key) for c in StudyGroup.__table__.columns} for i in plan["groups"]],
            "removed_course_links": [{c.name: getattr(db.get(StudyGroupCourse, UUID(lid)), c.key) for c in StudyGroupCourse.__table__.columns}
                                     for i in plan["groups"] for lid in i["remove_link_ids"]]}
    snap.write_text(json.dumps(copy, indent=1, default=str), encoding="utf-8")
    changed = 0
    for i in plan["groups"]:
        g = db.get(StudyGroup, UUID(i["group_id"]))
        if not (i["set_link"] or i["remove_link_ids"]):
            continue
        g.mock_exam_level_id = UUID(plan["level_id"])
        for lid in i["remove_link_ids"]:
            db.delete(db.get(StudyGroupCourse, UUID(lid)))
        group_audit(db, g.id, None, "group.multilevel_link", "group", g.id,
                    {"plan": plan["plan_id"], "mock_exam_level_id": plan["level_id"], "removed_courses": i["remove_courses"]})
        changed += 1
    db.commit()
    write_audit(db, actor_id=None, action="multilevel_groups_link_script",
                details=f"plan={plan['plan_id']}; groups={changed}; level={plan['level']}; removed C1 course links="
                        f"{sum(len(i['remove_link_ids']) for i in plan['groups'])} (owner request 2026-11-28)")
    return {"plan_id": plan["plan_id"], "changed": changed, "backup": str(snap)}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="stage")
    p = sub.add_parser("plan")
    p.add_argument("--name-prefix", default="Multilevel")
    a = sub.add_parser("apply")
    a.add_argument("--confirm", required=True)
    a.add_argument("--backup-dir", required=True)
    a.add_argument("--name-prefix", default="Multilevel")
    args = parser.parse_args()
    prefix = getattr(args, "name_prefix", "Multilevel")
    try:
        with SessionLocal() as db:
            if (args.stage or "plan") == "plan":
                plan = build_plan(db, prefix)
                print(f"Multilevel groups -> {plan['level']} — plan id {plan['plan_id']} ({plan['changes']} group(s) to change)")
                for i in plan["groups"]:
                    print(f"  {i['name']!r} [{i['status']}, {i['level']}, {i['students']} students] courses {i['courses']} -> "
                          f"{'LINK' if i['set_link'] else 'linked'}; remove {i['remove_courses'] or 'nothing'}")
                print("READ-ONLY: nothing was changed.")
            else:
                print(json.dumps(apply_plan(db, args.confirm, Path(args.backup_dir), prefix), ensure_ascii=False, indent=1))
    except RuntimeError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
