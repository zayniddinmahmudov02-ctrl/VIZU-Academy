"""One-off data repair: publishes existing Reading/Writing/Listening rows
that already have real content but are still sitting unpublished
(is_published=False, the column's default) and therefore invisible to
students at GET /readings|writings|listenings/lesson/{id} (both filter
published_only=True — see reading/listening/writing routers).

This does NOT change any schema, create any table, or touch any other
system — it only flips the existing `is_published` flag (already used
by Video/Grammar/Vocabulary/Quiz the same way) on rows that already
have real content, using the exact same publish() method the admin UI's
"Veröffentlichen" button already calls for Hören/Schreiben.

Rules (never publishes a row that looks incomplete/placeholder):
  - Reading:  is_published=False AND content is non-empty  -> publish.
  - Writing:  is_published=False AND instruction is non-empty -> publish.
  - Listening: is_published=False AND audio_url is non-empty -> publish.
    A Listening row with no real audio_url yet (audio_url="") is left
    exactly as-is — publishing it would show a broken/empty player,
    which is exactly what the is_published gate exists to prevent (see
    seed_lesson_1.py's own docstring on this).

Idempotent: rows already published, or without real content, are left
untouched — a second run reports 0 changes.

Run from the `backend/` directory:

    python -m app.scripts.publish_existing_lesson_content
"""

import app.models  # noqa: F401 — registers every model with Base before querying

from app.db.session import SessionLocal
from app.models.listening import Listening
from app.models.reading import Reading
from app.models.writing import Writing


def main() -> None:
    db = SessionLocal()
    try:
        readings = (
            db.query(Reading)
            .filter(Reading.is_published.is_(False), Reading.content.isnot(None), Reading.content != "")
            .all()
        )
        for r in readings:
            print(f"  [Lesen] publishing '{r.title}' (lesson_id={r.lesson_id})")
            r.is_published = True

        writings = (
            db.query(Writing)
            .filter(Writing.is_published.is_(False), Writing.instruction.isnot(None), Writing.instruction != "")
            .all()
        )
        for w in writings:
            print(f"  [Schreiben] publishing '{w.title}' (lesson_id={w.lesson_id})")
            w.is_published = True

        listenings = (
            db.query(Listening)
            .filter(Listening.is_published.is_(False), Listening.audio_url.isnot(None), Listening.audio_url != "")
            .all()
        )
        for l in listenings:
            print(f"  [Hören] publishing '{l.title}' (lesson_id={l.lesson_id})")
            l.is_published = True

        db.commit()
        print(
            f"Done. Published {len(readings)} Lesen, {len(listenings)} Hören, "
            f"{len(writings)} Schreiben row(s) that had real content but were unpublished."
        )
        if not readings and not listenings and not writings:
            print(
                "Nothing to publish — either everything with real content is already "
                "published, or no rows with real content exist yet."
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
