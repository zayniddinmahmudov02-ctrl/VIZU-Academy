"""B1 7. Unterricht — Medien im Alltag — Grammatik: Relativsätze (book pp. 111-128).

Book: title p.111, Frage des Themas (Wie informieren Sie sich?) p.112,
Relativsätze Teil 1 (Nominativ) p.113, Teil 2 (andere Kasus + Präpositionen)
p.114, Teil 3 (Fragewörter als Relativpronomen) p.115, Aufgabe 1 (Nominativ,
20 Sätze) p.116, Aufgabe 2 (andere Kasus + Präpositionen, 20 Sätze) p.117,
Aufgabe 3 (Fragewörter, 20 Sätze) p.118, Lesen Aufgabe 1 (Leser und
Nichtleser, Wendungen zuordnen) p.119, Lesen Aufgabe 2 (Mediennutzung in
Deutschland, Verben) p.120, Lesen Aufgabe 3 (Diagramm Fernsehformate, richtig
/ falsch) p.121, Hören Aufgabe 1 (Wer bestimmt eigentlich das
Fernsehprogramm?, Lückentext mit Wörterliste) p.122, Hören Aufgabe 2 (Wer liest
denn heute noch Bücher?, wer sagt was) p.123, Schreiben Aufgabe 1 (E-Books und
E-Reader in Österreich, Verben) p.124, Schreiben Aufgabe 2 (E-Mail an einen
Freund) p.125, Sprechen Teil 1 (Sprechen Sie zum Thema) p.126, Sprechen Teil 2
(Präsentation: Soziale Netzwerke als Nachrichtenquelle) p.127, Wortschatz
Medien und Alltag p.128.

Book defects (kept as printed, explained in the task): Aufgabe 1 offers
der / die / das / die only, but sentences 15 and 19 need "den" (Akkusativ);
Aufgabe 3 offers wer / wen / wem / was, but 12 (der), 15 (warum), 17 (die) and
19 (an dem) need other words — free input, every correct form accepted;
Aufgabe 2 sentences 14, 16-18, 20 print no preposition although the verb needs
one — the usual prepositions are accepted. Schreiben Aufgabe 1 sentence 1 is
shortened in the book ("52 Prozent der Österreicher (1) eine repräsentative
Umfrage") — held for review. Hören Aufgabe 1 text has print errors
("Vorteil sind die Zeiten", "Hetue") — corrected only where the audio confirms."""

from . import (
    base, example_gap, exercise, gap, intro_html, key_meta, match, meaning_sets, mc, mc_pending, summary_html, tf,
)

L = 7
LESSON_TITLE = "Medien im Alltag"
LESSON_DESCRIPTION = "Thema: Medien im Alltag · Grammatik: Relativsätze"
AUDIO = {"vizu-b1-l07-hoeren-01": "7.Unterricht Aufgabe 1.mp3", "vizu-b1-l07-hoeren-02": "7.Unterricht Aufgabe 2.mp3"}

EINFUEHRUNG_HTML = intro_html(
    7, "Medien im Alltag", "Relativsätze",
    ["nisbiy ergash gaplar: Relativpronomen Nominativ, Akkusativ, Dativ va predlog bilan;",
     "so'roq so'zlari nisbiy olmosh sifatida: wer, wen, wem, was;",
     "ommaviy axborot vositalari va kundalik hayot haqida so'zlar."],
    ["qanday ma'lumot olishingiz haqida gapirasiz;",
     "kitobxonlar haqidagi matn, media statistikasi va diagrammani tushunasiz;",
     "televizion dastur va kitob o'qish haqidagi radio suhbatini tinglaysiz;",
     "do'stingizga Germaniyadagi media haqida xat yozasiz;",
     "„Ijtimoiy tarmoqlar — yangiliklar manbai“ mavzusida taqdimot qilasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(7, [
    "Ein Relativsatz gibt zusätzliche Informationen über eine Person oder eine Sache — Das ist der Mann, der hier arbeitet.",
    "Relativpronomen: Nominativ der/die/das/die · Akkusativ den/die/das/die · Dativ dem/der/dem/denen.",
    "Genus und Numerus nach dem Bezugswort, Kasus nach der Funktion im Relativsatz. Präposition + Relativpronomen: der Freund, auf den ich warte.",
    "wer / wen / wem für Personen, was für Sachen und ganze Aussagen; nach alles, etwas, nichts, das Beste → was.",
    "Das Verb steht am Ende des Relativsatzes.",
    "<strong>Medien und Alltag:</strong> das Smartphone, die Nachricht, die sozialen Medien, herunterladen, die Privatsphäre.",
])

