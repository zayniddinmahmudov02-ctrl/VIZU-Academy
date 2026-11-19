"""Background jobs that make AI subtitles for a Medienwelt film (`film_subtitle_jobs`).

Flow: the admin starts TRANSCRIBE (audio language "auto" or chosen, optional translation languages) → the job runs in a worker thread of
the backend process → its result is a DRAFT track → TRANSLATE jobs follow for the chosen languages → an admin checks / edits / approves the
tracks; students only ever get APPROVED ones (`catalog.subtitles_of`).

TRANSCRIBE: ffmpeg finds the pauses of the film's audio once, the audio is cut into pieces of about SUBTITLE_CHUNK_SECONDS at pauses, each piece is
transcribed (subtitle_ai provider), the finished pieces are kept in `partial` (a retry or a restart continues with the next piece), then the
segments become cues (`build_cues` + `snap_to_speech`), are checked like an uploaded file and stored as normalised WebVTT.
TRANSLATE: the cues of the source track in batches of BATCH (a batch whose answer has the wrong count is split and asked again), same times.

Status: PENDING → PROCESSING → COMPLETED | FAILED (`error_code` / `error_message`; FAILED with code CANCELLED when the admin stopped it).
`retry` puts a FAILED job back to PENDING with its partial results. The worker claims a job with `FOR UPDATE SKIP LOCKED`; a PROCESSING job
whose heartbeat is older than STALE (the backend was restarted mid-job) is picked up again. Nothing here is visible to students."""

from __future__ import annotations

import logging
import os
import subprocess
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.core.audit import write_audit
from app.core.config import settings
from app.models.medien import (JOB_COMPLETED, JOB_FAILED, JOB_PENDING, JOB_PROCESSING, JOB_TRANSCRIBE, JOB_TRANSLATE, SOURCE_AI,
                               SOURCE_TRANSLATION, SUBTITLE_DRAFT, Film, FilmSubtitle, FilmSubtitleJob)
from app.models.user import User
from app.services.audio_files.service import find_tool, probe_duration_ms
from app.services.medien import common as c
from app.services.medien import subtitle_ai as ai
from app.services.medien import subtitles as subs

log = logging.getLogger("vizu.medien.subtitle_jobs")

LABELS = {"de": "Deutsch", "uz": "O'zbekcha", "en": "English", "ru": "Русский"}
BATCH = 60
STALE = timedelta(minutes=10)
FFMPEG_TIMEOUT = 3600
ACTIVE = (JOB_PENDING, JOB_PROCESSING)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fail(code: str, message: str, status: int = 409):
    return c.err(status, f"{code}: {message}")


# ---------------- starting jobs (admin) ----------------


def _existing(db: Session, film_id: UUID, language: str) -> FilmSubtitle | None:
    return db.scalar(select(FilmSubtitle).where(FilmSubtitle.film_id == film_id, FilmSubtitle.language == language))


def _active_job(db: Session, film_id: UUID, kind: str, language: str) -> FilmSubtitleJob | None:
    return db.scalar(select(FilmSubtitleJob).where(FilmSubtitleJob.film_id == film_id, FilmSubtitleJob.kind == kind,
                                                   FilmSubtitleJob.language == language, FilmSubtitleJob.status.in_(ACTIVE)))


def _check_targets(db: Session, film: Film, targets: list[str], replace: bool, exclude: str | None = None) -> list[str]:
    out = []
    for t in dict.fromkeys(targets):
        if t not in ai.LANGUAGES:
            raise c.err(422, "INVALID_LANGUAGE: de, en, uz or ru.")
        if t == exclude:
            continue
        if not replace and _existing(db, film.id, t):
            raise _fail("SUBTITLE_EXISTS", f"the film already has a {LABELS[t]} subtitle — tick 'replace' to make a new one.")
        out.append(t)
    return out


