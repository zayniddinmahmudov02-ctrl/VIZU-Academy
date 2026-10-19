"""A1 Hören: answer keys checked against the audio (audit 2026-10-19).

Every A1 Hören task (lessons 1-14) was compared with its audio file. Sources
per answer, in this order of weight:
  1. the audio itself — machine transcripts of the exact files stored on the
     server (same SHA-256), two independent speech models (Whisper large-v3
     and medium, CPU, language de), with timestamps;
  2. the book page of the task (VIZU-DEUTSCH A1, page in `page`);
  3. "Vizu-Javoblar A1.pdf" — the old answer sheet. It belongs to an older
     version of the course: where it contradicts the audio, the audio wins
     (e.g. L2 gap 1: the speaker says "Anna", the sheet "Peter").
An answer is written as VERIFIED only when the audio states it unambiguously
(both models agree, or the existing key / the sheet agrees with the audio);
anything else is written as NEEDS_REVIEW with the reason, for the admin to
decide in LMS -> Lösung after listening. Nothing is guessed.

The script never creates or deletes tasks or questions and never touches
attempts / scores. Per task it can: set the keys, correct a sentence of the
task text or the word list where it contradicts the audio (`text_fixes`,
`instruction`), record the verification (answer_key_reviews, note = source),
replace the audio (`audio_parts`: several book files joined in order), then
publish the task when every key is verified and the audio file exists — or
set it back to draft when it is published without that.

    python -m app.scripts.a1_hoeren_keys                 # dry run: prints the plan
    python -m app.scripts.a1_hoeren_keys --apply [--audio-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm.attributes import flag_modified

from app.core.audit import write_audit
from app.db.session import SessionLocal
from app.models.answer_key_review import REVIEW_NEEDS_REVIEW, REVIEW_VERIFIED, AnswerKeyReview
from app.models.lesson_skill import CONFIG_TYPES
from app.services.lesson_skills import hoeren_pdf_import as a1, loesung
from app.services.lesson_skills.admin import admin_question, listening_audio_path, validate_questions
from app.services.lesson_skills.question_types import GAP_PATTERN

TR = "Audio-Transkript (Whisper large-v3 + medium)"

# key per question, in question order:
#   Multiple Choice / Richtig-Falsch: the text of the correct option
#   Lückentext: {gap id: [accepted answers]}
# `review`: {question number (1-based): note} -> NEEDS_REVIEW instead of VERIFIED
from app.scripts.a1_hoeren_keys_data import TASKS  # noqa: E402


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _time_variants(t: str) -> list[str]:
    """'8' -> 8, 08, 8:00, 08:00, 8.00 · '8:30' -> 8:30, 08:30, 8.30, 08.30."""
    h, _, m = t.partition(":")
    h, m = int(h), (m or "00")
    out = [f"{h}:{m}", f"{h:02d}:{m}", f"{h}.{m}", f"{h:02d}.{m}"]
    if m == "00":
        out = [str(h), f"{h:02d}"] + out
    seen = []
    for v in out:
        if v not in seen:
            seen.append(v)
    return seen


def expand(spec) -> list[str]:
    if isinstance(spec, dict) and "time" in spec:
        return _time_variants(spec["time"])
    return list(spec)


def plan_task(lst, spec: dict) -> dict:
    """What would change for one task — raises ValueError when the stored
    questions do not have the structure the key was made for."""
    questions = loesung._sorted_questions(lst)
    keys = spec["keys"]
    if len(questions) != len(keys):
        raise ValueError(f"{len(questions)} Fragen gespeichert, Schlüssel für {len(keys)}")
    changes = []
    for n, (q, key) in enumerate(zip(questions, keys), start=1):
        item = admin_question(q)
        item = {**item, "id": str(item["id"]), "options": [{**o, "id": str(o["id"])} for o in item["options"]]}
        before = json.dumps(loesung._key_only(item), ensure_ascii=False, sort_keys=True, default=str)
        for old, new in spec.get("text_fixes", {}).get(n, []):
            target = item["config"]["text"] if q.question_type == "GAP_FILL" else item["question"]
            if new in target:
                continue  # already corrected (re-run) — `new` may contain `old`, never apply twice
            if old not in target:
                raise ValueError(f"Frage {n}: Textstelle „{old}“ nicht gefunden")
            if q.question_type == "GAP_FILL":
                item["config"] = {**item["config"], "text": target.replace(old, new, 1)}
            else:
                item["question"] = target.replace(old, new, 1)
        if q.question_type in ("MULTIPLE_CHOICE", "TRUE_FALSE"):
            hits = [o for o in item["options"] if o["text"].strip().casefold() == str(key).strip().casefold()]
            if len(hits) != 1:
                raise ValueError(f"Frage {n}: Option „{key}“ nicht eindeutig vorhanden ({[o['text'] for o in item['options']]})")
            for o in item["options"]:
                o["is_correct"] = o is hits[0]
        elif q.question_type == "GAP_FILL":
            config = dict(item["config"] or {})
            ids = GAP_PATTERN.findall(config.get("text") or "")
            if sorted(ids, key=int) != sorted(key, key=int):
                raise ValueError(f"Frage {n}: Lücken {ids} ≠ Schlüssel {sorted(key)}")
            gaps = dict(config.get("gaps") or {})
            for gid in ids:
                g = gaps.get(gid)
                g = dict(g) if isinstance(g, dict) else {}
                g["accepted"] = expand(key[gid])
                if g.get("options") and not any(a.casefold() == o.casefold() for a in g["accepted"] for o in g["options"]):
                    raise ValueError(f"Frage {n}, Lücke {gid}: „{g['accepted'][0]}“ ist keine der Auswahloptionen")
                gaps[gid] = g
            config["gaps"] = gaps
            config.pop("pending", None)
            item["config"] = config
        else:
            raise ValueError(f"Frage {n}: Typ {q.question_type} nicht vorgesehen")
        clean = validate_questions([item])[0]  # same rules as the editor
        after = json.dumps(loesung._key_only(clean), ensure_ascii=False, sort_keys=True, default=str)
        note = spec.get("review", {}).get(n)
        changes.append({"question": q, "number": n, "clean": clean, "changed": before != after, "before": before, "after": after,
                        "status": REVIEW_NEEDS_REVIEW if note else REVIEW_VERIFIED, "note": note or spec["evidence"]})
    return {"questions": changes}


def apply_question(db, q, c: dict) -> None:
    clean = c["clean"]
    q.question = clean["question"]
    if q.question_type in CONFIG_TYPES:
        q.config = clean["config"]
        flag_modified(q, "config")
    else:
        by_id = {str(o.id): o for o in q.options}
        for o in clean["options"]:
            row = by_id[str(o["id"])]
            row.option_text, row.is_correct = o["text"], o["is_correct"]
    db.flush()
    db.refresh(q)
    review = loesung._reviews(db, "hoeren", [q.id]).get(q.id)
    if review is None:
        review = AnswerKeyReview(listening_question_id=q.id, status=c["status"])
        db.add(review)
    review.status = c["status"]
    review.key_fingerprint = loesung.fingerprint(q) if c["status"] == REVIEW_VERIFIED else None
    review.note = c["note"][:2000]
    review.reviewed_by = None  # system audit (source in the note)
    review.reviewed_at = _now()


def audio_name(parts: list[str]) -> str:
    """Stored name after the replacement: the file itself, or 'A1-14.mp3' for A1-14.1.mp3 + A1-14.2.mp3."""
    return parts[0] if len(parts) == 1 else re.sub(r"\.\d+$", "", Path(parts[0]).stem) + ".mp3"


def replace_audio(db, lst, parts: list[Path]) -> str:
    """Joins the book files in order (ffmpeg) and uploads the result through
    the regular upload (type detection, private storage, old file removed)."""
    import asyncio
    import tempfile

    from starlette.datastructures import Headers, UploadFile

    from app.scripts.import_vizu_deutsch_a1 import _audio_duration, _concat_audio
    from app.services.lesson_skills import admin as skill_admin

    with tempfile.TemporaryDirectory() as tmp:
        if len(parts) == 1:  # the right book file as it is
            out = parts[0]
        else:
            out = Path(tmp) / audio_name([p.name for p in parts])
            _concat_audio(parts, out)
        ctype = "audio/mp4" if out.suffix.lower() == ".m4a" else "audio/mpeg"
        with open(out, "rb") as fh:
            upload = UploadFile(fh, filename=out.name, headers=Headers({"content-type": ctype}))
            asyncio.run(skill_admin.upload_listening_audio(db, lst.id, upload, _audio_duration(out)))
    db.refresh(lst)
    return lst.audio_original_name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="write (default: dry run)")
    parser.add_argument("--audio-dir", help="folder with the book audio files (only for tasks with audio_parts)")
    parser.add_argument("--no-publish", action="store_true", help="do not change the publish state")
    args = parser.parse_args()

    db = SessionLocal()
    failed = 0
    report = []
    try:
        tasks = {lst.content_id: (n, lst) for n, lesson in a1.a1_lessons(db).items() for lst in a1.lesson_listenings(db, lesson.id)}
        for cid, spec in TASKS.items():
            if cid not in tasks:
                print(f"\n{cid}: Aufgabe fehlt — übersprungen")
                failed += 1
                continue
            n, lst = tasks[cid]
            print(f"\nL{n} {lst.title}  [{cid}]  veröffentlicht={lst.is_published}")
            try:
                plan = plan_task(lst, spec)
            except (ValueError, HTTPException) as exc:
                print(f"  FEHLER: {getattr(exc, 'detail', exc)} — nichts geändert")
                failed += 1
                continue
            for c in plan["questions"]:
                mark = "Ä" if c["changed"] else "="
                print(f"  {mark} Frage {c['number']}: {c['status']}" + (f"  ({c['note']})" if c["status"] != REVIEW_VERIFIED else ""))
                if c["changed"]:
                    print(f"      vorher: {c['before'][:300]}\n      nachher: {c['after'][:300]}")
            if spec.get("instruction") and spec["instruction"] != lst.instruction:
                print(f"  Ä Anweisung: {spec['instruction'][:200]}")
            parts = spec.get("audio_parts")
            if parts and lst.audio_original_name == audio_name(parts) and listening_audio_path(lst) is not None:
                parts = None  # already done
            if parts:
                print(f"  Ä Audio: {' + '.join(parts)}  (bisher {lst.audio_original_name})")
            if not args.apply:
                continue
            before_task = {"instruction": lst.instruction, "audio": lst.audio_original_name, "published": lst.is_published}
            for c in plan["questions"]:
                apply_question(db, c["question"], c)
            if spec.get("instruction"):
                lst.instruction = spec["instruction"]
            db.commit()
            if parts:
                if not args.audio_dir:
                    print("  Audio NICHT ersetzt: --audio-dir fehlt")
                    failed += 1
                else:
                    paths = [Path(args.audio_dir) / p for p in parts]
                    missing = [p.name for p in paths if not p.is_file()]
                    if missing:
                        print(f"  Audio NICHT ersetzt: Datei fehlt {missing}")
                        failed += 1
                    else:
                        print(f"  -> Audio ersetzt: {replace_audio(db, lst, paths)}")
            db.refresh(lst)
            state = a1.readiness(db, lst)
            if not args.no_publish:
                if state["ready"] and not lst.is_published:
                    lst.is_published = True
                elif not state["ready"] and lst.is_published:
                    lst.is_published = False  # only verified keys are shown to students
                db.commit()
            print(f"  -> {'veröffentlicht' if lst.is_published else 'Entwurf'}" + ("" if state["ready"] else f" ({', '.join(state['reasons'])})"))
            write_audit(db, None, "a1_hoeren_keys_verified", details=json.dumps({
                "task": str(lst.id), "content_id": cid, "before": before_task, "published": lst.is_published,
                "questions": [{"n": c["number"], "status": c["status"], "changed": c["changed"], "before": c["before"][:600], "after": c["after"][:600]}
                              for c in plan["questions"]]}, ensure_ascii=False)[:8000])
            report.append({"content_id": cid, "published": lst.is_published, **state})
    finally:
        db.close()
    if args.apply:
        print("\nErgebnis:", json.dumps(report, ensure_ascii=False, default=str))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
