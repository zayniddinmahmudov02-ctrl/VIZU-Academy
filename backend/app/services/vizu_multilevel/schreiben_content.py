"""The 5 standard VIZU-Mock / VIZU-Multilevel Schreiben Aufgaben — the single
definition used by the seed script (`app.scripts.seed_vizu_mock_schreiben`)
and by `ensure_content` (the safety net that guarantees students never get
an empty Schreiben screen).

Writes into the existing tables (vizu_mock_writing_tasks /
vizu_mock_writing_rubric_criteria), matched by Aufgabe number
(order_index) — never duplicates. The CEFR level per task is internal and
never sent to students. Student submissions are never touched.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.vizu_multilevel_writing import VizuMultilevelWritingRubricCriterion, VizuMultilevelWritingTask

POINTS_PER_TASK = 20

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
            "- was ihr zusammen machen möchtet\n\n"
            "Schreibe 30–40 Wörter."
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
            "- Wie viel kostet der Kurs?\n\n"
            "Schreibe 50–70 Wörter."
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
            "Du hast folgende E-Mail von deinem Freund / deiner Freundin bekommen:\n\n"
            "\"Hallo!\n"
            "Ich möchte im nächsten Monat nach deiner Stadt kommen. Ich kenne die Stadt noch nicht. "
            "Kannst du mir ein paar Tipps geben? Was kann man dort besichtigen? Wo kann man gut essen? "
            "Und können wir uns treffen?\"\n\n"
            "Antworte auf die E-Mail.\n\n"
            "Schreibe über:\n"
            "- interessante Orte\n"
            "- einen Ort zum Essen\n"
            "- einen gemeinsamen Treffpunkt\n"
            "- einen Vorschlag für einen Tag\n\n"
            "Schreibe 80–100 Wörter."
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
            "Du schreibst einen Beitrag in einem Online-Forum zum Thema:\n\n"
            "„Sollten junge Menschen während des Studiums arbeiten?“\n\n"
            "Schreibe einen Beitrag.\n\n"
            "Gehe auf folgende Punkte ein:\n"
            "- deine persönliche Meinung\n"
            "- Vorteile des Arbeitens während des Studiums\n"
            "- mögliche Nachteile\n"
            "- ein Beispiel aus deiner Erfahrung oder deinem Umfeld\n\n"
            "Schreibe 120–150 Wörter."
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
            "Du liest folgende Aussage:\n\n"
            "„Immer mehr Menschen lernen heute online. Deshalb werden traditionelle Sprachkurse in Zukunft "
            "nicht mehr notwendig sein.“\n\n"
            "Schreibe eine ausführliche Stellungnahme.\n\n"
            "Gehe auf folgende Punkte ein:\n"
            "- deine Position zu dieser Aussage\n"
            "- Vorteile des Online-Lernens\n"
            "- Nachteile oder Grenzen des Online-Lernens\n"
            "- Vorteile des Präsenzunterrichts\n"
            "- Vergleich beider Lernformen\n"
            "- konkrete Beispiele\n"
            "- abschließende Schlussfolgerung\n\n"
            "Argumentiere klar und strukturiert.\n\n"
            "Schreibe 180–220 Wörter."
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


def _fields(spec: dict) -> dict:
    return {
        "level": spec["level"],
        "title": spec["title"],
        "instruction": spec["instruction"],
        "min_words": spec["min_words"],
        "max_words": spec["max_words"],
        "points": POINTS_PER_TASK,
        "is_active": True,
    }


def _add_rubric(db: Session, task: VizuMultilevelWritingTask, rubric: list[tuple[str, int]]) -> None:
    for index, (name, max_score) in enumerate(rubric, start=1):
        db.add(VizuMultilevelWritingRubricCriterion(task_id=task.id, name=name, max_score=max_score, order_index=index))


def seed(db: Session, update_existing: bool = True) -> dict:
    """Idempotent upsert of the 5 Aufgaben, matched by order_index.

    * missing Aufgabe -> created (with its rubric);
    * existing Aufgabe -> texts / word limits / points / rubric updated to the
      definition above (only when `update_existing`; unchanged content is a
      no-op).
    """
    created = updated = unchanged = 0
    for spec in TASKS:
        assert sum(m for _, m in spec["rubric"]) == POINTS_PER_TASK
        task = db.scalar(
            select(VizuMultilevelWritingTask)
            .where(VizuMultilevelWritingTask.order_index == spec["order"])
            .options(joinedload(VizuMultilevelWritingTask.rubric_criteria))
        )
        if task is None:
            task = VizuMultilevelWritingTask(order_index=spec["order"], **_fields(spec))
            db.add(task)
            db.flush()
            _add_rubric(db, task, spec["rubric"])
            created += 1
            continue
        if not update_existing:
            unchanged += 1
            continue

        changed = False
        for key, value in _fields(spec).items():
            if getattr(task, key) != value:
                setattr(task, key, value)
                changed = True
        current = [(c.name, c.max_score) for c in sorted(task.rubric_criteria, key=lambda c: c.order_index)]
        if current != spec["rubric"]:
            for criterion in list(task.rubric_criteria):
                db.delete(criterion)
            db.flush()
            _add_rubric(db, task, spec["rubric"])
            changed = True
        if changed:
            updated += 1
        else:
            unchanged += 1
    db.commit()
    return {"created": created, "updated": updated, "unchanged": unchanged}


def ensure_content(db: Session) -> bool:
    """Safety net against an empty Schreiben screen: if any of the 5
    standard Aufgaben (order 1-5) does not exist at all, create the missing
    ones. Existing Aufgaben (incl. admin edits or deactivation) are left
    untouched. Returns True if something was created."""
    existing = set(
        db.scalars(
            select(VizuMultilevelWritingTask.order_index).where(
                VizuMultilevelWritingTask.order_index.in_([spec["order"] for spec in TASKS])
            )
        )
    )
    if len(existing) == len(TASKS):
        return False
    return seed(db, update_existing=False)["created"] > 0
