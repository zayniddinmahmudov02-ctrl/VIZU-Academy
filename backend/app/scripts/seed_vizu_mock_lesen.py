"""Idempotent content import for VIZU-Mock's Lesen module: 10 Aufgaben
(2 per CEFR level A1-C1), 20 graded questions, 5 points each (100 max).

Matched by the natural key (skill, order_index) for tasks, then
(task_id, order_index) for questions and (question_id, order_index) for
options — an existing row's fields are updated in place rather than a
duplicate being inserted, so re-running this script after a content edit
is always safe (same convention as app/scripts/seed_default_language.py).

Run from the `backend/` directory:

    python -m app.scripts.seed_vizu_mock_lesen
"""

import app.models  # noqa: F401 — registers every model with Base before querying

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.vizu_mock_content import (
    QUESTION_TYPE_CLOZE_TEXT,
    QUESTION_TYPE_MULTIPLE_CHOICE,
    QUESTION_TYPE_TRUE_FALSE,
    SKILL_LESEN,
    VizuMockOption,
    VizuMockQuestion,
    VizuMockTask,
)

RICHTIG_FALSCH = [("Richtig", False), ("Falsch", True)]

# Each entry: (level, task_passage | None, [
#     (question_type, question_passage | None, prompt, [(option_text, is_correct), ...]),
#     ...
# ])
# task_passage is set when both of a task's questions share one reading
# passage (B1-C1 content); question_passage is set instead when each
# question has its own, unrelated passage (A1-A2 content) — see
# VizuMockTask/VizuMockQuestion's own docstrings for why both shapes
# exist in the real source content.
TASKS: list[tuple[str, str | None, list[tuple[str, str | None, str, list[tuple[str, bool]]]]]] = [
    # ---- A1 ----
    (
        "A1",
        None,
        [
            (
                QUESTION_TYPE_TRUE_FALSE,
                "Hallo! Ich heiße Maria. Ich bin 22 Jahre alt und komme aus Spanien. Jetzt wohne ich in Berlin. "
                "Ich lerne Deutsch und arbeite am Nachmittag in einem Café. In meiner Freizeit höre ich gern "
                "Musik und treffe meine Freunde.",
                "Maria arbeitet am Vormittag in einem Café.",
                RICHTIG_FALSCH,
            ),
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                "Heute ist Samstag. Paul steht um 8 Uhr auf. Danach frühstückt er und geht zum Supermarkt. "
                "Am Nachmittag spielt er Fußball mit seinen Freunden. Am Abend sieht er einen Film.",
                "Was macht Paul am Nachmittag?",
                [
                    ("Er geht zum Supermarkt.", False),
                    ("Er sieht einen Film.", False),
                    ("Er spielt Fußball.", True),
                    ("Er frühstückt.", False),
                ],
            ),
        ],
    ),
    (
        "A1",
        None,
        [
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                "Liebe Anna,\n\nich habe heute Geburtstag. Meine Party beginnt um 18 Uhr bei mir zu Hause. "
                "Wir essen Pizza und hören Musik. Kannst du bitte einen Kuchen mitbringen?\n\nLiebe Grüße\nSophie",
                "Wann beginnt die Party?",
                [
                    ("Um 16 Uhr.", False),
                    ("Um 17 Uhr.", False),
                    ("Um 18 Uhr.", True),
                    ("Um 20 Uhr.", False),
                ],
            ),
            (
                QUESTION_TYPE_TRUE_FALSE,
                "Im Hotel\n\nRezeption: Guten Morgen. Wie kann ich Ihnen helfen?\n\nHerr Klein: Ich habe ein "
                "Zimmer reserviert. Mein Name ist Klein.\n\nRezeption: Ja, Herr Klein. Ihr Zimmer ist Nummer 205. "
                "Das Frühstück gibt es von 7 bis 10 Uhr.",
                "Das Frühstück beginnt um 8 Uhr.",
                RICHTIG_FALSCH,
            ),
        ],
    ),
    # ---- A2 ----
    (
        "A2",
        None,
        [
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                "Am kommenden Wochenende findet in der Innenstadt ein Straßenfest statt. Die Veranstaltung "
                "beginnt am Samstag um 12 Uhr und endet am Sonntagabend. Besucher können verschiedene Gerichte "
                "probieren und Livemusik hören. Für Kinder gibt es einen kleinen Spielplatz. Wegen des Festes "
                "sind einige Straßen für Autos gesperrt.",
                "Warum können einige Straßen am Wochenende nicht mit dem Auto befahren werden?",
                [
                    ("Wegen einer Baustelle.", False),
                    ("Wegen des Straßenfestes.", True),
                    ("Wegen eines Fußballspiels.", False),
                    ("Wegen eines Unfalls.", False),
                ],
            ),
            (
                QUESTION_TYPE_CLOZE_TEXT,
                "Julia arbeitet seit sechs Monaten in einem neuen Büro. Am Anfang war alles schwierig, weil sie "
                "viele neue Kollegen kennenlernen musste. Heute fühlt sie sich dort sehr wohl. Besonders gut "
                "gefällt ihr, dass ihre Kollegen sehr ______ sind und ihr bei Problemen helfen.",
                "Besonders gut gefällt Julia, dass ihre Kollegen sehr ______ sind.",
                [
                    ("freundlich", True),
                    ("teuer", False),
                    ("geschlossen", False),
                    ("langsam", False),
                ],
            ),
        ],
    ),
    (
        "A2",
        None,
        [
            (
                QUESTION_TYPE_TRUE_FALSE,
                "Liebe Kundinnen und Kunden,\n\naufgrund von Renovierungsarbeiten bleibt unsere Filiale vom 3. "
                "bis zum 7. Oktober geschlossen. Ab Dienstag, dem 8. Oktober, sind wir wieder zu den normalen "
                "Öffnungszeiten für Sie da. Während der Renovierung können Sie unsere Filiale in der "
                "Bahnhofstraße besuchen.",
                "Die Filiale ist am 8. Oktober wieder geöffnet.",
                [("Richtig", True), ("Falsch", False)],
            ),
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                "Tom wollte am Samstag mit seinen Freunden wandern gehen. Da die Wettervorhersage starken "
                "Regen angekündigt hatte, änderten sie ihren Plan. Stattdessen trafen sie sich bei Tom zu Hause "
                "und kochten gemeinsam. Am Abend spielten sie noch ein Brettspiel.",
                "Warum haben die Freunde ihren ursprünglichen Plan geändert?",
                [
                    ("Tom war krank.", False),
                    ("Sie hatten keine Zeit.", False),
                    ("Das Wetter sollte schlecht werden.", True),
                    ("Der Wanderweg war geschlossen.", False),
                ],
            ),
        ],
    ),
    # ---- B1 ----
    (
        "B1",
        "Immer mehr Menschen entscheiden sich dafür, einen Teil ihrer Arbeitszeit von zu Hause aus zu erledigen. "
        "Für viele Beschäftigte bedeutet dies eine größere zeitliche Flexibilität. Sie sparen beispielsweise "
        "den täglichen Weg ins Büro. Gleichzeitig kann die Arbeit im Homeoffice neue Herausforderungen mit "
        "sich bringen. Manche Arbeitnehmer haben Schwierigkeiten, Berufliches und Privates voneinander zu "
        "trennen.",
        [
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                None,
                "Welcher Vorteil des Homeoffice wird im Text genannt?",
                [
                    ("Die Arbeitnehmer arbeiten automatisch weniger.", False),
                    ("Der Arbeitsweg fällt teilweise weg.", True),
                    ("Alle Arbeitnehmer verdienen mehr.", False),
                    ("Private Probleme verschwinden.", False),
                ],
            ),
            (
                QUESTION_TYPE_TRUE_FALSE,
                None,
                "Laut Text kann Homeoffice auch Schwierigkeiten bei der Trennung von Arbeit und Privatleben "
                "verursachen.",
                [("Richtig", True), ("Falsch", False)],
            ),
        ],
    ),
    (
        "B1",
        "Eine aktuelle Umfrage unter Studierenden zeigt, dass viele junge Menschen neben ihrem Studium "
        "arbeiten. Die wichtigsten Gründe dafür sind die Finanzierung des Lebensunterhalts und der Wunsch, "
        "praktische Berufserfahrung zu sammeln. Allerdings gaben einige Befragte an, dass die zusätzliche "
        "Arbeit ihre Studienleistungen negativ beeinflusse. Besonders während der Prüfungszeit falle es ihnen "
        "schwer, beide Bereiche miteinander zu vereinbaren.",
        [
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                None,
                "Warum arbeiten viele Studierende neben dem Studium?",
                [
                    ("Sie möchten weniger lernen.", False),
                    ("Sie möchten reisen.", False),
                    ("Sie benötigen Geld und möchten Berufserfahrung sammeln.", True),
                    ("Sie möchten ihr Studium verlängern.", False),
                ],
            ),
            (
                QUESTION_TYPE_CLOZE_TEXT,
                None,
                "Besonders während der ______ haben viele Studierende Schwierigkeiten, Arbeit und Studium zu "
                "vereinbaren.",
                [
                    ("Ferien", False),
                    ("Prüfungszeit", True),
                    ("Sommermonate", False),
                    ("Mittagspause", False),
                ],
            ),
        ],
    ),
    # ---- B2 ----
    (
        "B2",
        "Die zunehmende Nutzung digitaler Medien hat verändert, wie Menschen Informationen aufnehmen. Während "
        "Nachrichten früher häufig über Zeitungen oder Fernsehsendungen konsumiert wurden, erreichen "
        "Informationen heute innerhalb weniger Sekunden ein großes Publikum. Diese Entwicklung erleichtert "
        "zwar den Zugang zu Nachrichten, erhöht jedoch gleichzeitig die Verantwortung der Nutzer. Sie müssen "
        "stärker darauf achten, zwischen seriösen Informationen und unbelegten Behauptungen zu unterscheiden.",
        [
            (
                QUESTION_TYPE_TRUE_FALSE,
                None,
                "Der Text behauptet, dass digitale Medien den Zugang zu Informationen erschweren.",
                [("Richtig", False), ("Falsch", True)],
            ),
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                None,
                "Welche neue Verantwortung wird für Nutzer digitaler Medien genannt?",
                [
                    ("Sie müssen weniger Informationen lesen.", False),
                    ("Sie müssen Informationen schneller veröffentlichen.", False),
                    ("Sie müssen die Zuverlässigkeit von Informationen stärker prüfen.", True),
                    ("Sie müssen ausschließlich Zeitungen lesen.", False),
                ],
            ),
        ],
    ),
    (
        "B2",
        "Viele Städte investieren inzwischen in den Ausbau des öffentlichen Nahverkehrs. Dahinter steht nicht "
        "nur das Ziel, den Autoverkehr zu reduzieren. Ein gut ausgebautes Verkehrsnetz kann auch Menschen "
        "zugutekommen, die kein eigenes Auto besitzen. Allerdings führt der Ausbau allein nicht automatisch "
        "zu einer stärkeren Nutzung öffentlicher Verkehrsmittel. Entscheidend sind unter anderem die "
        "Zuverlässigkeit, die Preise und die Erreichbarkeit verschiedener Stadtteile.",
        [
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                None,
                "Welche Aussage entspricht dem Text?",
                [
                    ("Öffentliche Verkehrsmittel werden nur von Autofahrern genutzt.", False),
                    ("Der Ausbau des Verkehrsnetzes garantiert automatisch mehr Fahrgäste.", False),
                    ("Mehrere Faktoren beeinflussen die Nutzung öffentlicher Verkehrsmittel.", True),
                    ("Der Preis spielt bei der Verkehrsmittelwahl keine Rolle.", False),
                ],
            ),
            (
                QUESTION_TYPE_CLOZE_TEXT,
                None,
                "Ein gut ausgebautes Verkehrsnetz kann besonders Menschen helfen, die kein eigenes ______ "
                "besitzen.",
                [
                    ("Fahrrad", False),
                    ("Auto", True),
                    ("Haus", False),
                    ("Ticket", False),
                ],
            ),
        ],
    ),
    # ---- C1 ----
    (
        "C1",
        "Die Diskussion über die Auswirkungen künstlicher Intelligenz auf den Arbeitsmarkt wird häufig von "
        "zwei gegensätzlichen Positionen geprägt. Während die einen vor einem massiven Verlust von "
        "Arbeitsplätzen warnen, betonen andere die Möglichkeit, dass durch Automatisierung neue "
        "Tätigkeitsfelder entstehen. Beide Perspektiven greifen jedoch zu kurz, wenn sie technologische "
        "Veränderungen isoliert betrachten. Entscheidend dürfte vielmehr sein, wie schnell sich "
        "Bildungssysteme, Unternehmen und Arbeitnehmer an veränderte Anforderungen anpassen können.",
        [
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                None,
                "Welche Position vertritt der Text?",
                [
                    ("Künstliche Intelligenz wird ausschließlich Arbeitsplätze vernichten.", False),
                    ("Neue Technologien haben keinen Einfluss auf den Arbeitsmarkt.", False),
                    (
                        "Die Auswirkungen hängen auch davon ab, wie sich gesellschaftliche Institutionen "
                        "anpassen.",
                        True,
                    ),
                    ("Bildungssysteme sollten unverändert bleiben.", False),
                ],
            ),
            (
                QUESTION_TYPE_TRUE_FALSE,
                None,
                "Der Text stellt die beiden extremen Positionen als vollständig ausreichend dar.",
                [("Richtig", False), ("Falsch", True)],
            ),
        ],
    ),
    (
        "C1",
        "Politische Entscheidungen werden nicht selten anhand kurzfristig sichtbarer Ergebnisse bewertet. "
        "Eine solche Betrachtungsweise kann jedoch zu Fehleinschätzungen führen, wenn Maßnahmen erst nach "
        "mehreren Jahren ihre Wirkung entfalten. Umgekehrt kann eine kurzfristige Verbesserung langfristig "
        "mit unerwarteten Folgekosten verbunden sein. Eine differenzierte Bewertung sollte deshalb nicht nur "
        "unmittelbare Resultate berücksichtigen, sondern auch mögliche Nebenwirkungen und unterschiedliche "
        "zeitliche Perspektiven einbeziehen.",
        [
            (
                QUESTION_TYPE_MULTIPLE_CHOICE,
                None,
                "Was fordert der Text für eine differenzierte Bewertung?",
                [
                    ("Nur kurzfristige Ergebnisse zu berücksichtigen.", False),
                    ("Ausschließlich finanzielle Kosten zu betrachten.", False),
                    (
                        "Kurz- und langfristige Auswirkungen sowie mögliche Nebenwirkungen einzubeziehen.",
                        True,
                    ),
                    ("Politische Entscheidungen grundsätzlich nicht zu bewerten.", False),
                ],
            ),
            (
                QUESTION_TYPE_CLOZE_TEXT,
                None,
                "Eine kurzfristige Verbesserung kann langfristig mit unerwarteten ______ verbunden sein.",
                [
                    ("Folgekosten", True),
                    ("Ergebnissen", False),
                    ("Perspektiven", False),
                    ("Entscheidungen", False),
                ],
            ),
        ],
    ),
]


