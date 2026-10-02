"""The standard VIZU-Multilevel Sprechen bank: 5 Aufgaben (communicative
task types) x 5 CEFR levels = 25 variants, stored structurally in
vizu_multilevel_speaking_tasks (matched by (order_index, level) — never
duplicated). A student gets the ladder Aufgabe 1 @ A1 ... Aufgabe 5 @ C1
(sprechen_service.assigned_tasks); the other variants are the content bank
the admin can switch to per Aufgabe. The level is internal — never sent to
students while they take the test.

Used by the seed script (app.scripts.seed_vizu_multilevel_sprechen) and by
ensure_content (the API's safety net against an empty Sprechen screen)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vizu_multilevel_speaking import VizuMultilevelSpeakingTask

LEVELS = ["A1", "A2", "B1", "B2", "C1"]
POINTS_PER_TASK = 20

# Recommended answer length per level (seconds): min = hint, max = recording auto-stop.
DURATION_BY_LEVEL = {"A1": (30, 60), "A2": (45, 90), "B1": (60, 120), "B2": (90, 150), "C1": (120, 180)}

TASK_TYPES = {
    1: "Persönliche Vorstellung",
    2: "Beschreibung",
    3: "Meinung und Begründung",
    4: "Gespräch in einer Situation",
    5: "Präsentation",
}

# (order_index, level) -> (instruction, preparation hint)
CONTENT: dict[tuple[int, str], tuple[str, str]] = {
    (1, "A1"): (
        "Stellen Sie sich kurz vor. Sprechen Sie über Ihren Namen, Ihr Alter, Ihre Stadt und Ihre Hobbys.",
        "Name · Alter · Stadt · Hobbys — sprechen Sie in einfachen, ganzen Sätzen.",
    ),
    (1, "A2"): (
        "Erzählen Sie über Ihren Alltag und was Sie in Ihrer Freizeit machen.",
        "Morgens · tagsüber · abends · Freizeit — verbinden Sie Sätze mit „und“, „dann“, „weil“.",
    ),
    (1, "B1"): (
        "Erzählen Sie von einem wichtigen Erlebnis in Ihrem Leben.",
        "Wann und wo? Was ist passiert? Wie haben Sie sich gefühlt? Warum ist es wichtig für Sie?",
    ),
    (1, "B2"): (
        "Beschreiben Sie eine Entscheidung, die Ihr Leben verändert hat, und erklären Sie warum.",
        "Ausgangssituation · Abwägung · Entscheidung · Folgen — begründen Sie ausführlich.",
    ),
    (1, "C1"): (
        "Erklären Sie, welche Erfahrungen einen Menschen langfristig prägen können.",
        "Arten von Erfahrungen · Wirkung auf Persönlichkeit und Werte · Beispiele · Ihre Sicht.",
    ),
    (2, "A1"): (
        "Beschreiben Sie Ihre Wohnung / Ihr Zimmer.",
        "Wie viele Zimmer? Was steht wo? Was gefällt Ihnen?",
    ),
    (2, "A2"): (
        "Beschreiben Sie einen typischen Tag in Ihrer Stadt.",
        "Orte · Menschen · Verkehr · was man dort machen kann.",
    ),
    (2, "B1"): (
        "Beschreiben Sie eine Situation, in der Menschen gemeinsam ein Problem lösen müssen.",
        "Situation · Problem · wer hilft wie · Ergebnis.",
    ),
    (2, "B2"): (
        "Beschreiben Sie eine gesellschaftliche Situation und erklären Sie mögliche Ursachen.",
        "Situation genau beschreiben · mehrere Ursachen · Zusammenhänge erklären.",
    ),
    (2, "C1"): (
        "Analysieren Sie eine komplexe gesellschaftliche Situation und erläutern Sie unterschiedliche Perspektiven.",
        "Analyse · Perspektiven verschiedener Gruppen · Spannungen · eigene Einschätzung.",
    ),
    (3, "A1"): (
        "Was machen Sie lieber am Wochenende? Warum?",
        "Sagen Sie, was Sie gern machen, und geben Sie einen Grund mit „weil“.",
    ),
    (3, "A2"): (
        "Was ist besser: online lernen oder im Kurs lernen? Warum?",
        "Ihre Meinung · zwei Gründe · ein kurzes Beispiel.",
    ),
    (3, "B1"): (
        "Sollten junge Menschen während des Studiums arbeiten? Begründen Sie Ihre Meinung.",
        "Meinung · Vorteile · Nachteile · Beispiel · Fazit.",
    ),
    (3, "B2"): (
        "Sollten Unternehmen mehr Homeoffice anbieten? Diskutieren Sie Vorteile und Nachteile.",
        "Argumente für und gegen · Gewichtung · begründete Position.",
    ),
    (3, "C1"): (
        "Welche Auswirkungen hat künstliche Intelligenz auf Bildung und Gesellschaft?",
        "Chancen und Risiken · differenzierte Argumentation · Beispiele · Schlussfolgerung.",
    ),
    (4, "A1"): (
        "Sie möchten einen Termin vereinbaren. Führen Sie das Gespräch.",
        "Begrüßung · Grund · Tag und Uhrzeit vorschlagen · bestätigen · verabschieden.",
    ),
    (4, "A2"): (
        "Sie haben ein Problem in einem Hotel. Erklären Sie das Problem und bitten Sie um eine Lösung.",
        "Was ist das Problem? Seit wann? Was möchten Sie? Höflich bitten.",
    ),
    (4, "B1"): (
        "Sie müssen einen Termin verschieben. Erklären Sie die Situation und schlagen Sie einen neuen Termin vor.",
        "Entschuldigung · Grund · neuer Vorschlag · Alternative · Bestätigung.",
    ),
    (4, "B2"): (
        "Sie führen ein Gespräch über eine wichtige berufliche Entscheidung und müssen Ihre Position überzeugend erklären.",
        "Position · Argumente · auf mögliche Einwände eingehen · Kompromiss anbieten.",
    ),
    (4, "C1"): (
        "Führen Sie eine anspruchsvolle Diskussion, in der Sie auf Gegenargumente reagieren und Ihre Position differenziert vertreten.",
        "Position · Gegenargumente aufgreifen und entkräften · Zugeständnisse · differenziertes Fazit.",
    ),
    (5, "A1"): (
        "Erzählen Sie etwas über Ihre Familie und Ihr Leben.",
        "Familie · Wohnort · Arbeit oder Schule · was Sie gern machen.",
    ),
    (5, "A2"): (
        "Erzählen Sie über Ihre Pläne für die Zukunft.",
        "Was möchten Sie lernen, arbeiten, reisen? Warum?",
    ),
    (5, "B1"): (
        "Halten Sie eine kurze Präsentation über einen wichtigen gesellschaftlichen oder persönlichen Bereich.",
        "Einleitung · zwei bis drei Punkte · Beispiel · Schluss.",
    ),
    (5, "B2"): (
        "Halten Sie eine strukturierte Stellungnahme zu einem aktuellen gesellschaftlichen Thema.",
        "Thema einführen · Argumente strukturieren · Beispiele · klare Stellungnahme.",
    ),
    (5, "C1"): (
        "Halten Sie eine strukturierte, differenzierte Stellungnahme zu einem komplexen gesellschaftlichen Thema und berücksichtigen Sie unterschiedliche Perspektiven.",
        "Gliederung · mehrere Perspektiven · Abwägung · differenzierte Schlussfolgerung.",
    ),
}


def _fields(order: int, level: str) -> dict:
    instruction, preparation = CONTENT[(order, level)]
    minimum, maximum = DURATION_BY_LEVEL[level]
    return {
        "title": TASK_TYPES[order],
        "instruction": instruction,
        "preparation_text": preparation,
        "prep_seconds": 0,
        "min_seconds": minimum,
        "max_seconds": maximum,
        "points": POINTS_PER_TASK,
        "is_active": True,
    }


def seed(db: Session, update_existing: bool = True) -> dict:
    """Idempotent upsert of all 25 variants, matched by (order_index, level).
    `update_existing=False` only creates missing variants (never touches
    admin edits)."""
    created = updated = unchanged = 0
    for order, level in CONTENT:
        task = db.scalar(
            select(VizuMultilevelSpeakingTask).where(
                VizuMultilevelSpeakingTask.order_index == order, VizuMultilevelSpeakingTask.level == level
            )
        )
        fields = _fields(order, level)
        if task is None:
            db.add(VizuMultilevelSpeakingTask(order_index=order, level=level, **fields))
            created += 1
            continue
        if not update_existing:
            unchanged += 1
            continue
        changed = False
        for key, value in fields.items():
            if getattr(task, key) != value:
                setattr(task, key, value)
                changed = True
        updated += 1 if changed else 0
        unchanged += 0 if changed else 1
    db.commit()
    return {"created": created, "updated": updated, "unchanged": unchanged}


def ensure_content(db: Session) -> bool:
    """Creates any missing variant of the standard bank (never overwrites
    existing ones). Returns True if something was created."""
    existing = {
        (row.order_index, row.level)
        for row in db.execute(select(VizuMultilevelSpeakingTask.order_index, VizuMultilevelSpeakingTask.level))
    }
    if all(key in existing for key in CONTENT):
        return False
    return seed(db, update_existing=False)["created"] > 0
