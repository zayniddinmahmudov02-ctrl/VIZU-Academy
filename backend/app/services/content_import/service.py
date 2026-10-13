"""Claude/JSON content import: validation -> preview -> commit (unpublished)
-> admin publish.

* validate_document() is stateless and never writes: per item it reports
  errors, warnings, the resolved target lesson and a normalised preview
  (incl. answer keys — admin only).
* commit_document() re-validates and creates ONLY the valid items, always
  unpublished, each in its own savepoint; the batch is recorded in
  content_imports with per-item outcome.
* publish_batch() publishes what a batch created — a Hören task only once its
  audio has been uploaded and every question has its answer key.

Re-running an import never duplicates content: an item whose content_id is
already in the database is an error — or, with skip_existing (the book
import), it is reported as "skipped". skip_existing also skips content an
admin created by hand with the same title in the same lesson, and Wortschatz
words that the lesson already has."""

import hashlib
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
from app.models.grammar import Grammar
from app.models.language import Language
from app.models.lesson import Lesson
from app.models.lesson_skill import (
    CONFIG_TYPES,
    SKILL_GRAMMATIK,
    SKILL_SCHREIBEN,
    SKILL_UEBUNGEN,
    SKILL_WORTSCHATZ,
    SKILL_YAKUNIY,
    TASK_KIND_FRAGE,
    TASK_KIND_SPRECHEN,
    ListeningOption,
    ListeningQuestion,
    SkillExercise,
    SkillExerciseOption,
    SkillExerciseQuestion,
)
from app.models.listening import Listening
from app.models.lms import LessonCompetency
from app.models.module import Module
from app.models.reading import Reading
from app.models.reading_option import ReadingOption
from app.models.reading_question import ReadingQuestion
from app.models.speaking import Speaking
from app.models.user import User
from app.models.vocabulary import Vocabulary
from app.models.writing import Writing
from app.services.content_import.schema import SCHEMA_VERSION, SCHEMA_VERSIONS, ContentItem, Question
from app.services.lesson_skills import admin as skill_admin
from app.services.lesson_skills import ai_evaluation, levels
from app.services.lesson_skills.exercises import has_key

ITEM_ADAPTER = TypeAdapter(ContentItem)
SKILLS = ("frage", "grammatik", "lesen", "hoeren", "schreiben", "sprechen", "wortschatz", "yakuniy", "uebungen", "schreiben_uebungen", "kompetenz")
EXERCISE_ITEM_SKILLS = {"uebungen": SKILL_UEBUNGEN, "schreiben_uebungen": SKILL_SCHREIBEN}
MAX_ITEMS = 200
LETTERS = "ABCDEFGHIJKLMNO"
TRUE_WORDS = {"richtig", "r", "true", "wahr", "ja", "a"}
FALSE_WORDS = {"falsch", "f", "false", "nein", "b"}
PRACTICE_CHUNK = 20  # Wortschatz auto practice: questions per set


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


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").split()).casefold()


# ============================================================
# Questions -> the admin payload (validated by the same code as the editor)
# ============================================================


def question_payload(q: Question, allow_pending: bool = False) -> dict:
    """Converts one import question to the editor payload; raises ValueError.
    allow_pending: an option question without correct_answer is accepted with
    every option marked wrong (key set later by an admin)."""
    if q.type in ("multiple_choice", "true_false"):
        options = list(q.options or [])
        if q.type == "true_false" and not options:
            options = ["Richtig", "Falsch"]
        if q.type == "multiple_choice" and not 2 <= len(options) <= 6:
            raise ValueError("multiple_choice needs 2-6 options")
        if q.type == "true_false" and len(options) != 2:
            raise ValueError("true_false needs exactly 2 options")
        answer = q.correct_answer
        qtype = "TRUE_FALSE" if q.type == "true_false" else "MULTIPLE_CHOICE"
        if (answer is None or answer == "") and allow_pending:
            return {"question": q.question, "question_type": qtype, "points": q.points, "explanation": q.explanation,
                    "options": [{"text": o, "is_correct": False} for o in options], "key_pending": True}
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
            "question_type": qtype,
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
        if allow_pending and _gaps_incomplete(config):
            from app.services.lesson_skills.question_types import GAP_PATTERN

            gaps = {}
            for gid in GAP_PATTERN.findall(config["text"]):
                g = config["gaps"].get(gid) or []
                g = g if isinstance(g, dict) else {"accepted": g}
                gaps[gid] = {**g, "accepted": [a for a in (g.get("accepted") or []) if str(a).strip()]}
            if not gaps:
                raise ValueError("Lückentext: the text contains no [[gap]] placeholder")
            return {"question": q.question, "question_type": "GAP_FILL", "points": q.points, "explanation": q.explanation, "options": [],
                    "config": {"text": config["text"], "gaps": gaps, "case_sensitive": q.case_sensitive, "pending": True}, "key_pending": True}
        return {"question": q.question, "question_type": "GAP_FILL", "points": q.points, "explanation": q.explanation, "options": [], "config": config}
    config = {"accepted": q.accepted or [], "case_sensitive": q.case_sensitive, "max_length": q.max_length or 100}
    return {"question": q.question, "question_type": "SHORT_ANSWER", "points": q.points, "explanation": q.explanation, "options": [], "config": config}


