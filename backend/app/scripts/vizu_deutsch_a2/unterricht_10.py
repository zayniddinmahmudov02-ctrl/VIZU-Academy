"""A2 10. Unterricht — Lernen und Weiterbildung — Grammatik: Futur I und Futur II (book pp. 104-124).

A prüfungsnahes Unterricht (A2 exam format). Book: Frage p.105, Futur I / II
pp.106-107 (Aufgaben: 15 + 15 word orders), Lesen Teil 1-4 pp.108-115, Hören
Teil 1-4 pp.116-119 (no transcript, no key), Schreiben Teil 1 / 2 pp.120-121,
Sprechen Teil 1 / 2 pp.122-123, Wortschatzmethode p.124.

Keys: "Vizu-Antworten A2" has none for lesson 10. Lesen: every answer follows
from the text (quoted in the explanation; Teil 4 has one task without an ad,
X). Futur: one sentence each (accepted also with the time expression first).
Hören waits for an admin (key_pending); Teil 2 / 3 are picture tasks — the
pictures are described as options and the book page is attached as an
image. Audio: "A2 10.Unterricht Teil 1-4" — one Hören task per Teil.
Wortschatz: the book gives word lists without translations — no word list
is invented; the lists are shown as text and used for a writing task."""

from . import base, exercise, gap, intro_html, match, mc, mc_pending, short, summary_html, tf, ul

L = 10
LESSON_TITLE = "Lernen und Weiterbildung"
LESSON_DESCRIPTION = "Thema: Lernen und Weiterbildung · Grammatik: Futur I und Futur II · Prüfungstraining A2"
AUDIO = {"vizu-a2-l10-hoeren-01": "A2 10.Unterricht Teil 1.m4a", "vizu-a2-l10-hoeren-02": "A2 10.Unterricht Teil 2.m4a",
         "vizu-a2-l10-hoeren-03": "A2 10.Unterricht Teil 3.m4a", "vizu-a2-l10-hoeren-04": "A2 10.Unterricht Teil 4.m4a"}
IMAGES = [("p117_hoeren_teil2.jpg", "HOEREN", "Hören Teil 2 — Bilder a bis i (Buch, S. 117)"),
          ("p118_hoeren_teil3.jpg", "HOEREN", "Hören Teil 3 — Bilder (Buch, S. 118)")]
RETIRED_IMAGE_TITLES: list[str] = []

EINFUEHRUNG_HTML = intro_html(
    10, "Lernen und Weiterbildung", "Futur I und Futur II",
    ["Futur I (werden + Infinitiv) bilan reja va taxminlarni aytish;",
     "Futur II (werden + Partizip II + haben / sein) bilan kelajakda tugagan ishni aytish;",
     "A2 imtihon formatida Lesen, Hören, Schreiben va Sprechen topshiriqlarini bajarish."],
    ["Germaniyada o'qish imkoniyatlari haqida gapirasiz;",
     "gazeta matni, ma'lumot taxtasi, e-mail va e'lonlarni tushunasiz;",
     "qisqa matnlar, suhbat va intervyuni tinglab tushunasiz;",
     "SMS va rasmiy bo'lmagan e-mail yozasiz, savol berasiz va o'zingiz haqida gapirasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(10, [
    "<strong>Futur I:</strong> Pläne, Prognosen und Vermutungen — werden + Infinitiv: Ich werde dich morgen anrufen.",
    "<strong>Futur II:</strong> abgeschlossene Ereignisse in der Zukunft — werden + Partizip II + haben / sein: Ich werde die Aufgabe bis morgen erledigt haben.",
    "<strong>Unterschied:</strong> Futur I – Handlung liegt in der Zukunft · Futur II – Handlung wird in der Zukunft abgeschlossen sein.",
    "<strong>Prüfungstipp:</strong> Schlüsselwörter markieren, „zwischen den Zeilen“ lesen, zu allen Punkten schreiben.",
])

GRAMMAR_HTML = (
    "<h3>Futur I und Futur II (A2–B1)</h3>"
    "<table><thead><tr><th>Futur I</th><th>Futur II</th></tr></thead><tbody>"
    "<tr><td>Futur I wird für Pläne, Prognosen und Vermutungen in der Zukunft benutzt.</td>"
    "<td>Futur II wird für abgeschlossene Ereignisse in der Zukunft benutzt.</td></tr>"
    "<tr><td><strong>Vorform:</strong> werden + Infinitiv</td><td><strong>Vorform:</strong> werden + Partizip II + haben / sein</td></tr>"
    "<tr><td>Ich <strong>werde</strong> dich morgen anrufen.<br>Wir <strong>werden</strong> bald nach Spanien fliegen.<br>"
    "Lisa <strong>wird</strong> wohl schon geschlafen haben.</td>"
    "<td>Ich <strong>werde</strong> die Aufgabe bis morgen <strong>erledigt haben</strong>.<br>David <strong>wird</strong> um 23 Uhr zu Hause "
    "<strong>angekommen sein</strong>.<br>Lisa <strong>wird</strong> schon <strong>geschlafen haben</strong>, wenn du anrufst.</td></tr></tbody></table>"
    "<h4>Unterschied</h4><ul><li><strong>Futur I:</strong> Handlung liegt in der Zukunft.</li>"
    "<li><strong>Futur II:</strong> Handlung wird in der Zukunft abgeschlossen sein.</li></ul>"
)


