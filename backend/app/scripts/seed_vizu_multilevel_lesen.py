"""Seed for VIZU-Multilevel -> Lesen: 5 reading texts x 4 questions = 20
questions, 5 points each (100 points total).

Content is stored in the database as structured data (no CSV). Each text
carries an INTERNAL CEFR level (A1..C1) that is saved on the task for
scoring/statistics but is never sent to the student.

Idempotent and non-destructive: a text / question that already exists
(matched by its order) is left exactly as it is, so re-running creates no
duplicates and never overwrites edits an admin made later.

Run from backend/:  python -m app.scripts.seed_vizu_multilevel_lesen
"""

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.vizu_multilevel_content import (
    SKILL_LESEN,
    VizuMultilevelOption,
    VizuMultilevelQuestion,
    VizuMultilevelTask,
)

POINTS_PER_QUESTION = 5

TRUE_FALSE = "TRUE_FALSE"
MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
DETAIL = "DETAIL"
INFO_MATCH = "INFO_MATCH"
AD_MATCH = "AD_MATCH"
HEADLINE_MATCH = "HEADLINE_MATCH"
MAIN_IDEA = "MAIN_IDEA"
STATEMENT_MATCH = "STATEMENT_MATCH"
COMPREHENSION = "COMPREHENSION"


def q(question_type: str, prompt: str, options: list[str], correct: int) -> dict:
    """`correct` is the 0-based index of the right option."""
    return {"type": question_type, "prompt": prompt, "options": options, "correct": correct}