def _gaps_incomplete(config: dict) -> bool:
    from app.services.lesson_skills.question_types import GAP_PATTERN

    for gid in GAP_PATTERN.findall(config.get("text") or ""):
        g = (config.get("gaps") or {}).get(gid)
        accepted = g.get("accepted") if isinstance(g, dict) else g
        if not accepted or not any(str(a).strip() for a in (accepted if isinstance(accepted, list) else [accepted])):
            return True
    return False


def _validated_questions(questions: list[Question], errors: list[str], prefix: str = "questions", allow_pending: bool = False) -> list[dict]:
    out = []
    for n, q in enumerate(questions, start=1):
        try:
            payload = question_payload(q, allow_pending)
            if payload.get("key_pending"):
                text = payload["question"].strip()
                if not text or any(not o["text"].strip() for o in payload["options"]):
                    raise ValueError("question and options need a text")
                if not 1 <= payload["points"] <= 100:
                    raise ValueError("points 1-100")
            else:
                payload = skill_admin.validate_questions([payload])[0]
        except ValueError as exc:
            errors.append(f"{prefix}.{n - 1}: {exc}")
            continue
        except HTTPException as exc:
            errors.append(f"{prefix}.{n - 1}: {str(exc.detail).replace('Question 1: ', '')}")
            continue
        payload["passage"] = q.passage
        payload.setdefault("id", None)
        out.append(payload)
    return out


# ============================================================
# Wortschatz: automatic translation practice
# ============================================================


def _word_label(w) -> str:
    return f"{w.article} {w.word}" if w.article else w.word


def practice_sets(words: list, title: str) -> list[dict]:
    """Multiple choice 'What does … mean?' from the lesson's own words, with
    two distractors from the same list (deterministic). Sets of 20."""
    unique = []
    seen = set()
    for w in words:
        key = _word_key(w.word, w.translation)
        if _norm(w.translation) and key not in seen:
            seen.add(key)
            unique.append(w)
    translations = []
    for w in unique:
        if _norm(w.translation) not in {_norm(t) for t in translations}:
            translations.append(w.translation)
    if len(unique) < 3 or len(translations) < 3:
        return []
    questions = []
    for w in unique:
        others = [t for t in translations if _norm(t) != _norm(w.translation)]
        others.sort(key=lambda t: hashlib.sha256(f"{w.word}:{t}".encode()).hexdigest())
        options = [w.translation, *others[:2]]
        options.sort(key=lambda t: hashlib.sha256(f"{t}:{w.word}".encode()).hexdigest())
        questions.append(
            {
                "question": f"„{_word_label(w)}“ — o'zbekchasi qaysi?",
                "question_type": "MULTIPLE_CHOICE",
                "points": 1,
                "explanation": f"{_word_label(w)} — {w.translation}",
                "options": [{"text": o, "is_correct": _norm(o) == _norm(w.translation)} for o in options],
                "config": None,
                "id": None,
            }
        )
    chunks = [questions[i : i + PRACTICE_CHUNK] for i in range(0, len(questions), PRACTICE_CHUNK)]
    return [
        {"title": title if len(chunks) == 1 else f"{title} ({n}/{len(chunks)})", "instruction": "So'zning to'g'ri tarjimasini tanlang.",
         "source": "vizu", "questions": chunk}
        for n, chunk in enumerate(chunks, start=1)
    ]


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

