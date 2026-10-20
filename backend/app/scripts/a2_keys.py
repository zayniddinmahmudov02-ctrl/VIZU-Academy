"""A2 answer keys checked against their sources (audit 2026-10-21).

Hören — every A2 Hören task was compared with its audio: machine transcripts
of the exact files stored on the server (same SHA-256), two independent
speech models (Whisper large-v3 + medium, CPU, language de), with timestamps,
plus the task picture where the options are pictures. Keys / evidence live in
a2_keys_data.py. An answer is VERIFIED only when the audio states it
unambiguously; anything else is NEEDS_REVIEW with the reason (LMS -> Lösung).
Nothing is guessed. The same functions as the A1 audit are used
(a1_hoeren_keys.plan_task / apply_question: editor validation, fingerprints).

Lesen — the keys were already in the database (imported with the quoted text
passage as explanation). Each Lesen question was re-read against its text;
the script records that check (answer_key_reviews, VERIFIED + note) without
changing any key. Questions listed under `review` get NEEDS_REVIEW instead.

The script never creates or deletes tasks / questions, never touches attempts
or scores and never unpublishes. A Hören task is published when every key is
verified and its audio file exists (the A1 / A2 publish rule).

    python -m app.scripts.a2_keys                # dry run: prints the plan
    python -m app.scripts.a2_keys --apply [--no-publish]
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import func, select

from app.core.audit import write_audit
from app.db.session import SessionLocal
from app.models.answer_key_review import REVIEW_NEEDS_REVIEW, REVIEW_VERIFIED, AnswerKeyReview
from app.models.lesson_skill import LessonSkillAttempt
from app.models.listening import Listening
from app.models.reading import Reading
from app.scripts.a1_hoeren_keys import apply_question, plan_task
from app.scripts.a2_keys_data import HOEREN, LESEN
from app.services.lesson_skills import hoeren_pdf_import, loesung
from app.services.lms import structure

LEVEL = "A2"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _lessons(db) -> dict:
    course = structure.level_course(db, LEVEL)
    module = structure.main_module(db, course) if course else None
    return {lesson.id: lesson.number for lesson in structure.level_lessons(db, module)}


def _tasks(db, model, lesson_numbers: dict) -> dict:
    return {t.content_id: (lesson_numbers[t.lesson_id], t)
            for t in db.scalars(select(model).where(model.lesson_id.in_(list(lesson_numbers)))) if t.content_id}


def plan_removals(db, lst, wanted: list[str]) -> list:
    """Questions that are neither on the book page nor in the audio (an
    import slip), named by their exact text. Refused when the task already has
    student attempts — then nothing is removed and an admin decides."""
    if not wanted:
        return []
    questions = loesung._sorted_questions(lst)
    out = []
    for text in wanted:
        hits = [q for q in questions if q.question == text]
        if len(hits) > 1:
            raise ValueError(f"Frage „{text}“ mehrfach vorhanden")
        out += hits  # already removed on a re-run: nothing to do
    if out and db.scalar(select(func.count()).select_from(LessonSkillAttempt).where(LessonSkillAttempt.listening_id == lst.id)):
        raise ValueError("die Aufgabe hat schon Schülerversuche — Fragen werden nicht entfernt")
    return out


def run_hoeren(db, apply: bool, publish: bool, lessons: dict) -> tuple[int, list]:
    failed, report = 0, []
    tasks = _tasks(db, Listening, lessons)
    for cid, spec in HOEREN.items():
        if cid not in tasks:
            print(f"\n{cid}: Aufgabe fehlt — übersprungen")
            failed += 1
            continue
        n, lst = tasks[cid]
        print(f"\nHören L{n} {lst.title}  [{cid}]  veröffentlicht={lst.is_published}")
        if spec.get("verify_only"):
            # the stored key is right (e.g. a Zuordnung): record the check only
            changed = record_reviews(db, "hoeren", loesung._sorted_questions(lst), spec, apply)
            if changed is None:
                failed += 1
                continue
            if apply:
                db.refresh(lst)
                state = hoeren_pdf_import.readiness(db, lst)
                if publish and state["ready"] and not lst.is_published:
                    lst.is_published = True
                    db.commit()
                print(f"  -> {'veröffentlicht' if lst.is_published else 'Entwurf'}" + ("" if state["ready"] else f" ({', '.join(state['reasons'])})"))
                write_audit(db, None, "a2_hoeren_keys_verified", details=json.dumps(
                    {"task": str(lst.id), "content_id": cid, "verify_only": True, "questions": changed, "published": lst.is_published}, ensure_ascii=False))
                report.append({"content_id": cid, "published": lst.is_published, **state})
            continue
        try:
            removals = plan_removals(db, lst, spec.get("remove_questions", []))
            kept = [q for q in loesung._sorted_questions(lst) if q not in removals]
            plan = plan_task(SimpleNamespace(questions=kept), spec)
        except (ValueError, HTTPException) as exc:
            print(f"  FEHLER: {getattr(exc, 'detail', exc)} — nichts geändert")
            failed += 1
            continue
        for q in removals:
            print(f"  − Frage entfernen (nicht im Buch / nicht im Audio): {q.question}")
        for c in plan["questions"]:
            print(f"  {'Ä' if c['changed'] else '='} Frage {c['number']}: {c['status']}" + (f"  ({c['note']})" if c["status"] != REVIEW_VERIFIED else ""))
            if c["changed"]:
                print(f"      vorher: {c['before'][:300]}\n      nachher: {c['after'][:300]}")
        if spec.get("instruction") and spec["instruction"] != lst.instruction:
            print(f"  Ä Anweisung: {spec['instruction'][:200]}")
        if not apply:
            continue
        before = {"instruction": lst.instruction, "published": lst.is_published, "removed": [q.question for q in removals]}
        for q in removals:
            db.delete(q)  # options + review rows go with it (ON DELETE CASCADE)
        db.flush()
        for c in plan["questions"]:
            apply_question(db, c["question"], c)
        if spec.get("instruction"):
            lst.instruction = spec["instruction"]
        db.commit()
        db.refresh(lst)
        state = hoeren_pdf_import.readiness(db, lst)
        if publish and state["ready"] and not lst.is_published:
            lst.is_published = True
            db.commit()
        print(f"  -> {'veröffentlicht' if lst.is_published else 'Entwurf'}" + ("" if state["ready"] else f" ({', '.join(state['reasons'])})"))
        write_audit(db, None, "a2_hoeren_keys_verified", details=json.dumps({
            "task": str(lst.id), "content_id": cid, "before": before, "published": lst.is_published,
            "questions": [{"n": c["number"], "status": c["status"], "changed": c["changed"], "before": c["before"][:600], "after": c["after"][:600]}
                          for c in plan["questions"]]}, ensure_ascii=False)[:8000])
        report.append({"content_id": cid, "published": lst.is_published, **state})
    return failed, report


def record_reviews(db, kind: str, questions: list, spec: dict, apply: bool) -> list | None:
    """Record the check of keys that stay unchanged (Lesen; a correct Hören
    Zuordnung): VERIFIED + fingerprint, or NEEDS_REVIEW for questions listed
    under `review` / without a valid key. Returns the changed question
    numbers, or None when the stored structure is not the one checked."""
    if spec.get("questions") is not None and spec["questions"] != len(questions):
        print(f"  {len(questions)} Fragen gespeichert, geprüft wurden {spec['questions']} — nichts geändert")
        return None
    reviews = loesung._reviews(db, kind, [q.id for q in questions])
    plan = []
    for i, q in enumerate(questions, start=1):
        valid, problem = loesung.key_valid(q)
        note = spec.get("review", {}).get(i)
        status = REVIEW_NEEDS_REVIEW if (note or not valid) else REVIEW_VERIFIED
        r = reviews.get(q.id)
        same = bool(r and r.status == status and (status != REVIEW_VERIFIED or r.key_fingerprint == loesung.fingerprint(q)))
        plan.append((i, q, status, note or (f"Lösung ungültig: {problem}" if not valid else spec["evidence"]), same))
    changed = [p for p in plan if not p[4]]
    print(f"  {len(questions)} Fragen, {len(changed)} neu zu vermerken"
          + "".join(f"\n  Frage {i}: {st} ({note})" for i, _, st, note, _ in plan if st != REVIEW_VERIFIED))
    if apply and changed:
        column = "reading_question_id" if kind == "lesen" else "listening_question_id"
        for i, q, status, note, same in changed:
            r = reviews.get(q.id)
            if r is None:
                r = AnswerKeyReview(**{column: q.id}, status=status)
                db.add(r)
            r.status = status
            r.key_fingerprint = loesung.fingerprint(q) if status == REVIEW_VERIFIED else None
            r.note = note[:2000]
            r.reviewed_by = None  # system audit (source in the note)
            r.reviewed_at = _now()
        db.commit()
    return [{"n": i, "status": st} for i, _, st, _, _ in changed]


def run_lesen(db, apply: bool, lessons: dict) -> tuple[int, list]:
    failed, report = 0, []
    tasks = _tasks(db, Reading, lessons)
    for cid, spec in LESEN.items():
        if cid not in tasks:
            print(f"\n{cid}: Text fehlt — übersprungen")
            failed += 1
            continue
        n, reading = tasks[cid]
        print(f"\nLesen L{n} {reading.title[:60]}  [{cid}]")
        changed = record_reviews(db, "lesen", loesung._sorted_questions(reading), spec, apply)
        if changed is None:
            failed += 1
            continue
        if apply and changed:
            write_audit(db, None, "a2_lesen_keys_verified", details=json.dumps(
                {"reading": str(reading.id), "content_id": cid, "questions": changed}, ensure_ascii=False)[:8000])
            report.append({"content_id": cid, "changed": len(changed)})
    return failed, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="write (default: dry run)")
    parser.add_argument("--no-publish", action="store_true", help="do not publish ready Hören tasks")
    parser.add_argument("--only", choices=("hoeren", "lesen"), help="one section only")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        lessons = _lessons(db)
        if len(lessons) != 14:
            print(f"A2 hat {len(lessons)} Lektionen (erwartet 14) — abgebrochen")
            return 1
        f1, r1 = run_hoeren(db, args.apply, not args.no_publish, lessons) if args.only in (None, "hoeren") else (0, [])
        f2, r2 = run_lesen(db, args.apply, lessons) if args.only in (None, "lesen") else (0, [])
    finally:
        db.close()
    if args.apply:
        print("\nErgebnis Hören:", json.dumps(r1, ensure_ascii=False, default=str))
        print("Ergebnis Lesen:", json.dumps(r2, ensure_ascii=False, default=str))
    return 1 if (f1 or f2) else 0


if __name__ == "__main__":
    raise SystemExit(main())
