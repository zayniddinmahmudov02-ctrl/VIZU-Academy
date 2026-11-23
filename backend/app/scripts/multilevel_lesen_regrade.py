"""Multilevel Modelltest 1-6: score the Lesen sections that were closed BEFORE the Lesen keys existed (owner's decision 2026-11-23).

    python -m app.scripts.multilevel_lesen_regrade plan
    python -m app.scripts.multilevel_lesen_regrade apply --confirm <plan id> --backup-dir <dir>

Which sections: Lesen of Modelltest 1-6, closed (submitted / expired), still "not scored" (no raw_max, no score) while the test now has Lesen keys.
How: exactly what the exam does when a section closes with keys — multilevel_exam_service._grade_auto (each stored answer against the option flags)
and _recompute (the attempt's total, max and level now include Lesen). Open sections, other sections, answers' choices, Hören / Schreiben / Sprechen
scores and teachers' grades are never touched. A section where nothing was answered gets 0 of 35, the same as a new attempt would.
The plan runs that grading inside a transaction and rolls it back, so it shows the real before -> after of every attempt. apply re-checks the plan id,
locks the attempts, writes a JSON copy of every row it changes to --backup-dir first, commits once, and writes an audit entry. Idempotent."""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.db.session import SessionLocal
from app.models.kompetenz import Kompetenz
from app.models.mock_attempt_section import MockAttemptSection
from app.models.mock_question_answer import MockQuestionAnswer
from app.models.mock_test_attempt import MockTestAttempt
from app.models.model_test import ModelTest
from app.services.mock_exam import multilevel_exam_service as exam
from app.services.mock_exam import multilevel_keys as keys

NUMBERS = range(1, 7)
OPEN = "OPEN"


def _tests(db: Session) -> dict[int, ModelTest]:
    ids = exam._multilevel_level_ids(db)
    rows = db.scalars(select(ModelTest).where(ModelTest.level_id.in_(ids), ModelTest.sort_order.in_(list(NUMBERS)))) if ids else []
    return {t.sort_order: t for t in rows}


def _candidates(db: Session, lock: bool = False) -> list[tuple[int, MockTestAttempt, MockAttemptSection]]:
    out = []
    for number, test in sorted(_tests(db).items()):
        if keys.key_table(db, test.id, "LESEN")["keys_set"] == 0:
            continue  # no Lesen keys in this test: nothing to score with
        lesen = db.scalar(select(Kompetenz.id).where(Kompetenz.model_test_id == test.id, Kompetenz.type == "LESEN"))
        q = (select(MockAttemptSection, MockTestAttempt).join(MockTestAttempt, MockAttemptSection.attempt_id == MockTestAttempt.id)
             .where(MockAttemptSection.kompetenz_id == lesen, MockAttemptSection.status != OPEN, MockAttemptSection.score.is_(None))
             .order_by(MockTestAttempt.started_at, MockTestAttempt.id))
        if lock:
            q = q.with_for_update(of=MockTestAttempt)
        for s, attempt in db.execute(q).all():
            if not s.raw_max:  # "not scored" (raw_max 0 / None): exactly the sections _unscorable() leaves out
                out.append((number, attempt, s))
    return out


def _state(attempt: MockTestAttempt, s: MockAttemptSection) -> dict:
    return {"section_raw": s.raw_points, "section_max": s.raw_max, "section_score": s.score, "section_level": s.level,
            "attempt_status": attempt.status, "total": attempt.total_score, "max": attempt.max_score, "level": attempt.result_level}


def _snapshot(db: Session, rows) -> dict:
    """JSON copy of every row the regrade may change (for a row-level restore)."""
    out = {"taken_at": datetime.now(timezone.utc).isoformat(), "attempts": [], "sections": [], "answers": []}
    for _n, attempt, s in rows:
        out["attempts"].append({"id": str(attempt.id), "status": attempt.status, "total_score": attempt.total_score, "max_score": attempt.max_score,
                                "result_level": attempt.result_level, "result_rule": attempt.result_rule})
        for sec in db.scalars(select(MockAttemptSection).where(MockAttemptSection.attempt_id == attempt.id)):
            out["sections"].append({"id": str(sec.id), "section_type": sec.section_type, "status": sec.status, "raw_points": sec.raw_points,
                                    "raw_max": sec.raw_max, "score": sec.score, "level": sec.level})
        for a in db.scalars(select(MockQuestionAnswer).where(MockQuestionAnswer.attempt_id == attempt.id)):
            out["answers"].append({"id": str(a.id), "is_correct": a.is_correct, "points_earned": a.points_earned})
    return out