def _upsert_task(db: Session, order_index: int, level: str, passage: str | None) -> VizuMockTask:
    task = db.scalar(
        select(VizuMockTask).where(VizuMockTask.skill == SKILL_LESEN, VizuMockTask.order_index == order_index)
    )
    if task is None:
        task = VizuMockTask(skill=SKILL_LESEN, order_index=order_index)
        db.add(task)
        print(f"  Creating Aufgabe {order_index} ({level}).")
    else:
        print(f"  Aufgabe {order_index} ({level}) already exists — updating.")
    task.level = level
    task.passage_text = passage
    db.flush()
    return task


def _upsert_question(
    db: Session, task: VizuMockTask, order_index: int, question_type: str, passage: str | None, prompt: str
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
    question.passage_text = passage
    question.prompt = prompt
    question.points = 5
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
        for task_order, (level, task_passage, questions) in enumerate(TASKS, start=1):
            task = _upsert_task(db, task_order, level, task_passage)
            task_count += 1

            for question_order, (q_type, q_passage, prompt, options) in enumerate(questions, start=1):
                question = _upsert_question(db, task, question_order, q_type, q_passage, prompt)
                question_count += 1
                for option_order, (text, is_correct) in enumerate(options, start=1):
                    _upsert_option(db, question, option_order, text, is_correct)

        db.commit()
        print(f"Done. {task_count} Aufgabe(n), {question_count} question(s) seeded/updated for Lesen.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