_CONTENT_MODELS = (Reading, Listening, Writing, Speaking, Grammar, Vocabulary, SkillExercise)


def _existing_content_ids(db: Session, ids: set[str]) -> set[str]:
    """content_ids already used; sub-rows are stored as '<content_id>#<n>'."""
    if not ids:
        return set()
    found = set()
    for model in _CONTENT_MODELS:
        for cid in db.scalars(select(model.content_id).where(model.content_id.is_not(None))):
            base = cid.split("#", 1)[0]
            if base in ids:
                found.add(base)
    return found


def _existing_titles(db: Session, lesson_id: UUID, item) -> list[str]:
    """Titles of this item that the lesson already has (manual / earlier content)."""
    if item.skill == "lesen":
        titles, model, extra = [p.title for p in item.passages], Reading, ()
    elif item.skill == "grammatik":
        titles, model, extra = [r.title for r in item.rules], Grammar, ()
    elif item.skill in ("hoeren", "schreiben"):
        titles, model, extra = [item.title], Listening if item.skill == "hoeren" else Writing, ()
    elif item.skill in ("sprechen", "frage"):
        kind = TASK_KIND_FRAGE if item.skill == "frage" else TASK_KIND_SPRECHEN
        titles, model, extra = [item.title], Speaking, (Speaking.task_kind == kind,)
    else:
        return []
    have = {_norm(t) for t in db.scalars(select(model.title).where(model.lesson_id == lesson_id, *extra))}
    return [t for t in titles if _norm(t) in have]


def _word_key(word: str | None, translation: str | None) -> str:
    """'sie' (u) and 'sie' (ular) are two entries; the same word with the same
    meaning is one."""
    return f"{_norm(word)}|{_norm(translation)}"


def _existing_words(db: Session, lesson_id: UUID) -> set[str]:
    rows = db.execute(select(Vocabulary.german_word, Vocabulary.translation).where(Vocabulary.lesson_id == lesson_id)).all()
    return {_word_key(w, t) for w, t in rows}


def _new_words(db: Session, lesson_id: UUID, words: list) -> list:
    """The words of an import the lesson does not have yet. A word counts as
    present when the lesson has it with the same meaning — or, spelling only,
    as often as the book lists it (an admin may have shortened a translation;
    'sie' = u / ular stays two entries)."""
    from collections import Counter

    rows = db.execute(select(Vocabulary.german_word, Vocabulary.translation).where(Vocabulary.lesson_id == lesson_id)).all()
    exact = {_word_key(w, t) for w, t in rows}
    spelled = Counter(_norm(w) for w, _ in rows)
    seen: Counter = Counter()
    out = []
    for w in words:
        key = _word_key(w.word, w.translation)
        seen[_norm(w.word)] += 1
        if key in exact or spelled[_norm(w.word)] >= seen[_norm(w.word)]:
            continue
        exact.add(key)
        out.append(w)
    return out


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


def _exercise_sets(sets, errors: list[str], prefix: str = "exercises") -> list[dict]:
    out = []
    for n, ex in enumerate(sets):
        questions = _validated_questions(ex.questions, errors, f"{prefix}.{n}.questions")
        out.append({"title": ex.title, "instruction": ex.instruction, "source": ex.source, "questions": questions,
                    "max_points": sum(q["points"] for q in questions)})
    return out


