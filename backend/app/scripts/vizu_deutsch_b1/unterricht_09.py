"""B1 9. Unterricht — Wohnen und Architektur — Grammatik: Präpositionen mit
Genitiv (book pp. 143-159).

Book: title p.143, Frage des Themas (Wie würden Sie Ihr Zimmer ausrüsten?)
p.144, Präpositionen mit Genitiv (wegen, trotz, während, statt / anstatt,
außerhalb, innerhalb, aufgrund) p.145, Aufgaben: während / wegen p.146, trotz /
statt p.147, außerhalb / innerhalb p.148, alle sieben Präpositionen p.149, Lesen
Teil 1 (Heimat + Wohnen, richtig / falsch) p.150, Lesen Teil 2
(Grundausstattung Schlaf- und Wohnzimmer) p.151, Lesen Teil 3
(Grundausstattung der Küche) p.152, Hören Teil 1 (Sabine und Jana,
Infinitivkonstruktionen) p.153, Hören Teil 2 (Telefongespräch 3, ergänzen)
p.154, Schreiben Teil 1 (E-Mail: neues Haus, Einladung) p.155, Schreiben Teil 2
(Diskussionsbeitrag Alte oder moderne Architektur) p.156, Sprechen Aufgabe 1
(Präsentation Wohnen und Architektur) p.157, Sprechen Aufgabe 2 (gemeinsam
planen: neue Wohnung) p.158, Wortschatz Wohnen und Architektur (15
Redewendungen + Aufgabe) p.159.

Book defects (explained in the tasks): in the während / wegen and trotz / statt
pages several sentences are clauses ("…, wir krank waren", "…, er krank war")
that need weil / obwohl — the book wants the meaning (Zeit / Grund, Gegensatz /
Ersatz), so the meaning decides the key; außerhalb / innerhalb are used as
adverbs before "im Garten", "im Restaurant" … — key by meaning (draußen /
drinnen). Lesen Teil 2 / 3 say "15 Wörter, 5 brauchst du nicht, kreuze 10 an",
but Teil 2 lists 20 words (14 in the text) and Teil 3 lists 15 (13 in the
text) -> asked per word: steht im Text / brauchst du? (richtig / falsch).
Hören Teil 1 says "Ergänzen Sie … und hören Sie dann zur Kontrolle" — the key
follows the grammar, the audio confirms it."""

from . import (
    base, example_gap, exercise, gap, intro_html, key_meta, mc, meaning_sets, summary_html, tf,
)

L = 9
LESSON_TITLE = "Wohnen und Architektur"
LESSON_DESCRIPTION = "Thema: Wohnen und Architektur · Grammatik: Präpositionen mit Genitiv"
AUDIO = {"vizu-b1-l09-hoeren-01": "9.Unterricht Aufgabe 1.mp3", "vizu-b1-l09-hoeren-02": "9.Unterricht Aufgabe 2.mp3"}

EINFUEHRUNG_HTML = intro_html(
    9, "Wohnen und Architektur", "Präpositionen mit Genitiv",
    ["Genitiv talab qiladigan predloglar: wegen, trotz, während, statt / anstatt, außerhalb, innerhalb, aufgrund;",
     "ular sabab, qarama-qarshilik, vaqt, almashtirish yoki joyni bildiradi;",
     "uy-joy, jihozlar va arxitektura haqida so'zlar."],
    ["xonangizni qanday jihozlashingiz haqida gapirasiz;",
     "„Vatan“ va „Uy-joy“ haqidagi matnlarni va uy jihozlari ro'yxatini tushunasiz;",
     "infinitiv konstruksiyali dialog va telefon suhbatini tinglaysiz;",
     "yangi uyingizga do'stingizni taklif qilasiz va arxitektura haqida munozara matni yozasiz;",
     "„Uy-joy va arxitektura“ mavzusida taqdimot qilasiz va yangi kvartirani birga rejalashtirasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(9, [
    "Präpositionen mit Genitiv: Präp. + des / der / dieses + Nomen — alle verlangen den Genitiv (2. Fall)!",
    "<strong>wegen / aufgrund</strong> = Ursache, Grund · <strong>trotz</strong> = Gegensatz (obwohl) · <strong>während</strong> = Zeit · "
    "<strong>statt / anstatt</strong> = Ersatz · <strong>außerhalb</strong> = draußen · <strong>innerhalb</strong> = drinnen, in einem Zeitraum.",
    "Wegen des Streiks fällt der Zug aus. · Trotz des Regens gehen wir spazieren. · Innerhalb einer Woche war alles erledigt.",
    "<strong>Wohnen und Architektur:</strong> eine Wohnung mieten, einrichten, renovieren, Energie sparen, eine Baugenehmigung bekommen.",
])

