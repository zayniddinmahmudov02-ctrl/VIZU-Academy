"""A2 9. Unterricht — Medien, Nachrichten und Meinung — Grammatik: Finalsätze (damit / um … zu) (book pp. 94-103).

Book: Frage p.95, Finalsätze p.96, Grammatik-Aufgaben (15 x damit, 15 x
um … zu) p.97, Lesen (Nachrichten überall; eight Richtig/Falsch) pp.98-99,
Hören (Ordnen Sie zu: A-F, no transcript) p.100, Schreiben (Thema +
Kommentar) p.101, Sprechen p.102, Wortschatzmethode (five word sets) p.103.

Keys: Lesen and Hören from "Vizu-Antworten A2". um … zu: one sentence each
(the subject of both clauses is the same; "wollen" falls away), accepted
with and without comma. damit: the book's own example keeps "will" — the
expected form is ambiguous, so the damit column is a written task for the
teacher. Wortschatz: the book gives German definitions only, no Uzbek
translations — the definitions are used as the meaning (nothing invented)."""

from . import base, exercise, intro_html, match, mc, short, summary_html, tf, words

L = 9
LESSON_TITLE = "Medien, Nachrichten und Meinung"
LESSON_DESCRIPTION = "Thema: Medien, Nachrichten und Meinung · Grammatik: Finalsätze (damit / um … zu)"
AUDIO = {"vizu-a2-l09-hoeren-01": "A2 9.Unterricht Hören.mp3"}

EINFUEHRUNG_HTML = intro_html(
    9, "Medien, Nachrichten und Meinung", "Finalsätze: damit … / um … zu",
    ["maqsadni damit va um … zu bilan aytish;",
     "ikki xil ega bo'lsa damit, bir xil ega bo'lsa um … zu ishlatish;",
     "media, yangiliklar va fikr bildirish so'zlarini o'rganish."],
    ["internetdagi har bir xabarga ishonish mumkinmi — fikringizni aytasiz;",
     "bugungi kunda qanday ma'lumot olishimiz haqidagi matnni tushunasiz;",
     "kim qaysi mediadan foydalanishini tinglab moslashtirasiz;",
     "dugonangizning postiga izoh yozasiz va media odatlaringiz haqida gapirasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(9, [
    "<strong>Bedeutung:</strong> „damit“ und „um … zu“ zeigen den Zweck einer Handlung — Frage: Warum? / Wozu?",
    "<strong>damit</strong> (2 Personen): Subjekt + Verb …, damit + Subjekt + … Verb — Ich spare Geld, damit ich ein Fahrrad kaufen kann.",
    "<strong>um … zu</strong> (1 Person): Subjekt + Verb …, um + … zu + Verb — Ich spare Geld, um ein Fahrrad zu kaufen.",
    "<strong>Wortschatz:</strong> die Medien, die Nachrichten, der Vorteil, der Nachteil, die Quellen, die Meinung.",
])

GRAMMAR_HTML = (
    "<h3>Finalsätze: damit … / um … zu (A2)</h3>"
    "<h4>Bedeutung</h4><ul><li>„damit“ und „um … zu“ zeigen den <strong>Zweck</strong> einer Handlung.</li><li>Sie antworten auf die Frage: Warum?</li></ul>"
    "<h4>Zweck: Warum?</h4><p>Ich mache X, <strong>damit</strong> Y passiert. (2 Personen) → <strong>um … zu</strong>: um Y zu tun. (1 Person)</p>"
    "<h4>Satzbau</h4><ul><li><strong>damit</strong> → Subjekt + Verb …, damit + Subjekt + Verb (Verb am Ende)</li>"
    "<li><strong>um … zu</strong> → Subjekt + Verb …, um + zu + Verb</li></ul>"
    "<p>Ich spare Geld, <strong>damit</strong> ich ein Fahrrad kaufen kann. · Ich spare Geld, <strong>um</strong> ein Fahrrad <strong>zu</strong> kaufen.</p>"
    "<h4>Beispiele: damit (Fokus auf die Absicht von Person A)</h4><ol><li>Sie lernt Deutsch, damit sie in Deutschland studieren kann.</li>"
    "<li>Ich arbeite hart, damit meine Kinder ein besseres Leben haben.</li><li>Jonas ruft an, damit er mit Anna sprechen kann.</li>"
    "<li>Lisa geht einkaufen, damit sie Obst hat.</li><li>Tom steht früh auf, damit er den Bus nicht verpasst.</li>"
    "<li>Paul nimmt einen Regenschirm, damit er nicht nass wird.</li></ol>"
    "<h4>Beispiele: um … zu (Fokus auf die Handlung von Person B)</h4><ol><li>Sie lernt Deutsch, um in Deutschland zu studieren.</li>"
    "<li>Ich arbeite viel, um viel Geld zu verdienen.</li><li>Jonas ruft an, um mit Anna zu sprechen.</li><li>Lisa geht einkaufen, um Obst zu kaufen.</li>"
    "<li>Tom steht früh auf, um den Bus zu nehmen.</li><li>Paul nimmt einen Regenschirm, um nicht nass zu werden.</li></ol>"
    "<h4>Unterschiede im Vergleich</h4><ul><li>Er übt jeden Tag, damit er besser wird. / um besser zu werden.</li>"
    "<li>Sie spart Geld, damit sie reisen kann. / um reisen zu können.</li><li>Wir lernen Deutsch, damit wir gute Jobs bekommen. / um gute Jobs zu bekommen.</li>"
    "<li>Ich lese viel, damit ich mehr weiß. / um mehr zu wissen.</li><li>Er macht Sport, damit er gesund bleibt. / um gesund zu bleiben.</li>"
    "<li>Sie fragt nach, damit sie alles versteht. / um alles zu verstehen.</li></ul>"
)