# Each text: order (1-5), internal level, passage, exactly 4 questions.
TEXTS: list[dict] = [
    {
        "order": 1,
        "level": "A1",
        "passage": (
            "Hallo Tom,\n\n"
            "ich bin Anna. Ich wohne jetzt in Berlin. Meine Wohnung ist klein, aber schön. Sie hat zwei Zimmer und einen "
            "Balkon. Ich arbeite in einem Café. Das Café öffnet um 8 Uhr und schließt um 16 Uhr. Am Samstag habe ich frei. "
            "Dann koche ich gern mit Freunden. Am Samstag um 18 Uhr kommen drei Freunde zu mir. Kommst du auch? "
            "Bring bitte einen Salat mit.\n\n"
            "Liebe Grüße\nAnna"
        ),
        "questions": [
            q(TRUE_FALSE, "Anna wohnt jetzt in Berlin.", ["Richtig", "Falsch"], 0),
            q(MULTIPLE_CHOICE, "Wie viele Zimmer hat Annas Wohnung?", ["Ein Zimmer", "Zwei Zimmer", "Drei Zimmer"], 1),
            q(DETAIL, "Wann schließt das Café?", ["Um 8 Uhr", "Um 16 Uhr", "Um 18 Uhr"], 1),
            q(INFO_MATCH, "Was soll Tom mitbringen?", ["Ein Brot", "Einen Salat", "Ein Getränk"], 1),
        ],
    },
    {
        "order": 2,
        "level": "A2",
        "passage": (
            "Freizeit in Neustadt – drei Angebote\n\n"
            "A) Schwimmkurs für Erwachsene\n"
            "Jeden Samstag von 10 bis 11.30 Uhr im Stadtbad. Anfänger sind willkommen. Der Kurs kostet 45 Euro für sechs "
            "Termine. Anmeldung online oder an der Kasse.\n\n"
            "B) Kochabend international\n"
            "Jeden zweiten Freitag kochen wir zusammen Gerichte aus verschiedenen Ländern. Beginn ist um 18 Uhr im "
            "Bürgerhaus. Bitte bringen Sie eine Schürze mit. Teilnahme: 12 Euro, das Essen ist im Preis enthalten.\n\n"
            "C) Fahrradwerkstatt\n"
            "Hier können Sie Ihr Fahrrad selbst reparieren. Werkzeug und Hilfe sind kostenlos. Geöffnet dienstags und "
            "donnerstags von 16 bis 19 Uhr. Ersatzteile müssen Sie selbst bezahlen."
        ),
        "questions": [
            q(
                AD_MATCH,
                "Maria hat noch nie geschwommen und möchte es am Wochenende lernen. Welches Angebot passt?",
                ["Angebot A", "Angebot B", "Angebot C"],
                0,
            ),
            q(TRUE_FALSE, "Beim Kochabend muss man das Essen extra bezahlen.", ["Richtig", "Falsch"], 1),
            q(
                DETAIL,
                "Wann ist die Fahrradwerkstatt geöffnet?",
                ["Samstags am Vormittag", "Dienstags und donnerstags am Nachmittag", "Jeden zweiten Freitag am Abend"],
                1,
            ),
            q(MULTIPLE_CHOICE, "Was kostet der Schwimmkurs insgesamt?", ["12 Euro", "45 Euro", "Er ist kostenlos"], 1),
        ],
    },
    {
        "order": 3,
        "level": "B1",
        "passage": (
            "Immer mehr Menschen arbeiten von zu Hause. Vor fünf Jahren war das noch die Ausnahme, heute bieten viele "
            "Firmen zumindest einzelne Homeoffice-Tage an. Die Vorteile liegen auf der Hand: Man spart den Weg zur "
            "Arbeit, kann sich die Zeit freier einteilen und ist zu Hause oft ruhiger und konzentrierter als im "
            "Großraumbüro. Auch die Umwelt profitiert, weil weniger Menschen mit dem Auto pendeln.\n\n"
            "Allerdings gibt es auch Probleme. Viele Beschäftigte berichten, dass sie schlechter abschalten können, wenn "
            "der Arbeitsplatz im Wohnzimmer steht. Außerdem fehlt der spontane Austausch mit den Kollegen. Eine Studie "
            "zeigt, dass Teams, die sich nur noch online sehen, weniger neue Ideen entwickeln.\n\n"
            "Deshalb setzen viele Unternehmen jetzt auf ein gemischtes Modell: Zwei oder drei Tage im Büro, die übrigen "
            "Tage zu Hause. So bleibt der persönliche Kontakt erhalten, und trotzdem gewinnen die Mitarbeiter "
            "Flexibilität."
        ),
        "questions": [
            q(
                HEADLINE_MATCH,
                "Welche Überschrift passt am besten zum Text?",
                [
                    "Büroarbeit ist besser als Homeoffice",
                    "Homeoffice: Chancen, Probleme und ein Kompromiss",
                    "Warum immer mehr Menschen Auto fahren",
                ],
                1,
            ),
            q(
                DETAIL,
                "Was berichten viele Beschäftigte als Problem?",
                [
                    "Sie haben zu wenig Arbeit.",
                    "Sie können schlechter abschalten.",
                    "Sie müssen länger pendeln.",
                ],
                1,
            ),
            q(
                TRUE_FALSE,
                "Laut einer Studie entwickeln Teams, die sich nur online sehen, mehr neue Ideen.",
                ["Richtig", "Falsch"],
                1,
            ),
            q(
                MAIN_IDEA,
                "Was ist mit dem „gemischten Modell“ gemeint?",
                [
                    "Alle Mitarbeiter arbeiten nur noch zu Hause.",
                    "Einige Tage arbeitet man im Büro, die anderen zu Hause.",
                    "Das Büro wird in ein Großraumbüro umgebaut.",
                ],
                1,
            ),
        ],
    },
    {
        "order": 4,
        "level": "B2",
        "passage": (
            "Die Vier-Tage-Woche gilt für viele als Arbeitsmodell der Zukunft. In Island wurde die Arbeitszeit in "
            "mehreren Pilotprojekten von 40 auf 35 bis 36 Stunden gesenkt, ohne dass die Gehälter sanken. Das Ergebnis "
            "überraschte selbst die Skeptiker: Die Produktivität blieb nahezu gleich, während sich Stress und "
            "Erschöpfung der Beschäftigten deutlich verringerten.\n\n"
            "Befürworter argumentieren, dass kürzere Arbeitszeiten zu mehr Konzentration führen. Wer wisse, dass das "
            "Wochenende früher beginnt, arbeite effizienter und verliere sich weniger in unnötigen Besprechungen. "
            "Kritiker halten dagegen, dass sich das Modell nicht auf jede Branche übertragen lasse. In Krankenhäusern "
            "oder im Einzelhandel müsse die Besetzung über lange Zeiträume gesichert sein; eine kürzere Arbeitszeit "
            "bedeute dort schlicht, dass mehr Personal eingestellt werden müsse – was Kosten verursache und angesichts "
            "des Fachkräftemangels kaum realistisch sei.\n\n"
            "Arbeitsforscher weisen zudem darauf hin, dass der Erfolg der Pilotprojekte nicht allein von der "
            "Arbeitszeit abhing. Die Unternehmen hatten ihre Abläufe zuvor gründlich überprüft. Ob eine bloße "
            "Verkürzung der Arbeitszeit ohne solche Reformen dieselben Effekte hätte, ist daher offen."
        ),
        "questions": [
            q(
                DETAIL,
                "Was zeigten die Pilotprojekte in Island?",
                [
                    "Die Produktivität stieg deutlich, der Stress blieb gleich.",
                    "Die Produktivität blieb nahezu gleich, der Stress sank.",
                    "Die Gehälter mussten gesenkt werden, damit sich das Modell lohnt.",
                    "Die Beschäftigten arbeiteten insgesamt mehr Stunden als vorher.",
                ],
                1,
            ),
            q(
                STATEMENT_MATCH,
                "Welche Aussage entspricht der Position der Kritiker?",
                [
                    "Die Vier-Tage-Woche ist für alle Branchen gleich gut geeignet.",
                    "Pilotprojekte sind grundsätzlich nicht aussagekräftig.",
                    "In Branchen mit langer Besetzungspflicht verursacht eine kürzere Arbeitszeit zusätzliche Personalkosten.",
                    "Beschäftigte wollen am Wochenende lieber arbeiten.",
                ],
                2,
            ),
            q(
                COMPREHENSION,
                "Was geht aus dem letzten Absatz hervor?",
                [
                    "Die Arbeitszeitverkürzung allein erklärt die Erfolge sicher.",
                    "Es ist unklar, ob die Verkürzung allein die positiven Ergebnisse erklärt.",
                    "Die Unternehmen haben ihre Abläufe nicht verändert.",
                    "Die Forscher lehnen Pilotprojekte grundsätzlich ab.",
                ],
                1,
            ),
            q(
                MULTIPLE_CHOICE,
                "Warum arbeiten Beschäftigte laut den Befürwortern bei kürzerer Woche effizienter?",
                [
                    "Weil sie mehr Geld verdienen.",
                    "Weil sie weniger Zeit in unnötigen Besprechungen verlieren.",
                    "Weil sie häufiger Urlaub nehmen.",
                    "Weil sie mehr Kollegen zur Unterstützung haben.",
                ],
                1,
            ),
        ],
    },
    {
        "order": 5,
        "level": "C1",
        "passage": (
            "Es gehört mittlerweile zum guten Ton, die ständige Erreichbarkeit zu beklagen. Doch die Klage allein greift "
            "zu kurz, denn sie unterstellt, wir seien bloß Opfer einer Technik, die uns überrollt. Tatsächlich ist "
            "Aufmerksamkeit zu einem knappen Gut geworden, um das Plattformbetreiber mit erheblichem Aufwand "
            "konkurrieren – und sie tun das mit Mechanismen, die längst nicht mehr zufällig sind: endlose Feeds, "
            "Benachrichtigungen im Minutentakt, Belohnungen in unvorhersehbaren Abständen.\n\n"
            "Man könnte nun einwenden, jeder Mensch trage die Verantwortung für seinen eigenen Medienkonsum. Das ist "
            "nicht falsch, verkennt aber das Kräfteverhältnis: Wer einem Heer von Verhaltensforschern gegenübersteht, "
            "kann sich nicht allein auf seine Willenskraft verlassen. Ebenso wenig überzeugt freilich die Gegenposition, "
            "die nach strengen gesetzlichen Verboten ruft. Sie unterschätzt, wie stark digitale Angebote inzwischen Teil "
            "des Berufs- und Privatlebens sind, und ignoriert, dass die Regulierung der Entwicklung stets hinterherhinkt.\n\n"
            "Plausibler erscheint mir ein dritter Weg: Transparenz. Müssten Anbieter offenlegen, nach welchen Kriterien "
            "ihre Algorithmen Inhalte auswählen, könnten Nutzer und Aufsichtsbehörden zumindest beurteilen, wo Gestaltung "
            "in Manipulation umschlägt. Das löst das Problem nicht, verschiebt aber die Machtverhältnisse ein Stück weit "
            "– und das wäre mehr, als man von bloßen Appellen zur digitalen Selbstdisziplin erwarten darf."
        ),
        "questions": [
            q(
                COMPREHENSION,
                "Wie bewertet der Autor die verbreitete Klage über ständige Erreichbarkeit?",
                [
                    "Er hält sie für völlig unberechtigt.",
                    "Er hält sie für unzureichend, weil sie Nutzer nur als Opfer darstellt.",
                    "Er hält sie für die wichtigste Grundlage politischen Handelns.",
                    "Er hält sie für übertrieben, weil Technik harmlos sei.",
                ],
                1,
            ),
            q(
                STATEMENT_MATCH,
                "Welche Aussage entspricht dem Einwand des Autors gegen die reine Eigenverantwortung?",
                [
                    "Nutzer sind den gezielt entwickelten Mechanismen der Anbieter allein kaum gewachsen.",
                    "Medienkonsum hat keinerlei Einfluss auf den Alltag.",
                    "Verhaltensforscher arbeiten ausschließlich für Behörden.",
                    "Willenskraft ist nur eine Frage des Alters.",
                ],
                0,
            ),
            q(
                DETAIL,
                "Warum lehnt der Autor strenge gesetzliche Verbote ab?",
                [
                    "Weil Verbote immer zu teuer sind.",
                    "Weil sie die Bedeutung digitaler Angebote unterschätzen und der Entwicklung hinterherhinken.",
                    "Weil Plattformbetreiber keine Gesetze befolgen müssen.",
                    "Weil Nutzer Verbote grundsätzlich begrüßen.",
                ],
                1,
            ),
            q(
                MAIN_IDEA,
                "Wie schätzt der Autor die Wirkung seines Vorschlags (Transparenz) ein?",
                [
                    "Er löst das Problem vollständig.",
                    "Er bringt gar nichts und ist nur ein Appell.",
                    "Er löst das Problem nicht ganz, verändert aber das Kräfteverhältnis zugunsten der Nutzer.",
                    "Er ersetzt jede Form von Regulierung dauerhaft.",
                ],
                2,
            ),
        ],
    },
]


