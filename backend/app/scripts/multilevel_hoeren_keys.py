"""Multilevel Modelltest 1–6: the owner's Hören answer keys (app/data/multilevel/hoeren-keys.json) and the exam times of all Modelltests
(Lesen 60, Hören 60, Schreiben 60, Sprechen 15 minutes = 195). Default is the read-only plan.

    python -m app.scripts.multilevel_hoeren_keys plan
    python -m app.scripts.multilevel_hoeren_keys apply --confirm <plan id> [--overwrite]

What apply does (and nothing else): sets the Hören keys of Modelltest 1–6 through the same service the admin page uses (letters checked per question type,
count checked against the test: 35 for Modelltest 1, 30 for 2–6; the tokens keep their case), and sets Kompetenz.duration_minutes of every non-empty
section of every Multilevel Modelltest. Lesen keys, Hören audio, Schreiben and Sprechen tasks, attempts and answers are never touched. A Hören key
that already exists and differs is a CONFLICT: apply refuses unless --overwrite. Idempotent. Writes an audit entry. Take a DB backup before apply."""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.db.session import SessionLocal
from app.models.kompetenz import Kompetenz
from app.models.model_test import ModelTest
from app.models.teil import Teil
from app.services.mock_exam import multilevel_exam_service as exam
from app.services.mock_exam import multilevel_keys as keys

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "multilevel" / "hoeren-keys.json"
SECTION = "HOEREN"


def load_data(path: Path = DATA_FILE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _tests(db: Session) -> dict[int, ModelTest]:
    ids = exam._multilevel_level_ids(db)
    rows = db.scalars(select(ModelTest).where(ModelTest.level_id.in_(ids)).order_by(ModelTest.sort_order)) if ids else []
    return {t.sort_order: t for t in rows}


def build_plan(db: Session, data: dict | None = None) -> dict:
    data = data or load_data()
    tests = _tests(db)
    items = []
    for number_text, lines in sorted(data["tests"].items(), key=lambda kv: int(kv[0])):
        number = int(number_text)
        test = tests.get(number)
        item = {"number": number, "model_test_id": str(test.id) if test else None}
        if test is None:
            items.append({**item, "action": "missing-test", "expected": None, "given": None, "errors": ["Modelltest not found"]})
            continue
        rows = keys._questions(db, test.id, SECTION)
        entries, parse_errors = keys.parse_text("\n".join(lines))
        check = keys.validate(rows, entries, require_complete=True)
        errors = [e["message"] for e in parse_errors + check["errors"]]
        states = {"new": 0, "same": 0, "differs": 0}
        for n, (q, index, _token) in check["resolved"].items():
            current = keys._correct_index(q)
            states["new" if current is None else "same" if current == index else "differs"] += 1
        action = "invalid" if errors else "conflict" if states["differs"] else "skip" if states["new"] == 0 and all(
            (q.answer_key or "") == tok for q, _i, tok in check["resolved"].values()) else "set"
        items.append({**item, "action": action, "expected": check["expected"], "given": len(entries), "states": states, "errors": errors,
                      "digest": hashlib.sha256("\n".join(lines).encode()).hexdigest()[:10]})
    minutes = []
    for number, test in sorted(tests.items()):
        for k in db.scalars(select(Kompetenz).where(Kompetenz.model_test_id == test.id).order_by(Kompetenz.sort_order)):
            has_teile = bool(db.scalar(select(Teil.id).where(Teil.kompetenz_id == k.id).limit(1)))
            target = exam.DEFAULT_MINUTES.get(k.type)
            if has_teile and target and k.duration_minutes != target:
                minutes.append({"number": number, "kompetenz_id": str(k.id), "type": k.type, "from": k.duration_minutes, "to": target})
    state = {"items": [{k: i.get(k) for k in ("number", "action", "digest", "model_test_id")} for i in items], "minutes": minutes}
    return {"plan_id": hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()[:12], "items": items, "minutes": minutes}


def apply_plan(db: Session, confirm: str, overwrite: bool = False, data: dict | None = None) -> dict:
    data = data or load_data()
    plan = build_plan(db, data)
    if confirm != plan["plan_id"]:
        raise RuntimeError(f"plan changed or wrong id: current plan id is {plan['plan_id']} — nothing was changed")
    bad = [i for i in plan["items"] if i["action"] in ("invalid", "missing-test")]
    if bad:
        raise RuntimeError("STOP — " + "; ".join(f"MT{i['number']}: {i['action']} {i['errors'][:2]}" for i in bad) + " — nothing was changed")
    conflicts = [i for i in plan["items"] if i["action"] == "conflict"]
    if conflicts and not overwrite:
        raise RuntimeError("STOP — existing Hören keys differ in " + ", ".join(f"MT{i['number']}" for i in conflicts) + " (use --overwrite after checking) — nothing was changed")
    done = []
    for item in plan["items"]:
        if item["action"] == "skip":
            done.append({"number": item["number"], "action": "skip"})
            continue
        entries, _ = keys.parse_text("\n".join(data["tests"][str(item["number"])]))
        keys.apply_keys(db, None, UUID(item["model_test_id"]), SECTION, entries, require_complete=True, source="script")
        done.append({"number": item["number"], "action": item["action"], "answers": len(entries)})
    for m in plan["minutes"]:
        db.get(Kompetenz, UUID(m["kompetenz_id"])).duration_minutes = m["to"]
    db.commit()
    write_audit(db, actor_id=None, action="multilevel_exam_minutes",
                details=f"plan={plan['plan_id']}; Hören keys " + ", ".join(f"MT{d['number']}={d['action']}" for d in done) + f"; minutes changed: {len(plan['minutes'])}")
    return {"plan_id": plan["plan_id"], "keys": done, "minutes_changed": len(plan["minutes"])}


def _print_plan(plan: dict) -> None:
    print(f"Multilevel Hören keys + exam times — plan id {plan['plan_id']}")
    for i in plan["items"]:
        extra = f" new={i['states']['new']} same={i['states']['same']} differs={i['states']['differs']}" if i.get("states") else ""
        print(f"  {i['action'].upper():12} MT{i['number']}: {i['given']} answers for {i['expected']} questions{extra}{' — ' + '; '.join(i['errors'][:3]) if i['errors'] else ''}")
    by_test: dict[int, list[str]] = {}
    for m in plan["minutes"]:
        by_test.setdefault(m["number"], []).append(f"{m['type']} {m['from']}→{m['to']}")
    print("  exam minutes to change:" + ("" if by_test else " none"))
    for number, changes in by_test.items():
        print(f"    MT{number}: " + ", ".join(changes))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="stage")
    sub.add_parser("plan")
    a = sub.add_parser("apply")
    a.add_argument("--confirm", required=True)
    a.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        with SessionLocal() as db:
            if (args.stage or "plan") == "plan":
                _print_plan(build_plan(db))
                print("READ-ONLY: nothing was changed.")
            else:
                print(json.dumps(apply_plan(db, args.confirm, args.overwrite), ensure_ascii=False, indent=1))
    except RuntimeError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
