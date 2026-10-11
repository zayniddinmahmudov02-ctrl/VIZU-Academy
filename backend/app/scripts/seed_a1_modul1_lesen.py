"""Seed: VIZU-DEUTSCH A1 — Modul 1 — Lektion 1 "Herzlich Willkommen!" — Lesen.

Book page 8: three texts (Tom, Anna, Tom und Anna), 5 automatically graded
questions each (15 in total, 1 point each -> score out of 100). Every
question is answerable from its text alone.

Only this lesson's Lesen is touched. The lesson must already exist
(Language 'de' -> Course level 'A1' -> Module number 1 -> Lesson number 1);
it is never created or renamed. Idempotent: a text that already exists (same
title in the lesson) is left as it is, so admin edits are never overwritten.

    python -m app.scripts.seed_a1_modul1_lesen --dry-run
    python -m app.scripts.seed_a1_modul1_lesen
    python -m app.scripts.seed_a1_modul1_lesen --lesson-id <uuid>   # explicit target
"""

import argparse
from uuid import UUID

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.course import Course
from app.models.language import Language
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.reading import Reading
from app.models.reading_option import ReadingOption
from app.models.reading_question import ReadingQuestion

MC, TF = "MULTIPLE_CHOICE", "TRUE_FALSE"
R, F = "Richtig", "Falsch"


def _p(text: str) -> str:
    return f"<p>{text}</p>"


TEXTS = [
    {
        "title": "Text 1: Tom",
        "content": _p("Hallo! Ich heiße Tom und ich bin 10 Jahre alt. Ich komme aus Usbekistan und wohne in Taschkent. "
                      "Ich gehe in die Schule und lerne Deutsch. Ich mag Fußball. Danke!"),
        "questions": [
            (MC, "Wie alt ist Tom?", ["8 Jahre", "10 Jahre", "12 Jahre"], 1, "Matnda: „Ich bin 10 Jahre alt.“"),
            (MC, "Wo wohnt Tom?", ["In Berlin", "In München", "In Taschkent"], 2, "Matnda: „Ich wohne in Taschkent.“"),
            (TF, "Tom kommt aus Usbekistan.", [R, F], 0, "Matnda: „Ich komme aus Usbekistan.“"),
            (MC, "Was lernt Tom in der Schule?", ["Englisch", "Deutsch", "Russisch"], 1, "Matnda: „Ich gehe in die Schule und lerne Deutsch.“"),
            (MC, "Was mag Tom?", ["Malen", "Fußball", "Musik"], 1, "Matnda: „Ich mag Fußball.“"),
        ],
    },
    {
        "title": "Text 2: Anna",
        "content": _p("Hallo! Ich heiße Anna und ich bin 9 Jahre alt. Ich komme aus Usbekistan und wohne in Taschkent. "
                      "Ich gehe in die Schule und lerne Deutsch. Ich mag Malen und Musik. Danke!"),
        "questions": [
            (TF, "Anna ist 9 Jahre alt.", [R, F], 0, "Matnda: „Ich bin 9 Jahre alt.“"),
            (MC, "Was mag Anna?", ["Fußball und Tennis", "Malen und Musik", "Lesen und Schwimmen"], 1, "Matnda: „Ich mag Malen und Musik.“"),
            (MC, "Woher kommt Anna?", ["Aus Deutschland", "Aus Usbekistan", "Aus Österreich"], 1, "Matnda: „Ich komme aus Usbekistan.“"),
            (TF, "Anna wohnt in Berlin.", [R, F], 1, "Noto'g'ri — matnda: „Ich wohne in Taschkent.“"),
            (MC, "Was lernt Anna?", ["Deutsch", "Französisch", "Englisch"], 0, "Matnda: „Ich gehe in die Schule und lerne Deutsch.“"),
        ],
    },
    {
        "title": "Text 3: Tom und Anna",
        "content": _p("Hallo! Wir heißen Tom und Anna. Wir sind 10 und 9 Jahre alt. Wir kommen aus Usbekistan und wohnen in Taschkent. "
                      "Wir gehen in die Schule und lernen Deutsch. Wir mögen Fußball, Malen und Musik. Danke!"),
        "questions": [
            (TF, "Tom und Anna kommen aus Deutschland.", [R, F], 1, "Noto'g'ri — matnda: „Wir kommen aus Usbekistan.“"),
            (MC, "Wie alt sind Tom und Anna?", ["10 und 9 Jahre", "9 und 8 Jahre", "11 und 10 Jahre"], 0, "Matnda: „Wir sind 10 und 9 Jahre alt.“"),
            (MC, "Wo wohnen Tom und Anna?", ["In Samarkand", "In Taschkent", "In Buchara"], 1, "Matnda: „Wir wohnen in Taschkent.“"),
            (TF, "Tom und Anna gehen in die Schule.", [R, F], 0, "Matnda: „Wir gehen in die Schule.“"),
            (MC, "Was mögen Tom und Anna?", ["Fußball, Malen und Musik", "Tennis und Schwimmen", "Lesen und Kochen"], 0,
             "Matnda: „Wir mögen Fußball, Malen und Musik.“"),
        ],
    },
]


