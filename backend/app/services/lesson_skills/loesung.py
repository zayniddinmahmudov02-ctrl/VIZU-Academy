"""Lösung — answer-key management for the Lesen and Hören tasks of A1–C1
(Admin -> LMS A1–C1 -> Lösung).

One source of truth, reused everywhere:
  * the answer key stays where the scoring engine reads it
    (*_options.is_correct for Multiple Choice / Richtig-Falsch,
    *_questions.config for Zuordnung / Lückentext / Kurzantwort) and is
    validated with the same `validate_questions` as the lesson editor;
  * "has a key" = exercises.has_key (the rule the Hören publish check uses);
  * publishing goes through the existing services (ReadingService.publish,
    ListeningService.update with its audio + key checks).
New is only the manual verification (answer_key_reviews): a key counts as
verified while the question + key still hash to the fingerprint stored at
verification time — editing the key afterwards needs a new verification.
Saving never publishes; questions are never created or deleted here (options
of a Multiple-Choice question can be added / removed)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.audit import write_audit
from app.models.answer_key_review import REVIEW_NEEDS_REVIEW, REVIEW_UNVERIFIED, REVIEW_VERIFIED, AnswerKeyReview
from app.models.lesson_skill import CONFIG_TYPES, ListeningQuestion
from app.models.listening import Listening
from app.models.reading import Reading
from app.models.reading_question import ReadingQuestion
from app.models.user import User
from app.services.lesson_skills.admin import admin_question, listening_audio_path, validate_questions
from app.services.lesson_skills.exercises import has_key
from app.services.lms import structure

KINDS = ("lesen", "hoeren")
DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# Aufgabe states (filters)
ST_COMPLETE = "complete"          # every question has a key and it is verified
ST_MISSING = "missing"            # at least one question without a (valid) key
ST_NEEDS_REVIEW = "needs_review"  # keys present, not all verified or flagged
ST_MISSING_AUDIO = "missing_audio"
ST_READY = "ready"                # draft that passes every publish requirement
ST_PUBLISHED = "published"
ST_DRAFT = "draft"


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# Key fingerprint / verification
# ============================================================


def fingerprint(q) -> str:
    """Hash of what a reviewer checks: question text, type, options with the
    correct flag (in order) and the config (key) — not ids or timestamps."""
    data = {
        "q": q.question,
        "t": q.question_type,
        "o": [[o.option_text, bool(o.is_correct)] for o in sorted(q.options, key=lambda o: (o.order_index, o.created_at))],
        "c": {k: v for k, v in (q.config or {}).items() if k != "pending"} if q.question_type in CONFIG_TYPES else None,
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def key_valid(q) -> tuple[bool, str | None]:
    """The key exists AND passes the editor validation (same rules as saving)."""
    if not has_key(q):
        return False, "keine Lösung"
    try:
        validate_questions([admin_question(q)])
    except HTTPException as exc:
        return False, str(exc.detail).split(": ", 1)[-1]
    return True, None


def answer_fields(q) -> tuple[int, int]:
    """(answer fields, fields with a key): a Lückentext has one field per gap,
    a Zuordnung one per item, every other question one."""
    from app.services.lesson_skills.question_types import GAP_PATTERN

    config = q.config or {}
    if q.question_type == "GAP_FILL":
        ids = GAP_PATTERN.findall(config.get("text") or "")
        gaps = config.get("gaps") or {}

        def filled(g) -> bool:
            acc = g.get("accepted") if isinstance(g, dict) else g
            return bool(acc) and any(str(a).strip() for a in (acc if isinstance(acc, list) else [acc]))

        return len(ids), sum(filled(gaps.get(i)) for i in ids)
    if q.question_type == "MATCHING":
        items = config.get("items") or []
        pairs = config.get("pairs") or {}
        return len(items), sum(1 for it in items if pairs.get(str(it.get("id"))))
    return 1, int(has_key(q))


def question_state(q, review: AnswerKeyReview | None) -> dict:
    valid, problem = key_valid(q)
    verified = bool(valid and review and review.status == REVIEW_VERIFIED and review.key_fingerprint == fingerprint(q))
    flagged = bool(review and review.status == REVIEW_NEEDS_REVIEW)
    stale = bool(review and review.status == REVIEW_VERIFIED and not verified)
    fields, keyed = answer_fields(q)
    return {"has_key": valid, "key_problem": problem, "verified": verified, "needs_review": flagged, "verification_outdated": stale,
            "note": review.note if review else None, "reviewed_at": review.reviewed_at if review else None,
            "answer_fields": fields, "answer_fields_keyed": keyed}


# ============================================================
# Import notes (hints the import left for the admin — read-only)
# ============================================================


@lru_cache(maxsize=1)
def import_notes() -> dict[str, dict]:
    """content_id -> {note, book_page, source} from the course-book import
    documents in app/data (A1 / A2 …)."""
    out: dict[str, dict] = {}
    for path in sorted(DATA_DIR.glob("*/*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — unrelated / broken files are ignored
            continue
        for item in doc.get("items", []) if isinstance(doc, dict) else []:
            if not isinstance(item, dict) or item.get("skill") not in ("lesen", "hoeren"):
                continue
            meta = item.get("metadata") or {}
            out[item["content_id"]] = {"note": meta.get("note"), "book_page": meta.get("book_page"), "source": item.get("source"),
                                       "key_pending": bool(item.get("key_pending")), "key_source": meta.get("key_source"),
                                       "file": path.parent.name + "/" + path.name}
    return out


def _note_for(content_id: str | None) -> dict | None:
    if not content_id:
        return None
    return import_notes().get(content_id.split("#", 1)[0])


# ============================================================
# Loading (one query per table — no N+1)
# ============================================================


def _lesson_index(db: Session) -> dict:
    """lesson_id -> {level, number, title, lesson_id} for the main module of every level."""
    out = {}
    for level in structure.LEVELS:
        course = structure.level_course(db, level)
        module = structure.main_module(db, course) if course else None
        for lesson in structure.level_lessons(db, module):
            out[lesson.id] = {"level": level, "lesson_id": lesson.id, "lesson_number": lesson.number, "lesson_title": lesson.title}
    return out


def _load(db: Session, kind: str, lesson_ids: list) -> list:
    if not lesson_ids:
        return []
    if kind == "lesen":
        return list(db.scalars(select(Reading).where(Reading.lesson_id.in_(lesson_ids))
                               .options(selectinload(Reading.questions).selectinload(ReadingQuestion.options))))
    return list(db.scalars(select(Listening).where(Listening.lesson_id.in_(lesson_ids))
                           .options(selectinload(Listening.questions).selectinload(ListeningQuestion.options))))


def _reviews(db: Session, kind: str, question_ids: list) -> dict:
    if not question_ids:
        return {}
    col = AnswerKeyReview.reading_question_id if kind == "lesen" else AnswerKeyReview.listening_question_id
    return {getattr(r, col.key): r for r in db.scalars(select(AnswerKeyReview).where(col.in_(question_ids)))}


def _sorted_questions(task) -> list:
    return sorted(task.questions, key=lambda q: (q.order_index or 0, q.created_at))


def audio_state(listening: Listening) -> str:
    if listening.audio_storage_path:
        return "ok" if listening_audio_path(listening) is not None else "file_missing"
    return "external" if listening.audio_url else "none"


def _is_archived(task) -> bool:
    return (task.title or "").startswith("[Archiv]")


# ============================================================
# Validation report (publish requirements)
# ============================================================


def validation(kind: str, task, states: list[dict]) -> dict:
    """What stands between this Aufgabe and publishing — the existing rules
    (questions, valid keys, Hören audio) plus: every key verified, nothing
    flagged for review."""
    problems: list[dict] = []
    if not states:
        problems.append({"code": "NO_QUESTIONS", "message": "Die Aufgabe hat keine Fragen."})
    for n, st in enumerate(states, start=1):
        if not st["has_key"]:
            problems.append({"code": "KEY_MISSING", "question": n, "message": f"Frage {n}: {st['key_problem']}."})
        elif st["needs_review"]:
            problems.append({"code": "NEEDS_REVIEW", "question": n, "message": f"Frage {n}: als „prüfen“ markiert."})
        elif not st["verified"]:
            problems.append({"code": "NOT_VERIFIED", "question": n,
                             "message": f"Frage {n}: Lösung " + ("nach der Prüfung geändert — neu bestätigen." if st["verification_outdated"]
                                                                 else "noch nicht manuell bestätigt.")})
    if kind == "hoeren":
        audio = audio_state(task)
        if audio == "none":
            problems.append({"code": "AUDIO_MISSING", "message": "Kein Audio hochgeladen."})
        elif audio == "file_missing":
            problems.append({"code": "AUDIO_FILE_MISSING", "message": "Die Audiodatei fehlt auf dem Server."})
    return {"ready": not problems, "problems": problems}


def _summary(kind: str, task, lesson: dict, reviews: dict) -> dict:
    questions = _sorted_questions(task)
    states = [question_state(q, reviews.get(q.id)) for q in questions]
    report = validation(kind, task, states)
    n = len(states)
    with_key = sum(s["has_key"] for s in states)
    verified = sum(s["verified"] for s in states)
    flagged = sum(s["needs_review"] for s in states)
    if n == 0 or with_key < n:
        key_status = ST_MISSING
    elif verified == n and not flagged:
        key_status = ST_COMPLETE
    else:
        key_status = ST_NEEDS_REVIEW
    audio = audio_state(task) if kind == "hoeren" else None
    note = _note_for(task.content_id)
    return {
        "kind": kind, "id": task.id, "title": task.title, "order_index": task.order_index, **lesson,
        "questions": n, "with_key": with_key, "verified": verified, "flagged": flagged,
        "answer_fields": sum(s["answer_fields"] for s in states), "answer_fields_keyed": sum(s["answer_fields_keyed"] for s in states),
        "key_status": key_status, "audio": audio, "is_published": bool(task.is_published),
        "ready_to_publish": bool(not task.is_published and report["ready"]),
        "problems": len(report["problems"]),
        "import_note": (note or {}).get("note"),
        "updated_at": max([task.updated_at] + [q.updated_at for q in questions]),
    }


def _matches(item: dict, state: str | None) -> bool:
    if not state:
        return True
    return {
        ST_COMPLETE: item["key_status"] == ST_COMPLETE,
        ST_MISSING: item["key_status"] == ST_MISSING,
        ST_NEEDS_REVIEW: item["key_status"] == ST_NEEDS_REVIEW,
        ST_MISSING_AUDIO: item["kind"] == "hoeren" and item["audio"] in ("none", "file_missing"),
        ST_READY: item["ready_to_publish"],
        ST_PUBLISHED: item["is_published"],
        ST_DRAFT: not item["is_published"],
    }.get(state, True)


def overview(db: Session, *, level: str | None = None, lesson_id: UUID | None = None, section: str | None = None, state: str | None = None,
             publication: str | None = None, search: str | None = None) -> dict:
    lessons = _lesson_index(db)
    if level:
        lessons = {k: v for k, v in lessons.items() if v["level"] == level}
    if lesson_id:
        lessons = {k: v for k, v in lessons.items() if k == lesson_id}
    items = []
    for kind in KINDS:
        if section and section != kind:
            continue
        tasks = [t for t in _load(db, kind, list(lessons)) if not _is_archived(t)]
        reviews = _reviews(db, kind, [q.id for t in tasks for q in t.questions])
        items += [_summary(kind, t, lessons[t.lesson_id], reviews) for t in tasks]
    needle = (search or "").strip().casefold()
    if needle:
        hit_ids = _search_question_ids(db, needle)
        items = [i for i in items if needle in (i["title"] or "").casefold() or needle in (i["lesson_title"] or "").casefold() or i["id"] in hit_ids]
    if publication in ("draft", "published"):
        items = [i for i in items if i["is_published"] == (publication == "published")]
    items = [i for i in items if _matches(i, state)]
    order = {lv: n for n, lv in enumerate(structure.LEVELS)}
    items.sort(key=lambda i: (order[i["level"]], i["lesson_number"], KINDS.index(i["kind"]), i["order_index"] or 0, i["title"]))
    numbering: dict = {}
    for i in items:  # Aufgabe number within lesson + section (in the filtered list order)
        key = (i["lesson_id"], i["kind"])
        numbering[key] = numbering.get(key, 0) + 1
        i["number"] = numbering[key]
    stats = {
        "lesen_total": sum(i["kind"] == "lesen" for i in items),
        "hoeren_total": sum(i["kind"] == "hoeren" for i in items),
        "complete": sum(i["key_status"] == ST_COMPLETE for i in items),
        "missing": sum(i["key_status"] == ST_MISSING for i in items),
        "needs_review": sum(i["key_status"] == ST_NEEDS_REVIEW for i in items),
        "missing_audio": sum(i["kind"] == "hoeren" and i["audio"] in ("none", "file_missing") for i in items),
        "ready": sum(i["ready_to_publish"] for i in items),
        "published": sum(i["is_published"] for i in items),
    }
    lesson_options = sorted(({"id": v["lesson_id"], "level": v["level"], "number": v["lesson_number"], "title": v["lesson_title"]}
                             for v in _lesson_index(db).values() if not level or v["level"] == level),
                            key=lambda x: (order[x["level"]], x["number"]))
    return {"stats": stats, "items": items, "lessons": lesson_options}


def _search_question_ids(db: Session, needle: str) -> set:
    like = f"%{needle}%"
    ids = set(db.scalars(select(ReadingQuestion.reading_id).where(ReadingQuestion.question.ilike(like))))
    ids |= set(db.scalars(select(ListeningQuestion.listening_id).where(ListeningQuestion.question.ilike(like))))
    return ids


# ============================================================
# Detail / editor
# ============================================================


def _task(db: Session, kind: str, task_id: UUID):
    if kind not in KINDS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown section.")
    model, rel, qmodel = (Reading, Reading.questions, ReadingQuestion) if kind == "lesen" else (Listening, Listening.questions, ListeningQuestion)
    task = db.scalar(select(model).where(model.id == task_id).options(selectinload(rel).selectinload(qmodel.options)))
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aufgabe not found.")
    return task


def detail(db: Session, kind: str, task_id: UUID) -> dict:
    task = _task(db, kind, task_id)
    lessons = _lesson_index(db)
    lesson = lessons.get(task.lesson_id)
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aufgabe is not part of an A1–C1 lesson.")
    questions = _sorted_questions(task)
    reviews = _reviews(db, kind, [q.id for q in questions])
    states = [question_state(q, reviews.get(q.id)) for q in questions]
    note = _note_for(task.content_id)
    out = {
        **_summary(kind, task, lesson, reviews),
        "instruction": getattr(task, "instruction", None),
        "content": task.content if kind == "lesen" else None,
        "transcript": getattr(task, "transcript", None) if kind == "hoeren" else None,
        "audio_name": getattr(task, "audio_original_name", None) if kind == "hoeren" else None,
        "audio_duration": getattr(task, "audio_duration_seconds", None) if kind == "hoeren" else None,
        "import": note,
        "questions": [{**admin_question(q), **st, "number": n} for n, (q, st) in enumerate(zip(questions, states), start=1)],
        "validation": validation(kind, task, states),
    }
    # neighbours in the same order as the overview (whole course, all levels)
    full = overview(db)["items"]
    ids = [(i["kind"], str(i["id"])) for i in full]
    here = ids.index((kind, str(task.id))) if (kind, str(task.id)) in ids else -1
    nxt_incomplete = next((i for i in full[here + 1:] + full[:max(here, 0)] if i["key_status"] != ST_COMPLETE and (i["kind"], str(i["id"])) != (kind, str(task.id))), None)
    ref = lambda i: {"kind": i["kind"], "id": i["id"], "title": i["title"], "level": i["level"], "lesson_number": i["lesson_number"]} if i else None  # noqa: E731
    out["previous"] = ref(full[here - 1]) if here > 0 else None
    out["next"] = ref(full[here + 1]) if 0 <= here < len(full) - 1 else None
    out["next_incomplete"] = ref(nxt_incomplete)
    return out


# ============================================================
# Save one question's key (+ review)
# ============================================================


def save_question(db: Session, kind: str, task_id: UUID, question_id: UUID, payload: dict, actor: User, ip: str | None = None) -> dict:
    """payload: {question, options: [{id | null, text, is_correct}], config,
    explanation, review: "verified" | "needs_review" | "unverified" | null, note}.
    Multiple Choice: options without id are added, existing options missing
    from the list are removed (student attempts keep their stored answers and
    scores — no row references an option). Lückentext: the text (gaps) and
    every gap's accepted answers come with the config. Type and points stay.
    Validated with the editor rules; nothing is published. One transaction."""
    task = _task(db, kind, task_id)
    q = next((x for x in task.questions if x.id == question_id), None)
    if q is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found in this Aufgabe.")
    before = admin_question(q)
    old_fp = fingerprint(q)
    review_req = payload.get("review")
    if review_req not in (None, REVIEW_VERIFIED, REVIEW_NEEDS_REVIEW, REVIEW_UNVERIFIED):
        raise HTTPException(status_code=422, detail="review: verified, needs_review or unverified")
    if "options" in payload or "config" in payload or "question" in payload:
        options = before["options"] if "options" not in payload else payload.get("options")
        if q.question_type in CONFIG_TYPES:
            options = []
        existing = {str(o.id): o for o in q.options}
        unknown = [o for o in (options or []) if (o or {}).get("id") and str(o["id"]) not in existing]
        if unknown:
            raise HTTPException(status_code=422, detail="Unbekannte Antwortoption.")
        item = {"id": str(q.id), "question": payload.get("question", q.question), "question_type": q.question_type, "points": q.points,
                "explanation": payload.get("explanation", q.explanation),
                "options": [{"id": str(o["id"]) if o.get("id") else None, "text": o.get("text"), "is_correct": o.get("is_correct")} for o in (options or [])],
                "config": payload.get("config", q.config) if q.question_type in CONFIG_TYPES else None}
        clean = validate_questions([item])[0]  # 422 with the reason — e.g. "exactly one option must be correct"
        q.question = clean["question"]
        keep = set()
        option_model = type(q.options[0]) if q.options else None
        for order, o in enumerate(clean["options"], start=1):
            row = existing.get(str(o["id"])) if o["id"] else None
            if row is None:
                if option_model is None:
                    from app.models.lesson_skill import ListeningOption
                    from app.models.reading_option import ReadingOption

                    option_model = ReadingOption if kind == "lesen" else ListeningOption
                row = option_model(question_id=q.id, option_text=o["text"], is_correct=o["is_correct"], order_index=order)
                db.add(row)
                db.flush()
            row.option_text, row.is_correct, row.order_index = o["text"], o["is_correct"], order
            keep.add(str(row.id))
        for oid, row in existing.items():
            if oid not in keep:
                db.delete(row)
        q.config = clean["config"]
        q.explanation = clean["explanation"]
    elif "explanation" in payload:
        q.explanation = (str(payload.get("explanation") or "").strip() or None)
    db.flush()
    db.expire(q, ["options"])
    db.refresh(q)

    review = _reviews(db, kind, [q.id]).get(q.id)
    if review_req == REVIEW_VERIFIED and not key_valid(q)[0]:
        db.rollback()
        raise HTTPException(status_code=422, detail="Eine fehlende oder ungültige Lösung kann nicht bestätigt werden.")
    if review_req or "note" in payload:
        if review is None:
            review = AnswerKeyReview(status=REVIEW_UNVERIFIED, **({"reading_question_id": q.id} if kind == "lesen" else {"listening_question_id": q.id}))
            db.add(review)
        if review_req:
            review.status = review_req
            review.key_fingerprint = fingerprint(q) if review_req == REVIEW_VERIFIED else None
            review.reviewed_by = actor.id
            review.reviewed_at = _now()
        if "note" in payload:
            review.note = (str(payload.get("note") or "").strip()[:2000] or None)
    db.commit()
    db.refresh(q)
    after = admin_question(q)
    changed = fingerprint(q) != old_fp or before.get("explanation") != after.get("explanation")
    write_audit(db, str(actor.id), "answer_key_saved", details=json.dumps(
        {"kind": kind, "task": str(task.id), "question": str(q.id), "key_changed": fingerprint(q) != old_fp, "explanation_changed": changed,
         "review": review_req, "before": _key_only(before), "after": _key_only(after)}, ensure_ascii=False, default=str)[:4000], ip_address=ip)
    return detail(db, kind, task_id)


def _key_only(q: dict) -> dict:
    return {"question": q["question"], "options": [[o["text"], o["is_correct"]] for o in q["options"]], "config": q["config"]}


# ============================================================
# Publish (existing services, behind the validation report)
# ============================================================


def publish(db: Session, kind: str, task_id: UUID, actor: User, ip: str | None = None) -> dict:
    task = _task(db, kind, task_id)
    if task.is_published:
        return detail(db, kind, task_id)
    questions = _sorted_questions(task)
    reviews = _reviews(db, kind, [q.id for q in questions])
    report = validation(kind, task, [question_state(q, reviews.get(q.id)) for q in questions])
    if not report["ready"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "NOT_READY_TO_PUBLISH", "problems": report["problems"]})
    if kind == "lesen":
        from app.services.reading.service import ReadingService

        ReadingService(db).publish(task)
    else:
        from app.schemas.listening import ListeningUpdate
        from app.services.listening.service import ListeningService

        ListeningService(db).update(str(task.id), ListeningUpdate(is_published=True))  # its own audio + key checks apply
    write_audit(db, str(actor.id), "answer_key_task_published", details=json.dumps({"kind": kind, "task": str(task.id), "title": task.title}),
                ip_address=ip)
    return detail(db, kind, task_id)


def unpublish(db: Session, kind: str, task_id: UUID, actor: User, ip: str | None = None) -> dict:
    """Back to draft: students stop seeing the Aufgabe; attempts, scores,
    questions and keys stay untouched."""
    task = _task(db, kind, task_id)
    if task.is_published:
        task.is_published = False
        db.commit()
        write_audit(db, str(actor.id), "answer_key_task_unpublished", details=json.dumps({"kind": kind, "task": str(task.id), "title": task.title}),
                    ip_address=ip)
    return detail(db, kind, task_id)
