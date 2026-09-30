"""Idempotent content import for VIZU-Mock's Schreiben module: 5 Aufgaben
(1 per CEFR level A1-C1), each worth 20 points via its own rubric
(100 points total). No image is ever set here — images are uploaded
separately from the admin panel per Aufgabe (see the "Schreiben" admin
tab / VizuMockWritingTask.image_url), never embedded in this script.

Matched by the natural key `order_index` for tasks, then `(task_id,
order_index)` for rubric criteria — same idempotent upsert convention as
app/scripts/seed_vizu_mock_lesen.py / seed_vizu_mock_hoeren.py, so
re-running this script after a content edit never creates duplicates.
Since this module also supports admin editing afterward, re-running this
script WILL overwrite any admin edits back to the source content below —
that's the same tradeoff the other seed scripts already accept.

Run from the `backend/` directory:

    python -m app.scripts.seed_vizu_mock_schreiben
"""

import app.models  # noqa: F401 — registers every model with Base before querying

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.vizu_mock_writing import VizuMockWritingRubricCriterion, VizuMockWritingTask

# Each entry: (level, title, instruction, min_words, max_words, [(criterion_name, max_score), ...])
TASKS: list[tuple[str, str, str, int, int, list[tuple[str, int]]]] = [
    (
        "A1",
        "Eine Einladung beantworten",
        "Ihre Freundin Anna schreibt Ihnen:\n\n"
        '"Hallo! Ich habe am Samstag Geburtstag und möchte eine kleine Party bei mir zu Hause machen. '
        'Die Party beginnt um 18 Uhr. Kannst du kommen?"\n\n'
        "Antworten Sie Anna. Schreiben Sie eine kurze Nachricht.\n\n"
        "Schreiben Sie über:\n"
        "- ob Sie kommen können;\n"
        "- wann Sie kommen;\n"
        "- was Sie mitbringen.",
        # Spec only states a minimum (30 Wörter) for this Aufgabe; 50 is a
        # reasonable soft ceiling for an A1 "kurze Nachricht" so the word
        # counter has a range to show — admin can adjust it afterward.
        30,
        50,
        [
            ("Aufgaben erfüllt", 8),
            ("Verständlichkeit", 4),
            ("Wortschatz", 4),
            ("Grammatik", 4),
        ],
    ),
    (
        "A2",
        "Eine E-Mail beantworten",
        "Sie bekommen diese E-Mail von Ihrem Freund Lukas:\n\n"
        '"Hallo,\n\n'
        "ich möchte am nächsten Wochenende nach Samarkand fahren. Ich habe gehört, dass es dort viele "
        "interessante Orte gibt. Hast du Zeit und möchtest du mitkommen?\n\n"
        "Schreib mir bitte, wann du Zeit hast und was wir dort machen können.\n\n"
        "Viele Grüße\n"
        'Lukas"\n\n'
        "Antworten Sie auf die E-Mail.\n\n"
        "Schreiben Sie über:\n"
        "- ob Sie mitkommen können;\n"
        "- wann Sie Zeit haben;\n"
        "- welche Orte Sie besuchen möchten;\n"
        "- was Sie gemeinsam machen können.",
        50,
        70,
        [
            ("Aufgaben erfüllt", 8),
            ("Verständlichkeit & Struktur", 4),
            ("Wortschatz", 4),
            ("Grammatik", 4),
        ],
    ),
    (
        "B1",
        "Meinung und persönlicher Beitrag",
        "Sie lesen einen kurzen Beitrag in einem Online-Forum:\n\n"
        '"Homeoffice – eine gute Idee?\n\n'
        "Immer mehr Menschen arbeiten zumindest teilweise von zu Hause. Einige finden diese Möglichkeit sehr "
        'praktisch, andere vermissen den direkten Kontakt mit Kollegen."\n\n'
        "Schreiben Sie einen kurzen Beitrag für das Forum.\n\n"
        "Gehen Sie auf folgende Punkte ein:\n"
        "- Wie finden Sie Homeoffice?\n"
        "- Welche Vorteile gibt es?\n"
        "- Welche Nachteile gibt es?\n"
        "- Wie sieht Ihre persönliche Erfahrung oder Meinung aus?",
        100,
        120,
        [
            ("Inhalt / Aufgabenbearbeitung", 6),
            ("Kohärenz & Struktur", 4),
            ("Wortschatz", 4),
            ("Grammatik", 4),
            ("Kommunikative Angemessenheit", 2),
        ],
    ),
    (
        "B2",
        "Formelle E-Mail",
        "Sie haben an einem Sprachseminar teilgenommen. Nach dem Seminar möchten Sie der Organisation eine "
        "E-Mail schreiben.\n\n"
        "Schreiben Sie eine formelle E-Mail.\n\n"
        "Gehen Sie auf folgende Punkte ein:\n"
        "- bedanken Sie sich für die Veranstaltung;\n"
        "- beschreiben Sie kurz, was Ihnen gefallen hat;\n"
        "- nennen Sie einen Punkt, der verbessert werden könnte;\n"
        "- machen Sie einen konkreten Verbesserungsvorschlag.\n\n"
        "Achten Sie auf:\n"
        "- passende Anrede;\n"
        "- formellen Schreibstil;\n"
        "- klare Struktur;\n"
        "- passende Schlussformel.",
        150,
        180,
        [
            ("Aufgabenbearbeitung", 5),
            ("Argumentation / Inhalt", 5),
            ("Kohärenz & Struktur", 4),
            ("Wortschatz", 3),
            ("Grammatik & Sprachrichtigkeit", 3),
        ],
    ),
    (
        "C1",
        "Argumentativer Beitrag",
        "Sie schreiben einen Beitrag für eine deutschsprachige Bildungsplattform.\n\n"
        'Thema: "Sollte künstliche Intelligenz stärker im Unterricht eingesetzt werden?"\n\n'
        "Schreiben Sie einen strukturierten argumentativen Beitrag.\n\n"
        "Gehen Sie auf folgende Punkte ein:\n"
        "- beschreiben Sie die aktuelle Entwicklung;\n"
        "- nennen Sie mögliche Vorteile;\n"
        "- erläutern Sie mögliche Risiken;\n"
        "- vergleichen Sie unterschiedliche Perspektiven;\n"
        "- formulieren Sie Ihre eigene begründete Position;\n"
        "- geben Sie konkrete Empfehlungen für einen verantwortungsvollen Einsatz.\n\n"
        "Ihr Text soll logisch aufgebaut sein und eine klare Argumentation enthalten.",
        220,
        260,
        [
            ("Aufgabenbearbeitung", 4),
            ("Argumentation & Reflexion", 5),
            ("Kohärenz & Struktur", 4),
            ("Wortschatz / Ausdruck", 4),
            ("Grammatik & Sprachrichtigkeit", 3),
        ],
    ),
]