GRAMMAR_HTML = (
    "<h3>Relativsätze</h3><p>Relativsätze geben uns mehr Informationen über Personen, Dinge oder Sachverhalte. Sie werden mit Relativpronomen "
    "eingeleitet: der, die, das, die, welcher, welche, welches, deren.</p>"
    "<h4>Teil 1: Relativpronomen im Nominativ</h4><p>Ein Relativsatz gibt <strong>zusätzliche Informationen</strong> über eine Person oder eine "
    "Sache. Er beginnt meistens mit einem <strong>Relativpronomen</strong> und steht direkt nach dem Nomen, auf das er sich bezieht.</p>"
    "<table><thead><tr><th>Artikel</th><th>Relativpronomen</th></tr></thead><tbody><tr><td>der</td><td>der</td></tr><tr><td>die</td><td>die</td></tr>"
    "<tr><td>das</td><td>das</td></tr><tr><td>die (Plural)</td><td>die</td></tr></tbody></table>"
    "<ul><li>Das ist der Mann. Der Mann arbeitet hier. → Das ist der Mann, <strong>der</strong> hier arbeitet.</li>"
    "<li>Das ist die Frau. Die Frau spricht Deutsch. → Das ist die Frau, <strong>die</strong> Deutsch spricht.</li>"
    "<li>Das ist das Buch. Das Buch ist interessant. → Das ist das Buch, <strong>das</strong> interessant ist.</li>"
    "<li>Das sind die Studenten. Die Studenten lernen Deutsch. → Das sind die Studenten, <strong>die</strong> Deutsch lernen.</li></ul>"
    "<p><strong>Merke:</strong> Im Relativsatz steht das Relativpronomen anstelle des Nomens. Das Verb steht am Ende des Relativsatzes. "
    "(Nomen → Relativpronomen → … → Verb am Ende)</p>"
    "<h4>Teil 2: Relativpronomen in anderen Kasus + Präpositionen</h4>"
    "<table><thead><tr><th>Artikel</th><th>Nominativ</th><th>Akkusativ</th><th>Dativ</th></tr></thead><tbody>"
    "<tr><td>der</td><td>der</td><td>den</td><td>dem</td></tr><tr><td>die</td><td>die</td><td>die</td><td>der</td></tr>"
    "<tr><td>das</td><td>das</td><td>das</td><td>dem</td></tr><tr><td>die (Plural)</td><td>die</td><td>die</td><td>denen</td></tr></tbody></table>"
    "<ul><li><strong>Akkusativ:</strong> Das ist der Mann. Ich kenne den Mann. → Das ist der Mann, <strong>den</strong> ich kenne.</li>"
    "<li><strong>Dativ:</strong> Das ist der Mann. Ich helfe dem Mann. → Das ist der Mann, <strong>dem</strong> ich helfe.</li>"
    "<li>Das ist die Frau. Ich spreche mit der Frau. → Das ist die Frau, <strong>mit der</strong> ich spreche.</li></ul>"
    "<p><strong>Merke:</strong> Das Relativpronomen richtet sich beim Genus und Numerus nach dem Bezugswort. Der Kasus hängt aber von seiner "
    "Funktion im Relativsatz ab.</p><p><strong>Präposition + Relativpronomen</strong> — die Präposition bleibt vor dem Relativpronomen:</p>"
    "<ul><li>Das ist der Freund, <strong>auf den</strong> ich warte.</li><li>Das ist die Kollegin, <strong>mit der</strong> ich arbeite.</li>"
    "<li>Das ist das Thema, <strong>über das</strong> wir sprechen.</li></ul><p>Präposition + Relativpronomen + Satz … → Verb am Ende.</p>"
    "<h4>Teil 3: Fragewörter als Relativpronomen</h4><p>Nicht nur der, die, das, die können Relativsätze einleiten. Auch bestimmte Fragewörter "
    "können als Relativpronomen verwendet werden: <strong>wer – wen – wem – was</strong>.</p>"
    "<p><strong>wer – wen – wem (für Personen):</strong> Wer viel lernt, macht Fortschritte. · Wer Deutsch spricht, kann viele Menschen verstehen. · "
    "Wem ich vertraue, dem erzähle ich mein Geheimnis. · Wen du einlädst, das musst du selbst entscheiden.</p>"
    "<p><strong>was (für Sachen / Dinge / ganze Aussagen):</strong> Alles, was du lernst, ist wichtig. · Das ist etwas, was ich nicht verstehe. · "
    "Ich erzähle dir, was passiert ist. · Das ist das Beste, was ich bisher gesehen habe.</p>"
    "<p><strong>Merke:</strong> Nach Wörtern wie alles, etwas, nichts, das Beste, das Einzige verwendet man häufig <strong>was</strong>.</p>"
)


def rel(n: int, sentence: str, accepted: list[str], options: list[str] | None = None, note: str | None = None) -> dict:
    spec = {"accepted": accepted, "options": options} if options else accepted
    return gap(f"{n}. Setze das passende Relativpronomen ein.", sentence.replace("___", "[[1]]", 1), {"1": spec}, explanation=note or accepted[0])


