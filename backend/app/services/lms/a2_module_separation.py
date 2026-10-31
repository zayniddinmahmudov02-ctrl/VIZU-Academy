"""A2 module separation — the data step (docs/a2-module-separation-report.md).

Three changes to the A2 book edition, planned read-only first:

1. writings: the Grammatik written exercises, Wortschatz worksheets and the
   L5 Lesen open questions get their competency (vizu_deutsch_a2_buch.
   WRITING_COMPETENCY); every book writing's rubric is reset to NULL so the
   default of its competency / level applies (A2 Schreiben: 7 criteria,
   levels.py). Submissions stay attached to their task.
2. vocabularies: empty grammar fields and examples filled from VERIFIED
   Wörterbuch entries with the same article + lemma (wortschatz.enrichment).
3. Wortschatz tests: wortschatz_tests.build_sets() per lesson, created as
   published WORTSCHATZ exercise sets with content_id
   "vizu-a2buch-lNN-wortschatz-test-<type>"; an existing id is never touched
   (an admin may have edited it).

apply needs the plan id, writes the affected rows to a JSON backup first and
an audit entry per step; one transaction. Nothing is deleted."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import inspect as sa_inspect
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.lesson_skill import SKILL_WORTSCHATZ, SkillExercise
from app.models.module import Module
from app.models.student_writing import StudentWriting
from app.models.vocabulary import Vocabulary
from app.models.writing import Writing
from app.services.lesson_skills import admin as skill_admin
from app.services.lesson_skills import wortschatz, wortschatz_tests

LEVEL = "A2"
BOOK_PREFIX = "vizu-a2buch-"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _lessons(db: Session) -> list[Lesson]:
    return list(
        db.scalars(
            select(Lesson).join(Module, Module.id == Lesson.module_id).join(Course, Course.id == Module.course_id)
            .where(Course.level == LEVEL).order_by(Lesson.number)
        )
    )


def _target_competencies() -> dict[str, str]:
    from app.scripts.vizu_deutsch_a2_buch import NEW_PREFIX, OLD_PREFIX, WRITING_COMPETENCY

    return {NEW_PREFIX + cid[len(OLD_PREFIX):]: comp for cid, comp in WRITING_COMPETENCY.items()}


def test_content_id(lesson_number: int, key: str) -> str:
    return f"{BOOK_PREFIX}l{lesson_number:02d}-wortschatz-test-{key}"


def _plan_writings(db: Session, lessons: list[Lesson]) -> list[dict]:
    targets = _target_competencies()
    out = []
    rows = db.scalars(
        select(Writing).where(Writing.lesson_id.in_([lsn.id for lsn in lessons]), Writing.content_id.like(f"{BOOK_PREFIX}%")).order_by(Writing.content_id)
    )
    for w in rows:
        target = targets.get(w.content_id)
        if w.competency == target and w.rubric is None:
            continue
        subs = db.scalar(select(StudentWriting.id).where(StudentWriting.writing_id == w.id).limit(1)) is not None
        out.append({"id": str(w.id), "content_id": w.content_id, "title": w.title, "competency": [w.competency, target],
                    "rubric_reset": w.rubric is not None, "has_submissions": subs})
    return out


def _plan_words(db: Session, lessons: list[Lesson]) -> tuple[list[dict], dict]:
    index = wortschatz.entry_index(db)
    out, virtual = [], {}
    words = db.scalars(
        select(Vocabulary).where(Vocabulary.lesson_id.in_([lsn.id for lsn in lessons]), Vocabulary.is_published.is_(True))
        .order_by(Vocabulary.order_index, Vocabulary.created_at)
    )
    for w in words:
        entry = wortschatz.match_entry(index, w)
        fill = wortschatz.enrichment(w, entry)
        view = {c.key: getattr(w, c.key) for c in sa_inspect(Vocabulary).mapper.column_attrs}
        view.update({k: v for k, (v, _src) in fill.items()})
        virtual.setdefault(w.lesson_id, []).append(view)
        if fill or (entry is not None and w.dictionary_entry_id != entry.id):
            out.append({"id": str(w.id), "word": w.german_word, "entry": entry.word_id if entry else None,
                        "entry_id": str(entry.id) if entry else None, "fill": {k: list(v) for k, v in fill.items()}})
    return out, virtual


def _plan_tests(db: Session, lessons: list[Lesson], virtual: dict) -> list[dict]:
    existing = set(db.scalars(select(SkillExercise.content_id).where(SkillExercise.content_id.like(f"{BOOK_PREFIX}%-wortschatz-test-%"))))
    out = []
    for lesson in lessons:
        for s in wortschatz_tests.build_sets(virtual.get(lesson.id, [])):
            cid = test_content_id(lesson.number, s["key"])
            if cid in existing:
                continue
            questions = skill_admin.validate_questions(s["questions"])  # the editor's own validation
            out.append({"lesson_id": str(lesson.id), "lesson_number": lesson.number, "content_id": cid, "title": s["title"],
                        "instruction": s["instruction"], "questions": questions})
    return out


def plan(db: Session) -> dict:
    lessons = _lessons(db)
    if not lessons:
        raise RuntimeError("no A2 lessons")
    writings = _plan_writings(db, lessons)
    words, virtual = _plan_words(db, lessons)
    tests = _plan_tests(db, lessons, virtual)
    digest = hashlib.sha256(json.dumps([writings, words, [[t["content_id"], t["questions"]] for t in tests]], sort_keys=True, default=str).encode())
    return {"plan_id": digest.hexdigest()[:12], "writings": writings, "words": words, "tests": tests}


def summary(result: dict) -> dict:
    moved: dict[str, int] = {}
    for w in result["writings"]:
        if w["competency"][0] != w["competency"][1]:
            moved[w["competency"][1] or "SCHREIBEN"] = moved.get(w["competency"][1] or "SCHREIBEN", 0) + 1
    fields: dict[str, int] = {}
    for w in result["words"]:
        for k in w["fill"]:
            fields[k] = fields.get(k, 0) + 1
    per_lesson: dict[int, int] = {}
    for t in result["tests"]:
        per_lesson[t["lesson_number"]] = per_lesson.get(t["lesson_number"], 0) + len(t["questions"])
    return {
        "plan_id": result["plan_id"],
        "writings_moved": moved,
        "writings_rubric_reset": sum(1 for w in result["writings"] if w["rubric_reset"]),
        "writings_with_submissions": sum(1 for w in result["writings"] if w["has_submissions"]),
        "words_changed": len(result["words"]),
        "words_matched": sum(1 for w in result["words"] if w["entry"]),
        "fields_filled": fields,
        "test_sets": len(result["tests"]),
        "test_questions_per_lesson": per_lesson,
    }


def _row(obj) -> dict:
    return {c.key: getattr(obj, c.key) for c in sa_inspect(type(obj)).mapper.column_attrs}


def apply(db: Session, backup_root: Path, confirm: str, actor_id: str | None = None) -> dict:
    current = plan(db)
    if confirm != current["plan_id"]:
        raise RuntimeError(f"plan changed or wrong id: current plan id is {current['plan_id']} — nothing was changed")
    folder = backup_root / f"a2-module-separation-{_now().strftime('%Y%m%d-%H%M%S')}-{current['plan_id']}"
    folder.mkdir(parents=True, exist_ok=False)
    writings = {str(w.id): w for w in db.scalars(select(Writing).where(Writing.id.in_([w["id"] for w in current["writings"]])))}
    words = {str(v.id): v for v in db.scalars(select(Vocabulary).where(Vocabulary.id.in_([w["id"] for w in current["words"]])))}
    (folder / "backup.json").write_text(
        json.dumps({"plan_id": current["plan_id"], "writings": [_row(w) for w in writings.values()], "vocabularies": [_row(v) for v in words.values()]},
                   default=str, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )

    for item in current["writings"]:
        w = writings[item["id"]]
        w.competency = item["competency"][1]
        w.rubric = None
    for item in current["words"]:
        v = words[item["id"]]
        sources = dict(v.data_sources or {})
        for column, (value, source) in item["fill"].items():
            setattr(v, column, value)
            sources[column] = source
        v.data_sources = sources or None
        if item["entry_id"]:
            v.dictionary_entry_id = item["entry_id"]
    from app.services.content_import.service import _add_exercise

    created = []
    for t in current["tests"]:
        ref = _add_exercise(db, t["lesson_id"], SKILL_WORTSCHATZ,
                            {"title": t["title"], "instruction": t["instruction"], "source": "vizu", "questions": t["questions"]}, t["content_id"])
        db.get(SkillExercise, ref["id"]).is_published = True
        created.append(t["content_id"])

    info = summary(current)
    write_audit(db, actor_id=actor_id, action="a2_writings_competency_set",
                details=f"plan={current['plan_id']}; moved={info['writings_moved']}; rubric_reset={info['writings_rubric_reset']}; backup={folder}")
    write_audit(db, actor_id=actor_id, action="a2_vocabulary_enriched",
                details=f"plan={current['plan_id']}; words={info['words_changed']}; fields={info['fields_filled']}; backup={folder}")
    write_audit(db, actor_id=actor_id, action="a2_wortschatz_tests_created", details=f"plan={current['plan_id']}; sets={len(created)}")
    db.commit()
    report = {**info, "backup": str(folder), "test_sets_created": created}
    (folder / "report.json").write_text(json.dumps(report, default=str, ensure_ascii=False, indent=1), encoding="utf-8")
    return report