def _validate_item(db: Session, raw, index: int, language: str, create_missing: bool, cache: dict) -> dict:
    report = {"index": index, "content_id": None, "skill": None, "level": None, "title": None, "errors": [], "warnings": [],
              "target": None, "preview": None, "source": None, "skip": None, "_item": None}
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
    report["source"] = item.source
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
        pending = item.skill == "hoeren" and item.key_pending
        questions = _validated_questions(item.questions, errors, allow_pending=pending)
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
            preview["key_pending"] = sum(1 for q in questions if q.get("key_pending"))
            warnings.append("Audio muss nach dem Import hochgeladen werden — erst dann ist die Veröffentlichung möglich.")
            if preview["key_pending"]:
                warnings.append(f"{preview['key_pending']} Frage(n) ohne Lösung — nach dem Anhören des Audios im Hören-Tab festlegen.")
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
    elif item.skill == "sprechen":
        if item.min_duration > item.max_duration:
            errors.append("min_duration > max_duration")
        rubric = _check_rubric(item, errors, levels.speaking_rubric(item.level))
        lo, hi = guide["speaking_seconds"]
        if item.max_duration < lo * 0.5 or item.max_duration > hi * 2:
            warnings.append(f"Sprechzeit {item.max_duration}s — für {item.level} üblich {lo}-{hi}s.")
        preview.update(prompt=item.prompt, topic=item.topic, questions=item.questions, response_type=item.response_type,
                       min_duration=item.min_duration, max_duration=item.max_duration, preparation_time=item.preparation_time,
                       speech_goal=item.speech_goal, rubric=rubric or levels.speaking_rubric(item.level), rubric_is_default=not rubric)
    elif item.skill == "frage":
        if item.min_duration > item.max_duration:
            errors.append("min_duration > max_duration")
        preview.update(prompt=item.prompt, questions=item.questions, min_duration=item.min_duration, max_duration=item.max_duration)
    elif item.skill == "grammatik":
        if not item.rules and not item.exercises:
            errors.append("grammatik: rules or exercises are required")
        preview["rules"] = [{"title": r.title, "html": sanitize_html(r.html)} for r in item.rules]
        preview["exercises"] = _exercise_sets(item.exercises, errors)
    elif item.skill == "wortschatz":
        words = item.words
        seen, dupes = set(), []
        for w in words:
            key = _word_key(w.word, w.translation) + "|" + _norm(w.article)
            if key in seen:
                dupes.append(w.word)
            seen.add(key)
        if dupes:
            warnings.append(f"Doppelte Wörter in der Datei: {', '.join(sorted(set(dupes))[:10])}")
        preview["words"] = [w.model_dump() for w in words]
        preview["exercises"] = _exercise_sets(item.exercises, errors)
        if item.auto_practice:
            preview["auto_practice"] = sum(len(s["questions"]) for s in practice_sets(words, f"Wortschatz-Übung: {item.title}"))
    elif item.skill in EXERCISE_ITEM_SKILLS:
        preview["exercises"] = _exercise_sets(item.exercises, errors)
    elif item.skill == "kompetenz":
        html = sanitize_html(item.html)
        if not html.strip():
            errors.append("kompetenz: html is empty after sanitizing")
        preview.update(competency=item.competency, html=html)
    else:  # yakuniy
        questions = _validated_questions(item.questions, errors)
        total = sum(q["points"] for q in questions)
        if item.max_score is not None and len(questions) == len(item.questions) and item.max_score != total:
            errors.append(f"max_score {item.max_score} ≠ Summe der Fragenpunkte {total}")
        preview["questions"] = questions
        preview["max_points"] = total
    report["preview"] = preview
    report["_item"] = item
    return report