def _futur(n: int, words: str, answers: list[str]) -> dict:
    accepted = []
    for a in answers:
        accepted += [a, a.rstrip(".")]
    return short(f"{n}. {words}", accepted, explanation=answers[0], max_length=150)


FUTUR_I = [
    _futur(1, "ich | morgen | arbeiten | werde | viel", ["Ich werde morgen viel arbeiten.", "Morgen werde ich viel arbeiten."]),
    _futur(2, "wir | später | werden | ins Kino | gehen", ["Wir werden später ins Kino gehen.", "Später werden wir ins Kino gehen."]),
    _futur(3, "du | das Buch | lesen | wirst", ["Du wirst das Buch lesen."]),
    _futur(4, "sie | in Berlin | werden | leben", ["Sie werden in Berlin leben.", "In Berlin werden sie leben."]),
    _futur(5, "ich | dich | anrufen | werde | heute", ["Ich werde dich heute anrufen.", "Heute werde ich dich anrufen."]),
    _futur(6, "er | schnell | laufen | wird", ["Er wird schnell laufen."]),
    _futur(7, "wir | Deutsch | lernen | werden", ["Wir werden Deutsch lernen."]),
    _futur(8, "ihr | die Aufgabe | lösen | werdet", ["Ihr werdet die Aufgabe lösen."]),
    _futur(9, "sie | morgen | kommen | werden", ["Sie werden morgen kommen.", "Morgen werden sie kommen."]),
    _futur(10, "ich | ein Auto | kaufen | werde", ["Ich werde ein Auto kaufen."]),
    _futur(11, "du | deine Hausaufgaben | machen | wirst", ["Du wirst deine Hausaufgaben machen."]),
    _futur(12, "wir | im Sommer | reisen | werden", ["Wir werden im Sommer reisen.", "Im Sommer werden wir reisen."]),
    _futur(13, "er | das Problem | verstehen | wird", ["Er wird das Problem verstehen."]),
    _futur(14, "sie | ein Geschenk | bekommen | wird", ["Sie wird ein Geschenk bekommen."]),
    _futur(15, "ich | früh | aufstehen | werde", ["Ich werde früh aufstehen."]),
]
FUTUR_II = [
    _futur(1, "ich | die Arbeit | gemacht | haben | werde", ["Ich werde die Arbeit gemacht haben."]),
    _futur(2, "wir | das Projekt | beendet | haben | werden", ["Wir werden das Projekt beendet haben."]),
    _futur(3, "du | dein Ziel | erreicht | haben | wirst", ["Du wirst dein Ziel erreicht haben."]),
    _futur(4, "sie | den Text | gelesen | haben | wird", ["Sie wird den Text gelesen haben."]),
    _futur(5, "er | nach Hause | gegangen | sein | wird", ["Er wird nach Hause gegangen sein."]),
    _futur(6, "ich | alles | vorbereitet | haben | werde", ["Ich werde alles vorbereitet haben."]),
    _futur(7, "wir | das Essen | gekocht | haben | werden", ["Wir werden das Essen gekocht haben."]),
    _futur(8, "ihr | die Prüfung | bestanden | haben | werdet", ["Ihr werdet die Prüfung bestanden haben."]),
    _futur(9, "sie | die Aufgabe | gelöst | haben | wird", ["Sie wird die Aufgabe gelöst haben."]),
    _futur(10, "ich | das Buch | geschrieben | haben | werde", ["Ich werde das Buch geschrieben haben."]),
    _futur(11, "du | die Regeln | gelernt | haben | wirst", ["Du wirst die Regeln gelernt haben."]),
    _futur(12, "wir | das Haus | gebaut | haben | werden", ["Wir werden das Haus gebaut haben."]),
    _futur(13, "er | die Antwort | gefunden | haben | wird", ["Er wird die Antwort gefunden haben."]),
    _futur(14, "sie | die Reise | gemacht | haben | wird", ["Sie wird die Reise gemacht haben."]),
    _futur(15, "ich | die Nachricht | bekommen | haben | werde", ["Ich werde die Nachricht bekommen haben."]),
]