_NOM = ["der", "die", "das", "den"]
AUFGABE_1 = [
    ("Das ist der Mann, ___ jeden Morgen hier arbeitet.", "der"), ("Ich kenne eine Frau, ___ sehr gut Deutsch spricht.", "die"),
    ("Das ist das Buch, ___ auf dem Tisch liegt.", "das"), ("Das sind die Studenten, ___ heute Deutsch lernen.", "die"),
    ("Der Lehrer, ___ uns Deutsch unterrichtet, ist sehr freundlich.", "der"), ("Die Stadt, ___ am Rhein liegt, ist sehr schön.", "die"),
    ("Das Kind, ___ dort spielt, ist mein Bruder.", "das"), ("Die Menschen, ___ hier wohnen, sind sehr nett.", "die"),
    ("Ich habe einen Freund, ___ in Berlin lebt.", "der"), ("Das ist die Schule, ___ viele internationale Schüler besucht.", "die"),
    ("Der Hund, ___ im Garten schläft, gehört meinem Nachbarn.", "der"), ("Die Frau, ___ du gestern getroffen hast, ist meine Tante.", "die"),
    ("Das Auto, ___ vor dem Haus steht, ist neu.", "das"), ("Die Kinder, ___ im Park Fußball spielen, sind meine Freunde.", "die"),
    ("Das ist der Film, ___ wir gestern im Kino gesehen haben.", "den"), ("Der Student, ___ immer fleißig lernt, hat gute Noten.", "der"),
    ("Das Haus, ___ neben der Schule steht, ist sehr alt.", "das"), ("Die Sängerin, ___ heute im Konzert auftritt, ist bekannt.", "die"),
    ("Der Kurs, ___ ich besuche, ist sehr interessant.", "den"), ("Das sind die Bücher, ___ ich für das Projekt brauche.", "die"),
]
_AKK = "Akkusativ (wir haben den Film gesehen / ich besuche den Kurs) → den. Im Buch stehen nur der – die – das – die zur Auswahl."
AUFGABE_2 = [
    ("Das ist der Mann, ___ ich gestern gesehen habe.", ["den"]), ("Die Frau, ___ ich geholfen habe, ist meine Nachbarin.", ["der"]),
    ("Das ist der Freund, ___ ich immer warte. (auf)", ["auf den"]), ("Das ist die Kollegin, ___ ich jeden Tag spreche. (mit)", ["mit der"]),
    ("Das ist das Buch, ___ ich gerade lese.", ["das"]), ("Der Student, ___ der Lehrer eine Frage gestellt hat, antwortet.", ["dem"]),
    ("Das ist die Stadt, ___ ich schon lange träume. (von)", ["von der"]), ("Die Kinder, ___ wir geholfen haben, kommen aus Deutschland.", ["denen"]),
    ("Das ist der Film, ___ wir gestern gesprochen haben. (über)", ["über den"]), ("Das ist das Thema, ___ wir heute diskutieren. (über)", ["über das"]),
    ("Der Mann, ___ ich das Auto gekauft habe, ist mein Onkel.", ["von dem", "dem"]),
    ("Das Mädchen, ___ du gestern ein Geschenk gegeben hast, hat sich sehr gefreut.", ["dem"]),
    ("Das ist das Restaurant, ___ wir oft essen gehen. (in)", ["in dem", "wo"]), ("Die Schule, ___ ich früher gelernt habe, ist sehr modern.", ["an der", "in der", "wo"]),
    ("Das ist der Lehrer, ___ die Schüler viel lernen. (bei)", ["bei dem"]), ("Der Brief, ___ ich morgen antworte, ist sehr wichtig.", ["auf den"]),
    ("Das Haus, ___ meine Eltern wohnen, ist sehr groß.", ["in dem", "wo"]), ("Die Firma, ___ mein Bruder arbeitet, ist international.", ["bei der", "für die", "in der", "wo"]),
    ("Das ist der Park, ___ wir im Sommer spazieren gehen. (in)", ["in dem", "wo"]),
    ("Der Kurs, ___ ich mich angemeldet habe, ist sehr interessant.", ["zu dem", "für den", "bei dem"]),
]
_NOTE_2 = {11: "jemandem etwas abkaufen / etwas von jemandem kaufen → „von dem“ (auch „dem“ akzeptiert).",
           14: "Im Buch ohne Präposition: lernen an / in der Schule → „an der“ oder „in der“ (auch „wo“).",
           16: "Im Buch ohne Präposition: antworten auf → „auf den“.", 17: "wohnen in → „in dem“ (auch „wo“).",
           18: "Im Buch ohne Präposition: arbeiten bei / für / in → „bei der“, „für die“, „in der“.",
           20: "Im Buch ohne Präposition: sich anmelden zu / für → „zu dem“, „für den“ (auch „bei dem“)."}
AUFGABE_3 = [
    ("___ viel lernt, macht gute Fortschritte.", ["Wer"]), ("___ Deutsch spricht, kann viele Menschen verstehen.", ["Wer"]),
    ("___ du einlädst, musst du selbst entscheiden.", ["Wen"]), ("___ ich vertraue, dem erzähle ich mein Geheimnis.", ["Wem"]),
    ("Alles, ___ du heute lernst, ist wichtig.", ["was"]), ("Das ist etwas, ___ ich nicht verstehe.", ["was"]),
    ("Ich weiß nicht, ___ passiert ist.", ["was"]), ("Das ist das Beste, ___ ich bisher gesehen habe.", ["was"]),
    ("___ anderen hilft, bekommt auch Hilfe.", ["Wer"]), ("Alles, ___ er gesagt hat, war interessant.", ["was"]),
    ("___ du tust, tue es mit Herz.", ["Was"]), ("Ich suche jemanden, ___ mir bei der Arbeit helfen kann.", ["der"]),
    ("___ wir gestern getroffen haben, ist mein alter Freund.", ["Wen", "Der", "Den"]), ("Kannst du mir sagen, ___ dir dieses Buch empfohlen hat?", ["wer"]),
    ("Das ist der Grund, ___ ich heute nicht kommen konnte.", ["warum", "weshalb", "wieso"]), ("___ keinen Plan hat, sollte nicht der Chef sein.", ["Wer"]),
    ("Das ist die Idee, ___ wir lange diskutiert haben.", ["die", "über die"]), ("___ in der Gruppe arbeitet, lernt besser.", ["Wer"]),
    ("Ich erinnere mich an den Tag, ___ wir uns kennengelernt haben.", ["an dem", "als"]), ("Das ist alles, ___ ich dir sagen wollte.", ["was"]),
]
_NOTE_3 = {12: "„jemanden, der …“ — nach einem Nomen / Pronomen steht der (im Buch nur wer – wen – wem – was zur Auswahl).",
           13: "„Wen wir gestern getroffen haben, (der) ist …“ — auch „Der / Den …“ akzeptiert.", 15: "„der Grund, warum …“ (kein wer / wen / wem / was).",
           17: "„die Idee, die wir diskutiert haben“ (auch „über die“).", 19: "„der Tag, an dem …“ (auch „als“)."}

GRAMMATIK_SETS = [
    exercise("Aufgabe 1: Relativpronomen im Nominativ", [
        rel(n, s, [a], _NOM, _AKK if a == "den" else None) for n, (s, a) in enumerate(AUFGABE_1, start=1)],
        "Setze das passende Relativpronomen ein. Wähle aus: der – die – das – die (Buch S. 116). Satz 15 und 19 brauchen „den“ (Akkusativ) — "
        "deshalb steht „den“ mit in der Auswahl."),
    exercise("Aufgabe 2: Relativpronomen in anderen Kasus + Präpositionen", [
        rel(n, s, acc, None, _NOTE_2.get(n)) for n, (s, acc) in enumerate(AUFGABE_2, start=1)],
        "Setze das passende Relativpronomen oder die passende Präposition + Relativpronomen ein. Achte auf den richtigen Kasus! Akkusativ: den – die – "
        "das – die · Dativ: dem – der – dem – denen · Präpositionen: mit der – auf den – über das – von dem – in der – bei dem … (Buch S. 117)"),
    exercise("Aufgabe 3: Fragewörter als Relativpronomen", [
        rel(n, s, acc, None, _NOTE_3.get(n)) for n, (s, acc) in enumerate(AUFGABE_3, start=1)],
        "Setze das passende Relativpronomen ein. Wähle aus: wer – wen – wem – was (Buch S. 118). Einige Sätze im Buch brauchen ein anderes Wort "
        "(der, warum, die, an dem) — jede richtige Form zählt."),
]

