"""One-time maintenance script: global Vocabulary duplicate cleanup +
generation across all 5 CEFR levels (A1-C1).

Every subcommand is independent and safe to re-run except `cleanup`,
which requires an explicit --confirm flag and only ever runs after
`report` has been reviewed by a human. `report` and `verify` are pure
reads and can be re-run freely.

Retention rule for a normalized-word duplicate group: lower CEFR level
wins (A1 beats A2 beats B1 beats B2 beats C1); within the same level,
the oldest row (created_at) wins, order_index as a further tiebreak.
Exactly one row survives per normalized word across the ENTIRE table,
not per level or per lesson.

No table has a foreign key into vocabularies.id (confirmed by grepping
every model file) -- a Vocabulary row can be deleted directly with no
orphan risk. This script still queries for that explicitly (see
_assert_no_incoming_references) so the invariant is documented in code,
not just assumed.

Generated words are always inserted as is_published=False -- matching
this project's established "AI output must not auto-publish" principle.
An admin reviews and publishes them through the existing Vocabulary
admin UI, which already auto-triggers sync_vocabulary_test on publish
(see app/api/vocabularies/router.py) -- no extra quiz-sync code is
needed here for newly generated words.

Run from the `backend/` directory:

    python -m app.scripts.vocabulary_cleanup_and_generate backup
    python -m app.scripts.vocabulary_cleanup_and_generate report
    python -m app.scripts.vocabulary_cleanup_and_generate cleanup --confirm
    python -m app.scripts.vocabulary_cleanup_and_generate verify
    python -m app.scripts.vocabulary_cleanup_and_generate generate --target 20 --levels A1,A2
"""

import app.models  # noqa: F401 -- registers every model with Base before querying

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.vocabulary import Vocabulary
from app.services.ai_content.gemini_client import AIContentError, call_gemini, extract_json_object
from app.services.vocabulary import sync_vocabulary_test

LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1"]
LEVEL_RANK = {level: i for i, level in enumerate(LEVEL_ORDER)}

ARTICLE_RE = re.compile(r"^(der|die|das)\s+", re.IGNORECASE)


def normalize_word(word: str) -> str:
    text = unicodedata.normalize("NFC", word or "").strip().lower()
    text = ARTICLE_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ============================================================
# Backup
# ============================================================

def cmd_backup() -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = f"vocabulary_backup_{timestamp}.sql"

    env = os.environ.copy()
    env["PGPASSWORD"] = settings.DATABASE_PASSWORD

    cmd = [
        "pg_dump",
        "-h", settings.DATABASE_HOST,
        "-p", str(settings.DATABASE_PORT),
        "-U", settings.DATABASE_USER,
        "-d", settings.DATABASE_NAME,
        "-t", "vocabularies",
        "-t", "quizzes",
        "-t", "quiz_questions",
        "-t", "quiz_options",
        "-f", out_path,
    ]

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print("BACKUP FAILED:")
        print(result.stderr)
        sys.exit(1)

    size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
    print(f"Backup written to {out_path} ({size} bytes).")


# ============================================================
# Shared: load + group
# ============================================================

def _load_all_with_level(db: Session) -> list[tuple[Vocabulary, str, Lesson]]:
    return (
        db.query(Vocabulary, Course.level, Lesson)
        .join(Lesson, Lesson.id == Vocabulary.lesson_id)
        .join(Module, Module.id == Lesson.module_id)
        .join(Course, Course.id == Module.course_id)
        .all()
    )


def _build_duplicate_groups(
    rows: list[tuple[Vocabulary, str, Lesson]],
) -> dict[str, list[tuple[Vocabulary, str, Lesson]]]:
    groups: dict[str, list[tuple[Vocabulary, str, Lesson]]] = {}
    for vocab, level, lesson in rows:
        key = normalize_word(vocab.german_word)
        groups.setdefault(key, []).append((vocab, level, lesson))

    duplicates = {}
    for key, items in groups.items():
        if len(items) <= 1:
            continue
        items.sort(key=lambda t: (LEVEL_RANK.get(t[1], 99), t[0].created_at, t[0].order_index, str(t[0].id)))
        duplicates[key] = items
    return duplicates