DAMIT = ["Ich lerne Deutsch. Ich will in Deutschland studieren. (Beispiel: …, damit ich in Deutschland studieren will.)",
         "Sie arbeitet viel. Sie will mehr Geld verdienen.", "Wir sparen Geld. Wir wollen ein Auto kaufen.", "Er geht früh schlafen. Er will morgen fit sein.",
         "Ich kaufe ein Geschenk. Meine Mutter freut sich.", "Sie übt jeden Tag. Sie besteht die Prüfung.", "Wir fahren langsam. Wir kommen sicher an.",
         "Er trainiert viel. Er wird stärker.", "Ich erkläre dir das. Du verstehst es.", "Sie nimmt einen Regenschirm. Sie wird nicht nass.",
         "Wir lernen Grammatik. Wir sprechen besser.", "Er liest ein Buch. Er lernt neue Wörter.", "Ich rufe dich an. Wir besprechen alles.",
         "Sie kauft Obst. Sie bleibt gesund.", "Wir wiederholen die Lektion. Wir verstehen alles gut."]
_UM = [
    (2, "Sie arbeitet viel. Sie will mehr Geld verdienen.", "Sie arbeitet viel, um mehr Geld zu verdienen."),
    (3, "Wir sparen Geld. Wir wollen ein Auto kaufen.", "Wir sparen Geld, um ein Auto zu kaufen."),
    (4, "Er geht früh schlafen. Er will morgen fit sein.", "Er geht früh schlafen, um morgen fit zu sein."),
    (5, "Ich kaufe ein Geschenk. Ich will meine Mutter glücklich machen.", "Ich kaufe ein Geschenk, um meine Mutter glücklich zu machen."),
    (6, "Sie übt jeden Tag. Sie will die Prüfung bestehen.", "Sie übt jeden Tag, um die Prüfung zu bestehen."),
    (7, "Wir fahren langsam. Wir wollen sicher ankommen.", "Wir fahren langsam, um sicher anzukommen."),
    (8, "Er trainiert viel. Er will stärker werden.", "Er trainiert viel, um stärker zu werden."),
    (9, "Ich erkläre dir das. Ich will dir helfen.", "Ich erkläre dir das, um dir zu helfen."),
    (10, "Sie nimmt einen Regenschirm. Sie will nicht nass werden.", "Sie nimmt einen Regenschirm, um nicht nass zu werden."),
    (11, "Wir lernen Grammatik. Wir wollen besser sprechen.", "Wir lernen Grammatik, um besser zu sprechen."),
    (12, "Er liest ein Buch. Er will neue Wörter lernen.", "Er liest ein Buch, um neue Wörter zu lernen."),
    (13, "Ich rufe dich an. Ich will alles besprechen.", "Ich rufe dich an, um alles zu besprechen."),
    (14, "Sie kauft Obst. Sie will gesund bleiben.", "Sie kauft Obst, um gesund zu bleiben."),
    (15, "Wir wiederholen die Lektion. Wir wollen alles gut verstehen.", "Wir wiederholen die Lektion, um alles gut zu verstehen."),
]
UM_ZU = [short(f"{n}. {q} → um … zu", [a, a.replace(",", "")], explanation=a, max_length=200) for n, q, a in _UM]

