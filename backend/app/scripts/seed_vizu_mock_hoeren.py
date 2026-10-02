"""Idempotent production seed for VIZU-Mock -> Hören: 5 Aufgaben, 4 tests each
(20 tests, 80 options), 5 points per test (max 100), tests ordered 1-20.

VIZU-Mock and VIZU-Multilevel are ONE system (VIZU-Mock was renamed; both
URL prefixes /vizu-mock and /vizu-multilevel serve the same handlers and the
same `vizu_mock_*` tables), so this seed writes into that existing
architecture through the existing Hören importer — no parallel tables.
The content is embedded here (it does not read content/vizu_multilevel/
hoeren.json).

Safe to run repeatedly:
* identical content already present -> nothing changes ("unchanged");
* otherwise ONLY the Hören tasks/questions/options are replaced, in one
  transaction (any error rolls everything back);
* uploaded audio files are never touched — they stay linked to their
  Aufgabe number (1-5);
* Lesen, Schreiben, Sprechen and student attempts are not touched.

Run on the server (from backend/):
    python -m app.scripts.seed_vizu_mock_hoeren
"""

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.vizu_multilevel_content import (
    SKILL_HOEREN,
    VizuMultilevelOption,
    VizuMultilevelQuestion,
    VizuMultilevelTask,
)
from app.services.vizu_multilevel.hoeren_json_import_service import import_hoeren

A = []


def aufgabe(script, questions):
    n = len(A) + 1
    qs = []
    for text, options, correct in questions:
        qn = sum(len(a["questions"]) for a in A) + len(qs) + 1
        qs.append(
            {
                "id": qn,
                "order": qn,
                "type": "multiple_choice",
                "question": text,
                "options": [{"key": k, "text": t} for k, t in zip("ABCD", options)],
                "correct_answer": correct,
                "points": 5,
            }
        )
    A.append({"id": n, "order": n, "audio_script": script, "questions": qs})