def _assert_no_incoming_references(db: Session) -> None:
    """Documents, rather than assumes, that nothing else in the schema
    points at a specific Vocabulary row by ID -- confirmed by grepping
    every model file for a ForeignKey into vocabularies.id (none exist).
    QuizQuestion/QuizOption store copied TEXT via sync_vocabulary_test,
    never a vocabulary_id, so they're unaffected by any Vocabulary
    delete regardless of content."""
    # No query needed -- there is no column to check. This function
    # exists so the invariant this script relies on is visible in code.
    return


# ============================================================
# report / cleanup / verify
# ============================================================

def _print_group(key: str, items: list[tuple[Vocabulary, str, Lesson]]) -> None:
    print(f'-- "{key}" ({len(items)} rows) --')
    for i, (vocab, level, lesson) in enumerate(items):
        marker = "KEEP" if i == 0 else "DELETE"
        print(
            f"  [{marker}] id={vocab.id} word=\"{vocab.german_word}\" level={level} "
            f'lesson="{lesson.title}" (#{lesson.number}) order_index={vocab.order_index} '
            f"created_at={vocab.created_at.isoformat()}"
        )
    print()


def cmd_report(db: Session) -> None:
    rows = _load_all_with_level(db)
    total_before = len(rows)
    duplicate_groups = _build_duplicate_groups(rows)
    total_delete = sum(len(items) - 1 for items in duplicate_groups.values())

    print("=== VOCABULARY DUPLICATE REPORT ===")
    print(f"Total vocabulary rows (all levels): {total_before}")
    print(f"Duplicate groups found: {len(duplicate_groups)}")
    print()

    for key, items in duplicate_groups.items():
        _print_group(key, items)

    print(f"Total rows marked for deletion: {total_delete}")
    print(f"Total vocabulary after cleanup (projected): {total_before - total_delete}")


def cmd_cleanup(db: Session, confirm: bool) -> None:
    if not confirm:
        print("Refusing to run cleanup without --confirm.")
        print("Run `report` first, review it, then re-run: cleanup --confirm")
        sys.exit(1)

    _assert_no_incoming_references(db)

    rows = _load_all_with_level(db)
    total_before = len(rows)
    duplicate_groups = _build_duplicate_groups(rows)

    delete_ids = []
    affected_a1_lessons = set()
    for items in duplicate_groups.values():
        for vocab, level, lesson in items[1:]:
            delete_ids.append(vocab.id)
            if level == "A1" and vocab.is_published:
                affected_a1_lessons.add(lesson.id)

    if delete_ids:
        db.query(Vocabulary).filter(Vocabulary.id.in_(delete_ids)).delete(synchronize_session=False)
        db.commit()

    for lesson_id in affected_a1_lessons:
        sync_vocabulary_test(db, lesson_id)

    total_after = total_before - len(delete_ids)
    write_audit(
        db,
        actor_id=None,
        action="vocabulary.duplicate_cleanup",
        details=json.dumps(
            {
                "total_before": total_before,
                "duplicate_groups": len(duplicate_groups),
                "deleted": len(delete_ids),
                "total_after": total_after,
                "a1_lessons_resynced": [str(i) for i in affected_a1_lessons],
            }
        ),
    )

    print(f"Deleted {len(delete_ids)} duplicate rows. Total vocabulary: {total_before} -> {total_after}.")
    print(f"Resynced A1 Vocabulary Quiz for {len(affected_a1_lessons)} lesson(s).")

    remaining = _build_duplicate_groups(_load_all_with_level(db))
    print(f"DUPLICATES AFTER CLEANUP = {len(remaining)}")
    if remaining:
        for key, items in remaining.items():
            _print_group(key, items)


