"""Answer keys of the Multilevel Modelltests (Lesen / Hören): read as a numbered table, import from text ("1-b, 2-b, 3-R …"), edit, validate.

The scoring truth stays where the exam engine already reads it: `MockQuestionOption.is_correct` (multilevel_exam_service._grade_auto). This module only
translates between that and what the owner writes — a letter per question — and keeps the token exactly as typed in `MockQuestion.answer_key`
("R" stays "R", "b" stays "b"). Matching is case-insensitive. If another editor later changes the option flags so that the stored token no longer
points at the marked option, the table shows the key derived from the flags instead (source "derived") — the token is never trusted over the flags.

Letter → option, per question (the question numbers are the running numbers of the section: 1 … N over all Teile, in Teil / question order):
- SINGLE_CHOICE / MATCHING / DROPDOWN: a, b, c … = the 1st, 2nd, 3rd … option (a–c for three answers, a–h for the eight matching letters A–H);
- TRUE_FALSE: r = Richtig, f = Falsch (the option whose text starts with that letter); a / b = the 1st / 2nd option (the owner's Variante 1 writes a / b);
- anything else (multiple choice, ordering, free text) is refused: this tool sets exactly one correct option.

Rules: a whole key set must cover every question and nothing beyond (`require_complete`), so a wrong count can never be saved by accident; a single
edit may change one question. Everything is all-or-nothing in one transaction and goes to the audit log (no personal data). Only Multilevel tests.
"""

from __future__ import annotations

import re
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.models.kompetenz import Kompetenz
from app.models.listening_content import ListeningContent
from app.models.mock_question import TYPE_DROPDOWN, TYPE_MATCHING, TYPE_SINGLE_CHOICE, TYPE_TRUE_FALSE, MockQuestion
from app.models.mock_test_attempt import MockTestAttempt
from app.models.model_test import ModelTest
from app.models.reading_content import ReadingContent
from app.models.teil import Teil
from app.models.user import User
from app.services.mock_exam import multilevel_service
from app.services.mock_exam.multilevel_exam_service import is_multilevel_test

SECTIONS = ("LESEN", "HOEREN")
LETTER_TYPES = {TYPE_SINGLE_CHOICE, TYPE_MATCHING, TYPE_DROPDOWN, TYPE_TRUE_FALSE}
MAX_TEXT = 4000
# "12-b", "12 - B", "12:b", "12) c", "12=r" — one letter, not part of a longer word
_ENTRY = re.compile(r"(?<![\dA-Za-z])(\d{1,3})\s*[-–—:.)=]\s*([A-Za-z])(?![A-Za-z0-9])")


