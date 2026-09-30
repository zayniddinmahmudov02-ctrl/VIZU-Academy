"""Idempotent content import for VIZU-Mock's Hören module: 5 Aufgaben
(1 per CEFR level A1-C1), 20 graded questions, 1 point each (20 max).

No passage_text is ever set for Hören content — the source material is
audio, uploaded separately per Aufgabe from the admin panel (see
VizuMockAudio / the "Hören" admin tab) and never stored in this script or
in the database as a script/transcript.

Matched by the natural key (skill, order_index) for tasks, then
(task_id, order_index) for questions and (question_id, order_index) for
options — same idempotent upsert convention as
app/scripts/seed_vizu_mock_lesen.py, so re-running this script after a
content edit is always safe and never creates duplicates.

Run from the `backend/` directory:

    python -m app.scripts.seed_vizu_mock_hoeren
"""

import app.models  # noqa: F401 — registers every model with Base before querying

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.vizu_mock_content import (
    QUESTION_TYPE_CLOZE_TEXT,
    QUESTION_TYPE_MULTIPLE_CHOICE,
    QUESTION_TYPE_TRUE_FALSE,
    SKILL_HOEREN,
    VizuMockOption,
    VizuMockQuestion,
    VizuMockTask,
)

# Each entry: (level, [
#     (question_type, prompt, [(option_text, is_correct), ...]),
#     ...  # exactly 4 per Aufgabe, matching Test N-N+3 in the source spec
# ])
TASKS: list[tuple[str, list[tuple[str, str, list[tuple[str, bool]]]]]] = [
    # ---- Aufgabe 1 (A1) — Test 1-4 ----
    (
        "A1",
        [
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                "Wie alt ist Daniel?",
                [("21 Jahre", False), ("22 Jahre", False), ("23 Jahre", True), ("24 Jahre", False)],
            ),
            (
                QUESTION_TYPE_TRUE_FALSE,
                "Daniel wohnt in München.",
                [("Richtig", False), ("Falsch", True)],
            ),
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                "Wann steht Daniel auf?",
                [("Um 6 Uhr", False), ("Um 7 Uhr", True), ("Um 7:30 Uhr", False), ("Um 8 Uhr", False)],
            ),
            (
                QUESTION_TYPE_CLOZE_TEXT,
                "Daniel fährt mit dem ______ zur Arbeit.",
                [("Auto", False), ("Fahrrad", False), ("Zug", False), ("Bus", True)],
            ),
        ],
    ),
    # ---- Aufgabe 2 (A2) — Test 5-8 ----
    (
        "A2",
        [
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                "Warum findet der Deutschkurs am Montag nicht statt?",
                [
                    ("Der Lehrer ist krank.", True),
                    ("Die Schüler sind krank.", False),
                    ("Der Raum ist geschlossen.", False),
                    ("Der Lehrer ist im Urlaub.", False),
                ],
            ),
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                "Wann findet der Kurs stattdessen statt?",
                [
                    ("Montag um 18 Uhr", False),
                    ("Dienstag um 18 Uhr", False),
                    ("Mittwoch um 18 Uhr", True),
                    ("Donnerstag um 18 Uhr", False),
                ],
            ),
            (
                QUESTION_TYPE_TRUE_FALSE,
                "Der Unterricht findet in einem anderen Raum statt.",
                [("Richtig", False), ("Falsch", True)],
            ),
            (
                QUESTION_TYPE_CLOZE_TEXT,
                "Nach dem Unterricht möchte Lukas mit seinen Kollegen etwas ______ gehen.",
                [("trinken", False), ("essen", True), ("arbeiten", False), ("einkaufen", False)],
            ),
        ],
    ),
    # ---- Aufgabe 3 (B1) — Test 9-12 ----
    (
        "B1",
        [
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                "Welche Möglichkeit wird genannt, um den Autoverkehr zu reduzieren?",
                [
                    ("Mehr Autos zu kaufen.", False),
                    ("Öffentliche Verkehrsmittel zu benutzen.", True),
                    ("Längere Arbeitszeiten einzuführen.", False),
                    ("Mehr Parkplätze zu bauen.", False),
                ],
            ),
            (
                QUESTION_TYPE_TRUE_FALSE,
                "Für alle Menschen ist es problemlos möglich, vollständig auf das Auto zu verzichten.",
                [("Richtig", False), ("Falsch", True)],
            ),
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                "Was machen einige Städte, um alternative Verkehrsmittel attraktiver zu machen?",
                [
                    ("Sie bauen neue Straßen für Autos.", False),
                    ("Sie erhöhen die Ticketpreise.", False),
                    ("Sie bauen Fahrradwege und verbessern Busverbindungen.", True),
                    ("Sie schließen Buslinien.", False),
                ],
            ),
            (
                QUESTION_TYPE_CLOZE_TEXT,
                "Neben der Infrastruktur spielen auch ______ und Sicherheit eine wichtige Rolle.",
                [("Geschwindigkeit", False), ("Zuverlässigkeit", True), ("Werbung", False), ("Entfernung", False)],
            ),
        ],
    ),
    # ---- Aufgabe 4 (B2) — Test 13-16 ----
    (
        "B2",
        [
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                "Welcher Vorteil des Homeoffice wird für Beschäftigte genannt?",
                [
                    ("Sie müssen überhaupt nicht mehr arbeiten.", False),
                    ("Sie können ihren Arbeitsalltag teilweise flexibler organisieren.", True),
                    ("Sie bekommen automatisch ein höheres Gehalt.", False),
                    ("Sie müssen häufiger reisen.", False),
                ],
            ),
            (
                QUESTION_TYPE_TRUE_FALSE,
                "Laut dem Text kann Homeoffice auch zu Kommunikationsproblemen innerhalb eines Teams führen.",
                [("Richtig", True), ("Falsch", False)],
            ),
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                "Welche Gefahr wird im Zusammenhang mit Homeoffice genannt?",
                [
                    ("Die Büros werden größer.", False),
                    ("Die Arbeitszeit wird immer kürzer.", False),
                    ("Die Grenzen zwischen Arbeit und Freizeit können verschwimmen.", True),
                    ("Mitarbeiter müssen häufiger umziehen.", False),
                ],
            ),
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                "Welche Schlussfolgerung wird am Ende des Hörtexts vertreten?",
                [
                    ("Homeoffice sollte grundsätzlich verboten werden.", False),
                    ("Homeoffice ist immer besser als Büroarbeit.", False),
                    ("Entscheidend ist vor allem, wie Homeoffice organisiert wird.", True),
                    ("Unternehmen sollten nur noch online kommunizieren.", False),
                ],
            ),
        ],
    ),
    # ---- Aufgabe 5 (C1) — Test 17-20 ----
    (
        "C1",
        [
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                "Welche Kritik übt der Sprecher an der häufigen Diskussion über KI im Bildungsbereich?",
                [
                    ("Sie beschäftigt sich zu stark mit den Kosten von KI.", False),
                    ("Sie reduziert die Frage häufig auf Effizienz.", True),
                    ("Sie lehnt neue Technologien grundsätzlich ab.", False),
                    ("Sie konzentriert sich ausschließlich auf Schulen.", False),
                ],
            ),
            (
                QUESTION_TYPE_TRUE_FALSE,
                "Laut Text bedeutet ein sprachlich korrektes Ergebnis automatisch, dass ein erfolgreicher "
                "Lernprozess stattgefunden hat.",
                [("Richtig", False), ("Falsch", True)],
            ),
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                "Welche Kompetenz könnte laut Text durch den Einsatz von KI stärker in den Mittelpunkt rücken?",
                [
                    ("Mechanisches Abschreiben.", False),
                    ("Schnelles Tippen.", False),
                    ("Bewertung von Argumenten und Überprüfung von Quellen.", True),
                    ("Auswendiglernen von Texten.", False),
                ],
            ),
            (
                QUESTION_TYPE_CLOZE_TEXT,
                "Die zentrale Frage ist laut Text nicht, ______ KI eingesetzt werden sollte, sondern unter "
                "welchen Bedingungen ihr Einsatz den Lernprozess unterstützt.",
                [("warum", False), ("wann", False), ("ob", True), ("wo", False)],
            ),
        ],
    ),
]


