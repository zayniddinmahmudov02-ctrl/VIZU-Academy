"""Claude/JSON content import: validation -> preview -> commit (unpublished)
-> admin publish.

* validate_document() is stateless and never writes: per item it reports
  errors, warnings, the resolved target lesson and a normalised preview
  (incl. answer keys — admin only).
* commit_document() re-validates and creates ONLY the valid items, always
  unpublished, each in its own savepoint; the batch is recorded in
  content_imports with per-item outcome.
* publish_batch() publishes what a batch created — a Hören task only once its
  audio has been uploaded."""

import html
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.utils.safe_html import sanitize_html
from app.models.content_import import ContentImport
from app.models.course import Course
from app.models.language import Language
from app.models.lesson import Lesson
from app.models.lesson_skill import CONFIG_TYPES, ListeningOption, ListeningQuestion
from app.models.listening import Listening
from app.models.module import Module
from app.models.reading import Reading
from app.models.reading_option import ReadingOption
from app.models.reading_question import ReadingQuestion
from app.models.speaking import Speaking
from app.models.user import User
from app.models.writing import Writing
from app.services.content_import.schema import SCHEMA_VERSION, ContentItem, Question
from app.services.lesson_skills import admin as skill_admin
from app.services.lesson_skills import ai_evaluation, levels