# ---------- Lesen ----------
LESER = (
    "Im Land der Dichter und Denker scheiden sich die Geister*: Die einen kommen nicht ohne Bücher aus, die anderen brauchen überhaupt keine Bücher "
    "zum Leben. Neun Prozent der Bundesbürger, davon mehr als die Hälfte Männer, sind „buchresistent“: Wenn es um Bücher geht, werden sie zu "
    "„Totalverweigerern“. Statt Bücher zu lesen, greifen sie lieber zur TV-Fernbedienung oder surfen durchs Internet. Die größte Gruppe sind mit rund "
    "40 Prozent die „Wenigleser“. Sie konsumieren bis zu neun Bücher im Jahr.\n\n"
    "Ein Viertel der Bevölkerung zählt als „Normalleser“ und kommt auf 10 bis 18 Bücher im Jahr. Echte Bücherwürmer und Leseratten sind 27 Prozent der "
    "Deutschen. Sie verschlingen jährlich mindestens 19 Bücher. Dabei leihen gerade Vielleser viele Bücher bei Freunden oder in der Bibliothek aus, statt "
    "sie selbst neu zu kaufen. Sehr klein und sehr skurril ist die Gruppe der „Bücher kaufenden Nichtleser“: Sieben Prozent der Bundesbürger kaufen zwar "
    "regelmäßig Bücher, lesen sie aber kaum. Die Werke werden verschenkt oder als Dekoration ins Regal gestellt. 40 Prozent der Bundesbürger haben in "
    "ihrem Regal 50 bis 200 Bücher stehen. Jeder Vierte verfügt über 200 bis 500 Exemplare. Und bei 14 Prozent gibt es sogar mehr als 500 Bücher im "
    "Schrank.\n\n* Es scheiden sich die Geister. = Es gibt unterschiedliche Meinungen.")
WENDUNGEN = ["kommen nicht ohne (Bücher) aus", "Totalverweigerer", "Leseratte/Bücherwurm", "(buch)resistent sein", "ein Buch verschlingen", "skurril",
             "verfügt über"]
ERKLAERUNGEN = ["Person, die gern und viel liest", "schnell und mit Spannung lesen", "hat", "können ohne (Bücher) nicht leben",
                "sich nicht verführen lassen", "Person, die etwas prinzipiell ablehnt", "seltsam"]
LESEN_1 = [match("Welche Erklärungen passen zu den unterstrichenen Wendungen im Text? Ordnen Sie zu.", WENDUNGEN, ERKLAERUNGEN,
                 {"1": "D", "2": "F", "3": "A", "4": "E", "5": "B", "6": "G", "7": "C"}, points=7,
                 explanation="1 D · 2 F · 3 A · 4 E · 5 B · 6 G · 7 C")]
MEDIEN = (
    "Smartphone, Fernseher, Laptop und Tablet bestimmen unseren Alltag. Nach einer neuen Studie zum Thema Mediennutzung [[1]] der Fernseher mit 92 "
    "Prozent das meistgenutzte Gerät, gefolgt von dem Smartphone und dem PC/Laptop mit jeweils 87 Prozent. Auf Platz vier [[2]] das Radio mit 73 Prozent. "
    "Die Untersuchung [[3]] außerdem, dass die Smartphonenutzung in den letzten drei Jahren um 11 Prozent [[4]] ist. Ein weiteres Ergebnis der Studie "
    "ist, dass jeder zweite Umfrageteilnehmer täglich mehrere Bildschirme gleichzeitig [[5]]. Spitzenreiter ist hier die Kombination von Smartphone und "
    "Fernseher.\nZu den meistgenutzten Diensten im Internet [[6]] die E-Mail (83 Prozent) und die sozialen Netzwerke mit 74 Prozent. Die Hitliste bei "
    "den Social-Media-Plattformen wird zurzeit von WhatsApp (82 Prozent) und YouTube (81 Prozent) [[7]]. Facebook [[8]] als einziges "
    "Social-Media-Netzwerk eine sinkende Nutzung von minus 10 Prozent.")
MEDIEN_KEY = {"1": ["bleibt"], "2": ["liegt"], "3": ["ergab", "ergibt"], "4": ["gestiegen"], "5": ["benutzt", "nutzt"], "6": ["zählen"],
              "7": ["angeführt"], "8": ["verzeichnet"]}
LESEN_3 = [
    tf("Nachrichten sind das beliebteste Fernsehformat.", True, "Nachrichten 45 % — Platz 1."),
    tf("Krimiserien und Kriminalfilme sind beliebter als Sportübertragungen (live).", True, "27,7 % > 26,8 %."),
    tf("Comedy-Serien und Komödien sind beliebter als politische Magazine.", False, "16,6 % < 18,1 %."),
    tf("Sendungen zur Geschichte sind seltener beliebt als Kochshows.", False, "Geschichte 13,5 % > Kochshows 9,8 %."),
    tf("Heimatfilme und Volksmusiksendungen sind beliebter als Kunst- und Kultursendungen.", True, "8,5 % > 7 %."),
    tf("Serien und Filme aus den Bereichen Action, Abenteuer, Thriller, Horror sind beliebter als Quizsendungen, Rateshows.", False, "19 % < 19,8 %."),
]
FORMATE = [("Nachrichten", "45 %"), ("Krimiserien und Kriminalfilme", "27,7 %"), ("Sportübertragungen (live) und Sportsendungen", "26,8 %"),
           ("Regionale Informationen, Nachrichten, Beiträge", "25,9 %"), ("Tier- und Natursendungen", "25,6 %"),
           ("Reisemagazine, Sendungen über fremde Länder und Kulturen", "22,6 %"), ("Quizsendungen, Rateshows", "19,8 %"),
           ("Serien und Filme aus den Bereichen Action, Abenteuer, Thriller, Horror", "19 %"), ("Politische Magazine, Reportagen", "18,1 %"),
           ("Comedy-Serien und Komödien", "16,6 %"), ("Ratgebersendungen zu Gesundheit, Verkehr und Technik", "15,3 %"),
           ("Filme aus den Bereichen Science Fiction und Fantasy", "15,2 %"), ("Sendungen zur Geschichte", "13,5 %"),
           ("Familienserien und Arztserien", "11,8 %"), ("Politische Talkshows", "11,6 %"), ("Talentshows", "10,4 %"), ("Tägliche Serien, Soaps", "10,3 %"),
           ("Kochshows", "9,8 %"), ("Heimatfilme und Volksmusiksendungen", "8,5 %"), ("Kunst- und Kultursendungen", "7 %")]