def validate_document(db: Session, document, create_missing: bool = False, skip_existing: bool = False) -> dict:
    top_errors: list[str] = []
    if not isinstance(document, dict):
        raise HTTPException(status_code=422, detail="The import file must be a JSON object.")
    if document.get("schema_version") not in SCHEMA_VERSIONS:
        top_errors.append(f"schema_version must be one of {', '.join(SCHEMA_VERSIONS)}")
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
        target = r["target"] or {}
        if r["content_id"] in existing:
            if skip_existing:
                r["skip"] = "content_id bereits importiert"
            else:
                r["errors"].append("content_id existiert bereits (schon importiert) — neue content_id verwenden oder vorhandenen Inhalt bearbeiten.")
        if r["_item"] is None or not target.get("lesson_id") or r["errors"] or r["skip"]:
            continue
        lesson_id = UUID(target["lesson_id"])
        same = _existing_titles(db, lesson_id, r["_item"])
        if same and skip_existing and r["skill"] in ("hoeren", "schreiben", "sprechen", "frage"):
            r["skip"] = f"In der Lektion gibt es bereits: {same[0]}"
        elif same:
            r["warnings"].append(f"In dieser Lektion gibt es bereits Inhalt mit gleichem Titel: {', '.join(same)}"
                                 + (" — wird übersprungen" if skip_existing else ""))
        if r["skill"] == "kompetenz":
            row = _competency_row(db, lesson_id, r["_item"].competency)
            if row is not None and (row.body or "").strip():
                if skip_existing:
                    r["skip"] = "Kompetenz hat bereits einen Text"
                else:
                    r["errors"].append("Diese Kompetenz hat bereits einen Text — im Kurs-Editor bearbeiten.")
            else:
                r["warnings"].append("Der Text ist sichtbar, sobald Lektion und Kompetenz veröffentlicht sind.")
        if r["skill"] == "wortschatz":
            fresh = {id(w) for w in _new_words(db, lesson_id, r["_item"].words)}
            known = [w.word for w in r["_item"].words if id(w) not in fresh]
            if known:
                r["warnings"].append(f"{len(known)} Wort/Wörter gibt es in der Lektion schon — werden nicht doppelt angelegt.")

    for r in reports:
        r["valid"] = not r["errors"] and not top_errors and not r["skip"]
    return {
        "schema_version": SCHEMA_VERSION,
        "errors": top_errors,
        "total": len(reports),
        "valid": sum(r["valid"] for r in reports),
        "invalid": sum(bool(r["errors"]) or bool(top_errors) for r in reports),
        "skipped": sum(bool(r["skip"]) and not r["errors"] for r in reports),
        "items": reports,
    }


def public_report(report: dict) -> dict:
    return {**report, "items": [{k: v for k, v in r.items() if k != "_item"} for r in report["items"]]}


# ============================================================
# Commit (creates unpublished content)
# ============================================================


def _next_order(db: Session, model, lesson_id: UUID, *where) -> int:
    return int(db.scalar(select(func.max(model.order_index)).where(model.lesson_id == lesson_id, *where)) or 0) + 1


def _add_questions(db: Session, owner_id: UUID, questions: list[dict], kind: str, passage: int | None = None) -> None:
    order = 0
    for q in questions:
        if passage is not None and q["passage"] != passage:
            continue
        order += 1
        common = dict(question=q["question"], explanation=q["explanation"], order_index=order, question_type=q["question_type"],
                      points=q["points"], config=q.get("config"))
        if kind == "lesen":
            row, option_model = ReadingQuestion(reading_id=owner_id, is_published=True, **common), ReadingOption
        elif kind == "hoeren":
            row, option_model = ListeningQuestion(listening_id=owner_id, **common), ListeningOption
        else:
            row, option_model = SkillExerciseQuestion(exercise_id=owner_id, **common), SkillExerciseOption
        db.add(row)
        db.flush()
        if q["question_type"] in CONFIG_TYPES:
            continue
        for o_order, o in enumerate(q["options"], start=1):
            db.add(option_model(question_id=row.id, option_text=o["text"], is_correct=o["is_correct"], order_index=o_order))


def _add_exercise(db: Session, lesson_id: UUID, skill: str, ex: dict, content_id: str) -> dict:
    row = SkillExercise(lesson_id=lesson_id, skill=skill, title=ex["title"][:255], instruction=ex.get("instruction"),
                        order_index=_next_order(db, SkillExercise, lesson_id, SkillExercise.skill == skill), is_published=False,
                        source=ex.get("source") or "book", content_id=content_id)
    db.add(row)
    db.flush()
    _add_questions(db, row.id, ex["questions"], "exercise")
    return {"kind": "exercise", "id": str(row.id)}


def _competency_row(db: Session, lesson_id: UUID, kind: str) -> LessonCompetency | None:
    return db.scalar(select(LessonCompetency).where(LessonCompetency.lesson_id == lesson_id, LessonCompetency.kind == kind))