TEXT = (
    "Heute sind Medien ein wichtiger Teil unseres Lebens. Viele Menschen informieren sich jeden Tag über Nachrichten. Besonders junge Leute benutzen ihr "
    "Smartphone. Studien zeigen, dass über 70 % der Menschen Nachrichten online lesen.\n\nEin großer Vorteil ist die Geschwindigkeit. Man bekommt "
    "Nachrichten sofort. Zum Beispiel kann man morgens im Bus oder abends zu Hause Nachrichten lesen. Außerdem gibt es viele Themen: Politik, Sport, Musik "
    "oder Umwelt. Etwa 60 % der jungen Menschen nutzen soziale Medien wie Telegram oder Instagram, um Nachrichten zu bekommen.\n\nEin weiterer Vorteil "
    "ist, dass viele Angebote kostenlos sind. Man braucht nur Internet und ein Smartphone. Deshalb sind Online-Nachrichten sehr beliebt.\n\nAber es gibt "
    "auch Nachteile. Nicht alle Informationen im Internet sind richtig. Laut Studien sind fast 30 % der Nachrichten im Internet nicht komplett oder nicht "
    "korrekt. Das ist ein Problem. Deshalb ist es wichtig, verschiedene Quellen zu lesen.\n\nViele Menschen schreiben auch ihre Meinung im Internet. Rund "
    "50 % der Nutzer kommentieren Nachrichten oder diskutieren online. Das ist interessant, weil man andere Meinungen sehen kann. Aber manchmal gibt es "
    "Streit oder negative Kommentare.\n\nIch denke: Medien sind sehr wichtig und hilfreich. Aber man muss vorsichtig sein. Man soll nicht alles glauben "
    "und immer selbst denken.")
_K = "Javob: Vizu-Antworten A2 (9. Unterricht, Lesen)."
LESEN = [
    tf("Mehr als die Hälfte der Menschen liest Nachrichten online.", True, _K + " — „über 70 % der Menschen“."),
    tf("Nur ältere Menschen benutzen Smartphones für Nachrichten.", False, _K),
    tf("Man kann Nachrichten nur zu Hause lesen.", False, _K + " — „morgens im Bus oder abends zu Hause“."),
    tf("Soziale Medien sind eine wichtige Quelle für Nachrichten.", True, _K),
    tf("Alle Informationen im Internet sind korrekt.", False, _K),
    tf("Weniger als 30 % der Nachrichten im Internet sind problematisch.", True, _K + " — „fast 30 %“."),
    tf("Viele Menschen schreiben Kommentare im Internet.", True, _K),
    tf("Es ist besser, nur eine Quelle für Nachrichten zu nutzen.", False, _K + " — „verschiedene Quellen zu lesen“."),
]
HOEREN = [match("Ordnen Sie zu: Welches Medium nutzt die Person? (A – F)", [f"Person {i}" for i in range(1, 7)],
                ["Podcast", "Internet / soziale Medien", "Fernsehen", "Radio", "Telefon / Anruf", "Zeitung"],
                {"1": "F", "2": "A", "3": "D", "4": "B", "5": "C", "6": "E"}, points=6,
                explanation="Javob: Vizu-Antworten A2 (9. Unterricht, Hören): 1-F 2-A 3-D 4-B 5-C 6-E.")]

WORDS = words([
    ("die", "Medien", "Zeitungen, Internet, Fernsehen, Radio usw."), ("die", "Nachrichten", "Informationen über aktuelle Ereignisse"),
    ("der", "Vorteil", "etwas Gutes, ein positiver Aspekt"), ("der", "Nachteil", "etwas Schlechtes, ein negativer Aspekt"),
    ("die", "Quellen", "Orte, wo man Informationen findet"), ("die", "Meinung", "das, was man denkt")], "Wichtige Wörter (Bedeutung auf Deutsch)")
