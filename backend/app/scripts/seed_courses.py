"""Bootstrap script: seeds the Course/Module/Lesson structural hierarchy
from the exact levels, lesson counts, lesson numbers and lesson titles
already shown on the public site (frontend/src/constants/course-content.ts)
— that file is the source of truth; this script mirrors it and does not
invent any level, lesson count, or title.

Idempotent and additive only:
  - A Course already existing for (language, level) is left untouched
    (never duplicated, never overwritten) — including the pre-existing
    A1 row, which is reused as-is.
  - Each Course is topped up to exactly one Module (this project's course
    structure requires every Lesson to belong to a Module; the public
    site itself has no module-grouping concept, so one wrapping Module
    per Course is the minimal structural fit).
  - Each Lesson is matched by (module_id, number): existing ones are
    counted and never duplicated or retitled, only the missing ones are
    created. If a level already has MORE lessons than the canonical
    count, nothing is deleted — the discrepancy is only reported.
  - Never creates video/grammar/vocabulary/assessment content — those
    stay empty until an admin adds them.

Run from the `backend/` directory:

    python -m app.scripts.seed_courses
"""

import app.models  # noqa: F401 — registers every model with Base before querying

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.course import Course
from app.models.language import Language
from app.models.lesson import Lesson
from app.models.module import Module

# Mirrors frontend/src/constants/course-content.ts (COURSE_CONTENT) and
# frontend/src/constants/levels.ts (germanLevels) exactly.
COURSE_CONTENT = {
    "A1": {
        "title": "German Beginner",
        "description": "Deutsch von Anfang an lernen.",
        "lessons": [
            "Begrüßung", "Familie", "Freizeit", "Essen und Trinken", "Wohnen",
            "Berufe", "Tagesablauf", "Einkaufen", "Verkehr", "Gesundheit",
            "Reisen", "Feiertage", "Natur", "Prüfungsvorbereitung",
        ],
    },
    "A2": {
        "title": "German Elementary",
        "description": "Deutsch sicher im Alltag verwenden.",
        "lessons": [
            "Wiederholung A1", "Freunde", "Wohnung", "Arbeit", "Medien",
            "Umwelt", "Kleidung", "Gesund leben", "Urlaub", "Technik",
            "Service", "Kultur", "Kommunikation", "Prüfungsvorbereitung",
        ],
    },
    "B1": {
        "title": "German Intermediate",
        "description": "Selbstständig kommunizieren.",
        "lessons": [
            "Wiederholung A2", "Bildung", "Beruf", "Studium", "Bewerbung",
            "Gesellschaft", "Politik", "Wirtschaft", "Technologie", "Umwelt",
            "Gesundheit", "Reisen", "Kultur", "Literatur", "Medien",
            "Diskussion", "Präsentation", "Argumentation", "Schriftliche Kommunikation",
            "Prüfungsvorbereitung",
        ],
    },
    "B2": {
        "title": "German Upper Intermediate",
        "description": "Komplexe Themen sicher beherrschen.",
        "lessons": [
            "Wiederholung B1", "Wissenschaft", "Forschung", "Digitalisierung", "Globalisierung",
            "Arbeitswelt", "Migration", "Integration", "Recht", "Medizin",
            "Psychologie", "Klimawandel", "Nachhaltigkeit", "Innovation", "Literatur",
            "Philosophie", "Kunst", "Debatte", "Analyse", "Bericht",
            "Zusammenfassung", "Erörterung", "Statistik", "Grafikbeschreibung", "Interview",
            "Projektarbeit", "Präsentation", "Diskussion", "Argumentation", "Prüfungsvorbereitung",
        ],
    },
    "C1": {
        "title": "German Advanced",
        "description": "Akademisches und professionelles Deutsch.",
        "lessons": [
            "Akademisches Schreiben", "Wissenschaftliche Sprache", "Fachtexte", "Diskussion", "Debatte",
            "Analyse", "Interpretation", "Literatur", "Politik", "Wirtschaft",
            "Recht", "Philosophie", "Ethik", "Kultur", "Medien",
            "Rhetorik", "Vortrag", "Forschung", "Projekt", "Zusammenfassung",
            "Argumentation", "Prüfungsvorbereitung",
        ],
    },
}

LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1"]


def main() -> None:
    db = SessionLocal()
    created_courses = 0
    created_modules = 0
    created_lessons = 0
    over_target: list[str] = []

    try:
        language = db.scalar(select(Language).where(Language.code == "de", Language.deleted_at.is_(None)))
        if language is None:
            print("ERROR: no 'de' Language row found — run seed_default_language first.")
            return

        for sort_index, level in enumerate(LEVEL_ORDER, start=1):
            data = COURSE_CONTENT[level]
            expected_count = len(data["lessons"])

            course = db.scalar(
                select(Course).where(Course.language_id == language.id, Course.level == level)
            )
            if course is None:
                course = Course(
                    language_id=language.id,
                    level=level,
                    title=f"{level} Stufe",
                    description=data["description"],
                    order_index=sort_index,
                    is_active=True,
                )
                db.add(course)
                db.flush()
                created_courses += 1
                print(f"Created course: {level} ({course.id})")
            else:
                print(f"Course already exists: {level} — left untouched.")

            module = db.scalar(select(Module).where(Module.course_id == course.id))
            if module is None:
                module = Module(
                    course_id=course.id,
                    number=1,
                    title=data["title"],
                    description=data["description"],
                    order_index=1,
                    is_active=True,
                )
                db.add(module)
                db.flush()
                created_modules += 1
                print(f"  Created module for {level}.")
            else:
                print(f"  Module already exists for {level} — left untouched.")

            existing_count = db.scalar(
                select(func.count()).select_from(Lesson).where(Lesson.module_id == module.id)
            )

            if existing_count > expected_count:
                msg = (
                    f"    DISCREPANCY: {level} has {existing_count} lessons, more than the "
                    f"canonical count of {expected_count}. Not deleting anything — review manually."
                )
                print(msg)
                over_target.append(f"{level}: {existing_count} (expected {expected_count})")
                continue

            if existing_count == expected_count:
                print(f"    {level} already has exactly {expected_count} lessons — skipping.")
                continue

            missing = expected_count - existing_count
            for i in range(missing):
                n = existing_count + i + 1
                db.add(
                    Lesson(
                        module_id=module.id,
                        number=n,
                        title=data["lessons"][n - 1],
                        duration=0,
                        is_free=(n == 1),
                    )
                )
                created_lessons += 1
            print(f"    Created {missing} lesson(s) for {level} (had {existing_count}).")

        db.commit()

        print()
        print("Done.")
        print(f"Courses created: {created_courses}")
        print(f"Modules created: {created_modules}")
        print(f"Lessons created: {created_lessons}")
        if over_target:
            print("Discrepancies found (more lessons than canonical, not touched):")
            for line in over_target:
                print(f"  - {line}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
