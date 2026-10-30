"""A2 audio processing, lessons 1-13 (app/services/a2_audio/processing.py).

    python -m app.scripts.a2_audio_processing plan [--audio-dir DIR]
    python -m app.scripts.a2_audio_processing apply --confirm <plan id> [--audio-dir DIR] [--no-publish]

Per current A2 Hören task:
1. every stored audio file is hashed (SHA-256) and gets its transcript from
   app/data/a2_audio_transcripts.json — one row per content in
   a2_audio_transcripts; a content that already has a finished transcript is
   reused, never transcribed again;
2. the stored files must be exactly the files the keys were checked with
   (a2_audio_processing_data.TASKS[...]["audio"]) — otherwise nothing is
   applied and the task is NEEDS_REVIEW;
3. missing book files listed under `add_tracks` are added from --audio-dir
   (SHA-256 must match the transcribed file);
4. keys / corrections are written with the same functions as the A1 / A2
   audits (editor validation, Lösung VERIFIED or NEEDS_REVIEW + note);
5. the transcript is written into the task (shown to students after their
   first attempt, at once for a task without questions) — only a finished
   transcript and only where the task has none (a book transcript stays);
6. a task is published only when its audio file is on the server, the
   transcript belongs to it (MATCHED) and every key is verified (Hören
   publish rule); a Text slot (no questions) when its audio is verified.
Nothing is unpublished, no attempt or score is touched. Take a DB backup first."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import select

from app.core.audit import write_audit
from app.db.session import SessionLocal
from app.models.a2_audio_asset import VERIFY_OK, A2AudioAsset
from app.models.a2_audio_transcript import MATCH_MATCHED, MATCH_NEEDS_REVIEW, STATUS_TRANSCRIBED, A2AudioTranscript
from app.scripts.a1_hoeren_keys import apply_question, plan_task
from app.scripts.a2_audio_processing_data import TASKS
from app.scripts.a2_keys import plan_removals, record_reviews
from app.services.a2_audio import assets, lesson4_hoeren, processing
from app.services.lesson_skills import admin as skill_admin
from app.services.lesson_skills import hoeren_pdf_import, loesung

DATA = Path(__file__).resolve().parents[1] / "data" / "a2_audio_transcripts.json"
TRANSCRIPT_HEADER = "Transkript (automatisch aus dem Audio erstellt; unverständliche Stellen sind markiert)"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def nfc(name: str) -> str:
    """File names from macOS carry decomposed umlauts (NFD): compare in NFC."""
    return unicodedata.normalize("NFC", name)


def load_records(path: Path = DATA) -> tuple[dict, dict]:
    records = json.loads(path.read_text(encoding="utf-8"))["records"]
    return {r["sha256"]: r for r in records}, {nfc(r["original_name"]): r["sha256"] for r in records}


def find_file(folder: Path | None, name: str) -> Path | None:
    if folder is None or not folder.is_dir():
        return None
    return next((p for p in folder.iterdir() if p.is_file() and nfc(p.name) == nfc(name)), None)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _stored(rel: str) -> Path | None:
    return skill_admin._stored(rel)


def _spec(task, tasks: dict) -> tuple[str | None, dict | None]:
    for key in (task.task_key, task.content_id):
        if key and key in tasks:
            return key, tasks[key]
    return None, None


def plan(db, audio_dir: Path | None, records: dict, names: dict, tasks: dict | None = None) -> list[dict]:
    """Read-only: what apply would do for every current task of lessons 1-13."""
    tasks = TASKS if tasks is None else tasks
    out = []
    for task, lesson in assets.a2_tasks(db):
        if lesson.number not in processing.LESSONS:
            continue
        key, spec = _spec(task, tasks)
        files = processing.task_files(task)
        shas = [sha256(_stored(f["storage_path"])) if f["on_disk"] else None for f in files]
        item = {"lesson": lesson.number, "task": task, "key": key, "spec": spec, "files": files, "shas": shas, "actions": [], "problem": None,
                "add_tracks": []}
        if spec is None:
            item["problem"] = "keine Prüfdaten für diese Aufgabe"
            out.append(item)
            continue
        expected = [names.get(nfc(n)) for n in spec["audio"]]
        for t in spec.get("add_tracks", []):
            if any(f["label"] == t["label"] for f in files):
                continue
            src = find_file(audio_dir, t["file"])
            ok = bool(src and sha256(src) == names.get(nfc(t["file"])))
            item["add_tracks"].append({**t, "path": src, "ok": ok})
            if not ok:
                item["problem"] = f"Buchdatei „{t['file']}“ für die Spur „{t['label']}“ fehlt oder hat einen anderen Inhalt (--audio-dir)"
        have = shas + [names.get(nfc(t["file"])) for t in item["add_tracks"] if t["ok"]]
        if not item["problem"] and have != expected:
            item["problem"] = "die gespeicherten Audiodateien sind nicht die geprüften (SHA-256 weicht ab)"
        if not item["problem"] and any(h not in records for h in have):
            item["problem"] = "kein Transkript für eine der Audiodateien"
        item["have"] = have
        if not item["problem"] and spec["match"]["status"] == MATCH_MATCHED and not spec.get("audio_only"):
            try:
                if spec.get("verify_only"):
                    item["actions"].append("Lösung bestätigen (unverändert)")
                else:
                    removals = plan_removals(db, task, spec.get("remove_questions", []))
                    kept = [q for q in loesung._sorted_questions(task) if q not in removals]
                    item["removals"] = removals
                    item["key_plan"] = plan_task(SimpleNamespace(questions=kept), spec)
                    changed = sum(1 for c in item["key_plan"]["questions"] if c["changed"])
                    item["actions"].append(f"{len(item['key_plan']['questions'])} Lösungen prüfen/setzen ({changed} geändert)"
                                           + (f", {len(removals)} Frage(n) entfernen" if removals else ""))
            except (ValueError, HTTPException) as exc:
                item["problem"] = f"Fragenstruktur weicht ab: {getattr(exc, 'detail', exc)}"
        out.append(item)
    return out


def plan_id(items: list[dict]) -> str:
    data = [[str(i["task"].id), i["key"], i.get("have"), i["actions"], i["problem"]] for i in items]
    return hashlib.sha256(json.dumps(data, default=str).encode()).hexdigest()[:12]


def _upsert_transcript(db, rec: dict, storage_path: str, stats: dict) -> A2AudioTranscript:
    row = db.scalar(select(A2AudioTranscript).where(A2AudioTranscript.sha256 == rec["sha256"]))
    if row is None:
        row = A2AudioTranscript(sha256=rec["sha256"], storage_paths=[], matches={})
        db.add(row)
        stats["created"] += 1
    if row.status != STATUS_TRANSCRIBED or not row.text:  # a finished transcript is reused as it is
        for k in ("original_name", "size_bytes", "duration_seconds", "status", "text", "segments", "model", "quality", "review_note"):
            setattr(row, k, rec[k])
    else:
        stats["reused"] += 1
    if storage_path not in (row.storage_paths or []):
        row.storage_paths = [*(row.storage_paths or []), storage_path]
    return row


def _set_match(row: A2AudioTranscript, task_id, match: dict) -> None:
    row.matches = {**(row.matches or {}), str(task_id): {**match, "checked_at": _now().isoformat()}}


def _student_transcript(rows: list[A2AudioTranscript], labels: list[str | None]) -> str | None:
    if not rows or any(r.status != STATUS_TRANSCRIBED or not r.text for r in rows):
        return None
    if len(rows) == 1:
        return f"{TRANSCRIPT_HEADER}\n\n{rows[0].text}"
    return TRANSCRIPT_HEADER + "".join(f"\n\n{label or f'Audio {n}'}:\n{r.text}" for n, (r, label) in enumerate(zip(rows, labels), 1))


def _add_track(db, task, t: dict, records: dict, names: dict) -> None:
    from starlette.datastructures import Headers, UploadFile

    rec = records[names[nfc(t["file"])]]
    ctype = "audio/mp4" if t["path"].suffix.lower() == ".m4a" else "audio/mpeg"
    with open(t["path"], "rb") as fh:
        upload = UploadFile(fh, filename=t["file"], headers=Headers({"content-type": ctype}))
        asyncio.run(skill_admin.upload_audio_track(db, task.id, t["label"], upload, round(rec["duration_seconds"])))
    db.refresh(task)


def adopt_slot_audio(db, task, row: A2AudioTranscript) -> A2AudioAsset | None:
    """A Text slot whose audio came through the general Hören upload (not the
    slot page) gets a library entry for that SAME stored file, linked to the
    slot — so the slot page manages it again (verify, replace, delete). The
    file is not copied or moved; a content already in the library is not
    added twice (SHA-256)."""
    from app.models.a2_audio_asset import KIND_TEXT, VERIFY_PENDING
    from app.services.a2_audio import filename

    if db.scalar(select(A2AudioAsset.id).where(A2AudioAsset.sha256 == row.sha256)) is not None:
        return None
    slot = int(task.task_key.rsplit("-", 1)[1])
    fmt = Path(task.audio_storage_path).suffix.lstrip(".").lower()
    name = task.audio_original_name or row.original_name
    asset = A2AudioAsset(level="A2", unterricht=lesson4_hoeren.LESSON, audio_kind=KIND_TEXT, part=slot, title=f"A2 4.Unterricht Text {slot}",
                         original_filename=name, parsed=filename.parse(name), storage_path=task.audio_storage_path,
                         content_type=task.audio_content_type or assets.FORMATS.get(fmt, ("audio/mpeg",))[0], audio_format=fmt,
                         size_bytes=task.audio_size_bytes or row.size_bytes, sha256=row.sha256, duration_seconds=task.audio_duration_seconds,
                         sort_order=slot, verification=VERIFY_PENDING, listening_id=task.id, linked_at=_now())
    db.add(asset)
    db.flush()
    return asset


def apply(db, items: list[dict], records: dict, names: dict, publish: bool) -> list[dict]:
    stats = {"created": 0, "reused": 0}
    report = []
    for item in items:
        task, spec = item["task"], item["spec"]
        result = {"lesson": item["lesson"], "listening_id": str(task.id), "title": task.title, "key": item["key"], "problem": item["problem"],
                  "published_before": task.is_published}
        if spec is not None and not item["problem"]:
            for t in item["add_tracks"]:
                _add_track(db, task, t, records, names)
            if spec.get("audio_label") and task.audio_label != spec["audio_label"]:
                task.audio_label = spec["audio_label"]
        files = processing.task_files(task)
        rows = []
        for f in files:
            digest = sha256(_stored(f["storage_path"])) if f["on_disk"] else None
            rows.append(_upsert_transcript(db, records[digest], f["storage_path"], stats) if digest in records else None)
        db.flush()
        match = dict(spec["match"]) if spec else {"status": MATCH_NEEDS_REVIEW, "note": "keine Prüfdaten"}
        if item["problem"]:
            match = {"status": MATCH_NEEDS_REVIEW, "note": item["problem"]}
        for r in rows:
            if r is not None:
                _set_match(r, task.id, match)
        # durations from the decoded files (shown to students)
        if rows and rows[0] is not None and not task.audio_duration_seconds:
            task.audio_duration_seconds = round(rows[0].duration_seconds)
        for track, r in zip(task.audio_tracks, rows[1:]):
            if r is not None and not track.duration_seconds:
                track.duration_seconds = round(r.duration_seconds)
        applied = []
        if not item["problem"] and match["status"] == MATCH_MATCHED and not spec.get("audio_only"):
            if spec.get("verify_only"):
                record_reviews(db, "hoeren", loesung._sorted_questions(task), spec, True)
                applied.append("Lösung bestätigt")
            else:
                for q in item.get("removals", []):
                    db.delete(q)  # options + review rows go with it (ON DELETE CASCADE)
                db.flush()
                for c in item["key_plan"]["questions"]:
                    apply_question(db, c["question"], c)
                applied.append(f"{len(item['key_plan']['questions'])} Lösungen geprüft")
                if item.get("removals"):
                    applied.append("entfernt: " + " | ".join(q.question for q in item["removals"]))
        matched = match["status"] == MATCH_MATCHED and not item["problem"]
        text = _student_transcript(rows, [f["label"] for f in files]) if matched and rows and all(rows) else None
        if text and not (task.transcript or "").strip():  # only the task's own audio; a book transcript stays
            task.transcript = text
            applied.append("Transkript für Lernende gespeichert")
        db.commit()
        db.refresh(task)
        # publish
        if publish and not task.is_published and match["status"] == MATCH_MATCHED and not item["problem"]:
            if spec.get("audio_only"):
                asset = db.scalar(select(A2AudioAsset).where(A2AudioAsset.listening_id == task.id))
                if asset is None and rows and rows[0] is not None and task.task_key:
                    asset = adopt_slot_audio(db, task, rows[0])
                    applied.append("Audio in die A2-Audio-Bibliothek übernommen (gleiche Datei)")
                if asset is not None and asset.storage_path == task.audio_storage_path and asset.verification != VERIFY_OK and all(
                        r is not None and r.status == STATUS_TRANSCRIBED for r in rows):
                    asset.verification, asset.verified_at, asset.verified_by = VERIFY_OK, _now(), None
                    asset.verification_note = "Automatisch geprüft (Audio-Verarbeitung 2026-10-30): Datei vollständig transkribiert, Inhalt = " + match["note"]
                    db.commit()
                    applied.append("Audio als geprüft markiert (automatisch)")
                state = lesson4_hoeren._slot_state(db, int(task.task_key.rsplit("-", 1)[1]), task) if task.task_key else {"can_activate": False}
                if state.get("can_activate"):
                    task.is_published = True
            elif hoeren_pdf_import.readiness(db, task)["ready"]:
                task.is_published = True
            db.commit()
        db.refresh(task)
        questions, counts = processing._questions(db, task)
        status, problems = processing.task_status(processing.task_files(task), rows, match, counts, task.is_published)
        result.update(status=status, problems=problems, applied=applied, published=task.is_published, keys=counts)
        write_audit(db, None, "a2_audio_processed", details=json.dumps(
            {"task": str(task.id), "key": item["key"], "status": status, "applied": applied, "published": task.is_published,
             "match": match["status"]}, ensure_ascii=False)[:8000])
        report.append(result)
    return [{"transcripts": stats}] + report


def _print_plan(items: list[dict]) -> None:
    for i in items:
        t = i["task"]
        line = f"L{i['lesson']:>2} {t.title[:58]:58} pub={int(t.is_published)} files={len(i['files'])}"
        if i["problem"]:
            line += f"  -> NICHT ANGEWENDET: {i['problem']}"
        else:
            line += f"  -> {i['spec']['match']['status']}: " + ("; ".join(i["actions"]) or ("nur Audio" if i["spec"].get("audio_only") else "keine Lösung"))
            if i["add_tracks"]:
                line += " + Spur " + ", ".join(t["label"] for t in i["add_tracks"])
        print(line)
        for c in (i.get("key_plan") or {}).get("questions", []):
            if c["changed"] or c["status"] != "verified":
                print(f"       Frage {c['number']}: {c['status']}{' (geändert)' if c['changed'] else ''}")
        for q in i.get("removals", []):
            print(f"       − Frage entfernen: {q.question}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=("plan", "apply"), nargs="?", default="plan")
    parser.add_argument("--audio-dir", type=Path, help="folder with the book audio files (for add_tracks)")
    parser.add_argument("--confirm", help="plan id printed by `plan`")
    parser.add_argument("--no-publish", action="store_true")
    parser.add_argument("--json", type=Path, help="write the apply report here")
    args = parser.parse_args()
    records, names = load_records()
    with SessionLocal() as db:
        if len(assets.a2_lessons(db)) != 14:
            print("STOP: A2 hat nicht 14 Lektionen", file=sys.stderr)
            return 1
        items = plan(db, args.audio_dir, records, names)
        pid = plan_id(items)
        _print_plan(items)
        print(f"\nplan id {pid} — {len(items)} Aufgaben, {len({h for i in items for h in (i.get('have') or [])})} verschiedene Audioinhalte")
        if args.stage == "plan":
            print("READ-ONLY: nothing was changed.")
            return 0
        if args.confirm != pid:
            print(f"STOP: plan changed or wrong id (current {pid}) — nothing was changed", file=sys.stderr)
            return 1
        report = apply(db, items, records, names, not args.no_publish)
    text = json.dumps(report, ensure_ascii=False, indent=1, default=str)
    if args.json:
        args.json.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