GRAMMAR_HTML = (
    "<h3>Präpositionen mit Genitiv</h3>"
    "<table><thead><tr><th>Präposition</th><th>Struktur</th><th>Bedeutung</th><th>Beispielsatz</th></tr></thead><tbody>"
    "<tr><td>wegen</td><td>Präp. + des/der/dieses + Nomen</td><td>Ursache, Grund</td><td>Wegen des schlechten Wetters bleiben wir zu Hause.</td></tr>"
    "<tr><td>trotz</td><td>Präp. + des/der/dieses + Nomen</td><td>Gegensatz, obwohl</td><td>Trotz des Regens gehen wir spazieren.</td></tr>"
    "<tr><td>während</td><td>Präp. + des/der/dieses + Nomen</td><td>Zeitliche Begleitung</td><td>Während der Vorlesung darf man nicht telefonieren.</td></tr>"
    "<tr><td>statt / anstatt</td><td>Präp. + des/der/dieses + Nomen</td><td>Ersatz, etwas anderes</td><td>Statt eines Autos kaufte er ein Fahrrad.</td></tr>"
    "<tr><td>außerhalb</td><td>Präp. + des/der/dieses + Nomen</td><td>Nicht im Inneren, draußen</td><td>Das Café liegt außerhalb der Stadt.</td></tr>"
    "<tr><td>innerhalb</td><td>Präp. + des/der/dieses + Nomen</td><td>Im Inneren, in einem Zeitraum</td><td>Innerhalb einer Woche war alles erledigt.</td></tr>"
    "<tr><td>aufgrund</td><td>Präp. + des/dieses + Nomen</td><td>Grund, Ursache, auf Basis von etwas</td><td>Aufgrund eines Fehlers wurde der Flug abgesagt.</td></tr>"
    "</tbody></table><p><strong>Alle diese Präpositionen verlangen den Genitiv (2. Fall)!</strong> Sie zeigen Ursache, Gegensatz, Zeit, Ersatz oder "
    "Ort an. Beispiel: Wegen des Streiks fällt der Zug aus.</p><p>⚠ Achte auf die richtige Form des Genitivs!</p>"
)


def pick(n: int, sentence: str, accepted: list[str], options: list[str], note: str | None = None) -> dict:
    return gap(f"{n}. Setzen Sie das passende Wort ein.", sentence.replace("___", "[[1]]", 1),
               {"1": {"accepted": accepted, "options": options}}, explanation=note or accepted[0])


_WW = ["während", "wegen"]
_KLAUSEL = "Im Buch ein Nebensatz mit Verb am Ende — grammatisch richtig wäre „{}“; nach der Bedeutung ({}) passt „{}“."
WAEHREND_WEGEN = [
    ("___ des Unterrichts hörten wir aufmerksam zu.", "während"), ("Wir blieben zu Hause, ___ wir krank waren.", "wegen"),
    ("___ des Sommers arbeite ich in einem Café.", "während"), ("___ des Staus kamen wir zu spät an.", "wegen"),
    ("Er konnte nicht spielen, ___ des Regens.", "wegen"), ("___ der Ferien reiste ich nach Spanien.", "während"),
    ("Wir machten eine Pause, ___ es sehr heiß war.", "wegen"), ("Sie verpasste den Bus, ___ sie verschlafen hat.", "wegen"),
    ("___ der Musik vergaß ich die Zeit.", "wegen"), ("Wir blieben im Hotel, ___ des schlechten Wetters.", "wegen"),
    ("___ des Lärms konnte ich nicht schlafen.", "wegen"), ("Er nahm den Tag frei, ___ eines wichtigen Arzttermins.", "wegen"),
]
_WW_NOTE = {2: _KLAUSEL.format("weil", "Grund", "wegen"), 7: _KLAUSEL.format("weil", "Grund", "wegen"), 8: _KLAUSEL.format("weil", "Grund", "wegen"),
            9: "„Wegen der Musik“ (Grund); auch „Während der Musik“ (Zeit) ist sinnvoll — beide zählen."}
_TS = ["trotz", "statt"]
TROTZ_STATT = [
    ("___ des Regens gingen wir spazieren.", "trotz"), ("___ ins Kino zu gehen, blieben wir zu Hause.", "statt"),
    ("Er trainierte hart, ___ er krank war.", "trotz"), ("___ Geld zu sparen, kaufte er ein Fahrrad.", "statt"),
    ("Wir fuhren in den Urlaub, ___ teuer war.", "trotz"), ("___ eines Autos nahm er den Bus.", "statt"),
    ("___ der Müdigkeit machte sie weiter.", "trotz"), ("Er lernte viel, ___ er wenig Zeit hatte.", "trotz"),
    ("___ Kaffee trank er lieber Tee.", "statt"), ("___ nach Hause zu fahren, blieb er bei seinen Freunden.", "statt"),
    ("Wir gingen wandern, ___ müde zu sein.", "trotz"), ("___ Fleisch zu essen, wählte er Gemüse.", "statt"),
]
_TS_NOTE = {3: _KLAUSEL.format("obwohl", "Gegensatz", "trotz"), 5: "Im Buch unvollständig („…, ___ teuer war.“) — gemeint: obwohl es teuer war → trotz.",
            8: _KLAUSEL.format("obwohl", "Gegensatz", "trotz"),
            11: "Im Buch „…, ___ müde zu sein.“ — gemeint: obwohl wir müde waren (trotz der Müdigkeit); „statt“ zählt auch (= anstatt müde zu sein)."}
