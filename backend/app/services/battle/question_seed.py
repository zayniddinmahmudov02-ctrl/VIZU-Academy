"""Seed of the VIZU Battle text questions from app/data/battle/questions/<level>.json (2026-11-19).

The files hold the checked questions (vocabulary from VERIFIED Wörterbuch rows, grammar written per level), each with a stable
`id`. The plan is read-only: per question ADD (new), KEEP (its id is already in the bank — an admin's edit is never overwritten)
or DUPLICATE (the same question exists under another id — skipped, never added twice). A file with an invalid question stops the
plan. `apply --confirm <plan id>` adds the new questions as published (source `seed`), links the Wörterbuch row where one exists and
writes one audit entry. Nothing is changed or deleted."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.models.battle import BattleQuestion
from app.models.dictionary import DictionaryEntry
from app.services.battle import question_bank as bank

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "battle" / "questions"


class SeedError(Exception):
    pass


def load(data_dir: Path = DATA_DIR) -> list[dict]:
    items: list[dict] = []
    for level in bank.LEVELS:
        path = data_dir / f"{level}.json"
        if not path.is_file():
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("level") != level:
            raise SeedError(f"{path.name}: level {doc.get('level')!r} does not match the file name")
        items.extend({**q, "level": level} for q in doc.get("questions") or [])
    return items


def check(items: list[dict]) -> list[dict]:
    """Problems of the shipped files: invalid questions, a repeated id, the same question twice in one level."""
    problems, ids, keys = [], set(), set()
    for q in items:
        p = bank.validate(q)
        if not q.get("id") or len(q["id"]) > 40:
            p.append("ID")
        elif q["id"] in ids:
            p.append("ID_REPEATED")
        key = (q["level"], bank.norm_key(q.get("format") or "", q.get("prompt") or ""))
        if key in keys:
            p.append("DUPLICATE_IN_FILES")
        ids.add(q.get("id"))
        keys.add(key)
        if p:
            problems.append({"id": q.get("id"), "level": q["level"], "problems": p, "prompt": (q.get("prompt") or "")[:80]})
    return problems


def build_plan(db: Session, data_dir: Path = DATA_DIR) -> dict:
    items = load(data_dir)
    problems = check(items)
    have_ids = set(db.execute(select(BattleQuestion.seed_id).where(BattleQuestion.seed_id.is_not(None))).scalars())
    have_keys = set(db.execute(select(BattleQuestion.level, BattleQuestion.norm_key)).all())
    counts = {lv: {"add": 0, "keep": 0, "duplicate": 0, "vocab": 0, "grammar": 0} for lv in bank.LEVELS}
    add = []
    for q in items:
        c = counts[q["level"]]
        if q["id"] in have_ids:
            c["keep"] += 1
        elif (q["level"], bank.norm_key(q["format"], q["prompt"])) in have_keys:
            c["duplicate"] += 1
        else:
            c["add"] += 1
            c[q["kind"]] += 1
            add.append(q["id"])
    digest = hashlib.sha256(json.dumps({"add": sorted(add), "counts": counts}, sort_keys=True).encode()).hexdigest()[:12]
    return {"plan_id": digest, "counts": counts, "problems": problems, "add": add, "total_in_files": len(items)}


def _entries(db: Session) -> dict:
    rows = db.execute(select(DictionaryEntry.id, DictionaryEntry.level, DictionaryEntry.lemma, DictionaryEntry.article)
                      .where(DictionaryEntry.status == "verified", DictionaryEntry.is_primary.is_(True))).all()
    return {(lv, (lemma or "").lower(), art or ""): i for i, lv, lemma, art in rows}


def apply(db: Session, confirm: str, data_dir: Path = DATA_DIR) -> dict:
    plan = build_plan(db, data_dir)
    if plan["problems"]:
        raise SeedError(f"{len(plan['problems'])} invalid question(s) in the files — fix them first")
    if confirm != plan["plan_id"]:
        raise SeedError(f"plan id {confirm!r} does not match the current plan {plan['plan_id']!r} — run the plan again")
    wanted = set(plan["add"])
    entries = _entries(db)
    added = 0
    for q in load(data_dir):
        if q["id"] not in wanted:
            continue
        item = bank._prepare({**q, "status": "published"})
        entry = q.get("entry") or {}
        entry_id = entries.get((q["level"], (entry.get("lemma") or "").lower(), entry.get("article") or "")) if entry else None
        db.add(BattleQuestion(seed_id=q["id"], level=q["level"], kind=item["kind"], format=item["format"], topic=item["topic"],
                              prompt=item["prompt"], hint=item["hint"], answer=item["answer"], wrong=item["wrong"],
                              explanation=item["explanation"], norm_key=bank.norm_key(item["format"], item["prompt"]), ref=item["ref"],
                              status="published", source="seed", entry_id=entry_id))
        added += 1
    db.flush()
    per_level = {lv: c["add"] for lv, c in plan["counts"].items()}
    write_audit(db, actor_id=None, action="battle_questions_seeded", details=f"plan {plan['plan_id']}: {added} added {json.dumps(per_level)}")
    db.commit()
    return {"plan_id": plan["plan_id"], "added": added, "per_level": per_level}
