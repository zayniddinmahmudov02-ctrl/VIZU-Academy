import asyncio
import re
from datetime import UTC, datetime
from typing import AsyncIterator
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging.logger import logger
from app.core.storage.factory import StorageFactory
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.vocabulary import (
    AUDIO_STATUS_FAILED,
    AUDIO_STATUS_GENERATED,
    AUDIO_STATUS_PENDING,
    AUDIO_STATUS_RATE_LIMITED,
    Vocabulary,
)
from app.models.vocabulary_tts_usage import VocabularyTtsUsage
from app.repositories.vocabulary import VocabularyRepository
from app.services.vocabulary import ai_enrichment

_LIST_MARKER_RE = re.compile(r"^\s*(\d+[.)]|[-*•])\s*")


class DailyQuotaExceededError(ai_enrichment.AIServiceError):
    """Raised by _store_audio() before a real network call is even
    attempted, once this app's own local daily counter says
    VOCAB_BULK_TTS_MAX_PER_DAY is already spent — distinct from
    ai_enrichment.RateLimitError, which is Google itself saying so."""


def normalize_word_list(raw_text: str) -> list[str]:
    """Strips numbering ("1.", "2)"), bullets (-, *, •), and blank lines
    from a pasted block of words. Drops in-batch duplicates (case-
    insensitive), keeping the first occurrence's original casing."""

    words: list[str] = []
    seen: set[str] = set()

    for line in raw_text.splitlines():
        cleaned = _LIST_MARKER_RE.sub("", line.strip()).strip()
        if not cleaned:
            continue

        key = cleaned.lower()
        if key in seen:
            continue

        seen.add(key)
        words.append(cleaned)

    return words


