"""B1 8. Unterricht — Gesundheit und Fitness — Grammatik: Konditionale Sätze
(wenn / falls) (book pp. 129-142).

Book: title p.129, Frage des Themas (Was tun Sie für Ihre Gesundheit und
Körper?) p.130, Konditionalsätze wenn und falls p.131, Aufgabe 1 (wenn) +
Aufgabe 2 (falls) — open completions p.132, Lesen Teil 1 (Führungskräfte und
ihre Gesundheit, richtig / falsch) p.133, Lesen Teil 2 (Der menschliche Körper,
Quiz) p.134, Lesen Teil 3 (Organe / Körperteile zuordnen) p.135, Hören Teil 1
(Florian macht Sport, richtig / falsch) p.136, Hören Teil 2 (Anika, Eva,
Christian, Lucie — ergänzen) p.137, Schreiben Teil 1 (Ihre Meinung bitte!
Mittagsschlaf) p.138, Schreiben Teil 2 (Bürokrankheiten — 6 Dialoge) p.139,
Sprechen Teil 1 (Interview: Mittagsruhe) p.140, Sprechen Teil 2 (Wie sieht ein
gesunder Tagesablauf aus?) p.141, Wortschatz Gesundheit und Fitness p.142.

Book notes: Lesen Teil 2 says "kreuze die 2 richtige Antworten" but only
question 1 has two answers -> question 1 is asked per option (richtig /
falsch), the others are single choice; the quiz is general knowledge, no key in
the book -> VIZU key, held. Lesen Teil 3 has one book example (Sonnenbrand -> die
Haut); the other associations have more than one sensible answer -> dropdown,
VIZU key, held. Schreiben Teil 2 says "Nutzen Sie verschiedene Strukturen aus
Aufgabe 8" — the Konjunktiv-II structures are printed on the page.
Sprechen Teil 2 title is printed "Wie sieht eine gesunde Tagesablauf?"."""

from . import (
    base, completion, example_gap, exercise, gap, intro_html, key_meta, match, mc, summary_html, tf,
)

L = 8
LESSON_TITLE = "Gesundheit und Fitness"
LESSON_DESCRIPTION = "Thema: Gesundheit und Fitness · Grammatik: Konditionale Sätze (wenn / falls)"
AUDIO = {"vizu-b1-l08-hoeren-01": "8.Unterricht Aufgabe 1.mp3", "vizu-b1-l08-hoeren-02": "8.Unterricht Aufgabe 2.mp3"}

EINFUEHRUNG_HTML = intro_html(
    8, "Gesundheit und Fitness", "Konditionale Sätze (wenn / falls)",
    ["shart ergash gaplari: wenn (ehtimolliroq) va falls (rasmiyroq) — Nebensatz + Hauptsatz;",
     "sog'liq, sport va tana a'zolari haqida so'zlar;",
     "maslahat berish: Du solltest …, Es wäre gut, wenn …"],
    ["sog'lig'ingiz uchun nima qilishingiz haqida gapirasiz;",
     "rahbarlarning sog'lig'i haqidagi so'rovnoma va inson tanasi haqidagi testni tushunasiz;",
     "sport va sog'lom turmush haqidagi matnni tinglaysiz;",
     "tushlikdagi uyqu haqida fikr yozasiz va ofis kasalliklari bo'yicha maslahat dialoglarini yozasiz;",
     "sog'lom kun tartibi haqida gapirasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(8, [
    "Konditionalsätze drücken eine Bedingung oder Voraussetzung aus: <strong>wenn</strong> (wahrscheinlicher), <strong>falls</strong> (formeller).",
    "Struktur: Wenn / Falls + Nebensatz (Bedingung), Hauptsatz (Ergebnis) — Wenn es regnet, bleibe ich zu Hause.",
    "Der Nebensatz mit wenn oder falls steht an erster Stelle, der Hauptsatz an zweiter Stelle (Verb zuerst: …, nehme ich den Regenschirm).",
    "Ratschläge: Du solltest … · Du müsstest … · Es wäre gut, wenn … · Ich würde …",
    "<strong>Gesundheit und Fitness:</strong> Sport treiben, sich gesund ernähren, Stress abbauen, sich dehnen, auf seine Gesundheit achten.",
])

