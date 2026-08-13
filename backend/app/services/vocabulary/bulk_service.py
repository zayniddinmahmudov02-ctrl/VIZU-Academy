import asyncio
import re
from typing import AsyncIterator
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.storage.factory import StorageFactory
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.vocabulary import (
    AUDIO_STATUS_GENERATED,
    AUDIO_STATUS_PENDING,
    Vocabulary,
)
from app.repositories.vocabulary import VocabularyRepository
from app.services.vocabulary import ai_enrichment

_LIST_MARKER_RE = re.compile(r"^\s*(\d+[.)]|[-*•])\s*")


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
    """Backs the "Wörter importieren" bulk generator (Gemini text
    enrichment only — article/plural/word-type/translation/example
    sentence, see ai_enrichment.py) and the admin's own microphone
    recording flow for vocabulary audio (see audio_processing.py). No
    audio is ever AI-generated — recordings are the admin's real voice,
    cleaned and repeated 3x. Reuses Vocabulary/VocabularyRepository and
    the same public "audio" storage folder manual uploads already use,
    so audio_url stays a plain public URL either way."""

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
    # Audio (public "audio" folder — same one manual uploads use)
    # ==========================

    async def _write_audio_file(self, word: str, wav_bytes: bytes) -> str:
        safe_stub = re.sub(r"[^a-zA-Z0-9]+", "_", word.lower()).strip("_") or "wort"
        path = f"audio/{uuid4().hex}_{safe_stub}.wav"

        destination = self.storage.ROOT / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(destination.write_bytes, wav_bytes)

        return self.storage.url(path)

    async def _delete_audio(self, audio_url: str | None) -> None:
        if not audio_url:
            return
        prefix = self.storage.url("")  # e.g. "/uploads/"
        if not audio_url.startswith(prefix):
            return  # not one of ours (e.g. a manually pasted external URL) — leave it alone
        await self.storage.delete(audio_url[len(prefix):])

    async def save_recorded_audio(self, vocabulary: Vocabulary, wav_bytes: bytes) -> str:
        """wav_bytes is the already-processed (cleaned + repeated 3x)
        WAV produced by POST /vocabularies/audio/process — this just
        persists it. New file stored and the DB row committed before the
        old file is deleted, so a mid-save failure never leaves the word
        without a playable audio_url."""

        if not wav_bytes.startswith(b"RIFF"):
            raise ValueError("Erwartete WAV-Audiodaten (verarbeitete Aufnahme).")

        old_url = vocabulary.audio_url
        new_url = await self._write_audio_file(vocabulary.german_word, wav_bytes)

        vocabulary.audio_url = new_url
        vocabulary.audio_status = AUDIO_STATUS_GENERATED
        vocabulary.audio_error = None
        self.db.commit()
        self.db.refresh(vocabulary)

        await self._delete_audio(old_url)

        return new_url

    def get_missing_audio(self, lesson_id: UUID) -> list[Vocabulary]:
        """Words still needing a recording — backs both "Audio: ❌ Fehlt"
        in the table and the "Audio nacheinander aufnehmen" sequential
        recording workflow. Anything not already GENERATED, regardless
        of how it got that way (never recorded, or a prior failure)."""
        return (
            self.db.query(Vocabulary)
            .filter(
                Vocabulary.lesson_id == lesson_id,
                Vocabulary.audio_status != AUDIO_STATUS_GENERATED,
            )
            .order_by(Vocabulary.order_index)
            .all()
        )

    # ==========================
    # Analyze (streamed progress) — TEXT enrichment only, never audio
    # ==========================

    async def analyze_stream(
        self,
        lesson_id: UUID,
        raw_words: list[str],
        auto_complete: bool,
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
                        "is_duplicate": dup,
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
                        "is_duplicate": w.strip().lower() in existing,
                    }
                )

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
                # Bulk import never produces audio (see spec: TTS is gone
                # from this flow) — every new word starts PENDING and
                # waits for the admin to record it, same as the 53
                # pre-existing words this feature was built to unblock.
                audio_url=None,
                audio_status=AUDIO_STATUS_PENDING,
                order_index=next_order,
                is_published=bool(item.get("is_published")),
            )
            self.db.add(vocab)

            next_order += 1
            existing.add(word.lower())
            saved += 1

        self.db.commit()

        return {"saved_count": saved, "needs_review": needs_review}