class VocabularyBulkService:
    """Backs the "Wörter importieren" bulk generator: paste a word list,
    enrich it via Gemini (article/plural/word-type/translation/example
    sentence — see ai_enrichment.py), optionally generate German
    pronunciation audio with controlled concurrency, preview, edit, then
    save. Reuses Vocabulary/VocabularyRepository as-is — no new model,
    no migration — and the exact same public "audio" storage folder the
    existing manual upload (FileUploadField folder="audio") already
    writes to, so audio_url stays a plain public URL either way."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = VocabularyRepository(db)
        self.storage = StorageFactory.create(settings.STORAGE_PROVIDER)

    def get_lesson_level(self, lesson_id: UUID) -> str:
        row = (
            self.db.query(Course.level)
            .join(Module, Module.course_id == Course.id)
            .join(Lesson, Lesson.module_id == Module.id)
            .filter(Lesson.id == lesson_id)
            .first()
        )
        return row[0] if row else "A1"

    def _existing_words_lower(self, lesson_id: UUID) -> set[str]:
        rows = self.db.query(Vocabulary.german_word).filter(Vocabulary.lesson_id == lesson_id).all()
        return {r[0].strip().lower() for r in rows if r[0]}

    def _next_order_index(self, lesson_id: UUID) -> int:
        max_order = (
            self.db.query(func.max(Vocabulary.order_index))
            .filter(Vocabulary.lesson_id == lesson_id)
            .scalar()
        )
        return (max_order or 0) + 1

    # ==========================
    # Daily TTS budget (self-imposed, mirrors Google's real quota)
    # ==========================

    def _get_or_create_today_usage(self) -> VocabularyTtsUsage:
        today = datetime.now(UTC).date()
        usage = (
            self.db.query(VocabularyTtsUsage)
            .filter(VocabularyTtsUsage.usage_date == today)
            .first()
        )
        if usage is None:
            usage = VocabularyTtsUsage(usage_date=today, request_count=0)
            self.db.add(usage)
            self.db.commit()
            self.db.refresh(usage)
        return usage

    def get_quota_status(self) -> dict:
        """Feeds the admin UI's "Audio quota heute: X / Y verwendet"
        display — read-only, never reserves anything."""
        usage = self._get_or_create_today_usage()
        max_per_day = settings.VOCAB_BULK_TTS_MAX_PER_DAY
        return {
            "used_today": usage.request_count,
            "max_per_day": max_per_day,
            "max_per_minute": settings.VOCAB_BULK_TTS_MAX_PER_MINUTE,
            "exhausted": usage.request_count >= max_per_day,
        }

    def _reserve_daily_budget(self) -> bool:
        """Atomically checks-and-increments today's usage row before a
        real TTS call is attempted. Returns False (without incrementing)
        once the local daily cap is already reached."""
        usage = self._get_or_create_today_usage()
        if usage.request_count >= settings.VOCAB_BULK_TTS_MAX_PER_DAY:
            return False
        usage.request_count += 1
        self.db.commit()
        return True

    def _mark_daily_budget_exhausted(self) -> None:
        """Google itself just returned a real 429 with a PerDay quotaId —
        clamp the local counter up to the configured max so it stops
        disagreeing with reality for the rest of today, even though this
        counter can't know exactly what earlier usage caused it."""
        usage = self._get_or_create_today_usage()
        if usage.request_count < settings.VOCAB_BULK_TTS_MAX_PER_DAY:
            usage.request_count = settings.VOCAB_BULK_TTS_MAX_PER_DAY
            self.db.commit()

    # ==========================
    # Audio (public "audio" folder — same one manual uploads use)
    # ==========================

    async def _store_audio(self, word: str) -> tuple[str, int]:
        if not self._reserve_daily_budget():
            raise DailyQuotaExceededError(
                f"Tägliches Audio-Kontingent aufgebraucht "
                f"({settings.VOCAB_BULK_TTS_MAX_PER_DAY}/{settings.VOCAB_BULK_TTS_MAX_PER_DAY} heute verwendet)."
            )

        try:
            audio_bytes = await ai_enrichment.synthesize_word_audio(word)
        except ai_enrichment.RateLimitError as exc:
            if exc.is_daily:
                # The real provider confirms what our local counter
                # guessed at — resync it so nothing else attempts a call
                # today, then propagate the original error unchanged.
                self._mark_daily_budget_exhausted()
            raise

        safe_stub = re.sub(r"[^a-zA-Z0-9]+", "_", word.lower()).strip("_") or "wort"
        # .wav, not .mp3 — synthesize_word_audio() returns a WAV file
        # (Gemini's native TTS output is raw PCM, wrapped in a WAV
        # header); nginx picks the Content-Type it serves from this
        # extension, so it has to match the actual bytes.
        path = f"audio/{uuid4().hex}_{safe_stub}.wav"

        destination = self.storage.ROOT / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(destination.write_bytes, audio_bytes)

        return self.storage.url(path), len(audio_bytes)

    async def _delete_audio(self, audio_url: str | None) -> None:
        if not audio_url:
            return
        prefix = self.storage.url("")  # e.g. "/uploads/"
        if not audio_url.startswith(prefix):
            return  # not one of ours (e.g. a manually pasted external URL) — leave it alone
        await self.storage.delete(audio_url[len(prefix):])

    async def regenerate_audio(self, vocabulary: Vocabulary) -> str:
        """New file stored and the DB row committed before the old file
        is deleted — a failed regeneration never leaves the word without
        a playable audio_url."""

        old_url = vocabulary.audio_url
        try:
            new_url, _ = await self._store_audio(vocabulary.german_word)
        except ai_enrichment.AIServiceError as exc:
            vocabulary.audio_status = (
                AUDIO_STATUS_RATE_LIMITED
                if isinstance(exc, (DailyQuotaExceededError, ai_enrichment.RateLimitError))
                else AUDIO_STATUS_FAILED
            )
            vocabulary.audio_error = str(exc)
            self.db.commit()
            raise

        vocabulary.audio_url = new_url
        vocabulary.audio_status = AUDIO_STATUS_GENERATED
        vocabulary.audio_error = None
        self.db.commit()
        self.db.refresh(vocabulary)

        await self._delete_audio(old_url)

        return new_url

    def get_missing_audio(self, lesson_id: UUID) -> list[Vocabulary]:
        """Words eligible for "Fehlende Audios generieren" — anything
        not already GENERATED, regardless of how it got that way (never
        attempted, a prior real failure, or a prior rate-limit)."""
        return (
            self.db.query(Vocabulary)
            .filter(
                Vocabulary.lesson_id == lesson_id,
                Vocabulary.audio_status != AUDIO_STATUS_GENERATED,
            )
            .order_by(Vocabulary.order_index)
            .all()
        )

    async def generate_missing_audio_stream(self, lesson_id: UUID) -> AsyncIterator[dict]:
        """Backs "Fehlende Audios generieren": (re)attempts audio only
        for rows that don't already have it, never touching a word that
        already has audio_status == GENERATED. Processes sequentially —
        given the daily budget is a handful of requests, concurrency
        buys nothing here and would only complicate "stop the whole
        queue" once the daily quota is confirmed spent. Continues past
        an ordinary per-word failure but stops the entire remaining
        queue the moment either the local daily budget or a real
        Google daily-quota 429 says today's allowance is gone, rather
        than letting every remaining word burn its own retry cycle."""

        words = self.get_missing_audio(lesson_id)
        total = len(words)

        yield {"type": "queue_start", "total": total, "quota": self.get_quota_status()}

        if total == 0:
            yield {"type": "done", "generated": 0, "failed": 0, "remaining": 0, "stopped_for_quota": False, "quota": self.get_quota_status()}
            return

        generated = 0
        failed = 0
        stopped_for_quota = False

        for index, vocab in enumerate(words, start=1):
            size_bytes = None
            try:
                url, size_bytes = await self._store_audio(vocab.german_word)
            except DailyQuotaExceededError as exc:
                vocab.audio_status = AUDIO_STATUS_RATE_LIMITED
                vocab.audio_error = str(exc)
                failed += 1
                stopped_for_quota = True
            except ai_enrichment.RateLimitError as exc:
                vocab.audio_status = AUDIO_STATUS_RATE_LIMITED
                vocab.audio_error = str(exc)
                failed += 1
                stopped_for_quota = exc.is_daily
            except ai_enrichment.AIServiceError as exc:
                vocab.audio_status = AUDIO_STATUS_FAILED
                vocab.audio_error = str(exc)
                failed += 1
            else:
                vocab.audio_url = url
                vocab.audio_status = AUDIO_STATUS_GENERATED
                vocab.audio_error = None
                generated += 1

            self.db.commit()

            ok = vocab.audio_status == AUDIO_STATUS_GENERATED
            logger.info(
                "Vocabulary missing-audio queue %d/%d (%s): %s",
                index, total, vocab.german_word, "PASS" if ok else f"FAIL — {vocab.audio_error}",
            )

            yield {
                "type": "word_result",
                "word": vocab.german_word,
                "ok": ok,
                "reason": None if ok else vocab.audio_error,
                "size_kb": max(size_bytes // 1024, 1) if ok and size_bytes else None,
                "processed": index,
                "total": total,
                "generated": generated,
                "failed": failed,
            }

            if stopped_for_quota:
                break

        yield {
            "type": "done",
            "generated": generated,
            "failed": failed,
            "remaining": total - generated - failed,
            "stopped_for_quota": stopped_for_quota,
            "quota": self.get_quota_status(),
        }

    # ==========================
    # Analyze (streamed progress)
    # ==========================

    async def analyze_stream(
        self,
        lesson_id: UUID,
        raw_words: list[str],
        auto_complete: bool,
        generate_audio: bool,
    ) -> AsyncIterator[dict]:
        existing = self._existing_words_lower(lesson_id)
        level = self.get_lesson_level(lesson_id)
        total = len(raw_words)

        items: list[dict] = []

        if auto_complete and raw_words:
            yield {"type": "progress", "phase": "text", "processed": 0, "total": total}
            try:
                enriched = await ai_enrichment.enrich_words(raw_words, level)
            except ai_enrichment.AIServiceError as exc:
                yield {"type": "error", "message": str(exc)}
                return

            for e in enriched:
                dup = e["input"].strip().lower() in existing or e["base_word"].strip().lower() in existing
                items.append(
                    {
                        "input_word": e["input"],
                        "word_type": e["word_type"],
                        "article": e["article"],
                        "german_word": e["base_word"],
                        "plural": e["plural"],
                        "translation": e["translation"],
                        "example_sentence": e["example_sentence"],
                        "example_translation": e["example_translation"],
                        "audio_url": None,
                        "is_duplicate": dup,
                        "error": None,
                    }
                )
            yield {"type": "progress", "phase": "text", "processed": total, "total": total}
        else:
            for w in raw_words:
                items.append(
                    {
                        "input_word": w,
                        "word_type": "OTHER",
                        "article": None,
                        "german_word": w,
                        "plural": None,
                        "translation": "",
                        "example_sentence": "",
                        "example_translation": "",
                        "audio_url": None,
                        "is_duplicate": w.strip().lower() in existing,
                        "error": None,
                    }
                )

        if generate_audio and items:
            semaphore = asyncio.Semaphore(settings.VOCAB_BULK_TTS_CONCURRENCY)
            generated = 0
            failed = 0

            async def gen_one(item: dict):
                word = item["german_word"]
                async with semaphore:
                    try:
                        item["audio_url"], size_bytes = await self._store_audio(word)
                        return word, True, size_bytes
                    except ai_enrichment.AIServiceError as exc:
                        item["error"] = str(exc)
                        return word, False, str(exc)

            tasks = [asyncio.ensure_future(gen_one(item)) for item in items]

            yield {"type": "progress", "phase": "audio", "processed": 0, "total": total, "generated": 0, "failed": 0}
            for finished in asyncio.as_completed(tasks):
                word, ok, detail = await finished
                generated += 1 if ok else 0
                failed += 0 if ok else 1
                position = generated + failed

                if ok:
                    logger.info("Vocabulary bulk audio %d/%d: PASS (%dKB)", position, total, max(detail // 1024, 1))
                    yield {"type": "audio_result", "word": word, "ok": True, "size_kb": max(detail // 1024, 1)}
                else:
                    logger.warning("Vocabulary bulk audio %d/%d: FAIL — %s", position, total, detail)
                    yield {"type": "audio_result", "word": word, "ok": False, "reason": detail}

                yield {
                    "type": "progress",
                    "phase": "audio",
                    "processed": position,
                    "total": total,
                    "generated": generated,
                    "failed": failed,
                }

        for item in items:
            yield {"type": "item", **item}

        yield {"type": "done"}

    # ==========================
    # Save
    # ==========================

    async def bulk_save(self, lesson_id: UUID, items: list[dict]) -> dict:
        existing = self._existing_words_lower(lesson_id)
        next_order = self._next_order_index(lesson_id)

        saved = 0
        needs_review: list[dict] = []
        all_audio_urls = {it.get("audio_url") for it in items if it.get("audio_url")}
        kept_audio_urls: set[str] = set()

        for item in items:
            word = (item.get("german_word") or "").strip()

            if item.get("skip") or not word:
                continue

            is_dup = word.lower() in existing
            if is_dup and not item.get("force_duplicate"):
                needs_review.append({"word": word, "reason": "Dieses Wort existiert bereits."})
                continue

            translation = (item.get("translation") or "").strip()
            if not translation:
                needs_review.append({"word": word, "reason": "Übersetzung fehlt."})
                continue

            vocab = Vocabulary(
                lesson_id=lesson_id,
                german_word=word,
                article=item.get("article") or None,
                plural=item.get("plural") or None,
                translation=translation,
                example_sentence=item.get("example_sentence") or None,
                example_translation=item.get("example_translation") or None,
                audio_url=item.get("audio_url") or None,
                audio_status=AUDIO_STATUS_GENERATED if item.get("audio_url") else AUDIO_STATUS_PENDING,
                audio_error=item.get("error") if not item.get("audio_url") else None,
                order_index=next_order,
                is_published=bool(item.get("is_published")),
            )
            self.db.add(vocab)

            next_order += 1
            existing.add(word.lower())
            saved += 1
            if item.get("audio_url"):
                kept_audio_urls.add(item["audio_url"])

        self.db.commit()

        # Anything generated during analyze but not actually saved
        # (skipped duplicates, rows the admin removed, validation
        # failures) would otherwise sit in storage forever unreferenced.
        for url in all_audio_urls - kept_audio_urls:
            await self._delete_audio(url)

        return {"saved_count": saved, "needs_review": needs_review}