GRAMMAR_HTML = (
    "<h3>Konditionalsätze: wenn und falls</h3>"
    "<h4>Regel</h4><p>Konditionalsätze drücken eine <strong>Bedingung</strong> oder <strong>Voraussetzung</strong> aus. Es gibt zwei mögliche "
    "Einleiter:</p><ul><li><strong>wenn</strong> (wahrscheinlicher)</li><li><strong>falls</strong> (formeller)</li></ul>"
    "<h4>Struktur</h4><p><strong>Wenn</strong> + Nebensatz (Bedingung), Hauptsatz (Ergebnis) — z. B. Wenn es regnet, bleibe ich zu Hause.</p>"
    "<p><strong>Falls</strong> + Nebensatz (Bedingung), Hauptsatz (Ergebnis) — z. B. Falls du Zeit hast, ruf mich bitte an.</p>"
    "<h4>Beispiele</h4><ul><li><strong>Wenn</strong> es regnet, nehme ich den Regenschirm.</li><li><strong>Wenn</strong> du früh aufstehst, hast du "
    "mehr Zeit.</li><li><strong>Falls</strong> du kommst, bringe ich dir ein Geschenk mit.</li><li><strong>Falls</strong> ich viel lerne, bestehe ich "
    "die Prüfung.</li></ul>"
    "<p><strong>Wichtig!</strong> Der Nebensatz mit wenn oder falls steht immer an erster Stelle, der Hauptsatz an zweiter Stelle.</p>"
)

WENN = ["Wenn ich Zeit habe,", "Wenn es morgen sonnig ist,", "Wenn ich müde bin,", "Wenn du Hilfe brauchst,", "Wenn wir früh aufstehen,",
        "Wenn das Wetter schlecht ist,", "Wenn ich viel lerne,", "Wenn du krank bist,", "Wenn ich reich wäre,", "Wenn wir Urlaub haben,",
        "Wenn du mich anrufst,", "Wenn ich Hunger habe,", "Wenn mein Bus zu spät kommt,", "Wenn ich Deutsch spreche,", "Wenn du fleißig bist,"]
FALLS = ["Falls es regnet,", "Falls du Fragen hast,", "Falls ich gewinne,", "Falls du keine Zeit hast,", "Falls wir zu spät kommen,", "Falls du Lust hast,",
         "Falls er krank ist,", "Falls ich Geld habe,", "Falls die Prüfung schwer ist,", "Falls du nach Hause kommst,", "Falls sie mich besucht,",
         "Falls ich früh fertig bin,", "Falls du mich brauchst,", "Falls das Restaurant voll ist,", "Falls ich einen Fehler mache,"]

# ---------- Lesen ----------
FUEHRUNG = (
    "Eine aktuelle Umfrage zeigt, wie wichtig Führungskräfte ihre Gesundheit einschätzen und welche Maßnahmen sie dafür ergreifen. 90 % der Befragten "
    "rauchen nicht. Das ist ein sehr hoher Wert und zeigt ein starkes Bewusstsein für die eigene Gesundheit. 65 % essen weniger Fleisch, um sich "
    "ausgewogen zu ernähren und etwas für die Umwelt zu tun. 64 % treiben regelmäßig Sport, zum Beispiel durch Laufen oder Radfahren. Das hilft, fit und "
    "leistungsfähig zu bleiben. 31 % machen ab und zu ein Mittagsschläfchen. Kurze Pausen können die Konzentration und das Wohlbefinden verbessern. "
    "27 % nehmen Nahrungsergänzungsmittel wie Vitaminpillen. Ebenfalls 27 % wenden Entspannungstechniken an, zum Beispiel Meditation. Das hilft, Stress "
    "abzubauen und ruhiger zu werden. 11 % besuchen regelmäßig die Sauna, um sich zu entspannen und das Immunsystem zu stärken. Nur 8 % leben "
    "vegetarisch. Das ist der niedrigste Wert in der Umfrage. Insgesamt zeigen die Ergebnisse, dass viele Führungskräfte auf ihre Gesundheit achten und "
    "verschiedene Wege nutzen, um gesund zu bleiben.\n\n"
    "Diagramm „Das tun Führungskräfte für ihre Gesundheit“ (Wirtschaftswoche, 2017): rauchen nicht 90 % · essen weniger Fleisch 65 % · treiben "
    "regelmäßig Sport (z. B. Laufen, Radfahren) 64 % · machen ab und zu ein Mittagsschläfchen 31 % · nehmen Nahrungsergänzungsmittel (z. B. "
    "Vitaminpillen) 27 % · wenden Entspannungstechniken (z. B. Meditation) an 27 % · besuchen regelmäßig die Sauna 11 % · leben vegetarisch 8 %")
