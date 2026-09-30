"""Imports the real Hören listening-comprehension quiz (20 questions,
5 Aufgabe) into a lesson's real Quiz/QuizQuestion/QuizOption rows
(quiz_type=HOEREN — see app/models/quiz.py and
services/quiz/csv_import_service.py), so the student Hören section
shows real, database-backed questions instead of nothing.

Every question/option below is transcribed exactly as given — nothing
was changed, reworded, or added from general knowledge.

Targets A1 Lesson 1 by default (LEVEL/LESSON_NUMBER below) — the only
lesson with real seeded content at the time this script was written
(see seed_lesson_1.py). Edit those two constants to target a different
lesson; the import itself is idempotent either way (safe to re-run,
matches existing questions/options by their natural key instead of
duplicating them — see csv_import_service.import_rows).

Run from the `backend/` directory:

    python -m app.scripts.import_hoeren_quiz_csv
"""

import app.models  # noqa: F401 — registers every model with Base before querying

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.course import Course
from app.models.language import Language
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.quiz import QUIZ_TYPE_HOEREN
from app.services.quiz import csv_import_service

LEVEL = "A1"
LESSON_NUMBER = 1

# Each row: (aufgabe, question, type, [option_a..d], correct_answer, points, order)
ROWS: list[dict] = [
    {"aufgabe": "Aufgabe 1", "order": 1, "type": "MULTIPLE_CHOICE", "points": 1,
     "question": "Wie alt ist Daniel?",
     "option_a": "21 Jahre", "option_b": "22 Jahre", "option_c": "23 Jahre", "option_d": "24 Jahre",
     "correct_answer": "C"},
    {"aufgabe": "Aufgabe 1", "order": 2, "type": "TRUE_FALSE", "points": 1,
     "question": "Daniel wohnt in München.",
     "option_a": "Richtig", "option_b": "Falsch",
     "correct_answer": "B"},
    {"aufgabe": "Aufgabe 1", "order": 3, "type": "MULTIPLE_CHOICE", "points": 1,
     "question": "Wann steht Daniel auf?",
     "option_a": "Um 6 Uhr", "option_b": "Um 7 Uhr", "option_c": "Um 7:30 Uhr", "option_d": "Um 8 Uhr",
     "correct_answer": "B"},
    {"aufgabe": "Aufgabe 1", "order": 4, "type": "CLOZE", "points": 1,
     "question": "Daniel fährt mit dem _____ zur Arbeit.",
     "option_a": "Auto", "option_b": "Fahrrad", "option_c": "Zug", "option_d": "Bus",
     "correct_answer": "D"},
    {"aufgabe": "Aufgabe 2", "order": 5, "type": "MULTIPLE_CHOICE", "points": 1,
     "question": "Warum findet der Deutschkurs am Montag nicht statt?",
     "option_a": "Der Lehrer ist krank.", "option_b": "Die Schüler sind krank.",
     "option_c": "Der Raum ist geschlossen.", "option_d": "Der Lehrer ist im Urlaub.",
     "correct_answer": "A"},
    {"aufgabe": "Aufgabe 2", "order": 6, "type": "MULTIPLE_CHOICE", "points": 1,
     "question": "Wann findet der Kurs stattdessen statt?",
     "option_a": "Montag um 18 Uhr", "option_b": "Dienstag um 18 Uhr",
     "option_c": "Mittwoch um 18 Uhr", "option_d": "Donnerstag um 18 Uhr",
     "correct_answer": "C"},
    {"aufgabe": "Aufgabe 2", "order": 7, "type": "TRUE_FALSE", "points": 1,
     "question": "Der Unterricht findet in einem anderen Raum statt.",
     "option_a": "Richtig", "option_b": "Falsch",
     "correct_answer": "B"},
    {"aufgabe": "Aufgabe 2", "order": 8, "type": "CLOZE", "points": 1,
     "question": "Nach dem Unterricht möchte Lukas mit seinen Kollegen etwas _____ gehen.",
     "option_a": "trinken", "option_b": "essen", "option_c": "arbeiten", "option_d": "einkaufen",
     "correct_answer": "B"},
    {"aufgabe": "Aufgabe 3", "order": 9, "type": "MULTIPLE_CHOICE", "points": 1,
     "question": "Welche Möglichkeit wird genannt, um den Autoverkehr zu reduzieren?",
     "option_a": "Mehr Autos zu kaufen.", "option_b": "Öffentliche Verkehrsmittel zu benutzen.",
     "option_c": "Längere Arbeitszeiten einzuführen.", "option_d": "Mehr Parkplätze zu bauen.",
     "correct_answer": "B"},
    {"aufgabe": "Aufgabe 3", "order": 10, "type": "TRUE_FALSE", "points": 1,
     "question": "Für alle Menschen ist es problemlos möglich, vollständig auf das Auto zu verzichten.",
     "option_a": "Richtig", "option_b": "Falsch",
     "correct_answer": "B"},
    {"aufgabe": "Aufgabe 3", "order": 11, "type": "MULTIPLE_CHOICE", "points": 1,
     "question": "Was machen einige Städte, um alternative Verkehrsmittel attraktiver zu machen?",
     "option_a": "Sie bauen neue Straßen für Autos.", "option_b": "Sie erhöhen die Ticketpreise.",
     "option_c": "Sie bauen Fahrradwege und verbessern Busverbindungen.", "option_d": "Sie schließen Buslinien.",
     "correct_answer": "C"},
    {"aufgabe": "Aufgabe 3", "order": 12, "type": "CLOZE", "points": 1,
     "question": "Neben der Infrastruktur spielen auch _____ und Sicherheit eine wichtige Rolle.",
     "option_a": "Geschwindigkeit", "option_b": "Zuverlässigkeit", "option_c": "Werbung", "option_d": "Entfernung",
     "correct_answer": "B"},
    {"aufgabe": "Aufgabe 4", "order": 13, "type": "MULTIPLE_CHOICE", "points": 1,
     "question": "Welcher Vorteil des Homeoffice wird für Beschäftigte genannt?",
     "option_a": "Sie müssen überhaupt nicht mehr arbeiten.",
     "option_b": "Sie können ihren Arbeitsalltag teilweise flexibler organisieren.",
     "option_c": "Sie bekommen automatisch ein höheres Gehalt.", "option_d": "Sie müssen häufiger reisen.",
     "correct_answer": "B"},
    {"aufgabe": "Aufgabe 4", "order": 14, "type": "TRUE_FALSE", "points": 1,
     "question": "Laut dem Text kann Homeoffice auch zu Kommunikationsproblemen innerhalb eines Teams führen.",
     "option_a": "Richtig", "option_b": "Falsch",
     "correct_answer": "A"},
    {"aufgabe": "Aufgabe 4", "order": 15, "type": "MULTIPLE_CHOICE", "points": 1,
     "question": "Welche Gefahr wird im Zusammenhang mit Homeoffice genannt?",
     "option_a": "Die Büros werden größer.", "option_b": "Die Arbeitszeit wird immer kürzer.",
     "option_c": "Die Grenzen zwischen Arbeit und Freizeit können verschwimmen.",
     "option_d": "Mitarbeiter müssen häufiger umziehen.",
     "correct_answer": "C"},
    {"aufgabe": "Aufgabe 4", "order": 16, "type": "MULTIPLE_CHOICE", "points": 1,
     "question": "Welche Schlussfolgerung wird am Ende des Hörtexts vertreten?",
     "option_a": "Homeoffice sollte grundsätzlich verboten werden.",
     "option_b": "Homeoffice ist immer besser als Büroarbeit.",
     "option_c": "Entscheidend ist vor allem, wie Homeoffice organisiert wird.",
     "option_d": "Unternehmen sollten nur noch online kommunizieren.",
     "correct_answer": "C"},
    {"aufgabe": "Aufgabe 5", "order": 17, "type": "MULTIPLE_CHOICE", "points": 1,
     "question": "Welche Kritik übt der Sprecher an der häufigen Diskussion über KI im Bildungsbereich?",
     "option_a": "Sie beschäftigt sich zu stark mit den Kosten von KI.",
     "option_b": "Sie reduziert die Frage häufig auf Effizienz.",
     "option_c": "Sie lehnt neue Technologien grundsätzlich ab.",
     "option_d": "Sie konzentriert sich ausschließlich auf Schulen.",
     "correct_answer": "B"},
    {"aufgabe": "Aufgabe 5", "order": 18, "type": "TRUE_FALSE", "points": 1,
     "question": "Laut Text bedeutet ein sprachlich korrektes Ergebnis automatisch, dass ein erfolgreicher "
                 "Lernprozess stattgefunden hat.",
     "option_a": "Richtig", "option_b": "Falsch",
     "correct_answer": "B"},
    {"aufgabe": "Aufgabe 5", "order": 19, "type": "MULTIPLE_CHOICE", "points": 1,
     "question": "Welche Kompetenz könnte laut Text durch den Einsatz von KI stärker in den Mittelpunkt rücken?",
     "option_a": "Mechanisches Abschreiben.", "option_b": "Schnelles Tippen.",
     "option_c": "Bewertung von Argumenten und Überprüfung von Quellen.", "option_d": "Auswendiglernen von Texten.",
     "correct_answer": "C"},
    {"aufgabe": "Aufgabe 5", "order": 20, "type": "CLOZE", "points": 1,
     "question": "Die zentrale Frage ist laut Text nicht, _____ KI eingesetzt werden sollte, sondern unter "
                 "welchen Bedingungen ihr Einsatz den Lernprozess unterstützt.",
     "option_a": "warum", "option_b": "wann", "option_c": "ob", "option_d": "wo",
     "correct_answer": "C"},
]


