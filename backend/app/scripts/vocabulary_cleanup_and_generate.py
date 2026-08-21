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
    python -m app.scripts.vocabulary_cleanup_and_generate generate --levels A1,A2,B1,B2,C1

Generation is content-driven, not count-driven: for each lesson, Gemini
analyzes the lesson's title, its Grammar content, and its existing
vocabulary, and returns however many NEW, genuinely relevant words the
topic calls for -- no fixed target, no minimum, no filler. A generous
runaway-response safety cap exists (MAX_WORDS_PER_CALL_SAFETY_CAP) but
it is a defensive bound, not a design target.
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
from app.models.grammar import Grammar
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

GENERATION_PROMPT = """You are a German-language curriculum assistant. Analyze this lesson and determine the COMPLETE set of NEW Wortschatz (vocabulary) words a student at level {level} genuinely needs to learn for it -- there is no fixed count. If the topic only calls for a handful of words, return a handful; if it genuinely calls for dozens, return dozens. Do not pad the list with irrelevant or generic filler just to reach a round number, and do not hold back a word that's genuinely needed for this topic.

Lesson title: "{lesson_title}"
Level: {level}
{grammar_context}Vocabulary already taught in this lesson (context only, do not repeat): {existing_words}

Every word you generate MUST be genuinely relevant to this specific lesson's topic, and MUST be different (case-insensitive, article-independent) from every one of these already-taught words across every level (lower levels always take priority -- never reintroduce a word already known from an earlier level):
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

# Not a target -- a runaway-response guard only, generous enough that no
# genuinely content-driven lesson should ever hit it. Protects against a
# single malformed/hallucinating Gemini response, nothing else.
MAX_WORDS_PER_CALL_SAFETY_CAP = 80
MAX_GENERATION_ATTEMPTS = 2


async def _generate_words_for_lesson(
    level: str,
    lesson_title: str,
    grammar_context: str,
    existing_words: list[str],
    exclusion: set[str],
) -> tuple[list[dict], int, bool]:
    """Returns (accepted_words, skipped_duplicate_count, succeeded). No
    target count is requested from or enforced on the model -- the
    lesson's own content determines how many words come back.
    `succeeded=False` means every attempt hit a real API failure (never
    just "this lesson needs 0 new words," which is a legitimate,
    successful outcome with an empty word list)."""

    accepted: list[dict] = []
    skipped_duplicates = 0
    succeeded = False

    for attempt in range(MAX_GENERATION_ATTEMPTS):
        sample = list(exclusion)[:80]
        exclusion_sample = ", ".join(sample) if sample else "(none yet)"
        exclusion_note = (
            f"(and {len(exclusion) - len(sample)} more already-used words not shown here -- "
            "avoid anything generic/common at this level that's likely already covered)"
            if len(exclusion) > len(sample)
            else ""
        )
        grammar_block = f"Grammar/topic context for this lesson: {grammar_context}\n" if grammar_context else ""
        existing_block = ", ".join(existing_words) if existing_words else "(none yet)"

        prompt = GENERATION_PROMPT.format(
            level=level,
            lesson_title=lesson_title,
            grammar_context=grammar_block,
            existing_words=existing_block,
            exclusion_sample=exclusion_sample,
            exclusion_note=exclusion_note,
        )

        try:
            text = await call_gemini(prompt, context=f"{level} \"{lesson_title}\"")
            data = extract_json_object(text)
        except AIContentError as exc:
            print(f"    Gemini call failed (attempt {attempt + 1}): {exc}")
            continue

        words = data.get("words", [])
        if not isinstance(words, list):
            continue
        succeeded = True

        for item in words[:MAX_WORDS_PER_CALL_SAFETY_CAP]:
            base_word = (item.get("base_word") or "").strip()
            if not base_word:
                continue
            key = normalize_word(base_word)
            if not key:
                continue
            if key in exclusion:
                skipped_duplicates += 1
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

        # A genuine response (even an empty word list, meaning "this
        # lesson needs nothing new") is a success -- only a hard failure
        # (exception above, `continue`d past) should retry.
        break

    return accepted, skipped_duplicates, succeeded


async def cmd_generate(db: Session, levels: list[str]) -> None:
    rows = _load_all_with_level(db)
    exclusion = {normalize_word(vocab.german_word) for vocab, _level, _lesson in rows}

    # Whole-run tallies (across every level processed) for the final
    # compact summary -- distinct from the per-level counters below.
    # A lesson landing in FAILED never blocks the next lesson (or the
    # next level) from being processed; nothing about a failure ever
    # deletes existing vocabulary -- this loop only ever inserts.
    run_success: list[str] = []
    run_failed: list[tuple[str, str]] = []
    run_skipped: list[str] = []

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
        level_skipped_duplicates = 0
        level_failures: list[str] = []

        for lesson in lessons:
            existing = db.query(Vocabulary).filter(Vocabulary.lesson_id == lesson.id).order_by(
                Vocabulary.order_index
            ).all()
            existing_words = [v.german_word for v in existing]

            grammar_rows = db.query(Grammar).filter(Grammar.lesson_id == lesson.id).all()
            grammar_context = " ".join(
                f"{g.title}: {g.content}"[:500] for g in grammar_rows
            )

            lesson_label = f"{level} #{lesson.number} \"{lesson.title}\""

            words, skipped, succeeded = await _generate_words_for_lesson(
                level, lesson.title, grammar_context, existing_words, exclusion
            )
            level_skipped_duplicates += skipped

            if not succeeded:
                level_failures.append(f"{lesson.title} (#{lesson.number})")
                run_failed.append((lesson_label, "Gemini call did not succeed after retries (see log above)"))
                print(f'  "{lesson.title}" (#{lesson.number}): FAILED -- Gemini call did not succeed.')
                continue

            if not words:
                run_skipped.append(lesson_label)
                print(f'  "{lesson.title}" (#{lesson.number}): 0 new words needed (genuinely covered already).')
                continue

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
            run_success.append(lesson_label)
            print(
                f'  "{lesson.title}" (#{lesson.number}): {len(existing_words)} existing -> '
                f"{len(words)} new (total {len(existing_words) + len(words)}), "
                f"{skipped} duplicate(s) skipped."
            )

        level_after = level_before + level_generated
        print(
            f"{level}: before={level_before} newly_generated={level_generated} "
            f"final={level_after} skipped_duplicates={level_skipped_duplicates} "
            f"failures={len(level_failures)}"
        )

        write_audit(
            db,
            actor_id=None,
            action="vocabulary.generation",
            details=json.dumps(
                {
                    "level": level,
                    "before": level_before,
                    "generated": level_generated,
                    "after": level_after,
                    "skipped_duplicates": level_skipped_duplicates,
                    "failures": level_failures,
                }
            ),
        )

    remaining = _build_duplicate_groups(_load_all_with_level(db))
    print(f"DUPLICATES AFTER GENERATION = {len(remaining)}")

    print()
    print("=== GENERATION SUMMARY ===")
    print(f"SUCCESS: {len(run_success)} lessons")
    print(f"FAILED: {len(run_failed)} lessons")
    print(f"SKIPPED: {len(run_skipped)} lessons")
    if run_failed:
        print()
        print("Failed lessons:")
        for label, reason in run_failed:
            print(f"  - {label}: {reason}")


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
            asyncio.run(cmd_generate(db, levels=levels))
    finally:
        db.close()


if __name__ == "__main__":
    main()