def _create(db: Session, item, report: dict, target: dict, skip_existing: bool = False) -> list[dict]:
    lesson_id = _ensure_lesson(db, target, item)
    created = []
    preview = report["preview"]
    skip_titles = {_norm(t) for t in _existing_titles(db, lesson_id, item)} if skip_existing else set()
    if item.skill == "lesen":
        base = item.order or _next_order(db, Reading, lesson_id)
        for n, p in enumerate(item.passages, start=1):
            if _norm(p.title) in skip_titles:
                continue
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
    elif item.skill == "sprechen":
        rubric = None if preview["rubric_is_default"] else preview["rubric"]
        speaking = Speaking(
            lesson_id=lesson_id, title=item.title, topic=(item.topic or item.title)[:255],
            instruction=item.prompt if not item.instruction else f"{item.instruction}\n\n{item.prompt}",
            sample_answer=item.sample_answer, keywords=", ".join(item.keywords) if item.keywords else None,
            preparation_time=item.preparation_time, speaking_time=item.max_duration,
            order_index=item.order or _next_order(db, Speaking, lesson_id, Speaking.task_kind == TASK_KIND_SPRECHEN),
            is_published=False, ai_evaluation_enabled=True, ai_instructions=item.ai_instructions, feedback_language=item.feedback_language,
            max_score=item.max_score or sum(c["max"] for c in preview["rubric"]), rubric=rubric, max_attempts=item.max_attempts,
            min_duration_seconds=item.min_duration, response_type=item.response_type.upper(), questions=item.questions,
            speech_goal=item.speech_goal, content_id=item.content_id, task_kind=TASK_KIND_SPRECHEN,
        )
        db.add(speaking)
        db.flush()
        created.append({"kind": "speaking", "id": str(speaking.id)})
    elif item.skill == "frage":
        # no rubric: the answer is reviewed, never scored automatically
        speaking = Speaking(
            lesson_id=lesson_id, title=item.title, topic=item.title[:255],
            instruction=item.prompt if not item.instruction else f"{item.instruction}\n\n{item.prompt}",
            preparation_time=0, speaking_time=item.max_duration, min_duration_seconds=item.min_duration,
            order_index=item.order or _next_order(db, Speaking, lesson_id, Speaking.task_kind == TASK_KIND_FRAGE),
            is_published=False, ai_evaluation_enabled=False, max_score=100, max_attempts=3, questions=item.questions,
            content_id=item.content_id, task_kind=TASK_KIND_FRAGE,
        )
        db.add(speaking)
        db.flush()
        created.append({"kind": "speaking", "id": str(speaking.id)})
    elif item.skill == "grammatik":
        order = _next_order(db, Grammar, lesson_id)
        for n, rule in enumerate(item.rules, start=1):
            if _norm(rule.title) in skip_titles:
                continue
            grammar = Grammar(lesson_id=lesson_id, title=rule.title, content=sanitize_html(rule.html), order_index=order,
                              is_published=False, content_id=f"{item.content_id}#rule{n}")
            order += 1
            db.add(grammar)
            db.flush()
            created.append({"kind": "grammar", "id": str(grammar.id)})
        for n, ex in enumerate(preview["exercises"], start=1):
            created.append(_add_exercise(db, lesson_id, SKILL_GRAMMATIK, ex, f"{item.content_id}#ex{n}"))
    elif item.skill == "wortschatz":
        order = _next_order(db, Vocabulary, lesson_id)
        new_words = []
        fresh = {id(w) for w in _new_words(db, lesson_id, item.words)}
        for n, w in enumerate(item.words, start=1):
            if id(w) not in fresh:
                continue
            vocab = Vocabulary(lesson_id=lesson_id, german_word=w.word, article=w.article, plural=w.plural, translation=w.translation,
                               example_sentence=w.example, example_translation=w.example_translation, order_index=order,
                               is_published=False, content_id=f"{item.content_id}#w{n}")
            order += 1
            db.add(vocab)
            db.flush()
            new_words.append(vocab)
            created.append({"kind": "word", "id": str(vocab.id)})
        for n, ex in enumerate(preview["exercises"], start=1):
            created.append(_add_exercise(db, lesson_id, SKILL_WORTSCHATZ, ex, f"{item.content_id}#ex{n}"))
        if item.auto_practice:
            for n, ex in enumerate(practice_sets(item.words, f"Wortschatz-Übung: {item.title}"), start=1):
                created.append(_add_exercise(db, lesson_id, SKILL_WORTSCHATZ, ex, f"{item.content_id}#auto{n}"))
    elif item.skill in EXERCISE_ITEM_SKILLS:
        for n, ex in enumerate(preview["exercises"], start=1):
            created.append(_add_exercise(db, lesson_id, EXERCISE_ITEM_SKILLS[item.skill], ex, f"{item.content_id}#ex{n}"))
    elif item.skill == "kompetenz":
        from app.services.lms import structure

        structure.ensure_competencies(db, db.get(Lesson, lesson_id))
        row = _competency_row(db, lesson_id, item.competency)
        if row is not None and not (row.body or "").strip():
            row.body = preview["html"]
            db.flush()
            created.append({"kind": "competency", "id": str(row.id)})
    else:  # yakuniy
        ex = {"title": item.title, "instruction": item.instruction, "source": item.source, "questions": preview["questions"]}
        created.append(_add_exercise(db, lesson_id, SKILL_YAKUNIY, ex, f"{item.content_id}#ex1"))
    return created


