"""Put every finished Multilevel Modelltest attempt on the owner's scoring tables (2026-11-28) — multilevel_exam_service.rescore_attempt.

    python -m app.scripts.multilevel_rescore plan
    python -m app.scripts.multilevel_rescore apply --confirm <plan id> --backup-dir <dir>

What changes: Lesen / Hören scores come from the Lesen table (35 scale, Hören 30 → × 35 / 30) instead of correct / questions × 75; levels
use the bands (B1 38–50, B2 51–64, C1 65–75); a Schreiben / Sprechen score a teacher / admin gave becomes a manual (override) score and stays;
a Schreiben / Sprechen section that was never graded is queued for the AI (ai_status PENDING — the worker grades it). Raw points, answers,
texts, recordings and attempts are never deleted. `plan` is read-only (it computes inside a transaction it rolls back) and prints counts only
(no student data). `apply` checks the plan id again, writes a JSON copy of every attempt / section row it touches to --backup-dir, applies,
writes one audit log entry. Idempotent: a second plan says "0 to change"."""

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.core.audit import write_audit
from app.db.session import SessionLocal
from app.models.mock_attempt_section import MockAttemptSection
from app.models.mock_test_attempt import STATUS_IN_PROGRESS, MockTestAttempt
from app.models.model_test import ModelTest
from app.services.mock_exam import multilevel_exam_service as exam


def _attempts(db: Session) -> list[MockTestAttempt]:
    ids = exam._multilevel_level_ids(db)
    if not ids:
        return []
    return list(db.scalars(select(MockTestAttempt).join(ModelTest, MockTestAttempt.model_test_id == ModelTest.id)
                           .where(ModelTest.level_id.in_(ids), MockTestAttempt.status != STATUS_IN_PROGRESS)
                           .order_by(MockTestAttempt.started_at).with_for_update(of=MockTestAttempt)))


def _state(db: Session, a: MockTestAttempt) -> dict:
    secs = {s.section_type: s for s in db.scalars(select(MockAttemptSection).where(MockAttemptSection.attempt_id == a.id))}
    return {"total": a.total_score, "level": a.result_level, "status": a.status,
            "sections": {t: [s.score, s.level, s.score_source, s.ai_status, s.override_score] for t, s in sorted(secs.items())}}


def _simulate(db: Session) -> tuple[list[dict], dict]:
    settings = exam.get_settings(db)
    rows = []
    for a in _attempts(db):
        before = _state(db, a)
        exam.rescore_attempt(db, a, settings)
        db.flush()
        after = _state(db, a)
        if before != after:
            rows.append({"attempt_id": str(a.id), "before": before, "after": after})
    return rows, settings


def build_plan(db: Session) -> dict:
    try:
        rows, settings = _simulate(db)
    finally:
        db.rollback()
    counts: Counter = Counter()
    for r in rows:
        for t, (score, level, source, ai, _o) in r["after"]["sections"].items():
            b = r["before"]["sections"].get(t, [None] * 5)
            if score != b[0]:
                counts[f"{t} score changed"] += 1
            if level != b[1]:
                counts[f"{t} level changed"] += 1
            if source == "MANUAL" and b[2] is None:
                counts[f"{t} kept as manual score"] += 1
            if ai == "PENDING" and b[3] is None:
                counts[f"{t} queued for the AI"] += 1
        if r["after"]["total"] != r["before"]["total"]:
            counts["attempt total changed"] += 1
        if r["after"]["level"] != r["before"]["level"]:
            counts["attempt result level changed"] += 1
    fingerprint = json.dumps({"rows": rows, "tables": [settings["bands"], settings["lesen_table"], settings["schreiben_table"]]}, sort_keys=True, default=str)
    return {"plan_id": hashlib.sha256(fingerprint.encode()).hexdigest()[:12], "attempts": len(rows), "counts": dict(sorted(counts.items())),
            "attempt_ids": [r["attempt_id"] for r in rows]}


def apply_plan(db: Session, confirm: str, backup_dir: Path) -> dict:
    plan = build_plan(db)
    if confirm != plan["plan_id"]:
        raise RuntimeError(f"plan changed or wrong id: current plan id is {plan['plan_id']} — nothing was changed")
    if not plan["attempts"]:
        return {"plan_id": plan["plan_id"], "changed": 0}
    backup_dir.mkdir(parents=True, exist_ok=True)
    snap = backup_dir / f"multilevel-rescore-before-{plan['plan_id']}.json"
    ids = plan["attempt_ids"]
    copy = {"attempts": [{c.name: getattr(a, c.key) for c in MockTestAttempt.__table__.columns}
                         for a in db.scalars(select(MockTestAttempt).where(MockTestAttempt.id.in_(ids)))],
            "sections": [{c.name: getattr(s, c.key) for c in MockAttemptSection.__table__.columns}
                         for s in db.scalars(select(MockAttemptSection).where(MockAttemptSection.attempt_id.in_(ids)))]}
    snap.write_text(json.dumps(copy, indent=1, default=str), encoding="utf-8")
    rows, _ = _simulate(db)
    db.commit()
    write_audit(db, actor_id=None, action="multilevel_rescore_script",
                details=f"plan={plan['plan_id']}; attempts={len(rows)}; " + "; ".join(f"{k}={v}" for k, v in plan["counts"].items()))
    return {"plan_id": plan["plan_id"], "changed": len(rows), "backup": str(snap)}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="stage")
    sub.add_parser("plan")
    a = sub.add_parser("apply")
    a.add_argument("--confirm", required=True)
    a.add_argument("--backup-dir", required=True)
    args = parser.parse_args()
    try:
        with SessionLocal() as db:
            if (args.stage or "plan") == "plan":
                plan = build_plan(db)
                print(f"Multilevel rescore — plan id {plan['plan_id']}: {plan['attempts']} attempt(s) to change")
                for k, v in plan["counts"].items():
                    print(f"  {k}: {v}")
                print("READ-ONLY: nothing was changed.")
            else:
                print(json.dumps(apply_plan(db, args.confirm, Path(args.backup_dir)), ensure_ascii=False, indent=1))
    except RuntimeError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