def _err(code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


# ============================================================
# Pure helpers
# ============================================================


def parse_text(text: str) -> tuple[dict[int, str], list[dict]]:
    """"1-b, 2-b … 35-b" (commas, semicolons, spaces or one per line) → ({1: "b", …}, errors). Tokens keep their case."""
    text = text or ""
    entries: dict[int, str] = {}
    errors: list[dict] = []
    for m in _ENTRY.finditer(text):
        number = int(m.group(1))
        if number in entries:
            errors.append({"number": number, "code": "DUPLICATE", "message": f"Nr. {number} steht mehrmals in der Liste."})
        else:
            entries[number] = m.group(2)
    leftover = [t for t in re.split(r"[\s,;|]+", _ENTRY.sub(" ", text)) if t]
    for t in leftover[:10]:
        errors.append({"number": None, "code": "UNREADABLE", "message": f"„{t[:20]}“ ist kein Eintrag wie 12-b."})
    return entries, errors


def _option_index(q: MockQuestion, token: str) -> int:
    """Index of the option a letter selects; KeyError when this question has no such option."""
    letter = (token or "").strip().lower()
    if len(letter) != 1 or not letter.isalpha() or q.question_type not in LETTER_TYPES:
        raise KeyError(token)
    if q.question_type == TYPE_TRUE_FALSE:
        for i, o in enumerate(q.options):
            if letter in ("r", "f") and (o.option_text or "").strip().lower()[:1] == letter:
                return i
        if letter in ("a", "b") and ord(letter) - 97 < len(q.options):
            return ord(letter) - 97
        raise KeyError(token)
    index = ord(letter) - 97
    if 0 <= index < len(q.options):
        return index
    raise KeyError(token)


def _correct_index(q: MockQuestion) -> int | None:
    marked = [i for i, o in enumerate(q.options) if o.is_correct]
    return marked[0] if len(marked) == 1 else None


def canonical_key(q: MockQuestion) -> str | None:
    """The key derived from the option flags: R / F for true-false, A, B, C … otherwise; None when no or several options are marked."""
    i = _correct_index(q)
    if i is None:
        return None
    if q.question_type == TYPE_TRUE_FALSE:
        first = (q.options[i].option_text or "").strip()[:1].upper()
        if first in ("R", "F"):
            return first
    return chr(65 + i) if i < 26 else None


def effective_key(q: MockQuestion) -> tuple[str | None, str | None]:
    """(token, source): the token as typed when it still points at the marked option ("entered"), else the derived one ("derived"), else (None, None)."""
    derived = canonical_key(q)
    stored = (q.answer_key or "").strip()
    if stored and derived is not None:
        try:
            if _option_index(q, stored) == _correct_index(q):
                return stored, "entered"
        except KeyError:
            pass
    return derived, ("derived" if derived else None)


def _label(q: MockQuestion) -> str:
    return (q.question_text or "").split(".", 1)[0].strip()[:12]


# ============================================================
# Database
# ============================================================


def _test(db: Session, model_test_id: UUID, section: str) -> ModelTest:
    test = db.get(ModelTest, model_test_id)
    if test is None:
        raise _err(404, "MODEL_TEST_NOT_FOUND")
    if not is_multilevel_test(db, test):
        raise _err(404, "NOT_A_MULTILEVEL_TEST")
    if section not in SECTIONS:
        raise _err(422, "UNKNOWN_SECTION")
    return test


def _questions(db: Session, model_test_id: UUID, section: str) -> list[tuple[MockQuestion, Teil]]:
    content = ReadingContent if section == "LESEN" else ListeningContent
    link = MockQuestion.reading_content_id if section == "LESEN" else MockQuestion.listening_content_id
    stmt = (select(MockQuestion, Teil).join(content, link == content.id).join(Teil, content.teil_id == Teil.id)
            .join(Kompetenz, Teil.kompetenz_id == Kompetenz.id).where(Kompetenz.model_test_id == model_test_id, Kompetenz.type == section)
            .order_by(Teil.sort_order, MockQuestion.sort_order))
    return [(q, teil) for q, teil in db.execute(stmt).all()]


def key_table(db: Session, model_test_id: UUID, section: str = "HOEREN") -> dict:
    """The numbered key table of one section plus what still blocks publishing."""
    test = _test(db, model_test_id, section)
    rows = _questions(db, model_test_id, section)
    items = []
    for number, (q, teil) in enumerate(rows, start=1):
        token, source = effective_key(q)
        i = _correct_index(q)
        items.append({"number": number, "question_id": q.id, "label": _label(q), "teil": teil.title, "type": q.question_type, "option_count": len(q.options),
                      "answer": token, "source": source, "option_text": (q.options[i].option_text or "")[:80] if i is not None else None,
                      "editable": q.question_type in LETTER_TYPES})
    attempts = db.scalar(select(func.count()).select_from(MockTestAttempt).where(MockTestAttempt.model_test_id == model_test_id)) or 0
    r = multilevel_service.readiness(db, model_test_id)
    return {"model_test_id": test.id, "title": test.title, "number": test.sort_order, "status": test.status, "section": section,
            "question_count": len(items), "keys_set": sum(1 for x in items if x["answer"]), "complete": bool(items) and all(x["answer"] for x in items),
            "attempts": attempts, "items": items,
            "readiness": {"ready": r["ready"], "questions": r["questions"], "keys_set": r["keys_set"], "missing_keys": r["missing_keys"],
                          "missing_audio": r["missing_audio"], "missing_sections": r["missing_sections"]}}


def validate(rows: list[tuple[MockQuestion, Teil]], entries: dict[int, str], require_complete: bool) -> dict:
    """Checks a set of {number: letter} against the section's questions. Nothing is changed."""
    expected = len(rows)
    errors: list[dict] = []
    resolved: dict[int, tuple[MockQuestion, int, str]] = {}
    for number in sorted(entries):
        token = entries[number]
        if not 1 <= number <= expected:
            errors.append({"number": number, "code": "NO_SUCH_QUESTION", "message": f"Nr. {number}: Diese Frage gibt es nicht (das Teil hat {expected} Fragen)."})
            continue
        q = rows[number - 1][0]
        try:
            resolved[number] = (q, _option_index(q, token), token)
        except KeyError:
            if q.question_type not in LETTER_TYPES:
                errors.append({"number": number, "code": "TYPE_NOT_SUPPORTED", "message": f"Nr. {number}: Fragetyp {q.question_type} wird hier nicht unterstützt."})
            else:
                n = len(q.options)
                errors.append({"number": number, "code": "INVALID_ANSWER",
                               "message": f"Nr. {number}: „{token}“ ist keine gültige Antwort (erlaubt: a–{chr(96 + n)}"
                                          + (", r, f" if q.question_type == TYPE_TRUE_FALSE else "") + ")."})
    missing = [n for n in range(1, expected + 1) if n not in entries]
    if require_complete and missing:
        shown = ", ".join(str(n) for n in missing[:12]) + (" …" if len(missing) > 12 else "")
        errors.append({"number": None, "code": "COUNT_MISMATCH", "message": f"{len(entries)} Antworten für {expected} Fragen: es fehlen {len(missing)} (Nr. {shown})."})
    return {"expected": expected, "given": len(entries), "missing": missing, "errors": errors, "resolved": resolved}


def _summary(errors: list[dict]) -> str:
    return "; ".join(e["message"] for e in errors[:4]) + (f"; … (+{len(errors) - 4})" if len(errors) > 4 else "")


def apply_keys(db: Session, actor: User | None, model_test_id: UUID, section: str, entries: dict[int, str], *, require_complete: bool = False,
               source: str = "admin") -> dict:
    """Sets the keys (all or nothing). 422 INVALID_KEYS lists what is wrong; on success the fresh table is returned."""
    test = _test(db, model_test_id, section)
    rows = _questions(db, model_test_id, section)
    if not rows:
        raise _err(409, "NO_QUESTIONS: this section has no questions")
    if not entries:
        raise _err(422, "INVALID_KEYS: keine Antworten übergeben.")
    check = validate(rows, entries, require_complete)
    if check["errors"]:
        raise _err(422, "INVALID_KEYS: " + _summary(check["errors"]))
    changed = 0
    try:
        for number, (q, index, token) in check["resolved"].items():
            if _correct_index(q) != index:
                changed += 1
            for i, o in enumerate(q.options):
                o.is_correct = i == index
            q.answer_key = token
        db.commit()
    except Exception:
        db.rollback()
        raise
    write_audit(db, actor_id=actor.id if actor else None, action="multilevel_answer_keys",
                details=f"{test.title} {section}: {len(entries)} of {len(rows)} answers, {changed} changed ({source})")
    return key_table(db, model_test_id, section)


def import_text(db: Session, actor: User | None, model_test_id: UUID, section: str, text: str, *, dry_run: bool = True) -> dict:
    """Reads "1-b, 2-b, …", checks it against the section (count included) and — unless dry_run — saves it when it is fully valid."""
    if len(text or "") > MAX_TEXT:
        raise _err(422, "TEXT_TOO_LONG")
    _test(db, model_test_id, section)
    rows = _questions(db, model_test_id, section)
    entries, parse_errors = parse_text(text)
    check = validate(rows, entries, require_complete=True)
    errors = parse_errors + check["errors"]
    out = {"section": section, "expected": check["expected"], "given": len(entries), "ok": not errors and bool(entries), "errors": errors, "applied": False,
           "preview": [{"number": n, "answer": entries[n], "option_text": (check["resolved"][n][0].options[check["resolved"][n][1]].option_text or "")[:60]}
                       for n in sorted(check["resolved"])]}
    if out["ok"] and not dry_run:
        table = apply_keys(db, actor, model_test_id, section, entries, require_complete=True, source="import")
        out.update(applied=True, table=table)
    return out