_AI = ["außerhalb", "innerhalb"]
AUSSER_INNER = [
    ("Die Kinder spielen ___ im Garten.", "außerhalb"), ("Stell das Fahrrad bitte ___ des Hauses ab.", "außerhalb"),
    ("Wir bleiben heute ___ und schauen einen Film.", "innerhalb"), ("___ der Stadt gibt es viele schöne Dörfer.", "außerhalb"),
    ("Er wartet ___ vor der Schule auf seinen Freund.", "außerhalb"), ("Die Katze schläft ___ auf dem Sofa.", "innerhalb"),
    ("Wir essen ___ im Restaurant.", "innerhalb"), ("Das Auto steht ___ in der Garage.", "innerhalb"),
    ("___ des Zimmers ist es warm und gemütlich.", "innerhalb"), ("Das Konzert findet ___ der Halle statt.", "innerhalb"),
    ("Bitte bleib ___ der gelben Linie.", "innerhalb"), ("Die Bücher liegen ___ im Regal.", "innerhalb"),
]
_AI_NOTE = "Im Buch ohne Genitiv (adverbial, wie draußen / drinnen) — die Bedeutung entscheidet."
_ALLE = ["während", "trotz", "statt", "wegen", "aufgrund", "außerhalb", "innerhalb"]
ALLE = [
    ("___ des schlechten Wetters blieb er zu Hause.", ["wegen", "aufgrund"]), ("Sie ging spazieren, ___ des Regens.", ["trotz"]),
    ("___ der Vorlesung darf man nicht telefonieren.", ["während"]), ("___ eines Autos kaufte er ein Fahrrad.", ["statt"]),
    ("___ eines Fehlers wurde das Projekt verschoben.", ["aufgrund", "wegen"]), ("Das Café liegt ___ der Stadt.", ["außerhalb", "innerhalb"]),
    ("Die Arbeiten wurden ___ einer Woche abgeschlossen.", ["innerhalb"]), ("Er blieb ruhig, ___ des Stresses.", ["trotz"]),
    ("___ der hohen Preise kaufen viele Menschen weniger.", ["wegen", "aufgrund"]), ("Wir fuhren wandern, ___ der Müdigkeit.", ["trotz"]),
    ("___ des Sturms fiel der Strom aus.", ["wegen", "aufgrund"]), ("Die Kinder spielten ___ des Hauses im Garten.", ["außerhalb"]),
]
_ALLE_NOTE = {1: "wegen / aufgrund = Grund (beide richtig).", 5: "aufgrund / wegen (beide richtig).",
              6: "Buch S. 145: „Das Cafe liegt außerhalb der Stadt.“ — „innerhalb“ ist grammatisch auch möglich.",
              9: "wegen / aufgrund (beide richtig).", 11: "wegen / aufgrund (beide richtig)."}


def _ac(word: str, sentence: str) -> list[str]:
    """capitalised at the start of the sentence."""
    return [word.capitalize()] if sentence.startswith("___") else [word]


GRAMMATIK_SETS = [
    exercise("Aufgabe: während oder wegen", [
        pick(n, s, _ac(a, s) + (["Während"] if n == 9 else []), [w.capitalize() if s.startswith("___") else w for w in _WW], _WW_NOTE.get(n))
        for n, (s, a) in enumerate(WAEHREND_WEGEN, start=1)],
        "Setzen Sie in die Lücken das passende Wort: während oder wegen. während → in einer bestimmten Zeit (gleichzeitig), z. B. während des "
        "Urlaubs · wegen → aufgrund von (Ursache / Grund), z. B. wegen des Regens (Buch S. 146)."),
    exercise("Aufgabe: trotz oder statt", [
        pick(n, s, _ac(a, s) + (["statt"] if n == 11 else []), [w.capitalize() if s.startswith("___") else w for w in _TS], _TS_NOTE.get(n))
        for n, (s, a) in enumerate(TROTZ_STATT, start=1)],
        "Setzen Sie in die Lücken das passende Wort: trotz oder statt. trotz → obwohl, ungeachtet von etwas · statt → anstelle von etwas "
        "(Buch S. 147)."),
    exercise("Aufgabe: außerhalb oder innerhalb", [
        pick(n, s, _ac(a, s), [w.capitalize() if s.startswith("___") else w for w in _AI], None if " des " in s or " der " in s else _AI_NOTE)
        for n, (s, a) in enumerate(AUSSER_INNER, start=1)],
        "Setzen Sie in die Lücken das passende Wort: außerhalb oder innerhalb. außerhalb → draußen, nicht in einem Raum oder Gebäude · "
        "innerhalb → drinnen, in einem Raum oder Gebäude (Buch S. 148)."),
    exercise("Aufgabe: Präpositionen mit Genitiv (alle)", [
        pick(n, s, [a.capitalize() if s.startswith("___") else a for a in acc], [w.capitalize() if s.startswith("___") else w for w in _ALLE],
             _ALLE_NOTE.get(n))
        for n, (s, acc) in enumerate(ALLE, start=1)],
        "Setzen Sie die passende Präposition im Genitiv in die Lücken ein: während • trotz • statt • wegen • aufgrund • außerhalb • innerhalb. "
        "Tipp: Achte auf die Bedeutung! Frage dich: Wessen? Warum? Wann? Wo? (Buch S. 149)"),
]

# ---------- Lesen ----------
HEIMAT = (
    "Das Zentrum im Leben von Thomas ist sein Zuhause. Er lebt noch immer in der gleichen Region, in der er aufgewachsen ist. Hier tankt er Ruhe und "
    "Kraft. In seinem Leben wird er nur viermal seine Adresse ändern, im europäischen Vergleich ist das wenig. Historiker sehen die Bedeutung der Heimat "
    "unter anderem in geschichtlichen Ereignissen begründet. Durch verschiedene Kriege ist die Heimat im Bewusstsein der Deutschen zu einem bedrohten "
    "Gut geworden.")
WOHNEN = (
    "Thomas wohnt in einer 90 Quadratmeter großen Mietwohnung. Sein Lieblingszimmer, das Wohnzimmer, ist ausgestattet mit einer Couch, einem Tisch, "
    "einem Fernseher, einer Schrankwand, Stehlampen und Pflanzen. Seine Schränke sind voll, denn Thomas sammelt gern und kann nichts wegwerfen. Auch "
    "von seinen drei alten Mobiltelefonen, die nicht mehr funktionieren, kann er sich nicht trennen.\n"
    "Ganz oben auf seiner Wunschliste steht das Eigenheim. Davon träumt er so lange, bis er irgendwann einen Kredit aufnimmt und für sich, seine Kinder "
    "und seine Enkel ein Haus baut.\n"
    "Am Ende seines Lebens wird Thomas ein Vermögen im Wert von 195 000 Euro vererben. Damit liegt er im europäischen Vergleich nicht auf den vordersten "
    "Plätzen.")