aufgabe(
    "Daniel ist 23 Jahre alt. Er wohnt jetzt in Berlin. Jeden Morgen steht er um 7 Uhr auf. Danach fährt er mit dem Bus zur Sprachschule. Am Nachmittag arbeitet er in einem Café.",
    [
        ("Wie alt ist Daniel?", ["21 Jahre", "22 Jahre", "23 Jahre", "24 Jahre"], "C"),
        ("Wo wohnt Daniel jetzt?", ["In Spanien", "In Berlin", "In Hamburg", "In München"], "B"),
        ("Wie fährt Daniel zur Sprachschule?", ["Mit dem Auto", "Mit dem Fahrrad", "Mit dem Zug", "Mit dem Bus"], "D"),
        (
            "Was macht Daniel am Nachmittag?",
            ["Er arbeitet in einem Café.", "Er besucht seine Freunde.", "Er lernt an der Universität.", "Er geht einkaufen."],
            "A",
        ),
    ],
)
aufgabe(
    "Guten Morgen, hier ist eine Information für alle Kursteilnehmer. Der Deutschkurs am Dienstag beginnt nicht wie geplant um 18 Uhr, sondern erst um 19 Uhr. Der Unterricht findet außerdem nicht in Raum 204, sondern in Raum 208 statt. Der Kurs dauert wie gewohnt 90 Minuten. Bitte bringen Sie Ihr Kursbuch und Ihre Hausaufgaben mit. Nach dem Unterricht findet kein zusätzlicher Test statt.",
    [
        ("Wann beginnt der Deutschkurs?", ["Um 17 Uhr", "Um 18 Uhr", "Um 19 Uhr", "Um 20 Uhr"], "C"),
        ("In welchem Raum findet der Unterricht statt?", ["Raum 202", "Raum 204", "Raum 208", "Raum 218"], "C"),
        ("Wie lange dauert der Unterricht?", ["60 Minuten", "75 Minuten", "90 Minuten", "120 Minuten"], "C"),
        (
            "Was sollen die Kursteilnehmer mitbringen?",
            ["Nur einen Stift", "Kursbuch und Hausaufgaben", "Einen Laptop", "Einen neuen Test"],
            "B",
        ),
    ],
)
aufgabe(
    "In vielen Städten nutzen Menschen inzwischen häufiger öffentliche Verkehrsmittel. Ein Grund dafür ist, dass der Autoverkehr in den Innenstädten immer stärker zunimmt. Busse und Bahnen können dazu beitragen, Straßen zu entlasten und den Platzbedarf im Stadtzentrum zu reduzieren. Allerdings entscheiden sich nicht alle Menschen freiwillig für Bus und Bahn. Besonders außerhalb der großen Städte sind die Verbindungen teilweise unregelmäßig oder zu selten.\n\nEin weiterer wichtiger Punkt ist die Zuverlässigkeit. Wenn Busse häufig verspätet sind oder Anschlüsse nicht funktionieren, verlieren Fahrgäste schnell das Vertrauen in den öffentlichen Verkehr. Deshalb investieren viele Städte inzwischen nicht nur in neue Fahrzeuge, sondern auch in bessere Fahrpläne und digitale Informationssysteme.",
    [
        (
            "Warum nutzen Menschen häufiger öffentliche Verkehrsmittel?",
            [
                "Weil Autos in allen Städten verboten sind.",
                "Weil der Autoverkehr in Innenstädten zunimmt.",
                "Weil Busse immer schneller als Autos sind.",
                "Weil öffentliche Verkehrsmittel kostenlos sind.",
            ],
            "B",
        ),
        (
            "Was ist laut Audio ein Problem außerhalb großer Städte?",
            [
                "Es gibt zu viele Busse.",
                "Die Fahrkarten sind immer kostenlos.",
                "Die Verbindungen sind teilweise zu selten.",
                "Die Straßen sind zu breit.",
            ],
            "C",
        ),
        (
            "Was kann dazu führen, dass Fahrgäste das Vertrauen verlieren?",
            ["Neue Fahrzeuge", "Gute Fahrpläne", "Verspätungen und Probleme bei Anschlüssen", "Digitale Informationssysteme"],
            "C",
        ),
        (
            "Worin investieren viele Städte?",
            [
                "Nur in neue Straßen.",
                "Nur in größere Parkplätze.",
                "In neue Fahrzeuge, bessere Fahrpläne und digitale Informationssysteme.",
                "Ausschließlich in Fahrräder.",
            ],
            "C",
        ),
    ],
)
aufgabe(
    "Die zunehmende Verbreitung von Homeoffice hat die Organisation vieler Unternehmen verändert. Während einige Beschäftigte die gewonnene Flexibilität als großen Vorteil betrachten, berichten andere von Schwierigkeiten, Arbeit und Privatleben klar voneinander zu trennen. Besonders problematisch kann es werden, wenn Mitarbeiter auch außerhalb ihrer regulären Arbeitszeit ständig Nachrichten beantworten oder an digitalen Besprechungen teilnehmen.\n\nGleichzeitig hat sich gezeigt, dass Homeoffice nicht für jede Tätigkeit gleichermaßen geeignet ist. Aufgaben, die eine intensive persönliche Zusammenarbeit erfordern, lassen sich teilweise schwieriger vollständig online erledigen. Viele Unternehmen setzen deshalb inzwischen auf hybride Modelle, bei denen Beschäftigte einen Teil der Woche zu Hause und einen Teil im Büro arbeiten.\n\nEntscheidend ist dabei nicht allein die technische Ausstattung. Auch klare Kommunikationsregeln, realistische Arbeitszeiten und regelmäßiger persönlicher Austausch spielen eine wichtige Rolle.",
    [
        (
            "Welchen Vorteil sehen einige Beschäftigte im Homeoffice?",
            ["Weniger Verantwortung", "Mehr Flexibilität", "Höhere Gehälter", "Weniger Aufgaben"],
            "B",
        ),
        (
            "Welches Problem wird im Zusammenhang mit Homeoffice genannt?",
            [
                "Mitarbeiter haben keine technischen Geräte.",
                "Arbeit und Privatleben können schwer voneinander getrennt werden.",
                "Unternehmen müssen immer neue Büros bauen.",
                "Mitarbeiter können überhaupt nicht kommunizieren.",
            ],
            "B",
        ),
        (
            "Warum nutzen viele Unternehmen hybride Arbeitsmodelle?",
            [
                "Weil Homeoffice gesetzlich verboten ist.",
                "Weil persönliche Zusammenarbeit bei bestimmten Aufgaben weiterhin wichtig ist.",
                "Weil Mitarbeiter nicht zu Hause arbeiten möchten.",
                "Weil Büros vollständig abgeschafft werden sollen.",
            ],
            "B",
        ),
        (
            "Was ist laut Audio neben der technischen Ausstattung wichtig?",
            [
                "Längere Arbeitszeiten",
                "Weniger Kommunikation",
                "Klare Kommunikationsregeln, realistische Arbeitszeiten und persönlicher Austausch",
                "Mehr digitale Besprechungen außerhalb der Arbeitszeit",
            ],
            "C",
        ),
    ],
)
aufgabe(
    "Die Diskussion über den Einsatz künstlicher Intelligenz im Bildungsbereich wird häufig auf die Frage reduziert, ob KI Lernprozesse schneller und effizienter machen kann. Eine solche Perspektive greift jedoch zu kurz. Bildung besteht nicht ausschließlich darin, möglichst schnell Informationen aufzunehmen oder Aufgaben zu erledigen. Ebenso wichtig sind die Fähigkeit, Argumente zu beurteilen, Quellen kritisch zu hinterfragen und eigene Gedanken zu entwickeln.\n\nKI-Systeme können Lernende beispielsweise dabei unterstützen, unterschiedliche Erklärungen zu einem Thema zu erhalten oder erste Rückmeldungen zu einem selbst verfassten Text zu bekommen. Gleichzeitig besteht die Gefahr, dass Lernende die Verantwortung für den eigenen Denkprozess an ein System abgeben. Wenn eine KI eine vollständige Lösung liefert, kann das zwar kurzfristig Zeit sparen, führt aber nicht zwangsläufig zu einem nachhaltigen Lernerfolg.\n\nDeshalb sollte die zentrale Frage nicht lauten, ob KI im Unterricht eingesetzt werden darf, sondern unter welchen Bedingungen ihr Einsatz pädagogisch sinnvoll ist. Lehrkräfte benötigen dafür nicht nur technische Kenntnisse, sondern auch die Fähigkeit, Lernaufgaben so zu gestalten, dass KI als Werkzeug genutzt wird, ohne zentrale Denk- und Lernprozesse zu ersetzen.",
    [
        (
            "Warum greift die Perspektive auf KI als reines Effizienzwerkzeug laut Audio zu kurz?",
            [
                "Weil KI im Bildungsbereich noch nicht existiert.",
                "Weil Bildung mehr umfasst als die schnelle Aufnahme von Informationen.",
                "Weil KI keine Informationen verarbeiten kann.",
                "Weil Lernende keine digitalen Systeme benutzen möchten.",
            ],
            "B",
        ),
        (
            "Welche Möglichkeit von KI wird im Audio genannt?",
            [
                "KI kann Lernenden unterschiedliche Erklärungen geben und Rückmeldungen zu Texten liefern.",
                "KI kann Lehrer vollständig ersetzen.",
                "KI kann Prüfungen grundsätzlich abschaffen.",
                "KI kann nur mathematische Aufgaben lösen.",
            ],
            "A",
        ),
        (
            "Welche Gefahr wird beschrieben?",
            [
                "Lernende könnten zu viele Bücher lesen.",
                "Lernende könnten die Verantwortung für ihren eigenen Denkprozess an KI abgeben.",
                "Lehrkräfte könnten keine Computer mehr benutzen.",
                "Digitale Medien könnten vollständig verschwinden.",
            ],
            "B",
        ),
        (
            "Welche zentrale Frage wird am Ende des Audios formuliert?",
            [
                "Wie kann KI vollständig aus Schulen entfernt werden?",
                "Wie kann man möglichst viele KI-Systeme kaufen?",
                "Unter welchen Bedingungen kann KI pädagogisch sinnvoll eingesetzt werden?",
                "Wie kann man traditionelle Unterrichtsmethoden abschaffen?",
            ],
            "C",
        ),
    ],
)



DATASET = {
    "module": "hoeren",
    "title": "VIZU-Mock Hören",
    "total_questions": 20,
    "points_per_question": 5,
    "max_score": 100,
    "aufgaben": A,
}


def counts(db) -> dict:
    hoeren = VizuMultilevelTask.skill == SKILL_HOEREN
    tasks = db.scalar(select(func.count()).select_from(VizuMultilevelTask).where(hoeren))
    questions = db.scalar(
        select(func.count()).select_from(VizuMultilevelQuestion).join(VizuMultilevelTask).where(hoeren)
    )
    options = db.scalar(
        select(func.count())
        .select_from(VizuMultilevelOption)
        .join(VizuMultilevelQuestion)
        .join(VizuMultilevelTask)
        .where(hoeren)
    )
    points = db.scalar(select(func.sum(VizuMultilevelQuestion.points)).join(VizuMultilevelTask).where(hoeren))
    return {"aufgaben": tasks, "questions": questions, "options": options, "max_score": float(points or 0)}


def main() -> None:
    db = SessionLocal()
    try:
        result = import_hoeren(db, DATASET)
        print("seed:", result)
        print("database:", counts(db))
    finally:
        db.close()


if __name__ == "__main__":
    main()