# ---------- Hören ----------
FERNSEH = (
    "Vorbei sind die Zeiten, als Programmdirektoren das Fernsehprogramm nach ihrem eigenen Geschmack gestalteten. Heute dagegen wird das Programm von "
    "Marketing- und Werbespezialisten genau auf die Zielgruppen angepasst.\n"
    "Ein einfaches Beispiel: Kindersendungen laufen natürlich dann, wenn Kinder [[1]], also vor bzw. in den frühen Abend. Und so funktioniert es auch "
    "für alle anderen Zielgruppen, denn nach vielen Untersuchungen wissen die Experten sehr [[2]] die Sehgewohnheiten der Deutschen: Viele ältere "
    "Menschen sehen gern täglich [[3]], außerdem interessiert sie vor allem Doku-Soaps oder [[4]] gezeigt.\n"
    "Täglich sehen wir die Zeiten, [[5]] oder Krimis laufen. Jugendprogramme laufen in manchen „Morgengelände“ und 20.00 Uhr und höhere wird am "
    "regelmäßigsten und [[6]] geklickt. Zwischen 20.30 Uhr beginnt der harte Kampf um die Einschaltquoten und die Programmgestalter arbeiten ganz genau "
    "darauf, was die anderen Programme machen. Läuft zum Beispiel am Sonntagabend eine von allen Zielgruppen geliebte Unterhaltungsshow, sorgen die "
    "anderen Sender nur Spielfilme/weitbindungen. Oder: Läuft in einem Programm ein Fußballländerspiel, versuchen andere Programme nichts, einen "
    "Box-Welt-Titelkampf zu zeigen. [[7]] beide Sendungen die gleiche Zielgruppe haben: Männer zwischen 18 und 49.\n"
    "Spätestens kommen die Politik-Talkshows für politisch interessierte Menschen und ab Mitternacht denken die Programmgestalter verstärkt an [[8]] "
    "Herren. Man kann also sagen: Jeder Sender versucht, die [[9]] Zielgruppen zu bedienen, und berechnet dabei die anderen Sender ganz genau.\n"
    "Und [[10]] du eigentlich, was du siehst?")
FERNSEH_WOERTER = ["Kindern", "regelmäßig", "Quizshows", "ziemlich genau", "wissen", "beliebt", "ältere", "die", "vergleichen", "Spätabend", "laufen"]
HOEREN_1 = [gap(f"Hören Sie den Text und setzen Sie die richtigen Wörter in die Lücken ({a}–{b}) ein.", para,
                {str(i): [] for i in range(a, b + 1)}, points=b - a + 1)
            for para, a, b in [(p, int(p.split("[[")[1].split("]]")[0]), int(p.split("[[")[-1].split("]]")[0])) for p in FERNSEH.split("\n") if "[[" in p]]
RADIO = ["Laut einer aktuellen Studie werden immer weniger Bücher gelesen.", "Der Online-Buchhandel ist eine große Konkurrenz für Buchhändler.",
         "Viele Kunden lassen sich nicht mehr in Geschäften beraten.", "Bei der Entwicklung spielen E-Books eine große Rolle.",
         "Der Kundenkontakt ist intensiver geworden.", "Wer in der Jugend nicht liest, wird auch später nicht gern lesen.",
         "Lesen soll in erster Linie Spaß machen.", "Man sollte einfach mal wieder ein Buch in die Hand nehmen und lesen."]
_SPRECHER = ["Moderator", "Frau Baumgart", "Frau Kuhn"]
HOEREN_2 = [mc_pending(f"{n}. {s}", _SPRECHER) for n, s in enumerate(RADIO, start=1)]

# ---------- Schreiben ----------
EBOOKS = (
    "52 Prozent der Österreicher [[1]] eine repräsentative Umfrage, die das Marktforschungsinstitut MindTake Research unter 600 Personen [[2]] hat. "
    "Zum Lesen ihrer E-Books [[3]] die Österreicher am liebsten E-Book-Reader. Das Tablet [[4]] auf Platz zwei vor dem Smartphone. Beim Kauf von "
    "Lesegeräten und E-Books [[5]] die Konsumenten sehr auf den Preis. Als besonders positiv wird [[6]], dass man mehrere Bücher auf einem Gerät hat. "
    "Das [[7]] auf Reisen klare Vorteile. Außerdem [[8]] E-Books zu Hause keinen Platz im Bücherregal [[9]].")
EBOOKS_KEY = {"1": ["ergab", "lesen"], "2": ["durchgeführt"], "3": ["nutzen", "lesen"], "4": ["liegt"], "5": ["achten"], "6": ["hervorgehoben"],
              "7": ["bietet"], "8": ["nehmen"], "9": ["ein"]}
MEDIEN_WORT = [
    ("das Smartphone", "ein Handy, mit dem man telefonieren, schreiben und ins Internet gehen kann"),
    ("die Nachricht", "eine Information, die man jemandem schreibt oder erhält"), ("das Internet", "ein weltweites Netzwerk für Informationen und Kommunikation"),
    ("das Fernsehen", "ein Medium, über das man Sendungen sehen kann"), ("die Musik streamen", "Musik online hören, ohne sie herunterzuladen"),
    ("die Zeitung", "ein gedrucktes oder digitales Medium mit Nachrichten"), ("die sozialen Medien", "Plattformen wie Facebook, Instagram oder TikTok"),
    ("die E-Mail", "eine elektronische Nachricht"), ("herunterladen", "Daten aus dem Internet auf ein Gerät kopieren"),
    ("die Privatsphäre", "der persönliche Bereich, der geschützt werden soll"),
]