def start_transcription(db: Session, user: User, film: Film, language: str, translate_to: list[str], replace: bool) -> FilmSubtitleJob:
    """Checks everything that can be known now (service set up, ffmpeg, video file, language, existing tracks, no second running job) and
    queues the job. A conflict with the detected language ("auto") is found after the first piece and stops the job early."""
    language = (language or "auto").strip().lower()
    if language != "auto" and language not in ai.LANGUAGES:
        raise c.err(422, "INVALID_LANGUAGE: auto, de, en, uz or ru.")
    try:
        ai.stt_provider()
        if translate_to:
            ai.translator()
    except ai.SubtitleAIError as exc:
        raise _fail(exc.code, str(exc)) from None
    if not find_tool("ffmpeg"):
        raise _fail("FFMPEG_MISSING", "ffmpeg is not available on the server.", 503)
    if not film.video_key or not c.file_path(film.video_key):
        raise _fail("VIDEO_MISSING", "the film has no uploaded video file (an external link cannot be transcribed).")
    if language != "auto" and not replace and _existing(db, film.id, language):
        raise _fail("SUBTITLE_EXISTS", f"the film already has a {LABELS[language]} subtitle — tick 'replace' to make a new one.")
    targets = _check_targets(db, film, translate_to, replace, exclude=None if language == "auto" else language)
    if db.scalar(select(FilmSubtitleJob.id).where(FilmSubtitleJob.film_id == film.id, FilmSubtitleJob.kind == JOB_TRANSCRIBE,
                                                  FilmSubtitleJob.status.in_(ACTIVE))):
        raise _fail("JOB_RUNNING", "a transcription of this film is already running.")
    job = FilmSubtitleJob(film_id=film.id, kind=JOB_TRANSCRIBE, language=language, translate_to=targets, replace_existing=replace,
                          created_by_id=user.id, status=JOB_PENDING)
    db.add(job)
    db.commit()
    write_audit(db, actor_id=user.id, action="medien_subtitle_ai_started", details=f"{film.id} transcribe {language} → {','.join(targets) or '-'}")
    kick()
    return job


def start_translation(db: Session, user: User | None, film: Film, source: FilmSubtitle, target: str, replace: bool, *, audit: bool = True,
                      wake: bool = True) -> FilmSubtitleJob:
    target = (target or "").strip().lower()
    if source.film_id != film.id:
        raise c.err(404, "NOT_FOUND")
    if target == source.language:
        raise c.err(422, "SAME_LANGUAGE: choose another language than the source track.")
    try:
        ai.translator()
    except ai.SubtitleAIError as exc:
        raise _fail(exc.code, str(exc)) from None
    _check_targets(db, film, [target], replace)
    if _active_job(db, film.id, JOB_TRANSLATE, target):
        raise _fail("JOB_RUNNING", f"a {LABELS[target]} translation of this film is already running.")
    job = FilmSubtitleJob(film_id=film.id, kind=JOB_TRANSLATE, language=target, source_subtitle_id=source.id, replace_existing=replace,
                          created_by_id=user.id if user else None, status=JOB_PENDING)
    db.add(job)
    db.commit()
    if audit and user:
        write_audit(db, actor_id=user.id, action="medien_subtitle_ai_started", details=f"{film.id} translate {source.language} → {target}")
    if wake:
        kick()
    return job


def _job_of(db: Session, job_id: UUID, film_id: UUID | None = None) -> FilmSubtitleJob:
    job = db.get(FilmSubtitleJob, job_id)
    if job is None or (film_id and job.film_id != film_id):
        raise c.err(404, "NOT_FOUND")
    return job


def retry(db: Session, user: User, job_id: UUID, film_id: UUID | None = None) -> FilmSubtitleJob:
    """A FAILED job runs again and continues with the pieces / batches that are not done yet."""
    job = _job_of(db, job_id, film_id)
    if job.status != JOB_FAILED:
        raise _fail("JOB_NOT_FAILED", "only a failed job can be tried again.")
    if _active_job(db, job.film_id, job.kind, job.language):
        raise _fail("JOB_RUNNING", "the same job is already running.")
    job.status, job.error_code, job.error_message, job.finished_at = JOB_PENDING, None, None, None
    db.commit()
    write_audit(db, actor_id=user.id, action="medien_subtitle_ai_retry", details=f"{job.film_id} {job.kind} {job.language} {job.id}")
    kick()
    return job


def cancel(db: Session, user: User, job_id: UUID, film_id: UUID | None = None) -> FilmSubtitleJob:
    """Stops a waiting or running job (the worker stops after the current piece). Its finished pieces are kept for a retry."""
    job = _job_of(db, job_id, film_id)
    if job.status not in ACTIVE:
        raise _fail("JOB_NOT_ACTIVE", "the job is not running.")
    job.status, job.error_code, job.error_message, job.finished_at = JOB_FAILED, "CANCELLED", "Stopped by an admin.", _now()
    db.commit()
    write_audit(db, actor_id=user.id, action="medien_subtitle_ai_cancelled", details=f"{job.film_id} {job.kind} {job.language} {job.id}")
    return job