# ---------- Lesen Teil 1-4 ----------
TEXT_T1 = (
    "Tolle Sehenswürdigkeiten\n\nDas Brandenburger Tor, die Akropolis, der schiefe Turm von Pisa oder der Big Ben. Sehenswürdigkeiten gibt es viele auf der "
    "Welt. Fotografiere sie und gewinne tolle Preise!\n\nUnter dem Motto „Mein Denkmal“ startet der Jugendfotowettbewerb „Enjoy-Denkmäler“. Nimm deine "
    "Kamera oder dein Handy und fotografiere Sehenswürdigkeiten, Häuser oder Gebäude.\n\nDeine Aufgabe ist es, etwas zu fotografieren, was du für eine "
    "tolle Sehenswürdigkeit hältst. Du sollst aber auch etwas darüber schreiben, was dir an dieser Sehenswürdigkeit gefällt. Die Größe? Die Farbe? Die "
    "Architektur? Schreib das Wichtigste!\n\nBei diesem Wettbewerb kann jeder mitmachen. Die Teilnehmer dürfen aber höchstens 18 Jahre alt sein. "
    "Natürlich kannst du auch mit deiner Schulklasse oder mit deinen Freunden als Gruppe teilnehmen. Was du für eine Kamera oder was für ein Handy ihr "
    "benutzt, das ist egal.\n\nWo du deine Fotos machen kannst? Natürlich überall! In deiner Stadt, auf einem Ausflug mit deinen Eltern, Freunden, mit "
    "deiner Schulklasse, im Inland oder auch im Ausland. Es spielt überhaupt keine Rolle, wo du wohnst. Zu gewinnen gibt es tolle Geldpreise: Der Sieger "
    "bekommt 300, der zweite 200 und der dritte 100 Euro. Wir vergeben also insgesamt 600 Euro!\n\nDu schickst deine Fotos spätestens bis zum "
    "10. September (bitte keinen Tag später!) an folgende E-Mail-Adresse: fotowettbewerb@yahoo.de Also dann viel Spaß und viel Erfolg!")
LESEN_T1 = [
    mc("1 Wer bei „Enjoy-Denkmal“ mitmacht, …", ["muss Sehenswürdigkeiten, aber keine Häuser fotografieren.",
                                                 "muss angeben, von welchem Architekten diese Sehenswürdigkeit stammt.",
                                                 "muss auch begründen, warum er diese Sehenswürdigkeit gewählt hat."], "C",
       "„Du sollst aber auch etwas darüber schreiben, was dir an dieser Sehenswürdigkeit gefällt.“"),
    mc("2 Personen …", ["bis zu 18 Jahren dürfen beim Wettbewerb mitmachen.", "über 18 dürfen auch am Wettbewerb teilnehmen.",
                        "unter 18 dürfen nicht am Wettbewerb teilnehmen."], "A", "„Die Teilnehmer dürfen aber höchstens 18 Jahre alt sein.“"),
    mc("3 Die Fotos …", ["darf man nur mit einer Handy-Kamera machen.", "kann man an jedem möglichen Ort machen.", "soll man nur an seinem Wohnort machen."], "B",
       "„Wo du deine Fotos machen kannst? Natürlich überall!“"),
    mc("4 Wer das beste Foto macht, bekommt …", ["dreihundert Euro.", "eine goldene Kamera.", "insgesamt sechshundert Euro."], "A",
       "„Der Sieger bekommt 300 … Euro.“"),
    mc("5 Die Fotos …", ["sollen bis Ende September geschickt werden.", "sollen alle am 10. September geschickt werden.",
                         "sollen nicht später als am 10. September geschickt werden."], "C", "„… spätestens bis zum 10. September (bitte keinen Tag später!)“"),
]
TEXT_T2 = (
    "Im „KaDeWe“ finden Sie alles, was Sie brauchen!\n\nErdgeschoss: Information, Angebot der Woche, Post, Presse, Reisebüro, Apotheke, Friseur, Blumen und "
    "Pflanzen, Bankautomat, Service, Erste-Hilfe-Station\n1. Stock: Lederwaren, Regenschirme, Reisegepäck, Schreibwaren, Bücher, Musikinstrumente, alles "
    "fürs Hobby, alles fürs Haustier\n2. Stock: Babymode, Kindermode, Herrenjeans, Herrenmode, Herrenschuhe, Sonnenbrillen, Sportartikel\n3. Stock: Uhren "
    "& Schmuck, Parfümerie und Kosmetik, Blusen, Damentaschen, Kleider & Röcke, Damenschuhe, Haarpflege\n4. Stock: Licht und Wohnen, WC und Bad, "
    "Fernseher, Mobiltelefone, Rechner und Tablets, Radios, Lautsprecher, Car Hi-Fi, Autozubehör, PC-Spiele, Batterien, Drucker, Kameras, CDs, DVDs\n"
    "5. Stock: Alkohol und Getränke, Chips, Bäckerei, Konditorei, Fisch und Fleisch, Obst und Gemüse, Süßigkeiten, Cafeteria, Pizzeria, Fundbüro")