def find_a1_modul1_lesson1(db) -> Lesson | None:
    language = db.scalar(select(Language).where(Language.code == "de", Language.deleted_at.is_(None)))
    if language is None:
        return None
    course = db.scalar(select(Course).where(Course.language_id == language.id, Course.level == "A1").order_by(Course.order_index))
    if course is None:
        return None
    module = db.scalar(select(Module).where(Module.course_id == course.id, Module.number == 1))
    if module is None:
        return None
    return db.scalar(select(Lesson).where(Lesson.module_id == module.id, Lesson.number == 1))


def seed(db, lesson: Lesson, dry_run: bool) -> int:
    existing = {r.title for r in db.scalars(select(Reading).where(Reading.lesson_id == lesson.id))}
    created = 0
    for order, text in enumerate(TEXTS, start=1):
        if text["title"] in existing:
            print(f"  SKIP   {text['title']!r} (already exists)")
            continue
        print(f"  CREATE {text['title']!r} with {len(text['questions'])} questions")
        created += 1
        if dry_run:
            continue
        reading = Reading(lesson_id=lesson.id, title=text["title"], content=text["content"], order_index=order, is_published=True)
        db.add(reading)
        db.flush()
        for q_order, (qtype, question, options, correct, explanation) in enumerate(text["questions"], start=1):
            q = ReadingQuestion(reading_id=reading.id, question=question, explanation=explanation, order_index=q_order,
                                is_published=True, question_type=qtype, points=1)
            db.add(q)
            db.flush()
            for o_order, option in enumerate(options, start=1):
                db.add(ReadingOption(question_id=q.id, option_text=option, is_correct=(o_order - 1 == correct), order_index=o_order))
    if not dry_run:
        db.commit()
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed A1 Modul 1 Lektion 1 Lesen (3 texts, 15 questions).")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created, write nothing.")
    parser.add_argument("--lesson-id", type=UUID, help="Target lesson explicitly instead of looking up A1 / Modul 1 / Lektion 1.")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        lesson = db.get(Lesson, args.lesson_id) if args.lesson_id else find_a1_modul1_lesson1(db)
        if lesson is None:
            print("ERROR: lesson not found (de -> A1 -> Module 1 -> Lesson 1, or --lesson-id). Nothing changed.")
            raise SystemExit(1)
        print(f"Lesson: {lesson.id} — {lesson.number}. {lesson.title}")
        created = seed(db, lesson, args.dry_run)
        print(("DRY RUN — " if args.dry_run else "") + f"{created} text(s) {'would be' if args.dry_run else ''} created.".replace("  ", " "))
    finally:
        db.close()


if __name__ == "__main__":
    main()