ITEM_ADAPTER = TypeAdapter(ContentItem)
SKILLS = ("lesen", "hoeren", "schreiben", "sprechen")
MAX_ITEMS = 200
LETTERS = "ABCDEFGHIJKLMNO"
TRUE_WORDS = {"richtig", "r", "true", "wahr", "ja", "a"}
FALSE_WORDS = {"falsch", "f", "false", "nein", "b"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _pydantic_errors(exc: ValidationError) -> list[str]:
    out = []
    for err in exc.errors()[:30]:
        loc = ".".join(str(p) for p in err["loc"] if not (isinstance(p, str) and p in SKILLS))
        out.append(f"{loc}: {err['msg']}" if loc else err["msg"])
    return out


def _words(text: str) -> int:
    return len([w for w in str(text or "").split() if w.strip()])


def text_to_html(text: str, instruction: str | None = None) -> str:
    paragraphs = [p.strip() for p in str(text).replace("\r\n", "\n").split("\n\n") if p.strip()]
    body = "".join(f"<p>{html.escape(p, quote=False).replace(chr(10), '<br>')}</p>" for p in paragraphs)
    if instruction:
        body = f"<p><em>{html.escape(instruction, quote=False)}</em></p>" + body
    return sanitize_html(body)


# ============================================================
# Questions -> the admin payload (validated by the same code as the editor)
# ============================================================


def question_payload(q: Question) -> dict:
    """Converts one import question to the editor payload; raises ValueError."""
    if q.type in ("multiple_choice", "true_false"):
        options = list(q.options or [])
        if q.type == "true_false" and not options:
            options = ["Richtig", "Falsch"]
        if q.type == "multiple_choice" and not 2 <= len(options) <= 6:
            raise ValueError("multiple_choice needs 2-6 options")
        if q.type == "true_false" and len(options) != 2:
            raise ValueError("true_false needs exactly 2 options")
        answer = q.correct_answer
        if answer is None or answer == "":
            raise ValueError("correct_answer is missing")
        index = None
        if q.type == "true_false":
            word = str(answer).strip().casefold() if not isinstance(answer, bool) else ("true" if answer else "false")
            if word in TRUE_WORDS:
                index = 0
            elif word in FALSE_WORDS:
                index = 1
        if index is None and isinstance(answer, int) and not isinstance(answer, bool):
            index = answer - 1
        if index is None and isinstance(answer, str):
            a = answer.strip()
            if len(a) == 1 and a.upper() in LETTERS[: len(options)]:
                index = LETTERS.index(a.upper())
            elif a.isdigit():
                index = int(a) - 1
            else:
                matches = [i for i, o in enumerate(options) if o.strip().casefold() == a.casefold()]
                index = matches[0] if len(matches) == 1 else None
        if index is None or not 0 <= index < len(options):
            raise ValueError(f"correct_answer '{answer}' does not match any option")
        return {
            "question": q.question,
            "question_type": "TRUE_FALSE" if q.type == "true_false" else "MULTIPLE_CHOICE",
            "points": q.points,
            "explanation": q.explanation,
            "options": [{"text": o, "is_correct": i == index} for i, o in enumerate(options)],
        }
    if q.type == "matching":
        items, targets, pairs = q.items or [], q.targets or [], q.pairs or {}
        config = {
            "items": [{"id": str(i + 1), "text": t} for i, t in enumerate(items)],
            "targets": [{"id": LETTERS[i], "text": t} for i, t in enumerate(targets[: len(LETTERS)])],
            "pairs": {str(k).strip(): str(v).strip().upper() for k, v in pairs.items()},
        }
        return {"question": q.question, "question_type": "MATCHING", "points": q.points, "explanation": q.explanation, "options": [], "config": config}
    if q.type == "gap_fill":
        config = {"text": q.text or "", "gaps": q.gaps or {}, "case_sensitive": q.case_sensitive}
        return {"question": q.question, "question_type": "GAP_FILL", "points": q.points, "explanation": q.explanation, "options": [], "config": config}
    config = {"accepted": q.accepted or [], "case_sensitive": q.case_sensitive, "max_length": q.max_length or 100}
    return {"question": q.question, "question_type": "SHORT_ANSWER", "points": q.points, "explanation": q.explanation, "options": [], "config": config}


def _validated_questions(questions: list[Question], errors: list[str]) -> list[dict]:
    out = []
    for n, q in enumerate(questions, start=1):
        try:
            payload = question_payload(q)
            payload = skill_admin.validate_questions([payload])[0]
        except ValueError as exc:
            errors.append(f"questions.{n - 1}: {exc}")
            continue
        except HTTPException as exc:
            errors.append(f"questions.{n - 1}: {str(exc.detail).replace('Question 1: ', '')}")
            continue
        payload["passage"] = q.passage
        out.append(payload)
    return out


# ============================================================
# Target lesson
# ============================================================


def _resolve_target(db: Session, language: str, item, create_missing: bool, cache: dict) -> dict:
    key = (language, item.level, item.module, item.lesson)
    if key in cache:
        return cache[key]
    target = {"level": item.level, "module": item.module, "lesson": item.lesson, "course_id": None, "module_id": None,
              "lesson_id": None, "lesson_title": None, "create": None, "error": None}
    lang = db.scalar(select(Language).where(Language.code == language, Language.deleted_at.is_(None)))
    course = db.scalar(select(Course).where(Course.language_id == lang.id, Course.level == item.level)) if lang else None
    if course is None:
        target["error"] = f"Kurs {item.level} ({language}) existiert nicht — zuerst unter Courses anlegen."
    else:
        target["course_id"] = str(course.id)
        module = db.scalar(select(Module).where(Module.course_id == course.id, Module.number == item.module))
        lesson = db.scalar(select(Lesson).where(Lesson.module_id == module.id, Lesson.number == item.lesson)) if module else None
        if module is not None:
            target["module_id"] = str(module.id)
        if lesson is not None:
            target["lesson_id"] = str(lesson.id)
            target["lesson_title"] = lesson.title
        elif create_missing:
            target["create"] = "module+lesson" if module is None else "lesson"
        else:
            missing = f"Modul {item.module}" if module is None else f"Lektion {item.lesson} in Modul {item.module}"
            target["error"] = f"{item.level}: {missing} existiert nicht (Option 'fehlende Module/Lektionen anlegen')."
    cache[key] = target
    return target


def _ensure_lesson(db: Session, target: dict, item) -> UUID:
    if target["lesson_id"]:
        return UUID(target["lesson_id"])
    module_id = target["module_id"]
    if module_id is None:
        module = Module(course_id=target["course_id"], number=item.module, title=f"Modul {item.module}", order_index=item.module, is_active=True)
        db.add(module)
        db.flush()
        module_id = str(module.id)
        target["module_id"] = module_id
    title = str((item.metadata or {}).get("lesson_title") or f"Lektion {item.lesson}")[:255]
    lesson = Lesson(module_id=module_id, number=item.lesson, title=title, duration=0)
    db.add(lesson)
    db.flush()
    target["lesson_id"] = str(lesson.id)
    target["lesson_title"] = title
    target["create"] = None
    return lesson.id


# ============================================================
# Validation (stateless)
# ============================================================


def _existing_content_ids(db: Session, ids: set[str]) -> set[str]:
    if not ids:
        return set()
    found = set()
    for model in (Listening, Writing, Speaking):
        found |= set(db.scalars(select(model.content_id).where(model.content_id.in_(ids))))
    for cid in db.scalars(select(Reading.content_id).where(Reading.content_id.is_not(None))):
        base = cid.split("#", 1)[0]
        if base in ids:
            found.add(base)
    return found


def _check_rubric(item, errors: list[str], default: list[dict]) -> list[dict] | None:
    rubric = [r.model_dump() for r in item.rubric] if item.rubric else None
    if rubric:
        try:
            rubric = ai_evaluation.validate_rubric(rubric)
        except ValueError as exc:
            errors.append(f"rubric: {exc}")
    total = sum(c["max"] for c in (rubric or default))
    if item.max_score is not None and item.max_score != total:
        errors.append(f"max_score {item.max_score} ≠ Summe der Rubrik {total}")
    return rubric


def _validate_item(db: Session, raw, index: int, language: str, create_missing: bool, cache: dict) -> dict:
    report = {"index": index, "content_id": None, "skill": None, "level": None, "title": None, "errors": [], "warnings": [],
              "target": None, "preview": None, "_item": None}
    if isinstance(raw, dict):
        report["content_id"] = raw.get("content_id")
        report["skill"] = raw.get("skill")
        report["level"] = raw.get("level")
        report["title"] = raw.get("title")
    try:
        item = ITEM_ADAPTER.validate_python(raw)
    except ValidationError as exc:
        report["errors"] = _pydantic_errors(exc)
        return report
    errors, warnings = report["errors"], report["warnings"]
    guide = levels.guide(item.level)
    target = _resolve_target(db, language, item, create_missing, cache)
    report["target"] = {k: v for k, v in target.items() if k != "error"}
    if target["error"]:
        errors.append(target["error"])
    if target["create"]:
        warnings.append(f"Wird angelegt: {target['create']} ({item.level} · Modul {item.module} · Lektion {item.lesson})")
    if item.status != "draft":
        warnings.append("status wird ignoriert — Import ist immer ein Entwurf, Veröffentlichung nach Admin-Prüfung.")

    preview: dict = {"title": item.title, "instruction": item.instruction}
    if item.skill in ("lesen", "hoeren"):
        questions = _validated_questions(item.questions, errors)
        total = sum(q["points"] for q in questions)
        if item.max_score is not None and len(questions) == len(item.questions) and item.max_score != total:
            errors.append(f"max_score {item.max_score} ≠ Summe der Fragenpunkte {total}")
        preview["questions"] = questions
        preview["max_points"] = total
        if item.skill == "lesen":
            for n, q in enumerate(item.questions, start=1):
                if q.passage > len(item.passages):
                    errors.append(f"questions.{n - 1}.passage: Text {q.passage} existiert nicht (nur {len(item.passages)})")
            lo, hi = guide["reading_words"]
            for n, p in enumerate(item.passages, start=1):
                words = _words(p.text)
                if not lo * 0.5 <= words <= hi * 1.5:
                    warnings.append(f"Text {n}: {words} Wörter — für {item.level} üblich {lo}-{hi}.")
            preview["passages"] = [p.model_dump() for p in item.passages]
        else:
            preview["transcript"] = item.transcript
            preview["audio_hint"] = item.audio_file or item.audio_asset_id
            warnings.append("Audio muss nach dem Import hochgeladen werden — erst dann ist die Veröffentlichung möglich.")
            if not item.transcript:
                warnings.append("Kein Transkript angegeben.")
    elif item.skill == "schreiben":
        if item.min_words > item.max_words:
            errors.append("min_words > max_words")
        rubric = _check_rubric(item, errors, levels.writing_rubric(item.level))
        lo, hi = guide["writing_words"]
        if item.max_words < lo * 0.5 or item.min_words > hi * 1.5:
            warnings.append(f"Wortgrenze {item.min_words}-{item.max_words} — für {item.level} üblich {lo}-{hi}.")
        if item.task_type not in guide["text_types"]:
            warnings.append(f"Textsorte '{item.task_type}' ist für {item.level} unüblich ({', '.join(guide['text_types'])}).")
        preview.update(prompt=item.prompt, task_type=item.task_type, audience=item.audience, min_words=item.min_words,
                       max_words=item.max_words, time_limit=item.time_limit, support_phrases=item.support_phrases,
                       rubric=rubric or levels.writing_rubric(item.level), rubric_is_default=not rubric)
    else:  # sprechen
        if item.min_duration > item.max_duration:
            errors.append("min_duration > max_duration")
        rubric = _check_rubric(item, errors, levels.speaking_rubric(item.level))
        lo, hi = guide["speaking_seconds"]
        if item.max_duration < lo * 0.5 or item.max_duration > hi * 2:
            warnings.append(f"Sprechzeit {item.max_duration}s — für {item.level} üblich {lo}-{hi}s.")
        preview.update(prompt=item.prompt, topic=item.topic, questions=item.questions, response_type=item.response_type,
                       min_duration=item.min_duration, max_duration=item.max_duration, preparation_time=item.preparation_time,
                       speech_goal=item.speech_goal, rubric=rubric or levels.speaking_rubric(item.level), rubric_is_default=not rubric)
    report["preview"] = preview
    report["_item"] = item
    return report


def validate_document(db: Session, document, create_missing: bool = False) -> dict:
    top_errors: list[str] = []
    if not isinstance(document, dict):
        raise HTTPException(status_code=422, detail="The import file must be a JSON object.")
    if document.get("schema_version") != SCHEMA_VERSION:
        top_errors.append(f"schema_version must be '{SCHEMA_VERSION}'")
    extra = set(document) - {"schema_version", "language", "source", "items"}
    if extra:
        top_errors.append(f"unknown top-level fields: {sorted(extra)}")
    language = str(document.get("language") or "de")
    raw_items = document.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        top_errors.append("'items' must be a non-empty list")
        raw_items = []
    if len(raw_items) > MAX_ITEMS:
        top_errors.append(f"max {MAX_ITEMS} items per import")
        raw_items = raw_items[:MAX_ITEMS]

    cache: dict = {}
    reports = [_validate_item(db, raw, i, language, create_missing, cache) for i, raw in enumerate(raw_items)]

    # duplicates: inside the file and already in the database
    seen: dict[str, int] = {}
    for r in reports:
        cid = r["content_id"]
        if not cid:
            continue
        if cid in seen:
            r["errors"].append(f"content_id doppelt in der Datei (wie Eintrag {seen[cid] + 1})")
        else:
            seen[cid] = r["index"]
    existing = _existing_content_ids(db, {r["content_id"] for r in reports if isinstance(r["content_id"], str)})
    for r in reports:
        if r["content_id"] in existing:
            r["errors"].append("content_id existiert bereits (schon importiert) — neue content_id verwenden oder vorhandenen Inhalt bearbeiten.")
        target = r["target"] or {}
        if r["_item"] is not None and target.get("lesson_id") and not r["errors"]:
            model = {"lesen": Reading, "hoeren": Listening, "schreiben": Writing, "sprechen": Speaking}[r["skill"]]
            titles = [r["title"]] if r["skill"] != "lesen" else [p.title for p in r["_item"].passages]
            if db.scalar(select(func.count(model.id)).where(model.lesson_id == UUID(target["lesson_id"]), model.title.in_(titles))):
                r["warnings"].append("In dieser Lektion gibt es bereits einen Inhalt mit gleichem Titel.")

    for r in reports:
        r["valid"] = not r["errors"] and not top_errors
    return {
        "schema_version": SCHEMA_VERSION,
        "errors": top_errors,
        "total": len(reports),
        "valid": sum(r["valid"] for r in reports),
        "invalid": sum(not r["valid"] for r in reports),
        "items": reports,
    }


def public_report(report: dict) -> dict:
    return {**report, "items": [{k: v for k, v in r.items() if k != "_item"} for r in report["items"]]}


# ============================================================
# Commit (creates unpublished content)
# ============================================================


def _next_order(db: Session, model, lesson_id: UUID) -> int:
    return int(db.scalar(select(func.max(model.order_index)).where(model.lesson_id == lesson_id)) or 0) + 1


def _add_questions(db: Session, owner_id: UUID, questions: list[dict], kind: str, passage: int | None = None) -> None:
    order = 0
    for q in questions:
        if passage is not None and q["passage"] != passage:
            continue
        order += 1
        if kind == "lesen":
            row = ReadingQuestion(reading_id=owner_id, question=q["question"], explanation=q["explanation"], order_index=order,
                                  is_published=True, question_type=q["question_type"], points=q["points"], config=q.get("config"))
        else:
            row = ListeningQuestion(listening_id=owner_id, question=q["question"], explanation=q["explanation"], order_index=order,
                                    question_type=q["question_type"], points=q["points"], config=q.get("config"))
        db.add(row)
        db.flush()
        if q["question_type"] in CONFIG_TYPES:
            continue
        for o_order, o in enumerate(q["options"], start=1):
            option_model = ReadingOption if kind == "lesen" else ListeningOption
            db.add(option_model(question_id=row.id, option_text=o["text"], is_correct=o["is_correct"], order_index=o_order))


def _create(db: Session, item, report: dict, target: dict) -> list[dict]:
    lesson_id = _ensure_lesson(db, target, item)
    created = []
    preview = report["preview"]
    if item.skill == "lesen":
        base = item.order or _next_order(db, Reading, lesson_id)
        for n, p in enumerate(item.passages, start=1):
            reading = Reading(lesson_id=lesson_id, title=p.title, content=text_to_html(p.text, item.instruction if n == 1 else None),
                              order_index=base + n - 1, is_published=False, image_url=p.image_url, content_id=f"{item.content_id}#{n}")
            db.add(reading)
            db.flush()
            _add_questions(db, reading.id, preview["questions"], "lesen", passage=n)
            created.append({"kind": "reading", "id": str(reading.id)})
    elif item.skill == "hoeren":
        listening = Listening(lesson_id=lesson_id, title=item.title, instruction=item.instruction, transcript=item.transcript,
                              order_index=item.order or _next_order(db, Listening, lesson_id), is_published=False, content_id=item.content_id)
        db.add(listening)
        db.flush()
        _add_questions(db, listening.id, preview["questions"], "hoeren")
        created.append({"kind": "listening", "id": str(listening.id)})
    elif item.skill == "schreiben":
        rubric = None if preview["rubric_is_default"] else preview["rubric"]
        writing = Writing(
            lesson_id=lesson_id, title=item.title, instruction=item.prompt if not item.instruction else f"{item.instruction}\n\n{item.prompt}",
            min_words=item.min_words, max_words=item.max_words, order_index=item.order or _next_order(db, Writing, lesson_id),
            is_published=False, ai_evaluation_enabled=True, ai_instructions=item.ai_instructions, feedback_language=item.feedback_language,
            max_score=item.max_score or sum(c["max"] for c in preview["rubric"]), rubric=rubric, max_attempts=item.max_attempts,
            helper_words=", ".join(item.support_phrases) if item.support_phrases else None, image_url=item.image_url,
            text_type=item.task_type, audience=item.audience, time_limit_minutes=item.time_limit, content_id=item.content_id,
        )
        db.add(writing)
        db.flush()
        created.append({"kind": "writing", "id": str(writing.id)})
    else:
        rubric = None if preview["rubric_is_default"] else preview["rubric"]
        speaking = Speaking(
            lesson_id=lesson_id, title=item.title, topic=(item.topic or item.title)[:255],
            instruction=item.prompt if not item.instruction else f"{item.instruction}\n\n{item.prompt}",
            sample_answer=item.sample_answer, keywords=", ".join(item.keywords) if item.keywords else None,
            preparation_time=item.preparation_time, speaking_time=item.max_duration, order_index=item.order or _next_order(db, Speaking, lesson_id),
            is_published=False, ai_evaluation_enabled=True, ai_instructions=item.ai_instructions, feedback_language=item.feedback_language,
            max_score=item.max_score or sum(c["max"] for c in preview["rubric"]), rubric=rubric, max_attempts=item.max_attempts,
            min_duration_seconds=item.min_duration, response_type=item.response_type.upper(), questions=item.questions,
            speech_goal=item.speech_goal, content_id=item.content_id,
        )
        db.add(speaking)
        db.flush()
        created.append({"kind": "speaking", "id": str(speaking.id)})
    return created


def commit_document(db: Session, document, actor: User, filename: str | None, create_missing: bool = False) -> ContentImport:
    report = validate_document(db, document, create_missing)
    if report["errors"]:
        raise HTTPException(status_code=422, detail="; ".join(report["errors"]))
    language = str(document.get("language") or "de")
    cache: dict = {}
    items_out = []
    for r in report["items"]:
        entry = {"index": r["index"], "content_id": r["content_id"], "skill": r["skill"], "level": r["level"], "title": r["title"],
                 "errors": list(r["errors"]), "warnings": list(r["warnings"]), "status": "error", "created": [], "published": False}
        item = r["_item"]
        if r["valid"] and item is not None:
            target = _resolve_target(db, language, item, create_missing, cache)
            savepoint = db.begin_nested()
            try:
                entry["created"] = _create(db, item, r, target)
                savepoint.commit()
                entry["status"] = "created"
                entry["lesson_id"] = target["lesson_id"]
                if item.skill == "hoeren":
                    entry["audio_hint"] = item.audio_file or item.audio_asset_id
            except Exception as exc:  # noqa: BLE001 — reported per item, the batch goes on
                savepoint.rollback()
                cache.pop((language, item.level, item.module, item.lesson), None)
                entry["errors"].append(f"Anlegen fehlgeschlagen: {type(exc).__name__}")
        items_out.append(entry)
    batch = ContentImport(
        actor_id=actor.id, filename=(filename or "")[:255] or None, schema_version=SCHEMA_VERSION,
        levels=sorted({i["level"] for i in items_out if i["level"] in levels.LEVELS}),
        total_items=len(items_out), created_items=sum(i["status"] == "created" for i in items_out),
        failed_items=sum(i["status"] != "created" for i in items_out), items=items_out,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


# ============================================================
# Publish (after admin review)
# ============================================================

_KIND_MODEL = {"reading": Reading, "listening": Listening, "writing": Writing, "speaking": Speaking}


def publish_batch(db: Session, batch_id: UUID) -> ContentImport:
    batch = db.get(ContentImport, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Import not found.")
    items = [dict(i) for i in (batch.items or [])]
    for entry in items:
        if entry.get("status") != "created":
            continue
        problems = []
        rows = []
        for created in entry.get("created", []):
            row = db.get(_KIND_MODEL[created["kind"]], UUID(created["id"]))
            if row is None:
                problems.append("gelöscht")
                continue
            if created["kind"] == "listening" and not (row.audio_storage_path or row.audio_url):
                problems.append("AUDIO_REQUIRED")
            rows.append(row)
        if problems:
            entry["publish_problem"] = ", ".join(sorted(set(problems)))
            continue
        for row in rows:
            row.is_published = True
        entry["published"] = True
        entry.pop("publish_problem", None)
    batch.items = items
    batch.published_at = _now()
    db.commit()
    db.refresh(batch)
    return batch


def batch_summary(batch: ContentImport, with_items: bool = False) -> dict:
    out = {
        "id": batch.id, "filename": batch.filename, "schema_version": batch.schema_version, "levels": batch.levels or [],
        "total_items": batch.total_items, "created_items": batch.created_items, "failed_items": batch.failed_items,
        "published_items": sum(1 for i in (batch.items or []) if i.get("published")),
        "created_at": batch.created_at, "published_at": batch.published_at,
    }
    if with_items:
        out["items"] = batch.items or []
    return out