LESEN_T2 = [
    mc("6 Du interessierst dich für die neuen Handy-Modelle.", ["4. Stock", "1. Stock", "anderer Stock"], "A", "4. Stock: Mobiltelefone."),
    mc("7 Deine Mutter liest gern und du möchtest ihr etwas Passendes kaufen.", ["3. Stock", "1. Stock", "anderer Stock"], "B", "1. Stock: Bücher."),
    mc("8 Du suchst einen guten Rotwein für deinen Onkel.", ["3. Stock", "4. Stock", "anderer Stock"], "C", "5. Stock: Alkohol und Getränke → anderer Stock."),
    mc("9 Du interessierst dich für Computerspiele.", ["5. Stock", "4. Stock", "anderer Stock"], "B", "4. Stock: PC-Spiele."),
    mc("10 Tante Luise hat nächste Woche Geburtstag und du möchtest ihr ein Parfüm schenken.", ["Erdgeschoss", "3. Stock", "anderer Stock"], "B",
       "3. Stock: Parfümerie und Kosmetik."),
]
TEXT_T3 = (
    "Von: Inge · An: Matilda · Betreff: Motorroller\n\nHi Matilda,\nwie geht es dir? Mir geht es eigentlich ganz gut. In der Schule bekomme ich in letzter "
    "Zeit sehr gute Noten. Das freut mich natürlich sehr. In der letzten Mathearbeit habe ich sogar eine Eins bekommen! Du kannst dir vorstellen, dass "
    "mich das total glücklich gemacht hat.\n\nWas gibt es Neues bei dir? Geht es jetzt besser in Englisch, oder hast du immer noch Schwierigkeiten? Bei mir "
    "ist alles wie immer. Außer, dass ich einen Motorroller kaufen möchte. Du fragst dich sicher, wie ich das machen werde. Nun, ich spare schon seit zwei "
    "Jahren mein Taschengeld. Jetzt habe ich schon 1.500 Euro zusammen. Das reicht zwar für einen Motorroller, aber meine Eltern erlauben es mir leider "
    "nicht. Sie sagen die ganze Zeit: „Das ist zu gefährlich“ oder „Du bist noch zu jung dafür!“ Ich bin schon sechzehn und gefährlich ist es für die, die "
    "zu schnell oder unvorsichtig fahren. Ich bin doch immer vorsichtig! Mama und Papa können mich einfach nicht verstehen.\n\nEs wäre so praktisch für "
    "mich, damit zur Schule zu fahren. Dann müsste ich nicht jeden Morgen den Bus nehmen oder gefahren werden. Deshalb streiten wir uns zuletzt ziemlich "
    "oft. Wozu rätst du mir? Was soll ich tun? Ich hab doch das Geld und werde vorsichtig fahren. Aber „NEIN“, sie wollen mich einfach nicht verstehen!\n\n"
    "Schreib mir bitte bald!\nViele Grüße\nInge")
