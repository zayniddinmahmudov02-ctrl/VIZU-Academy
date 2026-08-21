import re
from typing import AsyncIterator
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.storage.factory import StorageFactory
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.vocabulary import Vocabulary
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
    """Backs the "Wörter importieren" bulk generator: paste a word list,
    enrich it via Gemini text-only (article/plural/word-type/translation/
    example sentence — see ai_enrichment.py), preview, edit, then save.
    No audio involved anywhere in this flow — pronunciation audio isn't
    part of the vocabulary feature currently."""

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

    async def _delete_audio(self, audio_url: str | None) -> None:
        """Manual audio uploads (FileUploadField, folder="audio") still
        exist as a plain optional field — this cleans up the stored file
        for our own storage-backed URLs when a word's audio is replaced
        or the word itself is deleted. Never touches externally-hosted
        URLs an admin may have pasted in by hand."""
        if not audio_url:
            return
        prefix = self.storage.url("")  # e.g. "/uploads/"
        if not audio_url.startswith(prefix):
            return
        await self.storage.delete(audio_url[len(prefix):])

    # ==========================
    # Analyze (streamed progress) — TEXT enrichment only
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
                # Never forward str(exc) to the client -- it embeds Gemini's
                # raw error response body. Log it server-side, surface a
                # clean, human-readable message instead.
                print(f"[bulk vocabulary] Gemini enrichment failed: {exc}")
                if exc.transient:
                    yield {
                        "type": "error",
                        "code": "GEMINI_UNAVAILABLE",
                        "message": (
                            "Gemini ist momentan stark ausgelastet. Dieser Abschnitt wurde "
                            "übersprungen und kann später erneut generiert werden."
                        ),
                    }
                else:
                    yield {
                        "type": "error",
                        "code": "GEMINI_ERROR",
                        "message": (
                            "Die automatische Vervollständigung ist fehlgeschlagen. Bitte versuche es "
                            "erneut oder deaktiviere „Automatisch vervollständigen“."
                        ),
                    }
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
                order_index=next_order,
                is_published=bool(item.get("is_published")),
            )
            self.db.add(vocab)

            next_order += 1
            existing.add(word.lower())
            saved += 1

        self.db.commit()

        return {"saved_count": saved, "needs_review": needs_review}

    # ==========================
    # Bulk delete
    # ==========================

    async def bulk_delete(self, lesson_id: UUID, vocabulary_ids: list[UUID]) -> int:
        """Deletes only the given IDs, scoped to lesson_id so a stray ID
        from another lesson (or a stale client-side selection) can never
        delete outside the lesson the admin is looking at. Cleans up any
        of our own stored audio files before removing the rows. Returns
        the number actually deleted."""

        rows = (
            self.db.query(Vocabulary)
            .filter(Vocabulary.lesson_id == lesson_id, Vocabulary.id.in_(vocabulary_ids))
            .all()
        )

        for row in rows:
            await self._delete_audio(row.audio_url)
            self.db.delete(row)

        self.db.commit()
        return len(rows)