LESEN_1 = [
    tf("90 % der Führungskräfte rauchen.", False, "„90 % der Befragten rauchen nicht.“"),
    tf("65 % der Befragten essen mehr Fleisch.", False, "„65 % essen weniger Fleisch …“"),
    tf("64 % treiben regelmäßig Sport.", True, "„64 % treiben regelmäßig Sport …“"),
    tf("31 % machen jeden Tag ein Mittagsschläfchen.", False, "„31 % machen ab und zu ein Mittagsschläfchen.“"),
    tf("27 % nehmen Vitaminpillen.", True, "„27 % nehmen Nahrungsergänzungsmittel wie Vitaminpillen.“"),
    tf("Nur 8 % leben vegetarisch.", True, "„Nur 8 % leben vegetarisch.“"),
]
LESEN_2 = [
    tf("1a) Die Nase wächst ein Leben lang.", True, "Nase und Ohren (Knorpel) wachsen ein Leben lang (Allgemeinwissen)."),
    tf("1b) Die Hände wachsen ein Leben lang.", False, "Die Hände wachsen nach der Pubertät nicht mehr."),
    tf("1c) Die Ohren wachsen ein Leben lang.", True, "Nase und Ohren (Knorpel) wachsen ein Leben lang."),
    mc("2. Was gehört nicht zu den Sinnesorganen?", ["die Augen", "die Haare", "die Haut"], "B", "Augen und Haut sind Sinnesorgane, Haare nicht."),
    mc("3. Welches Organ verarbeitet Informationen?", ["das Gehirn", "der Magen", "die Lunge"], "A"),
    mc("4. Wie viele Knochen hat ein erwachsener Mensch?", ["52 bis 56", "206 bis 212", "900 bis 1 000"], "B"),
    mc("5. Was ist am härtesten?", ["ein Knochen", "ein Zahn", "ein Fingernagel"], "B", "Der Zahnschmelz ist die härteste Substanz im Körper."),
    mc("6. Wo befindet sich der größte Knochen?", ["im Rücken", "im Oberarm", "im Oberschenkel"], "C", "Der Oberschenkelknochen ist der größte Knochen."),
    mc("7. Was ist das größte Organ des Körpers?", ["das Herz", "die Haut", "der Darm"], "B"),
]
ORGANE = ["die Lunge", "das Gehirn", "die Knochen", "die Haut", "die Hand", "der Magen", "das Herz", "die Augen", "die Nase", "das Ohr"]
SITUATIONEN = [
    ("Ich habe eine Prüfung und muss viel lernen.", ["das Gehirn"]), ("Ich leide unter Übelkeit.", ["der Magen"]), ("Ich bin total verliebt.", ["das Herz"]),
    ("Ich gehe ins Konzert.", ["das Ohr"]), ("Ich suche ein neues Parfüm.", ["die Nase"]), ("Ich spiele Fußball und werde gefoult.", ["die Knochen"]),
    ("Ich lese ein Buch.", ["die Augen"]), ("Ich besuche Wien und schreibe viele Postkarten an Freunde und Verwandte.", ["die Hand"]),
]
LESEN_3 = [match("Welches Organ / welche Körperteile assoziieren Sie mit der folgenden Situation? Ordnen Sie zu (Situationen 2–9).",
                 [f"{n}. {s}" for n, (s, _) in enumerate(SITUATIONEN, start=2)], ORGANE,
                 {str(i): "ABCDEFGHIJ"[ORGANE.index(acc[0])] for i, (_, acc) in enumerate(SITUATIONEN, start=1)}, points=len(SITUATIONEN),
                 explanation="Lösung (VIZU): " + " · ".join(f"{n} {acc[0]}" for n, (_, acc) in enumerate(SITUATIONEN, start=2)))]

# ---------- Hören ----------
HOEREN_1 = [tf(s, None) for s in [
    "Florian hat schon immer viel Sport gemacht.", "Florian hatte in letzter Zeit Gesundheitsprobleme.", "Florian geht nicht jeden Tag ins Fitnessstudio.",
    "Florian trainiert in der Regel mit einem persönlichen Trainer.", "Florians Freundin will den Halbmarathon laufen.",
    "Laura möchte auch am Halbmarathon teilnehmen."]]
