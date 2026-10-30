"""A2 audio processing (lessons 1-13): transcript of every Hören audio, its
match with the task, the verification of the task's answer keys and the
publish state — one pipeline status per task, shown in Admin -> Media
Management -> A2 -> Audio-Verarbeitung.

Pipeline status of a task (first that applies):
  FAILED               an audio file is missing on the server, or its transcription failed
  UPLOADED             an audio file has no transcript yet (new upload)
  TRANSCRIBING         transcription is running
  NEEDS_REVIEW         transcript or match needs a person, or a key is marked NEEDS_REVIEW
  TRANSCRIBED          transcribed, not compared with the task yet
  PUBLISHED            visible to students
  ANSWER_KEY_VERIFIED  every key verified in Lösung (or an audio-only task), not published
  MATCHED              audio belongs to the task, keys not (all) verified yet

Transcripts are keyed by the file CONTENT (SHA-256, a2_audio_transcripts):
identical bytes are never transcribed twice. The transcription itself runs
offline (faster-whisper, app/scripts/a2_audio_processing.py imports the
result); nothing here calls a speech service."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.a2_audio_asset import A2AudioAsset
from app.models.a2_audio_transcript import (
    MATCH_MATCHED,
    MATCH_MISMATCH,
    MATCH_NEEDS_REVIEW,
    STATUS_FAILED,
    STATUS_NEEDS_REVIEW,
    STATUS_TRANSCRIBING,
    A2AudioTranscript,
)
from app.services.a2_audio import assets
from app.services.lesson_skills import loesung
from app.services.lesson_skills.admin import admin_question, listening_audio_path, track_audio_path

LESSONS = range(1, 14)
UPLOADED, TRANSCRIBING, TRANSCRIBED = "UPLOADED", "TRANSCRIBING", "TRANSCRIBED"
MATCHED, KEYS_VERIFIED, PUBLISHED = "MATCHED", "ANSWER_KEY_VERIFIED", "PUBLISHED"
NEEDS_REVIEW, FAILED = "NEEDS_REVIEW", "FAILED"
PIPELINE = (UPLOADED, TRANSCRIBING, TRANSCRIBED, MATCHED, KEYS_VERIFIED, PUBLISHED, NEEDS_REVIEW, FAILED)


def task_files(task) -> list[dict]:
    """The task's audio files in playing order: main audio, then the extra tracks."""
    files = []
    if task.audio_storage_path:
        files.append({"slot": "main", "label": task.audio_label, "storage_path": task.audio_storage_path, "name": task.audio_original_name,
                      "size_bytes": task.audio_size_bytes, "duration_seconds": task.audio_duration_seconds,
                      "on_disk": listening_audio_path(task) is not None})
    for t in task.audio_tracks:
        if t.storage_path:
            files.append({"slot": str(t.id), "label": t.label, "storage_path": t.storage_path, "name": t.original_name, "size_bytes": t.size_bytes,
                          "duration_seconds": t.duration_seconds, "on_disk": track_audio_path(t) is not None})
    return files


def transcripts_by_path(db: Session) -> dict[str, A2AudioTranscript]:
    out = {}
    for row in db.scalars(select(A2AudioTranscript)):
        for path in row.storage_paths or []:
            out[path] = row
    return out


def _questions(db: Session, task) -> tuple[list[dict], dict]:
    qs = loesung._sorted_questions(task)
    reviews = loesung._reviews(db, "hoeren", [q.id for q in qs])
    items, counts = [], {"total": len(qs), "verified": 0, "needs_review": 0, "missing": 0}
    for n, q in enumerate(qs, 1):
        state = loesung.question_state(q, reviews.get(q.id))
        a = admin_question(q)
        counts["verified"] += state["verified"] and not state["needs_review"]
        counts["needs_review"] += state["needs_review"]
        counts["missing"] += not state["has_key"]
        items.append({"number": n, "question": a["question"], "type": q.question_type,
                      "options": [{"text": o["text"], "is_correct": o["is_correct"]} for o in a["options"]],
                      "config": a.get("config"), "has_key": state["has_key"], "verified": state["verified"],
                      "needs_review": state["needs_review"], "note": state["note"]})
    return items, counts