def commit_document(
    db: Session, document, actor: User | None, filename: str | None, create_missing: bool = False, skip_existing: bool = False
) -> ContentImport:
    report = validate_document(db, document, create_missing, skip_existing)
    if report["errors"]:
        raise HTTPException(status_code=422, detail="; ".join(report["errors"]))
    language = str(document.get("language") or "de")
    cache: dict = {}
    items_out = []
    for r in report["items"]:
        entry = {"index": r["index"], "content_id": r["content_id"], "skill": r["skill"], "level": r["level"], "title": r["title"],
                 "source": r.get("source"), "errors": list(r["errors"]), "warnings": list(r["warnings"]), "status": "error",
                 "created": [], "published": False}
        item = r["_item"]
        if r["skip"] and not r["errors"]:
            entry["status"] = "skipped"
            entry["skip"] = r["skip"]
            entry["lesson_id"] = (r["target"] or {}).get("lesson_id")
        elif r["valid"] and item is not None:
            target = _resolve_target(db, language, item, create_missing, cache)
            savepoint = db.begin_nested()
            try:
                entry["created"] = _create(db, item, r, target, skip_existing)
                savepoint.commit()
                entry["status"] = "created" if entry["created"] else "skipped"
                if not entry["created"]:
                    entry["skip"] = "alles bereits vorhanden"
                entry["lesson_id"] = target["lesson_id"]
                if item.skill == "hoeren":
                    entry["audio_hint"] = item.audio_file or item.audio_asset_id
            except Exception as exc:  # noqa: BLE001 — reported per item, the batch goes on
                savepoint.rollback()
                cache.pop((language, item.level, item.module, item.lesson), None)
                entry["errors"].append(f"Anlegen fehlgeschlagen: {type(exc).__name__}")
        items_out.append(entry)
    batch = ContentImport(
        actor_id=actor.id if actor else None, filename=(filename or "")[:255] or None, schema_version=SCHEMA_VERSION,
        levels=sorted({i["level"] for i in items_out if i["level"] in levels.LEVELS}),
        total_items=len(items_out), created_items=sum(i["status"] == "created" for i in items_out),
        failed_items=sum(i["status"] == "error" for i in items_out), items=items_out,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


# ============================================================
# Publish (after admin review)
# ============================================================

_KIND_MODEL = {
    "reading": Reading,
    "listening": Listening,
    "writing": Writing,
    "speaking": Speaking,
    "grammar": Grammar,
    "word": Vocabulary,
    "exercise": SkillExercise,
    "competency": LessonCompetency,
}


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
            if created["kind"] in ("listening", "exercise") and any(not has_key(q) for q in row.questions):
                problems.append("KEY_REQUIRED")
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
    items = batch.items or []
    out = {
        "id": batch.id, "filename": batch.filename, "schema_version": batch.schema_version, "levels": batch.levels or [],
        "total_items": batch.total_items, "created_items": batch.created_items, "failed_items": batch.failed_items,
        "skipped_items": sum(1 for i in items if i.get("status") == "skipped"),
        "published_items": sum(1 for i in items if i.get("published")),
        "created_at": batch.created_at, "published_at": batch.published_at,
    }
    if with_items:
        out["items"] = items
    return out