LESEN_1 = [
    tf("Thomas lebt nicht mehr in der Region, in der er aufgewachsen ist.", False, "„Er lebt noch immer in der gleichen Region, in der er aufgewachsen ist.“"),
    tf("Er ändert seine Adresse nur viermal im Leben.", True, "„In seinem Leben wird er nur viermal seine Adresse ändern …“"),
    tf("Im europäischen Vergleich zieht Thomas oft um.", False, "„… im europäischen Vergleich ist das wenig.“"),
    tf("Die Heimat hat für die Deutschen eine wichtige Bedeutung.", True,
       "„Durch verschiedene Kriege ist die Heimat im Bewusstsein der Deutschen zu einem bedrohten Gut geworden.“"),
    tf("Thomas wohnt in einer kleinen Wohnung.", False, "„… in einer 90 Quadratmeter großen Mietwohnung.“", passage=2),
    tf("Sein Wohnzimmer hat viele Möbel und Pflanzen.", True, "„… mit einer Couch, einem Tisch, einem Fernseher, einer Schrankwand, Stehlampen und Pflanzen.“",
       passage=2),
    tf("Er wirft gerne alte Dinge weg.", False, "„… Thomas sammelt gern und kann nichts wegwerfen.“", passage=2),
    tf("Er möchte in Zukunft ein eigenes Haus bauen.", True, "„Ganz oben auf seiner Wunschliste steht das Eigenheim … ein Haus baut.“", passage=2),
]
SCHLAF = (
    "Hier haben Lattenrost und Matratze oberste Priorität auf der Einkaufsliste, sofern diese nicht schon vorhanden sind und mitgenommen werden können. "
    "Für dein Bett benötigst du eine Bettdecke und ein Kopfkissen, zwei Bettlaken/Spannbettücher und zwei Bettwäschegarnituren. So kannst du dein Bett "
    "immer direkt neu beziehen, während die alten Laken in der Wäsche sind.\n"
    "Wichtig ist natürlich auch ein Kleiderschrank oder eine Kommode mit ausreichend Stauraum für deine Kleidung. Oft lässt sich zu zweit relativ leicht "
    "selbst ein großer Schrank aufbauen.\n"
    "Eine günstige Alternative zum Kleiderschrank ist eine Kleiderstange. Diese sind derzeit sehr beliebt und auch für einen schmalen Geldbeutel "
    "bezahlbar. Ein Beistelltisch oder auch Nachttisch und eine kleine Tisch- oder Wandleuchte runden den Schlafbereich ab.\n"
    "Wenn ausreichend Platz und Geld da ist, gehört ein Sofa im Wohnbereich zur Grundausstattung einer jeden Wohnung. Ein TV-Lowboard bietet sich "
    "platzsparend an, um nicht nur den Fernseher darauf abstellen zu können, sondern auch um wichtige Unterlagen oder Bücher zu verstauen. Alternativ "
    "reicht natürlich auch ein Bücherregal aus. Auch praktisch sind Wandregale, die du ebenfalls selbst anbringen kannst. Die meisten TV-Geräte lassen "
    "sich auch an der Wand befestigen.")
SCHLAF_WOERTER = [("Lattenrost", True), ("Matratze", True), ("Bettdecke", True), ("Kopfkissen", True), ("Bettlaken", True), ("Bettwäschegarnitur", True),
                  ("Kleiderschrank", True), ("Kommode", True), ("Kleiderstange", True), ("Nachttisch", True), ("Tischlampe", True), ("Sofa", True),
                  ("TV-Lowboard", True), ("Bücherregal", True), ("Esstisch", False), ("Stuhl", False), ("Teppich", False), ("Garderobe", False),
                  ("Waschmaschine", False), ("Kühlschrank", False)]
KUECHE = (
    "Zur Grundausstattung der Küche, die in vielen Wohnungen bereits vorhanden ist, gehören der Herd mit Backofen, ein Kühlschrank mit Tiefkühlfach, ein "
    "Spülbecken mit dazugehörigem Unterschrank sowie ein weiterer Unterschrank als Stauraum für Küchenartikel und ein bis zwei Hängeschränke für "
    "Geschirr und Lebensmittel. Die Neuanschaffung einer Küche ist oft sehr teuer, da alleine die Elektrogeräte mehrere 100 € oder gar bis zu 1.000 € "
    "kosten können.\n"
    "Hast du nicht das Glück, dass die Wohnung bereits mit einer möblierten Küche ausgestattet ist oder du die des Vormieters übernehmen kannst, kannst "
    "du viel Geld sparen, indem du dir eine gebrauchte Küche anschaffst. Sozialkaufhäuser oder Onlineplattformen bieten eine Fülle an "
    "unterschiedlichsten Modellen ab 100 € inklusive Elektrogeräte. Ein deutschlandweites Verzeichnis aller Sozialkaufhäuser oder Spendenabgaben "
    "findest du bei HelpTo. Noch mehr Geld sparen Umziehende, die die Elektrogeräte selbst anschließen.\n"
    "Außer den Küchenmöbeln benötigst du noch Besteck, Geschirr, Gläser und Tassen für mindestens sechs Personen, sodass du nicht improvisieren musst, "
    "wenn sich mal Besuch ankündigt. Mindestens zwei Kochtöpfe – ein großer und ein kleiner –, eine Pfanne und ein Sieb sowie eine Salatschüssel, eine "
    "Müslischale und ein Schneidebrett gehören ebenso zur Ausstattung der Küche wie Pfannenwender, Suppenkelle, Kochlöffel, Schneebesen und "
    "Schneidemesser.\n"
    "Für den Abwasch benötigst du außerdem Geschirrtücher sowie eine Spülbürste. Ein Küchentisch und mindestens zwei Stühle vervollständigen die Küche. "
    "Für deine Küchenabfälle sind außerdem ein bzw. mehrere Mülleimer wichtig.\n"
    "Elektrogeräte wie Kaffeemaschine, Mikrowelle, Toaster oder Wasserkocher gehören nicht zwingend zur Grundausstattung in jede erste Wohnung. Wenn dir "
    "diese Geräte jedoch besonders wichtig sind, solltest du diese auch in deine Ausgaben mit einkalkulieren.")