def get_lesson(db) -> Lesson | None:
    language = db.scalar(select(Language).where(Language.code == "de", Language.deleted_at.is_(None)))
    if language is None:
        return None
    course = db.scalar(select(Course).where(Course.language_id == language.id, Course.level == LEVEL))
    if course is None:
        return None
    module = db.scalar(select(Module).where(Module.course_id == course.id))
    if module is None:
        return None
    return db.scalar(select(Lesson).where(Lesson.module_id == module.id, Lesson.number == LESSON_NUMBER))


def main() -> None:
    db = SessionLocal()
    try:
        lesson = get_lesson(db)
        if lesson is None:
            print(
                f"ERROR: could not find {LEVEL} Lesson {LESSON_NUMBER}. "
                "Nothing to import — aborting without changes."
            )
            return

        # Normalize rows the way csv_import_service.import_csv_text would
        # (string values, lower-cased keys) since we're calling
        # import_rows directly with already-parsed dicts.
        rows = [{k: (str(v) if v is not None else v) for k, v in row.items()} for row in ROWS]

        result = csv_import_service.import_rows(
            db, lesson.id, QUIZ_TYPE_HOEREN, "Hören", rows
        )
        print(
            f"Done. Lesson={lesson.id} quiz_id={result['quiz_id']} "
            f"created={result['created_questions']} updated={result['updated_questions']} "
            f"total={result['total_questions']}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