def serialize(job: FilmSubtitleJob) -> dict:
    return {"id": job.id, "kind": job.kind, "status": job.status, "language": job.language, "detected_language": job.detected_language,
            "translate_to": job.translate_to or [], "replace": job.replace_existing, "provider": job.provider, "model": job.model,
            "progress_done": job.progress_done, "progress_total": job.progress_total, "attempts": job.attempts, "error_code": job.error_code,
            "error_message": job.error_message, "result_subtitle_id": job.result_subtitle_id, "source_subtitle_id": job.source_subtitle_id,
            "stats": job.stats or {}, "created_at": job.created_at, "started_at": job.started_at, "finished_at": job.finished_at}


def jobs_of(db: Session, film_id: UUID, limit: int = 20) -> list[dict]:
    rows = db.scalars(select(FilmSubtitleJob).where(FilmSubtitleJob.film_id == film_id).order_by(FilmSubtitleJob.created_at.desc()).limit(limit)).all()
    if any(r.status in ACTIVE for r in rows):
        kick()  # self-healing: a job left waiting (e.g. after a restart) gets a worker as soon as somebody looks at it
    return [serialize(r) for r in rows]


# ---------------- worker ----------------

_lock = threading.Lock()
_running = False


def kick() -> None:
    """Starts the worker thread unless it already runs (or the worker is switched off, as in the test suite)."""
    global _running
    if not settings.SUBTITLE_WORKER_ENABLED:
        return
    with _lock:
        if _running:
            return
        _running = True
    threading.Thread(target=_loop, name="subtitle-ai", daemon=True).start()


def _loop() -> None:
    global _running
    from app.db.session import SessionLocal

    try:
        while True:
            with SessionLocal() as db:
                if not run_one(db):
                    break
    except Exception:  # never let the thread die silently
        log.exception("subtitle worker stopped")
    finally:
        with _lock:
            _running = False
    try:
        with SessionLocal() as db:  # a job queued while the loop was ending
            if db.scalar(select(FilmSubtitleJob.id).where(FilmSubtitleJob.status == JOB_PENDING).limit(1)):
                kick()
    except Exception:
        log.exception("subtitle worker re-check failed")


def on_startup() -> None:
    """Backend start: a job that was PROCESSING when the backend stopped goes back to PENDING (it continues with its next piece), then the worker
    starts. Never blocks or breaks the start."""
    if not settings.SUBTITLE_WORKER_ENABLED or settings.APP_ENV == "test":
        return
    try:
        from app.db.session import SessionLocal

        with SessionLocal() as db:
            rows = db.scalars(select(FilmSubtitleJob).where(FilmSubtitleJob.status == JOB_PROCESSING)).all()
            for job in rows:
                job.status = JOB_PENDING
            db.commit()
            pending = db.scalar(select(FilmSubtitleJob.id).where(FilmSubtitleJob.status == JOB_PENDING).limit(1))
        if pending:
            kick()
    except Exception:
        log.exception("subtitle jobs: start-up recovery failed")


def claim(db: Session) -> FilmSubtitleJob | None:
    stale = _now() - STALE
    job = db.scalars(select(FilmSubtitleJob)
                     .where(or_(FilmSubtitleJob.status == JOB_PENDING,
                                and_(FilmSubtitleJob.status == JOB_PROCESSING, FilmSubtitleJob.heartbeat_at < stale)))
                     .order_by(FilmSubtitleJob.created_at).limit(1).with_for_update(skip_locked=True)).first()
    if job is None:
        db.rollback()
        return None
    job.status, job.attempts, job.heartbeat_at = JOB_PROCESSING, job.attempts + 1, _now()
    job.started_at = job.started_at or _now()
    job.error_code = job.error_message = None
    db.commit()
    return job


def run_one(db: Session) -> bool:
    """Claims and processes one job. False when nothing was waiting."""
    job = claim(db)
    if job is None:
        return False
    job_id = job.id
    try:
        if job.attempts > 6:
            raise ai.SubtitleAIError("INTERRUPTED", "The job was interrupted too often.")
        if job.kind == JOB_TRANSCRIBE:
            _transcribe(db, job)
        else:
            _translate(db, job)
    except _Cancelled:
        db.rollback()
    except ai.SubtitleAIError as exc:
        db.rollback()
        _finish_failed(db, job_id, exc.code, str(exc))
    except Exception as exc:
        db.rollback()
        log.exception("subtitle job %s failed", job_id)
        _finish_failed(db, job_id, "INTERNAL_ERROR", f"Unexpected error ({type(exc).__name__}). Try again; if it repeats, check the server log.")
    finally:
        _cleanup(job_id)
    return True