KUECHE_WOERTER = [("Herd mit Backofen", True), ("Kühlschrank mit Tiefkühlfach", True), ("Spülbecken mit Unterschrank", True), ("Hängeschränke", True),
                  ("Mikrowelle", False), ("Besteck, Geschirr, Gläser, Tassen", True), ("Kochtöpfe (2 Stück)", True), ("Pfanne", True), ("Sieb", True),
                  ("Salatschüssel", True), ("Pfannenwender", True), ("Geschirrtücher", True), ("Küchentisch", True), ("Sofa", False), ("Mülleimer", True)]


def _needs(words_: list[tuple[str, bool]], room: str, why_no: dict) -> list[dict]:
    return [tf(f"{n}. {w} — brauchst du laut Text für {room}?", ok,
               "Steht im Text als Grundausstattung." if ok else why_no.get(w, "Steht nicht im Text."))
            for n, (w, ok) in enumerate(words_, start=1)]


LESEN_2 = _needs(SCHLAF_WOERTER, "das Schlaf- und Wohnzimmer", {})
LESEN_3 = _needs(KUECHE_WOERTER, "die Küche", {"Mikrowelle": "„… Mikrowelle … gehören nicht zwingend zur Grundausstattung …“",
                                               "Sofa": "Ein Sofa gehört zum Wohnbereich, nicht zur Küche."})

# ---------- Hören ----------
DIALOG = (
    "Sabine: Jana, stell dir mal vor: Ich habe mich zu einem Kochkurs angemeldet.\n"
    "Jana: Du? Du machst einen Kurs, [[1]] (kochen lernen)? Ich dachte, du kochst nicht so gern.\n"
    "Sabine: Na ja, Kochen macht mir ehrlich gesagt keinen großen Spaß, aber [[2]] (immer Fertiggerichte kaufen) kann ich doch ab und zu selbst etwas "
    "kochen.\n"
    "Jana: Gute Idee! Kann ich dann mal bei dir vorbeikommen, [[3]] (deine Kochkünste bewundern)?\n"
    "Sabine: Natürlich, ich koche uns dann ein ganzes Menü!\n"
    "Jana: Das klingt gut. Ich freue mich schon darauf.\n"
    "Sabine: Wenn du willst, kann ich uns auch heute Abend schon etwas kochen, zum Beispiel Nudeln in Olivenöl. Das schaffe ich auch, [[4]] (vorher einen "
    "Kurs besuchen).\n"
    "Jana: Gerne. Und ich bringe die Nachspeise mit: selbst gemachten Apfelstrudel.\n"
    "Sabine: Ich habe gehofft, dass du das sagst. Deine Nachspeisen sind immer so lecker.")
DIALOG_KEY = {"1": ["um kochen zu lernen"], "2": ["statt immer Fertiggerichte zu kaufen", "anstatt immer Fertiggerichte zu kaufen"],
              "3": ["um deine Kochkünste zu bewundern"], "4": ["ohne vorher einen Kurs zu besuchen", "ohne vorher einen Kurs zu besuchen,"]}
TELEFON = (
    "Frau Klein: Martina Klein, Rechtsabteilung.\nHerr Wendisch: Guten Morgen, Frau Klein. Hier ist Albert Wendisch.\n"
    "Frau Klein: Guten Morgen, Herr Wendisch. Was kann ich für Sie [[1]]?\nHerr Wendisch: Ich würde gern Frau Schulze [[2]].\n"
    "Frau Klein: Das tut mir leid, Frau Schulze ist nicht im Hause. Kann ich ihr etwas [[3]]?\n"
    "Herr Wendisch: Ja, das wäre nett. Könnten Sie bitte Frau Schulze sagen, dass wir nächste Woche die neuen [[4]] brauchen?\n"
    "Frau Klein: Ja, natürlich. Ich richte es ihr aus.\n"
    "Herr Wendisch: Ach, noch etwas. Könnten Sie Frau Schulze bitten, dass sie mich heute oder morgen [[5]]? Ich habe noch eine wichtige Ergänzung zu den "
    "[[6]].\nFrau Klein: Ich gebe Frau Schulze sofort [[7]], wenn sie wieder im Hause ist.\nHerr Wendisch: Herzlichen Dank.")
HOEREN_1 = [gap("a) Ergänzen Sie die Infinitivkonstruktionen und hören Sie dann zur Kontrolle den Dialog.", DIALOG, DIALOG_KEY, points=4,
                explanation="1 um kochen zu lernen · 2 statt immer Fertiggerichte zu kaufen · 3 um deine Kochkünste zu bewundern · "
                            "4 ohne vorher einen Kurs zu besuchen")]
HOEREN_2 = [gap("c) Hören Sie Telefongespräch 3 und ergänzen Sie beim Hören die Nomen oder Verben.", TELEFON, {str(i): [] for i in range(1, 8)}, points=7)]