LESEN_T3 = [
    mc("11 Warum ist Inge froh?", ["Es geht ihr wieder besser.", "Sie bekommt in Mathematik immer die beste Note.",
                                   "Sie hat neulich im Mathe-Test eine „sehr gut“ bekommen."], "C", "„In der letzten Mathearbeit habe ich sogar eine Eins bekommen!“"),
    mc("12 Was wünscht sich Inge?", ["Gute Noten auch in Englisch.", "Einen Motorroller.", "Mehr Taschengeld."], "B", "„… dass ich einen Motorroller kaufen möchte.“"),
    mc("13 Was sagen die Eltern zu dem Wunsch von Inge?", ["Sie finden ihn gut.", "Sie finden ihn nicht gut.", "Die Eltern erlauben ihr alles."], "B",
       "„… aber meine Eltern erlauben es mir leider nicht.“"),
    mc("14 Wie geht Inge zur Schule?", ["Sie fährt mit dem Bus oder ihre Eltern bringen sie hin.", "Sie fährt mit dem Fahrrad.", "Sie geht immer zu Fuß."], "A",
       "„Dann müsste ich nicht jeden Morgen den Bus nehmen oder gefahren werden.“"),
    mc("15 Was passiert in letzter Zeit?", ["Inge streitet sich mit ihren Eltern.", "Inge ist sehr vorsichtig, wenn sie mit ihren Eltern spricht.",
                                            "Inge bekommt kein Taschengeld mehr."], "A", "„Deshalb streiten wir uns zuletzt ziemlich oft.“"),
]
TEXT_T4 = (
    "Elektronik für jeden Zweck – Alles, was du brauchst!\n\na) Auf dem Sofa bequem liegen … und fernsehen, allein, mit der Familie oder mit Freunden. "
    "Nichts macht mehr Spaß. Wir bieten alles rund um TV-Geräte: 3D-Fernseher, LED- & LCD-Fernseher, Curved-TVs, Plasma-Fernseher. Das Angebot ist "
    "riesig, die Preise sind niedrig.\n\nb) Haushalt & Wohnen: Waschmaschinen, Geschirrspüler, Staubsauger, Küchenmaschinen, Mikrowellen, "
    "Kaffeevollautomaten. Hier gibt es einfach alles für den Haushalt. Was Sie bei uns kaufen, liefern wir Ihnen kostenlos nach Hause. Geöffnet jeden "
    "Tag von 9 bis 21 Uhr, auch samstags.\n\nc) PCs und Zubehör: Einen Computer fürs Büro oder für zu Hause? Kein Problem, schaut einfach bei uns rein. "
    "Und aufgepasst! Diese Woche gibt es ganz tolle Sonderangebote. Erstklassige Geräte um 30% reduziert. PCs, Apple Mac, Mini-PCs, alles, was die "
    "Arbeit leichter macht.\n\nd) Für kleine und große Kinder: Von Sport über Strategie bis Action, von der Sony Playstation bis hin zur Microsoft Xbox, "
    "mit dem richtigen Gerät macht Spielen viel mehr Spaß. Bei uns findest du, was du brauchst – und alles mit Zwei-Jahres-Garantie.\n\ne) "
    "Mobiltelefone: Willst du dir die neuesten Modelle ansehen? Oder suchst du vielleicht ein billiges gebrauchtes Gerät? Bei uns findest du alle Marken "
    "und alle Modelle, egal ob Smartphones, Apple iPhones oder Seniorenhandys. Günstige Tarife für unbegrenztes Telefonieren, Fotografieren und Simsen.\n\n"
    "f) Super klein, super leicht, super gut! Wenn du deinen Rechner überall mitnehmen willst, wenn du nicht so viel Platz in deiner Tasche hast, dann "
    "solltest du keinen PC kaufen, sondern einen Laptop oder ein Tablet. Wir haben alle Marken, die keine Wünsche offen lassen.\n\nBeispiel: 0 Luisa sieht "
    "zu Haus sehr gern fern. → a")
LESEN_T4 = [match(
    "Welche Anzeige passt zu welcher Person? (Für eine Aufgabe gibt es keine Lösung: X)",
    ["16 Max möchte ein neues Handy kaufen.", "17 Helena hört gern Musik, wenn sie joggt.", "18 Theo möchte ein Tablet kaufen.",
     "19 Victoria möchte einen Heimcomputer kaufen.", "20 Rafael möchte eine Spielkonsole für seinen jüngeren Bruder kaufen."],
    ["Anzeige b) Haushalt & Wohnen", "Anzeige c) PCs und Zubehör", "Anzeige d) Für kleine und große Kinder", "Anzeige e) Mobiltelefone",
     "Anzeige f) Super klein, super leicht, super gut!", "X – keine passende Anzeige"],
    {"1": "D", "2": "F", "3": "E", "4": "B", "5": "C"}, points=5,
    explanation="16 → e (Mobiltelefone), 17 → X (keine Anzeige für Musik beim Joggen), 18 → f (Laptop oder Tablet), 19 → c (Computer für zu Hause), "
                "20 → d (Playstation, Xbox). Anzeige b bleibt übrig.")]

# ---------- Hören Teil 1-4 (no key in the book) ----------
HOEREN_T1 = [mc_pending(q, o) for q, o in [
    ("1 Was für eine Frisur hätte Werner gern?", ["Eine Langhaarfrisur.", "Eine Kurzhaarfrisur.", "Eine mittellange Frisur."]),
    ("2 Mit welchem Familienmitglied versteht sich Karolin am besten?", ["Mit ihrem Vater.", "Mit ihrer Mutter.", "Mit ihren Geschwistern."]),
    ("3 Welche Jahreszeit findet Kerstin sehr angenehm?", ["Den Sommer.", "Den Frühling.", "Den Winter."]),
    ("4 Wie hat Bayern München gegen Atletico Madrid gespielt?", ["Bayern München hat 1:2 verloren.", "Bayern München hat 1:0 gewonnen.",
                                                                  "Bayern München hat 2:1 gewonnen."]),
    ("5 Wie viel kosten heute die Jeanshosen?", ["70 Euro.", "17 Euro.", "25 Euro."])]]