def seed(db) -> dict:
    created_tasks = created_questions = 0
    question_order = 0
    for text in TEXTS:
        task = db.scalar(
            select(VizuMultilevelTask).where(
                VizuMultilevelTask.skill == SKILL_LESEN, VizuMultilevelTask.order_index == text["order"]
            )
        )
        if task is None:
            task = VizuMultilevelTask(
                skill=SKILL_LESEN,
                level=text["level"],
                order_index=text["order"],
                passage_text=text["passage"],
                is_published=True,
            )
            db.add(task)
            db.flush()
            created_tasks += 1

        for item in text["questions"]:
            question_order += 1  # global order 1..20
            exists = db.scalar(
                select(VizuMultilevelQuestion.id).where(
                    VizuMultilevelQuestion.task_id == task.id,
                    VizuMultilevelQuestion.order_index == question_order,
                )
            )
            if exists is not None:
                continue
            question = VizuMultilevelQuestion(
                task_id=task.id,
                question_type=item["type"],
                prompt=item["prompt"],
                order_index=question_order,
                points=POINTS_PER_QUESTION,
                is_active=True,
            )
            for index, option_text in enumerate(item["options"]):
                question.options.append(
                    VizuMultilevelOption(
                        option_text=option_text, is_correct=(index == item["correct"]), order_index=index + 1
                    )
                )
            db.add(question)
            created_questions += 1
    db.commit()
    return {"tasks_created": created_tasks, "questions_created": created_questions}


def main() -> None:
    db = SessionLocal()
    try:
        print(seed(db))
    finally:
        db.close()


if __name__ == "__main__":
    main()