def _upsert_task(
    db: Session, order_index: int, level: str, title: str, instruction: str, min_words: int, max_words: int
) -> VizuMockWritingTask:
    task = db.scalar(select(VizuMockWritingTask).where(VizuMockWritingTask.order_index == order_index))
    if task is None:
        task = VizuMockWritingTask(order_index=order_index)
        db.add(task)
        print(f"  Creating Aufgabe {order_index} ({level}).")
    else:
        print(f"  Aufgabe {order_index} ({level}) already exists — updating.")
    task.level = level
    task.title = title
    task.instruction = instruction
    task.min_words = min_words
    task.max_words = max_words
    task.points = 20
    task.is_active = True
    db.flush()
    return task


def _upsert_criterion(db: Session, task: VizuMockWritingTask, order_index: int, name: str, max_score: int) -> None:
    criterion = db.scalar(
        select(VizuMockWritingRubricCriterion).where(
            VizuMockWritingRubricCriterion.task_id == task.id, VizuMockWritingRubricCriterion.order_index == order_index
        )
    )
    if criterion is None:
        criterion = VizuMockWritingRubricCriterion(task_id=task.id, order_index=order_index)
        db.add(criterion)
    criterion.name = name
    criterion.max_score = max_score


def main() -> None:
    db = SessionLocal()
    task_count = 0
    criterion_count = 0

    try:
        for task_order, (level, title, instruction, min_words, max_words, criteria) in enumerate(TASKS, start=1):
            task = _upsert_task(db, task_order, level, title, instruction, min_words, max_words)
            task_count += 1

            for criterion_order, (name, max_score) in enumerate(criteria, start=1):
                _upsert_criterion(db, task, criterion_order, name, max_score)
                criterion_count += 1

        db.commit()
        print(f"Done. {task_count} Aufgabe(n), {criterion_count} rubric criterion/criteria seeded/updated for Schreiben.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