def _finish_failed(db: Session, job_id: UUID, code: str, message: str) -> None:
    job = db.get(FilmSubtitleJob, job_id)
    if job is None or job.status == JOB_FAILED:
        return
    job.status, job.error_code, job.error_message, job.finished_at = JOB_FAILED, code[:60], message[:500], _now()
    db.commit()
    write_audit(db, actor_id=None, action="medien_subtitle_ai_failed", details=f"{job.film_id} {job.kind} {job.language} {code}")


class _Cancelled(Exception):
    pass


def _heartbeat(db: Session, job: FilmSubtitleJob, partial: dict) -> None:
    """Saves the progress (`partial` is the worker's own copy and always written as a whole); stops when an admin cancelled the job meanwhile
    (only the changed columns are written, so a cancel is never overwritten)."""
    job.partial = partial
    flag_modified(job, "partial")
    job.heartbeat_at = _now()
    db.commit()
    if db.scalar(select(FilmSubtitleJob.status).where(FilmSubtitleJob.id == job.id)) != JOB_PROCESSING:
        raise _Cancelled()


# ---------------- audio ----------------


def _work_dir(job_id: UUID) -> Path:
    path = c.storage.ROOT / "ai-work" / str(job_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cleanup(job_id: UUID) -> None:
    folder = c.storage.ROOT / "ai-work" / str(job_id)
    if folder.is_dir():
        for f in folder.iterdir():
            f.unlink(missing_ok=True)
        folder.rmdir()


def _lower_priority() -> None:  # POSIX only: the web server stays responsive while ffmpeg works
    try:
        os.nice(10)
    except (AttributeError, OSError):
        pass


def _run_ffmpeg(args: list[str], timeout: int = FFMPEG_TIMEOUT) -> subprocess.CompletedProcess:
    ffmpeg = find_tool("ffmpeg")
    if not ffmpeg:
        raise ai.SubtitleAIError("FFMPEG_MISSING", "ffmpeg is not available on the server.")
    kwargs = {"preexec_fn": _lower_priority} if os.name == "posix" else {}
    try:
        return subprocess.run([ffmpeg, "-nostdin", "-hide_banner", *args], capture_output=True, text=True, timeout=timeout, **kwargs)
    except subprocess.TimeoutExpired:
        raise ai.SubtitleAIError("FFMPEG_TIMEOUT", "ffmpeg took too long.", retryable=True) from None


def find_silences(video: Path) -> list[tuple[float, float]]:
    out = _run_ffmpeg(["-i", str(video), "-vn", "-ac", "1", "-af", "silencedetect=noise=-32dB:d=0.35", "-f", "null", "-"])
    if out.returncode != 0 and "Output file #0 does not contain any stream" in out.stderr:
        raise ai.SubtitleAIError("NO_AUDIO", "The video has no audio track.")
    if out.returncode != 0 and not ai.parse_silences(out.stderr) and "Duration" not in out.stderr:
        raise ai.SubtitleAIError("AUDIO_READ_FAILED", "The audio of the video could not be read.")
    return ai.parse_silences(out.stderr)


def cut_piece(video: Path, start: float, length: float, folder: Path) -> tuple[bytes, str]:
    """One piece of the audio as small mono speech audio (16 kHz MP3, AAC if the MP3 encoder is missing) → (bytes, mime)."""
    target = folder / f"piece-{uuid4().hex}.mp3"
    base = ["-y", "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000"]
    out = _run_ffmpeg([*base, "-c:a", "libmp3lame", "-b:a", "48k", str(target)], 600)
    mime = "audio/mp3"
    if out.returncode != 0 or not target.is_file() or target.stat().st_size == 0:
        target = folder / f"piece-{uuid4().hex}.aac"
        out = _run_ffmpeg([*base, "-c:a", "aac", "-b:a", "64k", "-f", "adts", str(target)], 600)
        mime = "audio/aac"
        if out.returncode != 0 or not target.is_file() or target.stat().st_size == 0:
            raise ai.SubtitleAIError("AUDIO_CUT_FAILED", "A piece of the audio could not be prepared.")
    try:
        return target.read_bytes(), mime
    finally:
        target.unlink(missing_ok=True)


# ---------------- storing a track ----------------


def _video_ms(film: Film) -> int | None:
    return film.video_duration_ms or (film.duration_minutes * 60_000 if film.duration_minutes else None)


def _store_track(db: Session, job: FilmSubtitleJob, film: Film, language: str, cues: list[subs.Cue], source: str, source_language: str | None,
                 model: str | None) -> FilmSubtitle:
    warnings: list[dict] = []
    subs.check(cues, _video_ms(film), warnings)
    vtt = subs.to_vtt(cues)
    key = f"subtitles/{uuid4().hex}.vtt"
    path = c.storage.ROOT / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(vtt)
    old_key = None
    try:
        sub = _existing(db, film.id, language)
        if sub is not None and not job.replace_existing:
            raise ai.SubtitleAIError("SUBTITLE_EXISTS", f"The film already has a {LABELS[language]} subtitle; start again with 'replace'.")
        if sub is None:
            sub = FilmSubtitle(film_id=film.id, language=language, label=LABELS[language], file_key=key)
            db.add(sub)
        else:
            old_key, sub.file_key = sub.file_key, key
        sub.cue_count, sub.last_ms, sub.source_format = len(cues), max(cue.end for cue in cues), "vtt"
        sub.original_name, sub.file_size, sub.warnings = None, len(vtt), warnings
        sub.status, sub.source, sub.source_language, sub.ai_model = SUBTITLE_DRAFT, source, source_language, (model or "")[:80] or None
        sub.approved_at = sub.approved_by_id = sub.edited_at = None
        db.flush()
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise
    if old_key:
        old = c.file_path(old_key)
        if old:
            old.unlink(missing_ok=True)
    return sub


# ---------------- TRANSCRIBE ----------------


def _transcribe(db: Session, job: FilmSubtitleJob) -> None:
    film = db.get(Film, job.film_id)
    video = c.file_path(film.video_key) if film and film.video_key else None
    if video is None:
        raise ai.SubtitleAIError("VIDEO_MISSING", "The film has no uploaded video file.")
    provider = ai.stt_provider()
    job.provider, job.model = provider.name, provider.model
    partial = dict(job.partial or {})
    if "cuts" not in partial:
        duration_ms = probe_duration_ms(video) or _video_ms(film)
        if not duration_ms:
            raise ai.SubtitleAIError("AUDIO_READ_FAILED", "The length of the video could not be read.")
        silences = find_silences(video)
        partial = {"duration_ms": duration_ms, "silences": [[round(s, 3), round(e, 3)] for s, e in silences],
                   "cuts": ai.choose_cuts(duration_ms / 1000, silences, float(settings.SUBTITLE_CHUNK_SECONDS)), "pieces": {}}
    parts = ai.pieces(partial["cuts"])
    job.progress_total, job.progress_done = len(parts), len(partial["pieces"])
    _heartbeat(db, job, partial)
    hint = job.language if job.language in ai.LANGUAGES else None
    folder = _work_dir(job.id)
    for i, (start, end) in enumerate(parts):
        if str(i) in partial["pieces"]:
            continue
        data, mime = cut_piece(video, start, end - start, folder)
        result = provider.transcribe(data, mime, hint, end - start)
        partial["pieces"][str(i)] = {"language": result.language, "model": result.model,
                                     "segments": [{**s, "start": round(s["start"] + start, 3), "end": round(s["end"] + start, 3)} for s in result.segments]}
        job.model = result.model
        job.progress_done = len(partial["pieces"])
        if job.language == "auto" and not job.detected_language and result.segments:
            _detected(db, job, film, result.language)
        _heartbeat(db, job, partial)

    language = job.language if job.language in ai.LANGUAGES else ai.majority_language([p.get("language") for p in partial["pieces"].values() if p.get("segments")])
    if not language:
        raise ai.SubtitleAIError("NO_SPEECH", "No speech was found in the film's audio.")
    if language not in ai.LANGUAGES:
        raise ai.SubtitleAIError("LANGUAGE_NOT_SUPPORTED", f"The spoken language is '{language}'; supported: de, en, uz, ru.")
    segments = [s for p in partial["pieces"].values() for s in p.get("segments", [])]
    silences = [(s, e) for s, e in partial.get("silences", [])]
    cues = ai.snap_to_speech(ai.build_cues(segments, partial.get("duration_ms")), silences)
    if not cues:
        raise ai.SubtitleAIError("NO_SPEECH", "No speech was found in the film's audio.")
    sub = _store_track(db, job, film, language, cues, SOURCE_AI, None, job.model)
    speakers = max((len({s.get("speaker") for s in p.get("segments", []) if s.get("speaker")}) for p in partial["pieces"].values()), default=0)
    job.detected_language, job.result_subtitle_id = language, sub.id
    job.stats = {"cues": len(cues), "pieces": len(parts), "speakers_max_per_piece": speakers, "language": language, "warnings": len(sub.warnings or [])}
    job.status, job.finished_at, job.heartbeat_at = JOB_COMPLETED, _now(), _now()
    db.commit()
    write_audit(db, actor_id=None, action="medien_subtitle_ai_completed", details=f"{film.id} transcribe {language} {len(cues)} cues (draft)")
    for target in job.translate_to or []:
        if target == language:
            continue
        try:
            start_translation(db, None, film, sub, target, job.replace_existing, audit=False, wake=False)
        except Exception as exc:  # e.g. the translation service is not set up: the transcript stays, the admin sees no translation job
            db.rollback()
            log.warning("follow-up translation %s of film %s not queued: %s", target, film.id, getattr(exc, "detail", exc))


def _detected(db: Session, job: FilmSubtitleJob, film: Film, language: str | None) -> None:
    """The first piece with speech tells the language: stop at once when it is not supported or the film already has that track."""
    if language not in ai.LANGUAGES:
        raise ai.SubtitleAIError("LANGUAGE_NOT_SUPPORTED", f"The spoken language is '{language or '?'}'; supported: de, en, uz, ru.")
    if not job.replace_existing and _existing(db, film.id, language):
        raise ai.SubtitleAIError("SUBTITLE_EXISTS", f"The film is in {LABELS[language]} and already has a {LABELS[language]} subtitle; "
                                                    "start again with 'replace'.")
    job.detected_language = language
    job.translate_to = [t for t in (job.translate_to or []) if t != language]
    flag_modified(job, "translate_to")


# ---------------- TRANSLATE ----------------


def translate_lines(translator, lines: list[str], source: str, target: str, depth: int = 0) -> list[str]:
    """Translates a batch; when the answer has the wrong number of entries the batch is split in two and asked again (down to one line)."""
    try:
        return translator.translate(lines, source, target)
    except ai.SubtitleAIError as exc:
        if exc.code != "AI_TRANSLATION_COUNT" or len(lines) == 1 or depth > 6:
            raise
    half = len(lines) // 2
    return translate_lines(translator, lines[:half], source, target, depth + 1) + translate_lines(translator, lines[half:], source, target, depth + 1)


def _translate(db: Session, job: FilmSubtitleJob) -> None:
    film = db.get(Film, job.film_id)
    source = db.get(FilmSubtitle, job.source_subtitle_id) if job.source_subtitle_id else None
    path = c.file_path(source.file_key) if source else None
    if film is None or source is None or path is None:
        raise ai.SubtitleAIError("SOURCE_MISSING", "The subtitle to translate from no longer exists.")
    cues = subs.read_cues(path.read_bytes())
    translator = ai.translator()
    job.provider, job.model = translator.name, translator.model
    partial = dict(job.partial or {})
    if partial.get("source_cues") != len(cues):
        partial = {"source_cues": len(cues), "batches": {}}
    batches = [cues[i:i + BATCH] for i in range(0, len(cues), BATCH)]
    job.progress_total, job.progress_done = len(batches), len(partial["batches"])
    _heartbeat(db, job, partial)
    for i, batch in enumerate(batches):
        if str(i) in partial["batches"]:
            continue
        partial["batches"][str(i)] = translate_lines(translator, [cue.text for cue in batch], source.language, job.language)
        job.progress_done = len(partial["batches"])
        _heartbeat(db, job, partial)
    texts = [t for i in range(len(batches)) for t in partial["batches"][str(i)]]
    out = [subs.Cue(cue.start, cue.end, ai.wrap_text(text)[:subs.MAX_CUE_TEXT]) for cue, text in zip(cues, texts) if text.strip()]
    if not out:
        raise ai.SubtitleAIError("AI_EMPTY_ANSWER", "The translation came back empty.")
    sub = _store_track(db, job, film, job.language, out, SOURCE_TRANSLATION, source.language, job.model)
    job.result_subtitle_id, job.detected_language = sub.id, source.language
    job.stats = {"cues": len(out), "batches": len(batches), "from": source.language, "warnings": len(sub.warnings or [])}
    job.status, job.finished_at, job.heartbeat_at = JOB_COMPLETED, _now(), _now()
    db.commit()
    write_audit(db, actor_id=None, action="medien_subtitle_ai_completed", details=f"{film.id} translate {source.language} → {job.language} {len(out)} cues (draft)")