def _upsert_task(db: Session, order_index: int, level: str) -> VizuMockTask:
    task = db.scalar(
        select(VizuMockTask).where(VizuMockTask.skill == SKILL_HOEREN, VizuMockTask.order_index == order_index)
    )
    if task is None:
        task = VizuMockTask(skill=SKILL_HOEREN, order_index=order_index)
        db.add(task)
        print(f"  Creating Aufgabe {order_index} ({level}).")
    else:
        print(f"  Aufgabe {order_index} ({level}) already exists — updating.")
    task.level = level
    task.passage_text = None
    db.flush()
    return task


def _upsert_question(
    db: Session, task: VizuMockTask, order_index: int, question_type: str, prompt: str
) -> VizuMockQuestion:
    question = db.scalar(
        select(VizuMockQuestion).where(
            VizuMockQuestion.task_id == task.id, VizuMockQuestion.order_index == order_index
        )
    )
    if question is None:
        question = VizuMockQuestion(task_id=task.id, order_index=order_index)
        db.add(question)
    question.question_type = question_type
    question.passage_text = None
    question.prompt = prompt
    question.points = 1
    db.flush()
    return question


def _upsert_option(
    db: Session, question: VizuMockQuestion, order_index: int, text: str, is_correct: bool
) -> None:
    option = db.scalar(
        select(VizuMockOption).where(
            VizuMockOption.question_id == question.id, VizuMockOption.order_index == order_index
        )
    )
    if option is None:
        option = VizuMockOption(question_id=question.id, order_index=order_index)
        db.add(option)
    option.option_text = text
    option.is_correct = is_correct


def main() -> None:
    db = SessionLocal()
    task_count = 0
    question_count = 0

    try:
        for task_order, (level, questions) in enumerate(TASKS, start=1):
            task = _upsert_task(db, task_order, level)
            task_count += 1

            for question_order, (q_type, prompt, options) in enumerate(questions, start=1):
                question = _upsert_question(db, task, question_order, q_type, prompt)
                question_count += 1
                for option_order, (text, is_correct) in enumerate(options, start=1):
                    _upsert_option(db, question, option_order, text, is_correct)

        db.commit()
        # ASCII-only on purpose — some Windows consoles use a codepage
        # (e.g. cp1251) that can't encode "ö" and would crash this final
        # print after the transaction has already committed successfully.
        print(f"Done. {task_count} Aufgabe(n), {question_count} question(s) seeded/updated for Hoeren.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
