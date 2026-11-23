"""Multilevel Modelltest 1-6: the Lesen answer keys from the owner's PDF (app/data/multilevel/lesen-keys.json). Default is the read-only plan.

    python -m app.scripts.multilevel_lesen_keys plan
    python -m app.scripts.multilevel_lesen_keys apply --confirm <plan id> [--overwrite]

What apply does (and nothing else): sets the LESEN keys of Modelltest 1-6 through the same service the admin Answer Key page uses
(multilevel_keys.apply_keys: letter -> option per question type, exactly one correct option per question, 35 answers required, the tokens kept as
written). Every variant is checked before anything is written: 35 answers numbered 1-35, Teil 1 (Nr. 1-5) a permutation of a-e, Teil 3 (Nr. 11-17)
seven different letters, every letter valid for its question. Hören keys, questions, options' texts, audio, Schreiben, Sprechen, other Modelltests,
attempts and their results are never touched (a Lesen section already closed without keys stays unscored). A Lesen key that already exists and
differs is a CONFLICT: apply refuses unless --overwrite. Idempotent. Writes an audit entry. Take a DB backup before apply."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.db.session import SessionLocal
from app.models.model_test import ModelTest
from app.services.mock_exam import multilevel_exam_service as exam
from app.services.mock_exam import multilevel_keys as keys

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "multilevel" / "lesen-keys.json"
SECTION = "LESEN"
QUESTIONS = 35
ORDER_PART, HEADINGS_PART = range(1, 6), range(11, 18)


def load_data(path: Path = DATA_FILE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def entries_of(lines: list[str]) -> tuple[dict[int, str], list[str]]:
    """Parse one variant and check its own rules (independent of the database)."""
    entries, parse_errors = keys.parse_text("\n".join(lines))
    errors = [e["message"] for e in parse_errors]
    if sorted(entries) != list(range(1, QUESTIONS + 1)):
        errors.append(f"{len(entries)} answers, expected exactly Nr. 1-{QUESTIONS}")
    order = [entries.get(n, "").lower() for n in ORDER_PART]
    if sorted(order) != list("abcde"):
        errors.append(f"Teil 1 (Nr. 1-5) is not an order of a-e: {''.join(order)}")
    headings = [entries.get(n, "").lower() for n in HEADINGS_PART]
    if len(set(headings)) != len(headings) or not all(re.fullmatch(r"[a-j]", h) for h in headings):
        errors.append(f"Teil 3 (Nr. 11-17) needs seven different letters a-j: {''.join(headings)}")
    return entries, errors


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
        digest = hashlib.sha256("\n".join(lines).encode()).hexdigest()[:10]
        item = {"number": number, "model_test_id": str(test.id) if test else None, "digest": digest}
        if test is None:
            items.append({**item, "action": "missing-test", "expected": None, "given": None, "errors": ["Modelltest not found"]})
            continue
        entries, errors = entries_of(lines)
        rows = keys._questions(db, test.id, SECTION)
        check = keys.validate(rows, entries, require_complete=True)
        errors += [e["message"] for e in check["errors"]]
        if len(rows) != QUESTIONS:
            errors.append(f"the test has {len(rows)} Lesen questions, not {QUESTIONS}")
        states = {"new": 0, "same": 0, "differs": 0}
        for q, index, _token in check["resolved"].values():
            current = keys._correct_index(q)
            states["new" if current is None else "same" if current == index else "differs"] += 1
        same_tokens = all((q.answer_key or "") == tok for q, _i, tok in check["resolved"].values())
        action = ("invalid" if errors else "conflict" if states["differs"] else "skip" if states["new"] == 0 and same_tokens else "set")
        items.append({**item, "action": action, "expected": check["expected"], "given": len(entries), "states": states, "errors": errors})
    state = [{k: i.get(k) for k in ("number", "action", "digest", "model_test_id")} for i in items]
    return {"plan_id": hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()[:12], "items": items}


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
        raise RuntimeError("STOP — existing Lesen keys differ in " + ", ".join(f"MT{i['number']}" for i in conflicts)
                           + " (use --overwrite after checking) — nothing was changed")
    done = []
    for item in plan["items"]:
        if item["action"] == "skip":
            done.append({"number": item["number"], "action": "skip"})
            continue
        entries, _ = entries_of(data["tests"][str(item["number"])])
        keys.apply_keys(db, None, UUID(item["model_test_id"]), SECTION, entries, require_complete=True, source="script")
        done.append({"number": item["number"], "action": item["action"], "answers": len(entries)})
    write_audit(db, actor_id=None, action="multilevel_lesen_keys",
                details=f"plan={plan['plan_id']}; Lesen keys " + ", ".join(f"MT{d['number']}={d['action']}" for d in done))
    return {"plan_id": plan["plan_id"], "keys": done}


def _print_plan(plan: dict) -> None:
    print(f"Multilevel Lesen keys — plan id {plan['plan_id']}")
    for i in plan["items"]:
        extra = f" new={i['states']['new']} same={i['states']['same']} differs={i['states']['differs']}" if i.get("states") else ""
        print(f"  {i['action'].upper():12} MT{i['number']}: {i['given']} answers for {i['expected']} questions{extra}"
              f"{' — ' + '; '.join(i['errors'][:3]) if i['errors'] else ''}")


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