_BILDER = ["b) Spielzeugsoldaten", "c) Tischdecke", "d) Bausteine (Lego)", "e) Mofa", "f) Puppen", "g) Fahrrad", "h) Ananas", "i) Kiste mit Äpfeln"]
HOEREN_T2 = [gap("Was hat die Person auf dem Flohmarkt mitgebracht und verkauft? (Beispiel: 0 Anton → a)", f"{name}: [[1]]",
                 {"1": {"accepted": [], "options": _BILDER}})
             for name in ("6 Anne", "7 Olaf", "8 Harry", "9 Nicki", "10 Martin")]
HOEREN_T3 = [mc_pending(q, o) for q, o in [
    ("11 Mit wem hat sich Lisa gestritten?", ["a) mit der Frau (Bild a)", "b) mit dem Mann im gelben T-Shirt (Bild b)", "c) mit dem Jungen im grünen T-Shirt (Bild c)"]),
    ("12 Was möchte Lothar kaufen?", ["a) Tennisschuhe", "b) einen Tennisschläger", "c) Tennisbälle"]),
    ("13 Was zieht Eva zu der Jeanshose an?", ["a) ein T-Shirt", "b) eine Bluse", "c) ein Top"]),
    ("14 Was für ein Geburtstagsgeschenk bekommt Mark von Ivonne?", ["a) einen Basketball", "b) ein Computerspiel", "c) ein Buch"]),
    ("15 Wie verkleidet sich Rolf zum Karneval?", ["a) als Cowboy", "b) als Arzt", "c) als Pirat"])]]
HOEREN_T4 = [{"type": "true_false", "question": q, "options": ["Ja", "Nein"], "points": 1, "passage": 1} for q in [
    "16 Am „Europa-Camp“ können Jugendliche teilnehmen, die 14 Jahre oder älter sind.", "17 Ralf hat Ferien im „Europa-Camp“ in Spanien gemacht.",
    "18 Jeden Tag hatte er zwei Stunden Unterricht.", "19 Feriencamps gibt es in den Monaten Juni und Juli.",
    "20 Für die Arbeit im Feriencamp bekommt man ein kleines Taschengeld."]]

VARIANTEN = {
    "Variante 1": ["lernen", "der Kurs", "die Aufgabe", "das Lehrbuch", "der Test", "die Hausaufgaben"],
    "Variante 2": ["der Lehrer", "erklären", "sich erinnern", "die Sprache", "das Wörterbuch", "verbessern"],
    "Variante 3": ["die Schule", "die Prüfung", "die Note", "die Klassenarbeit", "die Wiederholung", "bestehen"],
    "Variante 4": ["die Weiterbildung", "der Kursleiter", "das Seminar", "teilnehmen", "sich anmelden", "das Zertifikat"],
    "Variante 5": ["die Universität", "die Ausbildung", "das Praktikum", "die Prüfung bestehen", "der Beruf", "die Karriere"],
}
WORTSCHATZ_HTML = (
    "<h3>Wort zu Wort Wortschatzmethode — Lernen und Weiterbildung A2</h3>"
    + "".join(f"<h4>{k}</h4>" + ul(v) for k, v in VARIANTEN.items())
    + "<p>Formulieren Sie einen Text mit den Wörtern einer Variante (Aufgabe im Bereich Schreiben).</p>"
)