def _word(w: str, m: str) -> dict:
    parts = w.split(" ", 1)
    if len(parts) == 2 and parts[0] in ("der", "die", "das") and parts[1][0].isupper():
        return {"word": parts[1], "article": parts[0], "translation": m, "group": "Medien und Alltag"}
    return {"word": w, "translation": m, "group": "Medien und Alltag"}


WORDS = [_word(w, m) for w, m in MEDIEN_WORT]

UEBUNGEN = [
    exercise("Relativsätze — Beispiele aus dem Buch", [
        example_gap("Das ist der Mann, ___ hier arbeitet.", "der", ["der", "den", "dem"], "Nominativ."),
        example_gap("Das ist der Mann, ___ ich kenne.", "den", ["den", "der", "dem"], "Akkusativ: Ich kenne den Mann."),
        example_gap("Das ist der Mann, ___ ich helfe.", "dem", ["dem", "den", "der"], "Dativ: Ich helfe dem Mann."),
        example_gap("Das ist die Frau, mit ___ ich spreche.", "der", ["der", "die", "dem"], "mit + Dativ → der."),
        example_gap("Das ist der Freund, ___ den ich warte.", "auf", ["auf", "über", "mit"], "warten auf."),
        example_gap("Das ist das Thema, über ___ wir sprechen.", "das", ["das", "dem", "den"], "über + Akkusativ → das."),
        example_gap("Alles, ___ du lernst, ist wichtig.", "was", ["was", "das", "wer"], "Nach alles → was."),
        example_gap("___ viel lernt, macht Fortschritte.", "Wer", ["Wer", "Was", "Wen"], "Person, Nominativ → wer."),
        example_gap("___ ich vertraue, dem erzähle ich mein Geheimnis.", "Wem", ["Wem", "Wen", "Wer"], "vertrauen + Dativ → wem."),
    ], "Wählen Sie die richtige Form (Buch S. 113–115).", source="vizu"),
]
ABSCHLUSSTEST = [
    mc("Wo steht das Verb im Relativsatz?", ["Am Ende", "Auf Position 2", "Am Anfang"], "A", "Buch S. 113: Das Verb steht am Ende des Relativsatzes."),
    mc("Wonach richtet sich der Kasus des Relativpronomens?", ["Nach seiner Funktion im Relativsatz", "Nach dem Bezugswort", "Nach dem Verb im Hauptsatz"],
       "A", "Buch S. 114: Genus und Numerus nach dem Bezugswort, der Kasus nach der Funktion im Relativsatz."),
    example_gap("Die Kinder, ___ wir geholfen haben, kommen aus Deutschland.", "denen", ["denen", "die", "dem"], "Dativ Plural → denen."),
    example_gap("Das ist die Stadt, von ___ ich schon lange träume.", "der", ["der", "die", "dem"]),
    example_gap("Das ist das Beste, ___ ich bisher gesehen habe.", "was", ["was", "das", "wer"]),
    example_gap("___ anderen hilft, bekommt auch Hilfe.", "Wer", ["Wer", "Wen", "Was"]),
    mc("Wie viele Bücher lesen „Leseratten“ laut Text mindestens im Jahr?", ["19", "9", "500"], "A", "Lesen Aufgabe 1: „Sie verschlingen jährlich mindestens 19 Bücher.“"),
    mc("Welches Fernsehformat ist am beliebtesten?", ["Nachrichten", "Kochshows", "Talentshows"], "A", "Lesen Aufgabe 3: Nachrichten 45 %."),
    mc("„herunterladen“ bedeutet …", ["Daten aus dem Internet auf ein Gerät kopieren", "Musik online hören", "eine elektronische Nachricht"], "A", "Wortschatz S. 128."),
    mc("„die Privatsphäre“ ist …", ["der persönliche Bereich, der geschützt werden soll", "ein gedrucktes Medium", "ein weltweites Netzwerk"], "A",
       "Wortschatz S. 128."),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: B1 7. Unterricht", source="vizu", page=111, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Wie informieren Sie sich?", page=112,
             prompt="Wie informieren Sie sich? Sprechen Sie über Ihre Gewohnheiten.",
             questions=["Online-Nachrichten", "Soziale Medien", "Fernsehen und Radio"], min_duration=30, max_duration=150,
             metadata={"book_samples": [
                 "Ich lese jeden Morgen die Nachrichten online. Ich informiere mich über aktuelle Themen aus der Welt, Politik und Wirtschaft.",
                 "Ich nutze soziale Medien wie Instagram und Facebook. Dort sehe ich, was meine Freunde teilen, und bleibe über wichtige Ereignisse auf "
                 "dem Laufenden.",
                 "Ich schaue abends die Tagesschau im Fernsehen oder höre Radio. Das ist für mich eine zuverlässige Informationsquelle."],
                 "tipp": "Es gibt viele Möglichkeiten, sich zu informieren. Wichtig ist, dass die Informationen seriös und aktuell sind."}),
        base(L, "grammatik", 1, "Grammatik: Relativsätze", page="113-118", rules=[{"title": "Relativsätze (Teil 1–3)", "html": GRAMMAR_HTML}],
             exercises=GRAMMATIK_SETS,
             metadata={"note": "Lösungen von VIZU nach der Grammatik; Buchfehler (fehlende Auswahl / Präposition) im Hinweis der Aufgabe und der Frage."}),
        base(L, "lesen", 1, "Lesen Aufgabe 1: Leser und Nichtleser", page=119,
             instruction="a) Welche Erklärungen passen zu den unterstrichenen Wendungen im Text? Ordnen Sie zu.",
             passages=[{"title": "Leser und Nichtleser", "text": LESER}], questions=LESEN_1, max_score=7, metadata=key_meta("vizu")),
        base(L, "lesen", 2, "Lesen Aufgabe 2: Mediennutzung in Deutschland", page=120,
             instruction="Setze die passenden Verben aus der Liste in der richtigen Form ein. Verben: ergeben • anführen • steigen • bestimmen • zählen • "
                         "bleiben • liegen • verzeichnen • benutzen",
             passages=[{"title": "Mediennutzung in Deutschland", "text": MEDIEN.replace("[[", "(").replace("]]", ") ……")}],
             questions=[gap("Setze die passenden Verben in der richtigen Form ein.", MEDIEN, MEDIEN_KEY, points=8,
                            explanation="1 bleibt · 2 liegt · 3 ergab · 4 gestiegen · 5 benutzt · 6 zählen · 7 angeführt · 8 verzeichnet "
                                        "(„bestimmen“ ist das Beispiel im ersten Satz)")],
             max_score=8, metadata=key_meta("vizu")),
        base(L, "lesen", 3, "Lesen Aufgabe 3: Die beliebtesten Fernsehformate in Deutschland", page=121,
             instruction="Lies das Diagramm und entscheide, ob die Aussagen richtig oder falsch sind. Tipp: Vergleiche die Prozentzahlen im Diagramm. "
                         "Merke: 45 % = fast die Hälfte, 25 % = ein Viertel.",
             passages=[{"title": "Die beliebtesten Fernsehformate in Deutschland (Auswahl, Quelle: Statista)",
                        "text": "\n".join(f"{f}: {p}" for f, p in FORMATE)}],
             questions=LESEN_3, max_score=len(LESEN_3), metadata=key_meta("vizu", "Lösung aus den Zahlen des Diagramms — bitte prüfen.")),
        base(L, "hoeren", 1, "Hören Aufgabe 1: Wer bestimmt eigentlich das Fernsehprogramm?", page=122, audio_file=AUDIO["vizu-b1-l07-hoeren-01"],
             key_pending=True,
             instruction="Höre den Text und setze die richtigen Wörter in die Lücken (1–10) ein. Achtung: Es gibt mehr Wörter als du brauchst. "
                         "Wörter: " + " • ".join(FERNSEH_WOERTER),
             questions=HOEREN_1, max_score=10,
             metadata=key_meta("pending", "Lücken nach dem Anhören in Lösung festlegen (Wörterliste im Buch, keine Lösung).")),
        base(L, "hoeren", 2, "Hören Aufgabe 2: Wer liest denn heute noch Bücher?", page=123, audio_file=AUDIO["vizu-b1-l07-hoeren-02"], key_pending=True,
             instruction="Sie hören jetzt ein Gespräch im Radio zum Thema Lesen. Ordnen Sie die Aussagen zu: Wer sagt was? Lesen Sie zuerst die Aussagen.",
             questions=HOEREN_2, max_score=8, metadata=key_meta("pending", "Keine Lösung im Buch — nach dem Anhören in Lösung festlegen.")),
        base(L, "uebungen", 2, "Schreiben Aufgabe 1: E-Books und E-Reader in Österreich", page=124, source="book",
             exercises=[exercise("Schreiben Aufgabe 1: E-Books und E-Reader in Österreich", [
                 gap("Ergänzen Sie die Verben in der richtigen Form.", EBOOKS, EBOOKS_KEY, points=9,
                     explanation="1 ergab (Satz im Buch verkürzt) · 2 durchgeführt · 3 nutzen · 4 liegt · 5 achten · 6 hervorgehoben · 7 bietet · "
                                 "8 nehmen … 9 ein")],
                 "Ergänzen Sie die Verben in der richtigen Form (Buch S. 124). Verben: liegen • achten • lesen • durchführen • hervorheben • einnehmen • "
                 "ergeben • nutzen • bieten. Im Buch hat die Lücke vor „E-Books“ keine Nummer — hier Lücke 8, die Nummer (8) im Buch ist hier Lücke 9.")],
             metadata={"note": "Prüfung nötig: Satz 1 ist im Buch verkürzt („52 Prozent der Österreicher (1) eine repräsentative Umfrage“) — "
                               "akzeptiert werden „ergab“ und „lesen“. Lösung von VIZU.",
                       "publish_hold": "Satz 1 im Buch verkürzt — Lösung in der Übung prüfen"}),
        base(L, "schreiben", 1, "Schreiben Aufgabe 2: Eine E-Mail an einen Freund", page=125, task_type="email",
             prompt="Sie wohnen seit einiger Zeit in Deutschland. Schreiben Sie eine E-Mail an eine Freundin / einen Freund.\n\nBeschreiben Sie kurz,\n"
                    "• wie es Ihnen geht und was Sie machen,\n• welche Medien Sie wie oft nutzen,\n• welche deutschen Fernsehsendungen Sie sehen "
                    "(Orientieren Sie sich an A20),\n• welche Fernsehsendungen aus Ihrem Heimatland Sie sich übers Internet ansehen bzw. welche Sendungen "
                    "Sie in Deutschland vermissen.\n\nTipps für Ihre E-Mail: Beginnen Sie mit einer freundlichen Anrede. Schreiben Sie in kurzen Absätzen. "
                    "Vergessen Sie nicht den Gruß am Schluss.\nNützliche Ausdrücke: Mir geht es gut / nicht so gut, aber … · In meiner Freizeit … · "
                    "Ich schaue gerne … / Ich interessiere mich für … · Am liebsten nutze ich … · Ich vermisse besonders … · Schreibe mir bald wieder!\n"
                    "Denken Sie daran: auf die vier Punkte einzugehen, Relativsätze zu verwenden, einen passenden Betreff zu wählen, mindestens 80–100 "
                    "Wörter zu schreiben.",
             audience="Ein Freund / eine Freundin (informell)", min_words=80, max_words=150, time_limit=25,
             metadata={"note": "„Orientieren Sie sich an A20“ verweist auf eine Seite, die es im Buch nicht gibt — die Fernsehformate von Lesen Aufgabe 3 helfen."}),
        base(L, "sprechen", 1, "Sprechen Teil 1: Sprechen Sie zum Thema!", page=126, topic="Nachrichten und Medien",
             prompt="Antworten Sie auf die Fragen. Sprechen Sie mit Ihrem Partner / Ihrer Partnerin.\n1. Worüber möchten Sie in den Nachrichten "
                    "informiert werden? (Weltgeschehen, politische Entwicklungen in Ihrem Heimatland, Neues aus der Wirtschaft oder der Wissenschaft, "
                    "Verbrechen, Leben von Prominenten, Wetter, Sportwettkämpfe …)\n2. Wie informieren Sie sich über aktuelle Politik? (im Fernsehen, im "
                    "Radio, in Zeitungen oder Zeitschriften, online (Nachrichtenportale), über soziale Medien, im Gespräch mit anderen …)\n3. Haben Sie "
                    "eine Lieblingsnachrichtensendung oder gibt es eine Nachrichtensprecherin / einen Nachrichtensprecher, die / den Sie besonders "
                    "mögen?\n4. Welche Themen beherrschen in Ihrem Heimatland die Nachrichtensendungen?\n\nTipp: Geben Sie Beispiele, erklären Sie kurz "
                    "und begründen Sie Ihre Meinung. Hören Sie aufmerksam zu und stellen Sie Rückfragen!",
             questions=["Worüber möchten Sie in den Nachrichten informiert werden?", "Wie informieren Sie sich über aktuelle Politik?",
                        "Haben Sie eine Lieblingsnachrichtensendung oder eine Nachrichtensprecherin / einen Nachrichtensprecher, die / den Sie besonders mögen?",
                        "Welche Themen beherrschen in Ihrem Heimatland die Nachrichtensendungen?"],
             response_type="dialog", min_duration=60, max_duration=240,
             speech_goal="Über Nachrichten und Mediengewohnheiten sprechen, Beispiele geben, Meinung begründen, Rückfragen stellen.",
             keywords=["Ich informiere mich …", "Am liebsten …", "In meinem Heimatland …", "Was meinst du?"]),
        base(L, "sprechen", 2, "Sprechen Teil 2: Präsentation — Soziale Netzwerke als Nachrichtenquelle", page=127,
             topic="Soziale Netzwerke als Nachrichtenquelle",
             prompt="Halten Sie eine Präsentation zum Thema „Soziale Netzwerke als Nachrichtenquelle“.\n1. Stellen Sie Ihr Thema vor. Erklären Sie den "
                    "Inhalt und die Struktur Ihrer Präsentation. (Worum geht es? Wie ist Ihre Präsentation aufgebaut? Warum ist das Thema wichtig?)\n"
                    "2. Berichten Sie von Ihrer Situation oder einem Erlebnis im Zusammenhang mit dem Thema. (Welche Erfahrungen haben Sie gemacht? Wie hat "
                    "sich die Situation auf Sie ausgewirkt? Was haben Sie daraus gelernt?)\n3. Berichten Sie von der Situation in Ihrem Heimatland und "
                    "geben Sie Beispiele. (Wie ist die Nutzung von sozialen Netzwerken in Ihrem Heimatland? Welche Plattformen sind besonders beliebt? "
                    "Geben Sie konkrete Beispiele.)\n4. Nennen Sie Vor- und Nachteile und äußern Sie Ihre Meinung zum Thema. (Welche Vorteile sehen Sie "
                    "in sozialen Netzwerken als Nachrichtenquelle? Welche Nachteile gibt es? Wie ist Ihre persönliche Meinung? Begründen Sie diese.)\n"
                    "5. Beenden Sie Ihre Präsentation und bedanken Sie sich bei den Zuhörern. (Fassen Sie die wichtigsten Punkte kurz zusammen. Bedanken "
                    "Sie sich für die Aufmerksamkeit und öffnen Sie die Runde für Fragen.)",
             questions=["Thema vorstellen", "Eigene Situation / Erlebnis", "Situation im Heimatland mit Beispielen", "Vor- und Nachteile, eigene Meinung",
                        "Abschluss und Dank"],
             response_type="monolog", preparation_time=300, min_duration=120, max_duration=180,
             speech_goal="Strukturierte Präsentation in 5 Schritten (Buch S. 127).",
             keywords=["Mein Thema ist", "Ich habe die Erfahrung gemacht", "In meinem Heimatland", "Ein Vorteil ist", "Danke für Ihre Aufmerksamkeit!"]),
        base(L, "wortschatz", 1, "Wortschatz: Medien und Alltag", page=128, words=WORDS, exercises=meaning_sets(WORDS), auto_practice=False,
             metadata={"note": "Das Buch erklärt die Wörter auf Deutsch (keine Übersetzung)."}),
        base(L, "schreiben", 2, "Wortschatz-Aufgabe: Medien und Alltag — eigene Beispielsätze", page=128, task_type="other",
             prompt="Hier sind 10 wichtige Wörter und Ausdrücke zum Thema „Medien und Alltag“. Lesen Sie die Wörter, ihre Bedeutungen und schreiben Sie "
                    "eigene Beispielsätze.\n\n" + "\n".join(f"{i}. {w} — {m}" for i, (w, m) in enumerate(MEDIEN_WORT, start=1)),
             min_words=40, max_words=300, time_limit=20, metadata={"note": "Ish varag'i — o'qituvchi tekshiradi."}),
        base(L, "uebungen", 1, "Übungen: B1 7. Unterricht", source="vizu", exercises=UEBUNGEN),
        base(L, "yakuniy", 1, "Abschlusstest: B1 7. Unterricht", source="vizu",
             instruction="Abschlusstest zu Relativsätzen, Lesen und Wortschatz (alle Sätze aus dem Buch).", questions=ABSCHLUSSTEST),
        base(L, "kompetenz", 2, "Zusammenfassung: B1 7. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