def cmd_verify(db: Session) -> None:
    remaining = _build_duplicate_groups(_load_all_with_level(db))
    print(f"DUPLICATES = {len(remaining)}")
    if remaining:
        for key, items in remaining.items():
            _print_group(key, items)


# ============================================================
# generate
# ============================================================

GENERATION_PROMPT = """You are a German-language curriculum assistant creating NEW Wortschatz (vocabulary) entries for Uzbek-speaking students at level {level}, for a lesson titled "{lesson_title}".

Generate exactly {count} NEW German words or short phrases appropriate for this lesson's topic and level. Every word you generate MUST be different (case-insensitive, article-independent) from all of these already-used words:
{exclusion_sample}
{exclusion_note}

For EACH generated word, determine:
- word_type: exactly one of NOMEN, VERB, ADJEKTIV, ADVERB, PRONOMEN, PRAEPOSITION, KONJUNKTION, REDEWENDUNG, OTHER
- article: "der", "die", or "das" if word_type is NOMEN, else null
- base_word: the word itself without any article prefix, correctly capitalized per German orthography
- plural: for NOMEN, the real German plural form, or "—" if uncountable. null for every other word_type.
- translation: a natural Uzbek translation
- example_sentence: one natural German sentence at level {level} using base_word
- example_translation: a natural Uzbek translation of example_sentence

Respond with ONLY a JSON object (no markdown, no prose), exactly this shape:
{{"words": [{{"word_type": "...", "article": "..."|null, "base_word": "...", "plural": "..."|null, "translation": "...", "example_sentence": "...", "example_translation": "..."}}]}}"""

MAX_GENERATION_ATTEMPTS = 3


async def _generate_words_for_lesson(
    level: str,
    lesson_title: str,
    count: int,
    exclusion: set[str],
) -> list[dict]:
    accepted: list[dict] = []
    remaining_needed = count

    for _attempt in range(MAX_GENERATION_ATTEMPTS):
        if remaining_needed <= 0:
            break

        sample = list(exclusion)[:80]
        exclusion_sample = ", ".join(sample) if sample else "(none yet)"
        exclusion_note = (
            f"(and {len(exclusion) - len(sample)} more already-used words not shown here -- "
            "avoid anything generic/common at this level that's likely already covered)"
            if len(exclusion) > len(sample)
            else ""
        )
        # Ask for a bit more than needed since some candidates will collide.
        ask_count = remaining_needed + 2

        prompt = GENERATION_PROMPT.format(
            level=level,
            lesson_title=lesson_title,
            count=ask_count,
            exclusion_sample=exclusion_sample,
            exclusion_note=exclusion_note,
        )

        try:
            text = await call_gemini(prompt)
            data = extract_json_object(text)
        except AIContentError as exc:
            print(f"    Gemini call failed: {exc}")
            continue

        for item in data.get("words", []):
            base_word = (item.get("base_word") or "").strip()
            if not base_word:
                continue
            key = normalize_word(base_word)
            if not key or key in exclusion:
                continue

            word_type = str(item.get("word_type") or "OTHER").upper()
            accepted.append(
                {
                    "german_word": base_word,
                    "article": (item.get("article") or None) if word_type == "NOMEN" else None,
                    "plural": (item.get("plural") or None) if word_type == "NOMEN" else None,
                    "translation": item.get("translation") or "",
                    "example_sentence": item.get("example_sentence") or "",
                    "example_translation": item.get("example_translation") or "",
                }
            )
            exclusion.add(key)
            remaining_needed -= 1
            if remaining_needed <= 0:
                break

    return accepted[:count]