REDEWENDUNGEN = [
    ("ein Haus bauen", "ein neues Haus errichten"), ("eine Wohnung mieten", "für eine bestimmte Zeit eine Wohnung nehmen"),
    ("die Wohnung renovieren", "eine Wohnung modernisieren"), ("die Wohnung einrichten", "Möbel kaufen und die Wohnung gestalten"),
    ("eine Wohnung kaufen", "eine Wohnung erwerben"), ("Energie sparen", "weniger Energie verbrauchen"), ("einen Balkon haben", "einen Balkon besitzen"),
    ("in der Stadt leben", "in einer Stadt wohnen"), ("aufs Land ziehen", "an einen ländlichen Ort ziehen"),
    ("etwas reparieren", "etwas kaputtes wieder in Ordnung bringen"), ("eine Mauer bauen", "eine Mauer errichten"),
    ("ein Fenster einbauen", "ein Fenster in eine Wand setzen"), ("das Haus isolieren", "das Haus gegen Kälte oder Wärme schützen"),
    ("einen Garten anlegen", "einen Garten gestalten"), ("eine Baugenehmigung bekommen", "von der Behörde die Erlaubnis zum Bauen erhalten"),
]
WORDS = [{"word": w, "translation": m, "group": "Wohnen und Architektur"} for w, m in REDEWENDUNGEN]

