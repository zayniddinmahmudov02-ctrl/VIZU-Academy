"""CSV export / import of a lesson's Wortschatz words (admin).

Columns: COLUMNS below; `id` empty = new word. Export is UTF-8 with BOM (Excel)
and neutralises formula cells (a leading = + - @ gets a ' prefix, removed
again on import). Import validates every row with the word editor's own
rules (exercises._word_fields); one bad row and nothing is written. Words are
matched by id within the lesson only; nothing is ever deleted."""

import csv
import hashlib
import io
from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vocabulary import Vocabulary
from app.services.lesson_skills import exercises
from app.services.lesson_skills.wortschatz import missing_fields

COLUMNS = ["id", "german_word", "article", "plural", "translation", "word_type", "verb_praeteritum", "verb_partizip_ii",
           "verb_auxiliary", "example_sentence", "example_translation", "order_index", "is_published"]
EXPORT_ONLY = ["missing"]
MAX_BYTES = 1_000_000
MAX_ROWS = 2000
ALLOWED_TYPES = {"text/csv", "application/vnd.ms-excel", "text/plain", "application/octet-stream", ""}
FORMULA = ("=", "+", "-", "@")


def _cell(value) -> str:
    text = "" if value is None else str(value)
    return "'" + text if text.startswith(FORMULA) else text


def _uncell(value: str | None) -> str:
    text = (value or "").strip()
    return text[1:] if len(text) > 1 and text[0] == "'" and text[1] in FORMULA else text


def export_csv(db: Session, lesson_id: UUID) -> bytes:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    writer.writerow(COLUMNS + EXPORT_ONLY)
    for v in db.scalars(select(Vocabulary).where(Vocabulary.lesson_id == lesson_id).order_by(Vocabulary.order_index, Vocabulary.created_at)):
        row = [_cell(getattr(v, c)) for c in COLUMNS]
        row[COLUMNS.index("is_published")] = "1" if v.is_published else "0"
        writer.writerow(row + [" ".join(missing_fields(v))])
    return ("﻿" + out.getvalue()).encode("utf-8")


async def read_upload(file: UploadFile) -> bytes:
    name = (file.filename or "").lower()
    if not name.endswith(".csv") or (file.content_type or "").split(";")[0].strip().lower() not in ALLOWED_TYPES:
        raise HTTPException(status_code=422, detail="CSV_REQUIRED: only .csv files")
    raw = await file.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="CSV_TOO_LARGE: max 1 MB")
    if b"\x00" in raw:
        raise HTTPException(status_code=422, detail="CSV_INVALID: binary content")
    return raw


def _rows(raw: bytes) -> list[dict]:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="CSV_INVALID: file must be UTF-8") from None
    reader = csv.DictReader(io.StringIO(text))
    header = [h.strip() for h in (reader.fieldnames or [])]
    missing = [c for c in ("german_word", "translation") if c not in header]
    if missing:
        raise HTTPException(status_code=422, detail=f"CSV_INVALID: missing columns {', '.join(missing)}")
    rows = []
    for n, row in enumerate(reader, start=2):
        if n - 1 > MAX_ROWS:
            raise HTTPException(status_code=422, detail=f"CSV_INVALID: max {MAX_ROWS} rows")
        clean = {k.strip(): _uncell(v) for k, v in row.items() if k and k.strip() in COLUMNS}
        if not any(clean.values()):
            continue
        rows.append({"line": n, **clean})
    return rows


def import_csv(db: Session, lesson_id: UUID, raw: bytes, apply: bool) -> dict:
    rows = _rows(raw)
    existing = {str(v.id): v for v in db.scalars(select(Vocabulary).where(Vocabulary.lesson_id == lesson_id))}
    errors, plan = [], []
    for row in rows:
        word_id = row.pop("id", "") or None
        line = row.pop("line")
        if word_id and word_id not in existing:
            errors.append(f"line {line}: id {word_id} is not a word of this lesson")
            continue
        current = existing.get(word_id) if word_id else None
        data = {k: v for k, v in row.items() if k in COLUMNS}
        # a column left out (or empty order) keeps the word's current value
        published = str(data.get("is_published") or "").strip().lower()
        data["is_published"] = (bool(current.is_published) if current else True) if not published else published not in ("0", "false", "nein", "no")
        if not data.get("order_index"):
            data.pop("order_index", None)
            if current is not None:
                data["order_index"] = current.order_index
        else:
            try:
                data["order_index"] = int(data["order_index"])
            except ValueError:
                errors.append(f"line {line}: order_index must be a number")
                continue
        try:
            fields = exercises._word_fields(data)
        except HTTPException as exc:
            errors.append(f"line {line}: {exc.detail}")
            continue
        if current is not None:
            changed = sorted(k for k, v in fields.items() if getattr(current, k) != v)
            plan.append({"line": line, "action": "update" if changed else "unchanged", "id": word_id, "word": fields["german_word"],
                         "changed": changed, "data": data})
        else:
            plan.append({"line": line, "action": "create", "id": None, "word": fields["german_word"], "changed": [], "data": data})
    report = {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "rows": len(rows),
        "created": sum(1 for p in plan if p["action"] == "create"),
        "updated": sum(1 for p in plan if p["action"] == "update"),
        "unchanged": sum(1 for p in plan if p["action"] == "unchanged"),
        "errors": errors,
        "applied": False,
        "items": [{k: p[k] for k in ("line", "action", "id", "word", "changed")} for p in plan],
    }
    if errors or not apply:
        return report
    for p in plan:
        if p["action"] == "create":
            exercises.save_word(db, lesson_id, p["data"], commit=False)
            db.flush()
        elif p["action"] == "update":
            exercises.save_word(db, None, p["data"], UUID(p["id"]), commit=False)
    db.commit()
    report["applied"] = True
    return report