def _regrade(db: Session, rows) -> list[dict]:
    settings = exam.get_settings(db)
    items = []
    for number, attempt, s in rows:
        before = _state(attempt, s)
        answered = db.scalar(select(MockQuestionAnswer.id).where(MockQuestionAnswer.attempt_id == attempt.id).limit(1)) is not None
        exam._grade_auto(db, attempt, s, settings)
        exam._recompute(db, attempt, settings)
        db.flush()
        items.append({"number": number, "attempt_id": str(attempt.id), "section_id": str(s.id), "answered_anything": answered,
                      "before": before, "after": _state(attempt, s)})
    return items


def build_plan(db: Session) -> dict:
    rows = _candidates(db)
    try:
        items = _regrade(db, rows)  # the real grading, then thrown away
    finally:
        db.rollback()
    state = [(i["section_id"], i["after"]["section_raw"], i["after"]["total"], i["after"]["level"]) for i in items]
    return {"plan_id": hashlib.sha256(json.dumps(state, sort_keys=True, default=str).encode()).hexdigest()[:12], "items": items}


def apply_plan(db: Session, confirm: str, backup_dir: Path) -> dict:
    plan = build_plan(db)
    if confirm != plan["plan_id"]:
        raise RuntimeError(f"plan changed or wrong id: current plan id is {plan['plan_id']} — nothing was changed")
    if not plan["items"]:
        return {"plan_id": plan["plan_id"], "regraded": 0}
    rows = _candidates(db, lock=True)
    backup_dir.mkdir(parents=True, exist_ok=True)
    snap = backup_dir / f"lesen-regrade-before-{plan['plan_id']}.json"
    snap.write_text(json.dumps(_snapshot(db, rows), indent=1, default=str), encoding="utf-8")
    try:
        items = _regrade(db, rows)
        state = [(i["section_id"], i["after"]["section_raw"], i["after"]["total"], i["after"]["level"]) for i in items]
        if hashlib.sha256(json.dumps(state, sort_keys=True, default=str).encode()).hexdigest()[:12] != plan["plan_id"]:
            raise RuntimeError("the data changed between plan and apply — nothing was changed")
        db.commit()
    except Exception:
        db.rollback()
        raise
    write_audit(db, actor_id=None, action="multilevel_lesen_regrade",
                details=f"plan={plan['plan_id']}; sections={len(items)}; " + ", ".join(f"MT{i['number']}:{i['after']['section_raw']}/{i['after']['section_max']}" for i in items))
    return {"plan_id": plan["plan_id"], "regraded": len(items), "backup": str(snap)}


def _print_plan(plan: dict) -> None:
    print(f"Multilevel Lesen regrade — plan id {plan['plan_id']} — {len(plan['items'])} section(s)")
    for i in plan["items"]:
        b, a = i["before"], i["after"]
        print(f"  MT{i['number']} attempt {i['attempt_id'][:8]} ({b['attempt_status']}{'' if i['answered_anything'] else ', nothing answered'}): "
              f"Lesen not scored -> {a['section_raw']}/{a['section_max']} = {a['section_score']} ({a['section_level']}); "
              f"total {b['total']}/{b['max']} {b['level']} -> {a['total']}/{a['max']} {a['level']} ({a['attempt_status']})")


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
                _print_plan(build_plan(db))
                print("READ-ONLY: nothing was changed.")
            else:
                print(json.dumps(apply_plan(db, args.confirm, Path(args.backup_dir)), ensure_ascii=False, indent=1))
    except RuntimeError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