UEBUNGEN = [
    exercise("Präpositionen mit Genitiv — Beispiele aus dem Buch", [
        example_gap("___ des schlechten Wetters bleiben wir zu Hause.", "Wegen", ["Wegen", "Trotz", "Statt"], "Grund → wegen."),
        example_gap("___ des Regens gehen wir spazieren.", "Trotz", ["Trotz", "Wegen", "Während"], "Gegensatz → trotz."),
        example_gap("___ der Vorlesung darf man nicht telefonieren.", "Während", ["Während", "Statt", "Trotz"], "Zeit → während."),
        example_gap("Statt ___ Autos kaufte er ein Fahrrad.", "eines", ["eines", "ein", "einem"], "Genitiv: eines Autos."),
        example_gap("Das Café liegt außerhalb ___ Stadt.", "der", ["der", "die", "den"], "Genitiv feminin: der Stadt."),
        example_gap("Innerhalb ___ Woche war alles erledigt.", "einer", ["einer", "eine", "einem"], "Genitiv: einer Woche."),
        example_gap("Aufgrund ___ Fehlers wurde der Flug abgesagt.", "eines", ["eines", "ein", "einen"]),
        example_gap("Wegen ___ Streiks fällt der Zug aus.", "des", ["des", "dem", "den"]),
    ], "Wählen Sie die richtige Form (Buch S. 145).", source="vizu"),
]
ABSCHLUSSTEST = [
    mc("Welchen Kasus verlangen wegen, trotz, während, statt, außerhalb, innerhalb, aufgrund?", ["Genitiv", "Dativ", "Akkusativ"], "A", "Buch S. 145."),
    mc("„trotz“ bedeutet …", ["Gegensatz, obwohl", "Ursache, Grund", "Ersatz"], "A"),
    mc("„statt / anstatt“ bedeutet …", ["Ersatz, etwas anderes", "Zeitliche Begleitung", "Grund"], "A"),
    example_gap("___ des Sturms fiel der Strom aus.", "Wegen", ["Wegen", "Trotz", "Statt"], "Grund."),
    example_gap("Er blieb ruhig, trotz ___ Stresses.", "des", ["des", "dem", "der"]),
    mc("Wie oft ändert Thomas laut Text seine Adresse?", ["nur viermal im Leben", "jedes Jahr", "nie"], "A", "Lesen Teil 1."),
    mc("Was gehört laut Text nicht zwingend zur Grundausstattung der Küche?", ["die Mikrowelle", "der Herd mit Backofen", "die Pfanne"], "A", "Lesen Teil 3."),
    mc("„eine Baugenehmigung bekommen“ bedeutet …", ["von der Behörde die Erlaubnis zum Bauen erhalten", "einen Garten gestalten",
                                                       "eine Wohnung modernisieren"], "A", "Wortschatz S. 159."),
    mc("„das Haus isolieren“ bedeutet …", ["das Haus gegen Kälte oder Wärme schützen", "ein Haus errichten", "etwas reparieren"], "A"),
    example_gap("Sie ging spazieren, ___ des Regens.", "trotz", ["trotz", "wegen", "während"]),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: B1 9. Unterricht", source="vizu", page=143, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Wie würden Sie Ihr Zimmer ausrüsten?", page=144, prompt="Wie würden Sie Ihr Zimmer ausrüsten?",
             questions=["Einfach", "Normal", "Luxuriös"], min_duration=30, max_duration=150,
             metadata={"book_samples": {
                 "Einfach": "Ich richte mein Zimmer einfach und praktisch ein. Ich habe nur das Nötigste: ein Bett, einen Tisch, einen Schrank und ein Regal. "
                            "Wichtig ist für mich Ordnung und Sauberkeit.",
                 "Normal": "Ich richte mein Zimmer modern und gemütlich ein. Ich habe ein bequemes Bett, einen Schreibtisch, Regale und schöne Dekoration. "
                           "Mir ist wichtig, dass ich mich wohlfühle und gut lernen kann.",
                 "Luxuriös": "Ich richte mein Zimmer luxuriös und stilvoll ein. Ich habe ein großes Bett, einen bequemen Sessel, hochwertige Möbel und "
                             "moderne Technik. Design und Komfort sind mir sehr wichtig."}}),
        base(L, "grammatik", 1, "Grammatik: Präpositionen mit Genitiv", page="145-149",
             rules=[{"title": "Präpositionen mit Genitiv", "html": GRAMMAR_HTML}], exercises=GRAMMATIK_SETS,
             metadata={"note": "Lösungen von VIZU nach der Bedeutung; Buchfehler (Nebensätze statt Nomen, adverbiales außerhalb / innerhalb) im Hinweis."}),
        base(L, "lesen", 1, "Lesen Teil 1: Heimat und Wohnen", page=150, instruction="Lesen Sie die Texte und entscheiden Sie: Richtig oder Falsch?",
             passages=[{"title": "1 Heimat", "text": HEIMAT}, {"title": "2 Wohnen", "text": WOHNEN}], questions=LESEN_1, max_score=len(LESEN_1),
             metadata=key_meta("vizu")),
        base(L, "lesen", 2, "Lesen Teil 2: Grundausstattung des Schlaf- und Wohnzimmers", page=151,
             instruction="Lies den Text und markiere die Möbel und Dinge, die du für das Schlaf- und Wohnzimmer brauchst. (Im Buch: „Es gibt 15 Wörter, "
                         "5 davon brauchst du nicht, kreuze die richtigen 10 an“ — die Liste hat aber 20 Wörter, 14 davon stehen im Text. Deshalb wird "
                         "jedes Wort einzeln gefragt: richtig = du brauchst es laut Text.)",
             passages=[{"title": "Grundausstattung des Schlaf- und Wohnzimmers", "text": SCHLAF}], questions=LESEN_2, max_score=len(LESEN_2),
             metadata=key_meta("vizu", "Buch: 20 Wörter statt 15, 14 im Text — pro Wort gefragt; „Tischlampe“ = „Tisch- oder Wandleuchte“. Bitte prüfen.")),
        base(L, "lesen", 3, "Lesen Teil 3: Grundausstattung der Küche", page=152,
             instruction="Lies den Text und markiere die Möbel und Dinge, die du für die Küche brauchst. (Im Buch: „5 davon brauchst du nicht“ — laut Text "
                         "gehören 13 der 15 Wörter zur Grundausstattung. Jedes Wort wird einzeln gefragt.)",
             passages=[{"title": "Grundausstattung der Küche", "text": KUECHE}], questions=LESEN_3, max_score=len(LESEN_3),
             metadata=key_meta("vizu", "Buch: 13 von 15 Wörtern stehen im Text (nicht: Mikrowelle, Sofa) — pro Wort gefragt. Bitte prüfen.")),
        base(L, "hoeren", 1, "Hören Teil 1: Sabine und Jana — Infinitivkonstruktionen", page=153, audio_file=AUDIO["vizu-b1-l09-hoeren-01"],
             instruction="a) Ergänzen Sie die Infinitivkonstruktionen und hören Sie dann zur Kontrolle den Dialog. Lesen Sie das Gespräch danach laut. "
                         "Tipp: Infinitivkonstruktionen mit „zu“ drücken den Zweck oder die Absicht aus (Ich gehe ins Kino, um einen Film zu sehen.).",
             questions=HOEREN_1, max_score=4,
             metadata=key_meta("vizu", "Lösung nach der Grammatik (um … zu / statt … zu / ohne … zu) — nach dem Anhören in Lösung bestätigen.")),
        base(L, "hoeren", 2, "Hören Teil 2: Telefongespräch 3 — Frau Klein und Herr Wendisch", page=154, audio_file=AUDIO["vizu-b1-l09-hoeren-02"],
             key_pending=True,
             instruction="c) Hören Sie Telefongespräch 3 und ergänzen Sie beim Hören die Nomen oder Verben. Lesen Sie den Dialog danach laut. "
                         "Tipp: Achten Sie beim Hören auf die Satzstruktur und den Sinn des Gesprächs.",
             questions=HOEREN_2, max_score=7, metadata=key_meta("pending", "Keine Lösung im Buch — nach dem Anhören in Lösung festlegen.")),
        base(L, "schreiben", 1, "Schreiben Teil 1: E-Mail — Einladung in mein neues Zuhause", page=155, task_type="email",
             prompt="Sie haben ein neues Haus gekauft. Schreiben Sie eine E-Mail an Ihren Freund / Ihre Freundin und laden Sie ihn / sie ein.\n\n"
                    "Schreiben Sie über diese Punkte:\n1. Erzählen Sie, dass Sie ein neues Haus gekauft haben.\n2. Schlagen Sie einen Termin vor, an dem "
                    "er / sie Sie besuchen kann.\n3. Beschreiben Sie kurz Ihr neues Haus (Zimmer, Garten usw.).\n4. Machen Sie einen Vorschlag für etwas, "
                    "das Sie zusammen machen können.\n\nMuster (Buch): Betreff: Einladung in mein neues Zuhause — Hallo lieber Freund / liebe Freundin, "
                    "ich habe eine tolle Nachricht: Ich habe ein neues Haus gekauft! Ich bin sehr glücklich und möchte dich gerne einladen. Kommst du mich "
                    "besuchen? Ich schlage vor, dass du am … (Datum) gegen … (Uhrzeit) kommst. Mein neues Haus ist … (z. B. groß, modern, ruhig). Es hat "
                    "… (z. B. einen großen Garten, viele Zimmer, eine schöne Terrasse). Wir können zusammen … (z. B. Kaffee trinken, grillen, den Garten "
                    "anschauen, Musik hören). Ich freue mich sehr auf deinen Besuch! Liebe Grüße …",
             audience="Ein Freund / eine Freundin (informell)", min_words=60, max_words=130, time_limit=20),
        base(L, "schreiben", 2, "Schreiben Teil 2: Diskussionsbeitrag — Alte oder moderne Architektur, was ist besser?", page=156, task_type="opinion",
             prompt="Schreiben Sie einen Diskussionsbeitrag (ca. 150 Wörter) zum Thema: „Alte oder moderne Architektur – was ist besser?“ Nehmen Sie im "
                    "Forum teil und schreiben Sie Ihre Meinung.\n\nBeachten Sie diese Punkte in Ihrem Beitrag:\n1. Ihre Meinung: Welche Architektur "
                    "gefällt Ihnen besser: alte oder moderne? Warum?\n2. Vorteile nennen: Nennen Sie Vorteile der alten Architektur und der modernen "
                    "Architektur.\n3. Beispiele geben: Geben Sie Beispiele für alte und moderne Gebäude, die Sie kennen.\n4. Schlussfolgerung: Welchen "
                    "Baustil bevorzugen Sie am Ende? Begründen Sie Ihre Wahl.\n\nTipp: Schreiben Sie mindestens 150 Wörter. Achten Sie auf einen klaren "
                    "Aufbau und eine gute Begründung.",
             audience="Internet-Forum", min_words=140, max_words=220, time_limit=35),
        base(L, "sprechen", 1, "Sprechen Aufgabe 1: Präsentation — Wohnen und Architektur", page=157, topic="Wohnen und Architektur",
             prompt="Sie halten eine kurze Präsentation zum Thema „Wohnen und Architektur“. Sprechen Sie über die folgenden Punkte.\n1. Ihre Erfahrung: "
                    "Wo wohnen Sie? Wie sieht Ihre Wohnung oder Ihr Haus aus? Welche Erfahrungen haben Sie mit verschiedenen Wohnformen?\n2. Vor- und "
                    "Nachteile: Welche Vorteile hat eine moderne Wohnung? Welche Nachteile gibt es? Was ist besser: eine Wohnung oder ein Haus?\n"
                    "3. Situation in Ihrem Heimatland: Wie wohnen die Menschen in Ihrem Heimatland? Gibt es viele moderne Gebäude? Sind traditionelle "
                    "Häuser noch beliebt?\n4. Eigene Meinung: Welche Architektur gefällt Ihnen besser: alt oder modern? Wie sollte ein ideales Zuhause "
                    "aussehen? Was ist für Sie beim Wohnen besonders wichtig?\n5. Schluss: „Zusammenfassend möchte ich sagen, dass …“ „Für mich "
                    "persönlich ist … besonders wichtig, weil …“\n\nSprechen Sie frei und verwenden Sie Beispiele aus Ihrem Leben!",
             questions=["Ihre Erfahrung", "Vor- und Nachteile", "Situation in Ihrem Heimatland", "Eigene Meinung", "Schluss"],
             response_type="monolog", preparation_time=300, min_duration=120, max_duration=180,
             speech_goal="Strukturierte Präsentation in 5 Punkten (Buch S. 157).",
             keywords=["Ich wohne in …", "Ein Vorteil ist …", "In meinem Heimatland …", "Zusammenfassend möchte ich sagen, dass …"]),
        base(L, "sprechen", 2, "Sprechen Aufgabe 2: Gemeinsam planen — eine neue Wohnung einrichten", page=158, topic="Eine neue Wohnung planen",
             prompt="Sie und Ihr Partner / Ihre Partnerin ziehen in eine neue Wohnung. Sie möchten die Wohnung gemeinsam planen und einrichten.\n"
                    "1. Welche Wohnung? Wohnung oder Haus? Wie viele Zimmer brauchen Sie? Welche Lage ist ideal?\n2. Wie einrichten? Welche Möbel "
                    "brauchen Sie? Modern oder klassisch? Welche Farben und welcher Stil?\n3. Wie viel Geld? Wie hoch ist Ihr Budget? Was kaufen Sie neu? "
                    "Was können Sie gebraucht kaufen?\n4. Was machen wir zuerst? Was müssen Sie zuerst kaufen? Wann gehen Sie einkaufen? Wer übernimmt "
                    "welche Aufgabe?\n\nNützliche Redemittel: Ich würde vorschlagen, dass … · Was hältst du davon, wenn …? · Ich bin dafür / Ich bin "
                    "dagegen, weil … · Das klingt gut. · Dann machen wir es so.",
             questions=["Welche Wohnung?", "Wie einrichten?", "Wie viel Geld?", "Was machen wir zuerst?"], response_type="dialog",
             min_duration=90, max_duration=240, speech_goal="Gemeinsam planen: Vorschläge machen, Meinung sagen, sich einigen.",
             keywords=["Ich würde vorschlagen, dass …", "Was hältst du davon, wenn …?", "Ich bin dafür / dagegen, weil …", "Dann machen wir es so."]),
        base(L, "wortschatz", 1, "Wortschatz: Wohnen und Architektur — 15 Redewendungen", page=159, words=WORDS, exercises=meaning_sets(WORDS),
             auto_practice=False, metadata={"note": "Das Buch erklärt die Redewendungen auf Deutsch („Bedeutung“)."}),
        base(L, "schreiben", 3, "Wortschatz-Aufgabe: 5 Redewendungen — eigene Sätze", page=159, task_type="other",
             prompt="Wählen Sie 5 Redewendungen aus der Liste. Schreiben Sie für jede Redewendung einen passenden Satz zum Thema „Wohnen und Architektur“. "
                    "Beispielstrukturen: Ich möchte … · Wir planen, … · Es ist wichtig, dass …\n\n"
                    + "\n".join(f"{i}. {w} — {m}" for i, (w, m) in enumerate(REDEWENDUNGEN, start=1)),
             min_words=30, max_words=200, time_limit=15, metadata={"note": "Ish varag'i — o'qituvchi tekshiradi."}),
        base(L, "uebungen", 1, "Übungen: B1 9. Unterricht", source="vizu", exercises=UEBUNGEN),
        base(L, "yakuniy", 1, "Abschlusstest: B1 9. Unterricht", source="vizu",
             instruction="Abschlusstest zu Präpositionen mit Genitiv, Lesen und Wortschatz (alle Sätze aus dem Buch).", questions=ABSCHLUSSTEST),
        base(L, "kompetenz", 2, "Zusammenfassung: B1 9. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
