"""Idempotent seed for VIZU-Mock -> Schreiben: exactly 5 Aufgaben, 20 points
each (100 total), each with its analytic rubric.

Writes into the existing VIZU-Mock Schreiben tables (vizu_mock_writing_tasks /
_rubric_criteria) — no parallel system. Matching is by Aufgabe number
(order_index):
* missing task -> created;
* existing task -> its texts / word limits / points updated in place;
* rubric replaced only if it differs from the definition below.
Re-running with unchanged content changes nothing. Student submissions are
never touched. The CEFR level stored per task is internal and never sent to
students.

Run on the server (from backend/):
    python -m app.scripts.seed_vizu_mock_schreiben
"""

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.session import SessionLocal
from app.models.vizu_multilevel_writing import VizuMultilevelWritingRubricCriterion, VizuMultilevelWritingTask

TASKS = [
    {
        "order": 1,
        "level": "A1",
        "title": "Eine Nachricht an einen Freund",
        "instruction": (
            "Du möchtest dich am Wochenende mit deinem Freund / deiner Freundin treffen.\n\n"
            "Schreibe eine kurze Nachricht.\n\n"
            "Schreibe über:\n"
            "- wann du Zeit hast\n"
            "- wo ihr euch treffen könnt\n"
            "- was ihr zusammen machen möchtet"
        ),
        "min_words": 30,
        "max_words": 40,
        "rubric": [("Aufgabenbearbeitung", 6), ("Wortschatz", 4), ("Grammatik", 4), ("Verständlichkeit", 3), ("Rechtschreibung", 3)],
    },
    {
        "order": 2,
        "level": "A2",
        "title": "E-Mail an einen Sprachkurs",
        "instruction": (
            "Du möchtest einen Deutschkurs besuchen.\n\n"
            "Schreibe eine E-Mail an die Sprachschule.\n\n"
            "Frage:\n"
            "- Wann beginnt der nächste Deutschkurs?\n"
            "- Wie oft findet der Kurs statt?\n"
            "- Wie viel kostet der Kurs?"
        ),
        "min_words": 50,
        "max_words": 70,
        "rubric": [("Aufgabenbearbeitung", 6), ("Wortschatz", 4), ("Grammatik", 4), ("Verständlichkeit", 3), ("Rechtschreibung/Form", 3)],
    },
    {
        "order": 3,
        "level": "B1",
        "title": "Antwort auf eine E-Mail",
        "instruction": (
            "Hallo!\n"
            "Ich möchte im nächsten Monat nach deiner Stadt kommen. Ich kenne die Stadt noch nicht. "
            "Kannst du mir ein paar Tipps geben? Was kann man dort besichtigen? Wo kann man gut essen? "
            "Und können wir uns treffen?\n\n"
            "Antworte auf die E-Mail.\n\n"
            "Schreibe über:\n"
            "- interessante Orte\n"
            "- einen Ort zum Essen\n"
            "- einen gemeinsamen Treffpunkt\n"
            "- einen Vorschlag für einen Tag"
        ),
        "min_words": 80,
        "max_words": 100,
        "rubric": [("Aufgabenbearbeitung", 6), ("Wortschatz", 4), ("Grammatik", 4), ("Textaufbau/Kohärenz", 3), ("Rechtschreibung", 3)],
    },
    {
        "order": 4,
        "level": "B2",
        "title": "Beitrag für ein Online-Forum",
        "instruction": (
            "„Sollten junge Menschen während des Studiums arbeiten?“\n\n"
            "Schreibe einen Beitrag.\n\n"
            "Gehe auf folgende Punkte ein:\n"
            "- deine persönliche Meinung\n"
            "- Vorteile des Arbeitens während des Studiums\n"
            "- mögliche Nachteile\n"
            "- ein Beispiel aus deiner Erfahrung oder deinem Umfeld"
        ),
        "min_words": 120,
        "max_words": 150,
        "rubric": [
            ("Aufgabenbearbeitung und Inhalt", 5),
            ("Wortschatz", 4),
            ("Grammatik", 4),
            ("Textaufbau und Kohärenz", 4),
            ("Rechtschreibung", 3),
        ],
    },
    {
        "order": 5,
        "level": "C1",
        "title": "Stellungnahme",
        "instruction": (
            "„Immer mehr Menschen lernen heute online. Deshalb werden traditionelle Sprachkurse in Zukunft "
            "nicht mehr notwendig sein.“\n\n"
            "Schreibe eine ausführliche Stellungnahme.\n\n"
            "Gehe auf folgende Punkte ein:\n"
            "- deine Position\n"
            "- Vorteile des Online-Lernens\n"
            "- Nachteile oder Grenzen\n"
            "- Vorteile des Präsenzunterrichts\n"
            "- Vergleich beider Lernformen\n"
            "- konkrete Beispiele\n"
            "- Schlussfolgerung"
        ),
        "min_words": 180,
        "max_words": 220,
        "rubric": [
            ("Aufgabenbearbeitung und Argumentation", 5),
            ("Wortschatz", 4),
            ("Grammatik", 4),
            ("Textaufbau, Kohärenz und Verknüpfungen", 4),
            ("Rechtschreibung und sprachliche Genauigkeit", 3),
        ],
    },
]

POINTS_PER_TASK = 20


def seed(db) -> dict:
    created = updated = unchanged = 0
    for spec in TASKS:
        assert sum(m for _, m in spec["rubric"]) == POINTS_PER_TASK
        task = db.scalar(
            select(VizuMultilevelWritingTask)
            .where(VizuMultilevelWritingTask.order_index == spec["order"])
            .options(joinedload(VizuMultilevelWritingTask.rubric_criteria))
        )
        fields = {
            "level": spec["level"],
            "title": spec["title"],
            "instruction": spec["instruction"],
            "min_words": spec["min_words"],
            "max_words": spec["max_words"],
            "points": POINTS_PER_TASK,
            "is_active": True,
        }
        if task is None:
            task = VizuMultilevelWritingTask(order_index=spec["order"], **fields)
            db.add(task)
            db.flush()
            for index, (name, max_score) in enumerate(spec["rubric"], start=1):
                db.add(VizuMultilevelWritingRubricCriterion(task_id=task.id, name=name, max_score=max_score, order_index=index))
            created += 1
            continue

        changed = False
        for key, value in fields.items():
            if getattr(task, key) != value:
                setattr(task, key, value)
                changed = True
        current = [(c.name, c.max_score) for c in sorted(task.rubric_criteria, key=lambda c: c.order_index)]
        if current != spec["rubric"]:
            for criterion in list(task.rubric_criteria):
                db.delete(criterion)
            db.flush()
            for index, (name, max_score) in enumerate(spec["rubric"], start=1):
                db.add(VizuMultilevelWritingRubricCriterion(task_id=task.id, name=name, max_score=max_score, order_index=index))
            changed = True
        if changed:
            updated += 1
        else:
            unchanged += 1
    db.commit()
    return {"created": created, "updated": updated, "unchanged": unchanged}


def main() -> None:
    db = SessionLocal()
    try:
        print("seed:", seed(db))
    finally:
        db.close()


if __name__ == "__main__":
    main()