PERSONEN = [
    ("Anika", "a) ist Studentin (Beispiel). b) macht für ihre Gesundheit [[1]]. c) [[2]] freitags und samstags [[3]]."),
    ("Eva", "a) arbeitet als Assistentin und fühlt sich manchmal [[1]]. b) macht Yoga. Das hilft ihr, sich zu [[2]]. Es tut ihr [[3]]. "
            "c) ernährt sich [[4]]."),
    ("Christian", "a) macht gerade [[1]] beim Fernsehen. b) benutzt eine [[2]], die ihm genau sagt, wie viel er sich [[3]] hat. c) kauft sich oft "
                  "[[4]] zum Aufwärmen in der Mikrowelle."),
    ("Lucie", "a) [[1]] viel am Computer oder in Meetings. b) achtet sehr auf [[2]]. c) geht samstags eine Stunde [[3]]."),
]
HOEREN_2 = [gap(f"{name}: Hören Sie den Text noch einmal und ergänzen Sie die Informationen.", text,
                {str(i): [] for i in range(1, text.count("[[") + 1)}, points=text.count("[[")) for name, text in PERSONEN]

BUERO = [
    ("Schmerzen im Schulterbereich", ["langes Sitzen vermeiden", "öfter eine Pause machen"]),
    ("Schmerzen in den Armen, Händen oder Fingern", ["mit einer ergonomischen Maus und Tastatur arbeiten", "die Hände regelmäßig bewegen",
                                                     "die Maus mit beiden Händen bedienen"]),
    ("Probleme mit den Augen", ["nicht immer auf den Bildschirm sehen", "manchmal Augenübungen machen"]),
    ("Kopfschmerzen und Konzentrationsprobleme", ["für gute Beleuchtung am Arbeitsplatz sorgen", "regelmäßig das Fenster öffnen",
                                                  "einfache und effektive Entspannungsübungen machen", "ein kurzes Mittagsschläfchen machen"]),
    ("Sie sind nervös und fühlen sich gestresst.", ["sich ein gutes Hobby suchen", "regelmäßig Sport treiben", "lernen, Nein zu sagen"]),
    ("Probleme mit Herz und Kreislauf", ["sich viel bewegen", "auf eine gesunde Ernährung achten"]),
]
INTERVIEW = ["Wann beginnt in Ihrem Heimatland ein normaler Büro-Arbeitstag und wann endet er? Wann sind die Hauptverkehrszeiten?",
             "Zu welcher Tageszeit fühlen Sie sich müde oder unkonzentriert?", "Machen Sie mittags ein Schläfchen oder eine Ruhepause? Wenn ja, wie lange?",
             "Gibt es in Ihrem Heimatland traditionell eine Mittagsruhe?"]
TAGESABLAUF = [
    ("Regelmäßig aufstehen und früh beginnen", ["Früh aufzustehen gibt mehr Energie für den Tag.", "Ein fester Rhythmus stabilisiert den Körper.",
                                                "Der Morgen ist ideal für wichtige Aufgaben."]),
    ("Gesundes Frühstück und ausgewogene Ernährung", ["Frühstück liefert Energie und verbessert die Konzentration.",
                                                       "Mehr Obst, Gemüse und Vollkornprodukte essen.", "Weniger Zucker, Fett und Fast Food."]),
    ("Regelmäßige Bewegung und Aktivität", ["Sport stärkt Herz, Muskeln und Immunsystem.", "Bewegung reduziert Stress und macht glücklich.",
                                            "30 Minuten am Tag reichen schon aus."]),
    ("Effektiv arbeiten und Pausen machen", ["Planung hilft, produktiv zu bleiben.", "Kurze Pausen steigern die Leistung und Kreativität.",
                                             "Die Pomodoro-Methode ist sehr effektiv."]),
    ("Ausreichend Schlaf und Erholung", ["7–8 Stunden Schlaf sind ideal für Erwachsene.", "Guter Schlaf verbessert Gedächtnis und Stimmung.",
                                         "Vor dem Schlafen: kein Handy, entspannen."]),
    ("Positive Gedanken und soziale Kontakte", ["Positive Einstellung reduziert Stress.", "Zeit mit Familie und Freunden macht glücklich.",
                                                "Dankbarkeit und Optimismus verbessern die Lebensqualität."]),
]
FITNESS = [
    ("Schlaf bekommen", "Ich muss heute früh Schlaf bekommen."), ("Wasser trinken", "Es ist wichtig, genug Wasser zu trinken."),
    ("Sport treiben", "Ich treibe dreimal pro Woche Sport."), ("sich gesund ernähren", "Ich achte darauf, mich gesund zu ernähren."),
    ("Gewicht verlieren", "Ich möchte ein paar Kilo Gewicht verlieren."), ("sich dehnen", "Vor dem Training dehne ich mich immer."),
    ("zum Arzt gehen", "Ich gehe heute zum Arzt, um mich durchchecken zu lassen."), ("Vitamine nehmen", "Ich nehme jeden Morgen Vitamine."),
    ("Stress abbauen", "Yoga hilft mir, Stress abzubauen."), ("Fahrrad fahren", "Am Wochenende fahre ich oft Fahrrad."),
    ("tief durchatmen", "Bei Anspannung atme ich tief durch."), ("Muskeln aufbauen", "Krafttraining hilft, Muskeln aufzubauen."),
    ("mit dem Rauchen aufhören", "Ich möchte mit dem Rauchen aufhören."), ("einen Trainingsplan erstellen", "Ich habe mir einen neuen Trainingsplan erstellt."),
    ("auf seine Gesundheit achten", "Wir sollten jeden Tag auf unsere Gesundheit achten."),
]
# the book has no meaning column: the example sentence of the book is the "meaning" shown in the practice
WORDS = [{"word": w, "translation": ex, "example": ex, "group": "Gesundheit und Fitness"} for w, ex in FITNESS]