def _hoeren(n: int, title: str, page: int, instruction: str, questions: list[dict]) -> dict:
    return base(L, "hoeren", n, title, page=page, audio_file=AUDIO[f"vizu-a2-l10-hoeren-{n:02d}"], key_pending=True, instruction=instruction,
                questions=questions, metadata={"note": "Kitobda kalit va transkript yo'q — admin audioni tinglab javoblarni belgilaydi."})


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: A2 10. Unterricht", source="vizu", page=104, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Welche Möglichkeiten gibt es in Deutschland zum Studium?", page=105,
             prompt="Welche Möglichkeiten gibt es in Deutschland zum Studium?",
             questions=["Universität", "Fachhochschule", "Duales Studium"], min_duration=20, max_duration=120,
             metadata={"book_answers": [
                 "Man kann an einer Universität studieren. Dort gibt es viele Studiengänge und man kann einen Bachelor oder Master machen.",
                 "Man kann an einer Fachhochschule studieren. Dort ist das Studium praxisnah und bereitet gut auf den Beruf vor.",
                 "Man kann ein duales Studium machen. Dabei verbindet man das Studium an einer Hochschule mit einer Ausbildung in einem Unternehmen."]}),
        base(L, "grammatik", 1, "Grammatik: Futur I und Futur II", page="106-107", rules=[{"title": "Futur I und Futur II", "html": GRAMMAR_HTML}],
             exercises=[exercise("Futur I: Ordne die Wörter und bilde Sätze", FUTUR_I, "Ordne die Wörter und bilde Sätze im Futur I."),
                        exercise("Futur II: Ordne die Wörter und bilde Sätze", FUTUR_II, "Ordne die Wörter und bilde Sätze im Futur II.")]),
        base(L, "lesen", 1, "Lesen Teil 1: Tolle Sehenswürdigkeiten", page="108-109",
             instruction="Du liest in einer Zeitung diesen Text. Wähle für die Aufgaben 1 bis 5 die richtige Lösung a, b oder c. (7–8 Minuten)",
             passages=[{"title": "Tolle Sehenswürdigkeiten", "text": TEXT_T1}], questions=LESEN_T1, max_score=5),
        base(L, "lesen", 2, "Lesen Teil 2: Informationstafel im „KaDeWe“", page="110-111",
             instruction="Du bist im Einkaufszentrum „KaDeWe“ in Berlin. In welchen Stock musst du gehen? Wähle a, b oder c. (Beispiel: Hemd für den Vater → 2. Stock)",
             passages=[{"title": "Im „KaDeWe“ finden Sie alles, was Sie brauchen!", "text": TEXT_T2}], questions=LESEN_T2, max_score=5),
        base(L, "lesen", 3, "Lesen Teil 3: E-Mail von Inge", page="112-113",
             instruction="Du liest eine E-Mail. Wähle für die Aufgaben 11 bis 15 die richtige Lösung a, b oder c.",
             passages=[{"title": "E-Mail: Motorroller", "text": TEXT_T3}], questions=LESEN_T3, max_score=5),
        base(L, "lesen", 4, "Lesen Teil 4: Elektronik für jeden Zweck", page="114-115",
             instruction="Sechs Jugendliche suchen im Internet nach Multimedia-Geräten. Welche Anzeige passt zu welcher Person? Für eine Aufgabe gibt es keine Lösung.",
             passages=[{"title": "Elektronik für jeden Zweck – Alles, was du brauchst!", "text": TEXT_T4}], questions=LESEN_T4, max_score=5),
        _hoeren(1, "Hören Teil 1: Fünf kurze Texte", 116, "Du hörst fünf kurze Texte. Du hörst jeden Text zweimal. Wähle für die Aufgaben 1 bis 5 a, b oder c.",
                HOEREN_T1),
        _hoeren(2, "Hören Teil 2: Flohmarkt", 117, "Du hörst ein Gespräch einmal. Wähle für die Aufgaben 6 bis 10 ein passendes Bild aus a bis i (Bild im Abschnitt). "
                                                  "Wähle jeden Buchstaben nur einmal. Ein Bild bleibt übrig.", HOEREN_T2),
        _hoeren(3, "Hören Teil 3: Fünf kurze Gespräche", 118, "Du hörst fünf kurze Gespräche. Du hörst jeden Text einmal. Wähle für die Aufgaben 11 bis 15 a, b "
                                                              "oder c (Bilder im Abschnitt).", HOEREN_T3),
        _hoeren(4, "Hören Teil 4: Interview — Europa-Camp", 119, "Du hörst ein Interview. Du hörst den Text zweimal. Wähle für die Aufgaben 16 bis 20 „Ja“ oder "
                                                                 "„Nein“.", HOEREN_T4),
        base(L, "schreiben", 1, "Schreiben Teil 1: SMS an Marko", page=120, task_type="message",
             prompt="Du bist auf dem Fußballplatz und schreibst deinem Freund Marko eine SMS.\n• Erzähl ihm, wo du bist.\n• Schreib ihm, mit wem du bist.\n"
                    "• Sag ihm, was ihr heute macht.\n• Schreib, warum Fußball deine Lieblingssportart ist.\n\nWichtig: Schreib 20–30 Wörter. Schreib eine SMS / "
                    "informellen Text. Vergiss nicht: Anrede und Gruß.",
             audience="Freund Marko (informell)", min_words=20, max_words=40, time_limit=10),
        base(L, "schreiben", 3, "Schreiben Teil 2: E-Mail an Herrn Müller", page=121, task_type="email",
             prompt="Dein Nachbar, Herr Müller, lädt dich am Samstag zu seinem Geburtstag ein. Schreib Herrn Müller eine E-Mail.\n• Bedanke dich und sage zu.\n"
                    "• Frage nach der Uhrzeit.\n• Sage, was du mitbringen könntest.\n\nWichtig: Schreib 30–40 Wörter. Schreib zu allen drei Punkten. Schreib "
                    "deutlich und freundlich. Achte auf die Reihenfolge. Überprüfe deine E-Mail am Ende.",
             audience="Nachbar Herr Müller (formell)", min_words=30, max_words=50, time_limit=15),
        base(L, "schreiben", 4, "Wortschatz-Aufgabe: Wort zu Wort Wortschatzmethode (Lernen und Weiterbildung)", page=124, task_type="description",
             prompt="Formulieren Sie mit den Wörtern einer Variante einen Text.\n\n" + "\n".join(f"{k}: {', '.join(v)}" for k, v in VARIANTEN.items()),
             min_words=40, max_words=200, time_limit=25),
        base(L, "sprechen", 1, "Sprechen Teil 1: Fragen zur Person", page=122, topic="Fragen zur Person", response_type="dialog",
             prompt="Du nimmst vier Karten und stellst mit diesen Karten vier Fragen. Dein Partner / deine Partnerin antwortet. Stelle die vier Fragen und "
                    "beantworte sie auch selbst.",
             questions=["Kandidat 1: Alter?", "Kandidat 1: Großeltern?", "Kandidat 1: Lieblingsfach?", "Kandidat 1: Tanzen?", "Kandidat 2: Geschwister?",
                        "Kandidat 2: Schwimmen?", "Kandidat 2: Mathematik oder Sprachen?", "Kandidat 2: Geburtstag?"],
             min_duration=30, max_duration=150, speech_goal="Zu jedem Stichwort eine korrekte Frage stellen und beantworten (Wie alt …? Hast du …?).",
             keywords=["Wie alt", "Hast du", "Was ist dein", "Wann"]),
        base(L, "sprechen", 2, "Sprechen Teil 2: Von sich erzählen", page=123, topic="Von sich erzählen",
             prompt="Du bekommst eine Karte und erzählst etwas über dein Leben. Aufgabenkarte A: Was machst du oft abends? Aufgabenkarte B: Was ist dein Lieblingsessen?",
             questions=["Karte A: Abendessen?", "Karte A: mit Freunden ausgehen?", "Karte A: fernsehen, diskutieren?", "Karte A: Computer?",
                        "Karte B: Welches, warum?", "Karte B: Was isst du auch gern?", "Karte B: Wer kocht es, wie oft?", "Karte B: Restaurant?"],
             response_type="monolog", min_duration=45, max_duration=150, speech_goal="Zu einer Aufgabenkarte zusammenhängend von sich erzählen.",
             keywords=["abends", "oft", "gern", "Lieblingsessen", "weil"]),
        base(L, "kompetenz", 3, "Wortschatz: Lernen und Weiterbildung (Wortschatzmethode)", page=124, competency="WORTSCHATZ", html=WORTSCHATZ_HTML,
             metadata={"note": "Kitobda tarjima berilmagan — so'z ro'yxati to'qib chiqarilmadi, matn sifatida ko'rsatiladi."}),
        base(L, "yakuniy", 1, "Abschlusstest: A2 10. Unterricht", source="vizu",
             instruction="Futur I / II va dars matnlari bo'yicha yakuniy test (dars materiali asosida).",
             questions=[
                 mc("Futur I: Ich ___ dich morgen anrufen.", ["werde", "wurde", "habe"], "A"),
                 mc("Futur II: Ich werde die Aufgabe bis morgen ___.", ["erledigt haben", "erledigen", "erledigt"], "A"),
                 mc("David wird um 23 Uhr zu Hause ___.", ["angekommen sein", "angekommen haben", "ankommen sein"], "A", "ankommen → sein."),
                 mc("Wofür benutzt man Futur II?", ["für abgeschlossene Ereignisse in der Zukunft", "für Pläne", "für die Vergangenheit"], "A"),
                 mc("Wie alt dürfen die Teilnehmer beim Fotowettbewerb höchstens sein?", ["18 Jahre", "16 Jahre", "20 Jahre"], "A", "Lesen Teil 1."),
                 mc("Was möchte Inge kaufen?", ["einen Motorroller", "ein Fahrrad", "ein Handy"], "A", "Lesen Teil 3."),
                 tf("Im „KaDeWe“ findet man Bücher im 1. Stock.", True, "Lesen Teil 2."),
                 mc("Wir ___ bald nach Spanien fliegen.", ["werden", "wird", "werdet"], "A"),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: A2 10. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