def task_status(files: list[dict], rows: list, match: dict | None, counts: dict, published: bool) -> tuple[str, list[str]]:
    problems = []
    if not files:
        return FAILED, ["kein Audio"]
    if any(not f["on_disk"] for f in files):
        return FAILED, ["Audiodatei fehlt auf dem Server"]
    if any(r is not None and r.status == STATUS_FAILED for r in rows):
        return FAILED, ["Transkription fehlgeschlagen"]
    if any(r is None for r in rows):
        return UPLOADED, ["noch nicht transkribiert"]
    if any(r.status == STATUS_TRANSCRIBING for r in rows):
        return TRANSCRIBING, []
    if any(r.status == STATUS_NEEDS_REVIEW for r in rows):
        problems += [r.review_note or "Transkript prüfen" for r in rows if r.status == STATUS_NEEDS_REVIEW]
    if match and match.get("status") in (MATCH_NEEDS_REVIEW, MATCH_MISMATCH):
        problems.append(match.get("note") or "Zuordnung prüfen")
    if counts["needs_review"]:
        problems.append(f"{counts['needs_review']} Lösung(en) „Prüfung nötig“")
    if problems:
        return NEEDS_REVIEW, problems
    if not match:
        return TRANSCRIBED, []
    if published:
        return PUBLISHED, []
    if counts["missing"]:
        return MATCHED, [f"{counts['missing']} Frage(n) ohne Lösung"]
    if counts["verified"] < counts["total"]:
        return MATCHED, [f"{counts['total'] - counts['verified']} Lösung(en) nicht geprüft"]
    return KEYS_VERIFIED, []


def _transcript(row: A2AudioTranscript | None) -> dict | None:
    if row is None:
        return None
    return {"id": row.id, "sha256": row.sha256, "status": row.status, "model": row.model, "text": row.text, "segments": row.segments,
            "quality": row.quality, "review_note": row.review_note, "duration_seconds": row.duration_seconds, "updated_at": row.updated_at}


def overview(db: Session) -> dict:
    by_path = transcripts_by_path(db)
    lessons = {lesson.number: lesson for lesson in assets.a2_lessons(db)}
    tasks = [(t, lesson) for t, lesson in assets.a2_tasks(db, list(lessons.values())) if lesson.number in LESSONS]
    library = {a.listening_id: a for a in db.scalars(select(A2AudioAsset).where(A2AudioAsset.listening_id.is_not(None)))}
    out = {n: {"number": n, "title": lessons[n].title if n in lessons else None, "is_published": bool(n in lessons and lessons[n].is_published),
               "tasks": []} for n in LESSONS}
    for t, lesson in tasks:
        files = task_files(t)
        rows = [by_path.get(f["storage_path"]) for f in files]
        match = next((r.matches.get(str(t.id)) for r in rows if r is not None and (r.matches or {}).get(str(t.id))), None)
        questions, counts = _questions(db, t)
        status, problems = task_status(files, rows, match, counts, t.is_published)
        asset = library.get(t.id)
        out[lesson.number]["tasks"].append({
            "listening_id": t.id, "title": t.title, "content_id": t.content_id, "task_key": t.task_key, "is_published": t.is_published,
            "status": status, "problems": problems, "match": match, "keys": counts, "questions": questions,
            "student_transcript": bool((t.transcript or "").strip()),
            "library_verification": asset.verification if asset else None,
            "files": [{**{k: v for k, v in f.items() if k != "storage_path"}, "transcript": _transcript(r)} for f, r in zip(files, rows)],
        })
    all_tasks = [x for lesson in out.values() for x in lesson["tasks"]]
    by_status = {s: sum(1 for x in all_tasks if x["status"] == s) for s in PIPELINE}
    files = [f for x in all_tasks for f in x["files"]]
    return {
        "summary": {"tasks": len(all_tasks), "published": by_status[PUBLISHED], "by_status": by_status,
                    "audio_files": len(files), "transcribed": sum(1 for f in files if f["transcript"] and f["transcript"]["status"] != STATUS_TRANSCRIBING),
                    "unique_contents": len({f["transcript"]["sha256"] for f in files if f["transcript"]}),
                    "matched": sum(1 for x in all_tasks if (x["match"] or {}).get("status") == MATCH_MATCHED),
                    "keys_verified": sum(1 for x in all_tasks if x["keys"]["total"] and x["keys"]["verified"] == x["keys"]["total"]),
                    "percent_published": round(100 * by_status[PUBLISHED] / len(all_tasks)) if all_tasks else 0},
        "lessons": [{**lesson, "published_tasks": sum(1 for x in lesson["tasks"] if x["is_published"]), "task_count": len(lesson["tasks"])}
                    for lesson in out.values()],
    }