def _fitness_gap(expr: str, sentence: str, options: list[str]) -> dict:
    words_ = [w for w in expr.replace("sich ", "").split() if w[0].isupper()]
    noun = words_[0] if words_ else None
    if noun and noun in sentence:
        return example_gap(sentence.replace(noun, "___", 1), noun, options, f"Redewendung: {expr}")
    return None


UEBUNGEN = [
    exercise("wenn oder falls? — Satzbau (Beispiele aus dem Buch)", [
        example_gap("Wenn es regnet, ___ ich den Regenschirm.", "nehme", ["nehme", "ich nehme", "nehmen"], "Hauptsatz an zweiter Stelle: Verb zuerst."),
        example_gap("Wenn du früh aufstehst, ___ du mehr Zeit.", "hast", ["hast", "du hast", "haben"]),
        example_gap("Falls du ___, bringe ich dir ein Geschenk mit.", "kommst", ["kommst", "kommen", "du kommst"], "Im Nebensatz steht das Verb am Ende."),
        example_gap("Falls ich viel lerne, ___ ich die Prüfung.", "bestehe", ["bestehe", "ich bestehe", "bestehen"]),
        example_gap("___ du Zeit hast, ruf mich bitte an.", "Falls", ["Falls", "Dass", "Ob"], "Bedingung: falls / wenn."),
        example_gap("Wenn es regnet, ___ ich zu Hause.", "bleibe", ["bleibe", "ich bleibe", "bleiben"]),
    ], "Wählen Sie die richtige Form (Buch S. 131).", source="vizu"),
    exercise("Gesundheit und Fitness — Redewendungen", [q for q in [
        example_gap("Ich treibe dreimal pro Woche ___.", "Sport", ["Sport", "Stress", "Gewicht"], "Sport treiben."),
        example_gap("Yoga hilft mir, ___ abzubauen.", "Stress", ["Stress", "Muskeln", "Schlaf"], "Stress abbauen."),
        example_gap("Krafttraining hilft, ___ aufzubauen.", "Muskeln", ["Muskeln", "Vitamine", "Wasser"], "Muskeln aufbauen."),
        example_gap("Ich möchte ein paar Kilo ___ verlieren.", "Gewicht", ["Gewicht", "Sport", "Stress"], "Gewicht verlieren."),
        example_gap("Bei Anspannung atme ich tief ___.", "durch", ["durch", "auf", "ab"], "tief durchatmen."),
        example_gap("Ich möchte mit dem Rauchen ___.", "aufhören", ["aufhören", "abbauen", "erstellen"], "mit dem Rauchen aufhören."),
        example_gap("Vor dem Training ___ ich mich immer.", "dehne", ["dehne", "ernähre", "achte"], "sich dehnen."),
        example_gap("Wir sollten jeden Tag ___ unsere Gesundheit achten.", "auf", ["auf", "an", "für"], "auf seine Gesundheit achten."),
    ] if q], "Wählen Sie das passende Wort (Wortschatz S. 142).", source="vizu"),
]
ABSCHLUSSTEST = [
    mc("Was drücken Konditionalsätze aus?", ["Eine Bedingung oder Voraussetzung", "Einen Grund", "Ein Ziel"], "A", "Buch S. 131."),
    mc("Welcher Einleiter ist formeller?", ["falls", "wenn", "weil"], "A", "Buch S. 131: wenn (wahrscheinlicher), falls (formeller)."),
    mc("Wo steht der Nebensatz mit wenn / falls laut Buch?", ["An erster Stelle", "An zweiter Stelle", "In der Mitte"], "A", "Buch S. 131: „Wichtig!“"),
    example_gap("Wenn du früh aufstehst, hast du mehr ___.", "Zeit", ["Zeit", "Geld", "Hunger"]),
    mc("Wie viel Prozent der Führungskräfte treiben regelmäßig Sport?", ["64 %", "90 %", "8 %"], "A", "Lesen Teil 1."),
    mc("Was ist das größte Organ des Körpers?", ["die Haut", "das Herz", "der Darm"], "A", "Lesen Teil 2."),
    mc("Wie viele Stunden Schlaf sind laut Buch ideal für Erwachsene?", ["7–8 Stunden", "4–5 Stunden", "10–12 Stunden"], "A", "Sprechen Teil 2."),
    example_gap("Es ist wichtig, genug ___ zu trinken.", "Wasser", ["Wasser", "Kaffee", "Vitamine"], "Wasser trinken."),
    example_gap("Du ___ dir einen ergonomischen Bürostuhl kaufen.", "solltest", ["solltest", "sollst", "sollte"], "Ratschlag (Schreiben Teil 2)."),
    example_gap("Es wäre gut, wenn du öfter aufstehen ___.", "würdest", ["würdest", "wirst", "würde"], "Schreiben Teil 2, Beispiel."),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: B1 8. Unterricht", source="vizu", page=129, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Was tun Sie für Ihre Gesundheit und Körper?", page=130,
             prompt="Was tun Sie für Ihre Gesundheit und Körper?",
             questions=["Ich treibe regelmäßig Sport.", "Ich esse gesund.", "Ich schlafe genug.", "Ich entspanne mich."], min_duration=30, max_duration=150,
             metadata={"book_samples": ["Ich treibe regelmäßig Sport. Ich jogge, gehe ins Fitnessstudio oder mache Yoga.",
                                        "Ich esse gesund. Ich achte auf eine ausgewogene Ernährung und esse viel Obst und Gemüse.",
                                        "Ich schlafe genug. Ich gehe früh ins Bett und schlafe 7-8 Stunden pro Nacht.",
                                        "Ich entspanne mich. Ich nehme mir Zeit für mich, meditiere oder lese ein gutes Buch."]}),
        base(L, "grammatik", 1, "Grammatik: Konditionalsätze — wenn und falls", page=131,
             rules=[{"title": "Konditionalsätze: wenn und falls", "html": GRAMMAR_HTML}]),
        completion(L, 3, "Grammatik Aufgabe 1: Sätze mit „wenn“", 132, "Ergänze die Sätze mit einem passenden Hauptsatz. Beginne mit „wenn“.", WENN),
        completion(L, 4, "Grammatik Aufgabe 2: Sätze mit „falls“", 132, "Ergänze die Sätze mit einem passenden Hauptsatz. Beginne mit „falls“.", FALLS),
        base(L, "lesen", 1, "Lesen Teil 1: Führungskräfte und ihre Gesundheit", page=133, instruction="Lesen Sie den Text. Richtig oder Falsch?",
             passages=[{"title": "Führungskräfte und ihre Gesundheit", "text": FUEHRUNG}], questions=LESEN_1, max_score=len(LESEN_1), metadata=key_meta("vizu")),
        base(L, "lesen", 2, "Lesen Teil 2: Der menschliche Körper", page=134,
             instruction="Lies die Fragen und kreuze die richtige Antwort (a, b oder c) an! Frage 1 hat 2 richtige Antworten — sie wird hier für jede "
                         "Antwort einzeln gefragt (richtig / falsch).",
             passages=[{"title": "Der menschliche Körper — Quiz",
                        "text": "1 Welche Körperteile / Sinnesorgane wachsen ein Leben lang? (2 richtige Antworten) a) die Nase b) die Hände c) die Ohren\n"
                                "2 Was gehört nicht zu den Sinnesorganen? a) die Augen b) die Haare c) die Haut\n3 Welches Organ verarbeitet "
                                "Informationen? a) das Gehirn b) der Magen c) die Lunge\n4 Wie viele Knochen hat ein erwachsener Mensch? a) 52 bis 56 "
                                "b) 206 bis 212 c) 900 bis 1 000\n5 Was ist am härtesten? a) ein Knochen b) ein Zahn c) ein Fingernagel\n6 Wo befindet "
                                "sich der größte Knochen? a) im Rücken b) im Oberarm c) im Oberschenkel\n7 Was ist das größte Organ des Körpers? a) das "
                                "Herz b) die Haut c) der Darm"}],
             questions=LESEN_2, max_score=len(LESEN_2),
             metadata=key_meta("vizu", "Wissensquiz ohne Text und ohne Lösung im Buch — Lösung von VIZU (Allgemeinwissen), bitte prüfen.")),
        base(L, "lesen", 3, "Lesen Teil 3: Der menschliche Körper — Organe zuordnen", page=135,
             instruction="b) Welches Organ / welche Körperteile assoziieren Sie mit der folgenden Situation? (Beispiel: 1 Ich habe zu lange in der Sonne "
                         "gelegen und einen Sonnenbrand bekommen. → die Haut)",
             passages=[{"title": "Organe / Körperteile", "text": " • ".join(ORGANE)}], questions=LESEN_3, max_score=len(SITUATIONEN),
             metadata=key_meta("vizu", "Nur das Beispiel steht im Buch; die übrigen Zuordnungen sind Assoziationen (z. T. mehrere sinnvoll) — "
                                       "Lösung von VIZU, bitte prüfen.")),
        base(L, "hoeren", 1, "Hören Teil 1: Florian macht Sport", page=136, audio_file=AUDIO["vizu-b1-l08-hoeren-01"], key_pending=True,
             instruction="a) Hören Sie den Text. Sind die Aussagen richtig oder falsch? Kreuzen Sie an.", questions=HOEREN_1, max_score=6,
             metadata=key_meta("pending", "Keine Lösung im Buch — nach dem Anhören in Lösung festlegen.")),
        base(L, "hoeren", 2, "Hören Teil 2: Hören und ergänzen — Anika, Eva, Christian, Lucie", page=137, audio_file=AUDIO["vizu-b1-l08-hoeren-02"],
             key_pending=True, instruction="b) Hören Sie den Text noch einmal und ergänzen Sie die Informationen. (Beispiel: Anika a) ist Studentin.)",
             questions=HOEREN_2, max_score=14, metadata=key_meta("pending", "Keine Lösung im Buch — nach dem Anhören in Lösung festlegen.")),
        base(L, "schreiben", 1, "Schreiben Teil 1: Ihre Meinung bitte! — Mittagsschlaf im Büro", page=138, task_type="opinion",
             prompt="Lesen Sie den Text und antworten Sie. Schreiben Sie etwa 80 Wörter.\n\nSie haben im Fernsehen eine Talkshow zum Thema Mittagsschlaf "
                    "gesehen. Im Online-Gästebuch der Sendung lesen Sie die folgende Meldung:\n\nDaniela aus Köln schrieb am 8.8. um 11:30 Uhr: Meiner "
                    "Meinung nach sollte man den Mittagsschlaf im Büro fördern. Der Mittagsschlaf ist gesünder als die vielen Tassen Kaffee, die "
                    "Mitarbeiter normalerweise trinken, um wach zu bleiben. Nach einem Power-Nap kann man sich z. B. viel besser konzentrieren.\n\n"
                    "Schreiben Sie Ihre Meinung:\n• Was halten Sie von Danielas Meinung?\n• Finden Sie den Mittagsschlaf im Büro eine gute Idee?\n"
                    "• Welche Vorteile oder Nachteile hat er Ihrer Meinung nach?\n• Wie oft machen Sie selbst Mittagsschlaf?\n• Was machen Sie "
                    "stattdessen, wenn Sie müde sind?\n\nTipp: Geben Sie Beispiele und erklären Sie Ihre Meinung.",
             audience="Online-Gästebuch einer Fernsehsendung", min_words=70, max_words=120, time_limit=25),
        base(L, "schreiben", 2, "Schreiben Teil 2: Bürokrankheiten und was Sie dagegen tun können — 6 Dialoge", page=139, task_type="other",
             prompt="Formulieren Sie Ratschläge und spielen Sie einen Dialog. Nutzen Sie verschiedene Strukturen: Du solltest … · Du müsstest … · Es "
                    "wäre gut, wenn … · Ich würde …\n\nBeispiel — A: Rückenschmerzen. Ich habe oft Rückenschmerzen. B: Tipps: sich einen ergonomischen "
                    "Bürostuhl kaufen, öfter aufstehen. → 1. B: Du solltest dir einen ergonomischen Bürostuhl kaufen. 2. B: Und es wäre gut, wenn du "
                    "öfter aufstehen würdest.\n\n" + "\n".join(f"{i}. {p} — Tipps: {', '.join(t)}" for i, (p, t) in enumerate(BUERO, start=1))
                    + "\n\nSchreiben Sie 6 Dialoge (ca. 80–100 Wörter). Verwenden Sie verschiedene Strukturen und geben Sie konkrete Tipps. Tipp: Höflich "
                      "bleiben, begründen, konkrete Tipps geben, verschiedene Strukturen verwenden.",
             min_words=80, max_words=200, time_limit=25,
             metadata={"note": "Im Buch steht „Strukturen aus Aufgabe 8“ — gemeint sind die auf der Seite gedruckten Strukturen."}),
        base(L, "sprechen", 1, "Sprechen Teil 1: Interview — Mittagsruhe", page=140, topic="Mittagsruhe",
             prompt="Einige Führungskräfte gaben in der Umfrage an, dass sie ein kurzes Mittagsschläfchen machen. Führen Sie ein Interview mit zwei "
                    "Kursteilnehmern. Geben Sie danach die interessantesten Informationen wieder.\nTipps für das Interview: Stellen Sie alle Fragen. "
                    "Hören Sie aufmerksam zu. Stellen Sie Nachfragen. Notieren Sie wichtige Informationen.",
             questions=INTERVIEW, response_type="dialog", min_duration=60, max_duration=240,
             speech_goal="Interview führen, nachfragen und die interessantesten Informationen wiedergeben.",
             keywords=["Wann beginnt …?", "Zu welcher Tageszeit …?", "Er / Sie hat gesagt, dass …", "Interessant fand ich …"]),
        base(L, "sprechen", 2, "Sprechen Teil 2: Wie sieht ein gesunder Tagesablauf aus?", page=141, topic="Ein gesunder Tagesablauf",
             prompt="Sprechen Sie über einen gesunden Tagesablauf. Gehen Sie auf die sechs Punkte ein und geben Sie eigene Beispiele.\n\n"
                    + "\n".join(f"{i}. {t}: " + " ".join(p) for i, (t, p) in enumerate(TAGESABLAUF, start=1))
                    + "\n\nMerke dir! Ein gesunder Tagesablauf bringt mehr Energie, bessere Leistung und ein glücklicheres Leben!",
             questions=[t for t, _ in TAGESABLAUF], response_type="monolog", preparation_time=180, min_duration=90, max_duration=180,
             speech_goal="Einen gesunden Tagesablauf in sechs Punkten beschreiben und mit eigenen Beispielen begründen.",
             keywords=["Zuerst", "Außerdem", "Wenn man …, …", "Es ist wichtig, …", "Meiner Meinung nach"],
             metadata={"note": "Titel im Buch: „Wie sieht eine gesunde Tagesablauf?“ (Druckfehler)."}),
        base(L, "wortschatz", 1, "Wortschatz: Gesundheit und Fitness — 15 Redewendungen (Nomen + Verb)", page=142, words=WORDS, auto_practice=False,
             metadata={"note": "Das Buch gibt zu jeder Redewendung einen Beispielsatz (keine Erklärung, keine Übersetzung)."}),
        base(L, "uebungen", 1, "Übungen: B1 8. Unterricht", source="vizu", exercises=UEBUNGEN),
        base(L, "yakuniy", 1, "Abschlusstest: B1 8. Unterricht", source="vizu",
             instruction="Abschlusstest zu Konditionalsätzen, Lesen, Sprechen und Wortschatz (alle Sätze aus dem Buch).", questions=ABSCHLUSSTEST),
        base(L, "kompetenz", 2, "Zusammenfassung: B1 8. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