VARIANTEN = {
    "Variante 1": ["lesen", "die Nachrichten", "online", "informieren", "wichtig", "die Information"],
    "Variante 2": ["die Medien", "benutzen", "das Smartphone", "schnell", "modern", "die App"],
    "Variante 3": ["das Fernsehen", "sehen", "die Sendung", "interessant", "berichten", "die Nachrichten"],
    "Variante 4": ["hören", "das Radio", "die Musik", "die Information", "täglich", "unterwegs"],
    "Variante 5": ["die Meinung", "schreiben", "kommentieren", "diskutieren", "das Internet", "wichtig"],
}


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: A2 9. Unterricht", source="vizu", page=94, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Kann man allen Nachrichten im Internet vertrauen?", page=95,
             prompt="Kann man allen Nachrichten im Internet vertrauen? Wählen Sie eine Meinung und begründen Sie sie.",
             questions=["Ja, man kann", "Es kommt darauf an", "Nein, man kann nicht"], min_duration=20, max_duration=120,
             metadata={"book_points": {
                 "ja": ["Viele Nachrichten sind wahr.", "Große Nachrichtenportale prüfen ihre Informationen.", "Journalisten recherchieren und arbeiten professionell.",
                        "Es gibt Fakten und Beweise zu wichtigen Themen.", "Man kann Quellen überprüfen und vergleichen.",
                        "Bildung und Medienkompetenz helfen, Wahres zu erkennen."],
                 "es_kommt_darauf_an": ["Es hängt von der Quelle ab.", "Nicht alle Seiten sagen die Wahrheit.", "Manche Nachrichten sind voreingenommen.",
                                        "Man sollte kritisch lesen und denken.", "Vergleiche helfen, die Wahrheit zu finden.",
                                        "Nicht alles ist falsch, aber man muss vorsichtig sein."],
                 "nein": ["Es gibt viele Fake News im Internet.", "Jeder kann etwas schreiben und veröffentlichen.", "Viele Informationen sind übertrieben oder falsch.",
                          "Es gibt Seiten, die nur Lügen verbreiten.", "Man weiß oft nicht, wer hinter der Nachricht steckt.",
                          "Sensationelle Nachrichten bringen mehr Klicks, auch wenn sie falsch sind."]}}),
        base(L, "grammatik", 1, "Grammatik: Finalsätze — damit / um … zu", page="96-97", rules=[{"title": "Finalsätze: damit … / um … zu", "html": GRAMMAR_HTML}],
             exercises=[exercise("Um … zu (2–15)", UM_ZU, "Verbinden Sie die Sätze mit um … zu. Beispiel 1: Ich lerne Deutsch, um in Deutschland zu studieren.")]),
        base(L, "schreiben", 2, "Grammatik-Aufgabe: Sätze mit damit", page=97, task_type="other",
             prompt="Verbinden Sie die Sätze mit „damit“ (Verb am Ende).\n\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(DAMIT, start=1)),
             min_words=60, max_words=300, time_limit=25,
             metadata={"note": "damit-ustuni: kutilgan shakl bir ma'noli emas (kitob misolida „will“ saqlanadi) — o'qituvchi tekshiradi."},
             support_phrases=["Ich kaufe ein Geschenk, damit meine Mutter sich freut.", "Ich erkläre dir das, damit du es verstehst."]),
        base(L, "lesen", 1, "Lesen: Nachrichten überall – Wie informieren wir uns heute?", page="98-99", instruction="Lesen Sie den Text. Richtig oder Falsch?",
             passages=[{"title": "Nachrichten überall – Wie informieren wir uns heute?", "text": TEXT}], questions=LESEN, max_score=len(LESEN)),
        base(L, "hoeren", 1, "Hören: Aufgabe zum Hören — Medien zuordnen", page=100, audio_file="A2 9.Unterricht Hören.mp3",
             instruction="Hören Sie die Personen. Ordnen Sie zu: A – F.", questions=HOEREN, max_score=6),
        base(L, "schreiben", 1, "Schreiben: Wie informiere ich mich?", page=101, task_type="description",
             prompt="Schreiben Sie einen kurzen Text über das Thema „Wie informiere ich mich?“. Schreiben Sie mindestens 80 Wörter.\n\nPunkte:\n"
                    "• Welche Informationsquellen nutzen Sie?\n• Wie oft informieren Sie sich über Nachrichten?\n"
                    "• Welche Themen interessieren Sie am meisten? (Politik, Sport, Kultur …)\n• Warum ist Information für Sie wichtig?\n"
                    "• Welche Vorteile und Nachteile haben soziale Medien?\n• Wie überprüfen Sie Informationen im Internet?",
             min_words=80, max_words=160, time_limit=25),
        base(L, "schreiben", 3, "Schreiben: Kommentar — Post von meiner Freundin", page=101, task_type="message",
             prompt="Ihre Freundin hat einen Post im Internet geschrieben. Schreiben Sie einen Kommentar dazu. Schreiben Sie mindestens 80 Wörter.\n\n"
                    "Post von meiner Freundin: „Ich finde, dass soziale Medien heute die beste Informationsquelle sind. Man bekommt schnell alle Nachrichten und "
                    "kann direkt mit anderen diskutieren.“\n\nPunkte:\n• Reagieren Sie auf den Post (Ihre Meinung).\n• Stimmen Sie zu oder nicht? Warum?\n"
                    "• Nennen Sie eigene Erfahrungen mit sozialen Medien.\n• Geben Sie Beispiele (positive oder negative).\n• Machen Sie einen Vorschlag oder Tipp.\n"
                    "• Stellen Sie eine Frage an Ihre Freundin.",
             audience="Ihre Freundin (informell, Kommentar)", min_words=80, max_words=160, time_limit=25),
        base(L, "schreiben", 4, "Wortschatz-Aufgabe: Wort zu Wort Wortschatzmethode (Medien und Nachrichten)", page=103, task_type="description",
             prompt="Formulieren Sie mit den Wörtern einer Variante einen Text (Variante 2–5).\n\n" + "\n".join(f"{k}: {', '.join(v)}" for k, v in VARIANTEN.items())
                    + "\n\nBeispiel (Variante 1) — Überschrift: Nachrichten online lesen ist praktisch. Ich lese jeden Tag Nachrichten online, weil Informationen "
                      "für mich sehr wichtig sind. Ich informiere mich über verschiedene Themen im Internet. Online kann man schnell aktuelle Nachrichten lesen. "
                      "Das finde ich sehr praktisch und interessant.",
             min_words=40, max_words=200, time_limit=25),
        base(L, "sprechen", 1, "Sprechen: Meine Mediennutzung", page=102, topic="Meine Mediennutzung", prompt="Sprechen Sie über das Thema.",
             questions=["Welche Medien nutzen Sie am meisten?", "Wann und wie lange nutzen Sie Medien täglich?",
                        "Wofür nutzen Sie Medien? (Information, Unterhaltung, Lernen …)", "Welche sozialen Medien verwenden Sie und warum?",
                        "Was gefällt Ihnen besonders an Medien?", "Gibt es Nachteile von Medien? Welche?"],
             response_type="monolog", min_duration=60, max_duration=180,
             speech_goal="Über die eigene Mediennutzung sprechen und den Zweck nennen (um … zu / damit).",
             keywords=["Medien", "um … zu", "damit", "Nachrichten", "soziale Medien"]),
        base(L, "wortschatz", 1, "Wortschatz: Wichtige Wörter — Medien", page=98, words=WORDS, auto_practice=False,
             metadata={"note": "Kitobda faqat nemischa izoh berilgan, o'zbekcha tarjima yo'q — izoh ma'no sifatida ko'rsatiladi."}),
        base(L, "uebungen", 1, "Übungen: A2 9. Unterricht", source="vizu", exercises=[
            exercise("damit oder um … zu?", [
                mc("Ich spare Geld, ___ ein Fahrrad zu kaufen.", ["um", "damit", "weil"], "A", "1 Person + zu: um … zu."),
                mc("Ich arbeite hart, ___ meine Kinder ein besseres Leben haben.", ["damit", "um", "dass"], "A", "2 Personen: damit."),
                mc("Paul nimmt einen Regenschirm, um nicht nass ___.", ["zu werden", "wird", "werden"], "A"),
                mc("Tom steht früh auf, damit er den Bus nicht ___.", ["verpasst", "zu verpassen", "verpassen"], "A", "damit: Verb am Ende."),
                mc("Wann benutzt man „um … zu“?", ["Wenn das Subjekt gleich ist", "Wenn es zwei Personen gibt", "Nur mit Modalverben"], "A"),
            ], "Finalsätze (kitob, 96-bet).", source="vizu")]),
        base(L, "yakuniy", 1, "Abschlusstest: A2 9. Unterricht", source="vizu",
             instruction="Finalsätze va media so'zlari bo'yicha yakuniy test (dars materiali asosida).",
             questions=[
                 mc("Sie lernt Deutsch, ___ in Deutschland zu studieren.", ["um", "damit", "dass"], "A"),
                 mc("Er übt jeden Tag, damit er besser ___.", ["wird", "werden", "zu werden"], "A"),
                 mc("Ich lese viel, um mehr ___.", ["zu wissen", "weiß", "wissen"], "A"),
                 mc("Wie viele Menschen lesen Nachrichten online?", ["über 70 %", "etwa 30 %", "etwa 50 %"], "A", "Lesen."),
                 tf("Fast 30 % der Nachrichten im Internet sind nicht komplett oder nicht korrekt.", True, "Lesen."),
                 mc("„die Quellen“ bedeutet …", ["Orte, wo man Informationen findet", "das, was man denkt", "etwas Schlechtes"], "A"),
                 mc("„der Nachteil“ bedeutet …", ["etwas Schlechtes, ein negativer Aspekt", "etwas Gutes", "aktuelle Ereignisse"], "A"),
                 mc("„die Meinung“ bedeutet …", ["das, was man denkt", "eine Zeitung", "ein Radio"], "A"),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: A2 9. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