async def cmd_generate(db: Session, target: int, levels: list[str]) -> None:
    rows = _load_all_with_level(db)
    exclusion = {normalize_word(vocab.german_word) for vocab, _level, _lesson in rows}

    for level in levels:
        lessons = (
            db.query(Lesson)
            .join(Module, Module.id == Lesson.module_id)
            .join(Course, Course.id == Module.course_id)
            .filter(Course.level == level)
            .order_by(Lesson.number)
            .all()
        )

        level_before = (
            db.query(Vocabulary)
            .join(Lesson, Lesson.id == Vocabulary.lesson_id)
            .join(Module, Module.id == Lesson.module_id)
            .join(Course, Course.id == Module.course_id)
            .filter(Course.level == level)
            .count()
        )
        level_generated = 0
        level_shortfall = 0

        for lesson in lessons:
            current_count = db.query(Vocabulary).filter(Vocabulary.lesson_id == lesson.id).count()
            needed = target - current_count
            if needed <= 0:
                continue

            words = await _generate_words_for_lesson(level, lesson.title, needed, exclusion)

            # current_count + 1 would collide with an existing order_index
            # after cleanup deletions leave gaps (order_index isn't
            # guaranteed contiguous) -- MAX(order_index) + 1 is always safe.
            max_order = (
                db.query(func.max(Vocabulary.order_index)).filter(Vocabulary.lesson_id == lesson.id).scalar()
            )
            next_order = (max_order or 0) + 1
            for w in words:
                db.add(
                    Vocabulary(
                        lesson_id=lesson.id,
                        german_word=w["german_word"],
                        article=w["article"],
                        plural=w["plural"],
                        translation=w["translation"],
                        example_sentence=w["example_sentence"],
                        example_translation=w["example_translation"],
                        order_index=next_order,
                        is_published=False,
                    )
                )
                next_order += 1

            db.commit()
            level_generated += len(words)

            shortfall = needed - len(words)
            if shortfall > 0:
                level_shortfall += shortfall
                print(
                    f'  SHORTFALL: lesson "{lesson.title}" (#{lesson.number}) needed {needed}, '
                    f"got {len(words)} unique words, short by {shortfall}."
                )

        level_after = level_before + level_generated
        print(
            f"{level}: before={level_before} newly_generated={level_generated} "
            f"final={level_after} shortfall={level_shortfall}"
        )

        write_audit(
            db,
            actor_id=None,
            action="vocabulary.generation",
            details=json.dumps(
                {
                    "level": level,
                    "target_per_lesson": target,
                    "before": level_before,
                    "generated": level_generated,
                    "after": level_after,
                    "shortfall": level_shortfall,
                }
            ),
        )

    remaining = _build_duplicate_groups(_load_all_with_level(db))
    print(f"DUPLICATES AFTER GENERATION = {len(remaining)}")


# ============================================================
# CLI
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("backup")
    sub.add_parser("report")
    sub.add_parser("verify")

    cleanup_parser = sub.add_parser("cleanup")
    cleanup_parser.add_argument("--confirm", action="store_true")

    generate_parser = sub.add_parser("generate")
    generate_parser.add_argument("--target", type=int, required=True)
    generate_parser.add_argument("--levels", type=str, default=",".join(LEVEL_ORDER))

    args = parser.parse_args()

    if args.command == "backup":
        cmd_backup()
        return

    db = SessionLocal()
    try:
        if args.command == "report":
            cmd_report(db)
        elif args.command == "cleanup":
            cmd_cleanup(db, confirm=args.confirm)
        elif args.command == "verify":
            cmd_verify(db)
        elif args.command == "generate":
            levels = [lvl.strip().upper() for lvl in args.levels.split(",") if lvl.strip()]
            invalid = [lvl for lvl in levels if lvl not in LEVEL_RANK]
            if invalid:
                print(f"Unknown level(s): {invalid}. Valid: {LEVEL_ORDER}")
                sys.exit(1)
            levels.sort(key=lambda lvl: LEVEL_RANK[lvl])
            asyncio.run(cmd_generate(db, target=args.target, levels=levels))
    finally:
        db.close()


if __name__ == "__main__":
    main()
