"""A2 12. Unterricht — Kultur, Tradition und Gesellschaft — Grammatik: Relativsätze (book pp. 147-163).

Prüfungsnah. Book: Frage p.148, Relativsätze p.149, Aufgaben (25 x Auswahl)
p.150, Lesen Teil 1-4 pp.151-154, Hören Teil 1-4 pp.155-158 (no transcript,
no key), Schreiben Teil 1 / 2 p.159, Sprechen Teil 1-3 pp.160-162,
Wortschatzmethode p.163.

Keys: "Vizu-Antworten A2" has none. Corrections (marked in the metadata):
the book's pronoun table mixes up the columns (Dativ feminin "die", Genitiv
plural "denen") — the correct table is shown. Aufgabe 20 ("Das Kind, ___ Ball
verloren hat" — dessen/dem/den) has no grammatically correct option and is
not imported. Lesen Teil 1: the printed text breaks off between the columns
(homework / internet part missing), questions 3 and 4 cannot be decided and
are not imported. Lesen Teil 4: Birgit (Sport) fits both ad a and ad f — not
imported. Hören waits for an admin (key_pending); Teil 2 / 3 pictures are
attached as book images. Audio: "A2 12.Unterricht Teil_1-4". Wortschatz:
word lists without translations — no word list is invented."""

from . import base, exercise, gap, html_table, intro_html, match, mc, mc_pending, summary_html, tf, ul

L = 12
LESSON_TITLE = "Kultur, Tradition und Gesellschaft"
LESSON_DESCRIPTION = "Thema: Kultur, Tradition und Gesellschaft · Grammatik: Relativsätze · Prüfungstraining A2"
AUDIO = {"vizu-a2-l12-hoeren-01": "A2 12.Unterricht Teil_1.m4a", "vizu-a2-l12-hoeren-02": "A2 12.Unterricht Teil_2.m4a",
         "vizu-a2-l12-hoeren-03": "A2 12.Unterricht Teil_3.m4a", "vizu-a2-l12-hoeren-04": "A2 12.Unterricht Teil_4.m4a"}
IMAGES = [("p156_hoeren_teil2.jpg", "HOEREN", "Hören Teil 2 — Was kommt in den Koffer? Bilder a bis i (Buch, S. 156)"),
          ("p157_hoeren_teil3.jpg", "HOEREN", "Hören Teil 3 — Bilder (Buch, S. 157)")]
RETIRED_IMAGE_TITLES: list[str] = []

EINFUEHRUNG_HTML = intro_html(
    12, "Kultur, Tradition und Gesellschaft", "Relativsätze",
    ["nisbiy olmoshlar bilan ergash gap tuzish: Das ist der Mann, der hier arbeitet.;",
     "der / die / das, den, dem, dessen / deren, denen shakllarini kelishik bo'yicha tanlash;",
     "predlog + nisbiy olmosh: Das ist der Kollege, mit dem ich zusammenarbeite."],
    ["an'analar jamiyat uchun nima uchun muhimligini aytasiz;",
     "gazeta matni, TV dasturi, e-mail va sayohat e'lonlarini tushunasiz;",
     "qisqa matnlar, suhbat va intervyuni tinglab tushunasiz;",
     "SMS va e-mail yozasiz, savol berasiz va kinoga borish vaqtini kelishasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(12, [
    "<strong>Relativsatz:</strong> beschreibt ein Nomen näher, beginnt mit einem Relativpronomen, ist ein Nebensatz (Verb am Ende).",
    "<strong>Nominativ:</strong> der / die / das / die · <strong>Akkusativ:</strong> den / die / das / die · <strong>Dativ:</strong> dem / der / dem / denen · "
    "<strong>Genitiv:</strong> dessen / deren / dessen / deren",
    "<strong>Mit Präposition:</strong> Das ist der Kollege, mit dem ich zusammenarbeite. · Das ist das Restaurant, in dem wir gegessen haben.",
    "<strong>wo / als:</strong> Sie sucht das Haus, wo sie früher gewohnt hat. · Ich war glücklich, als ich studiert habe.",
])

GRAMMAR_HTML = (
    "<h3>Relativsätze (A2)</h3>"
    "<h4>Was ist ein Relativsatz?</h4><ul><li>Ein Relativsatz beschreibt ein Nomen näher.</li><li>Er fängt mit einem Relativpronomen an.</li>"
    "<li>Ein Relativsatz ist ein Nebensatz: Das Verb steht am Ende.</li></ul>"
    "<h4>Struktur</h4><p>Hauptsatz + …, Relativpronomen + Nebensatz (Verb am Ende)</p>"
    + html_table(["", "Nominativ", "Akkusativ", "Dativ", "Genitiv"],
                 [["Maskulin", "der", "den", "dem", "dessen"], ["Feminin", "die", "die", "der", "deren"], ["Neutrum", "das", "das", "dem", "dessen"],
                  ["Plural", "die", "die", "denen", "deren"]])
    + "<p><em>Hinweis: Die Tabelle im Buch hat die Spalten vertauscht (z. B. Dativ feminin „die“, Genitiv Plural „denen“) — hier die richtigen Formen.</em></p>"
    "<h4>Fragewörter: wer, wo, wann</h4><ul><li>Ich kenne jemanden, der sehr freundlich ist.</li><li>Sie sucht das Haus, wo sie früher gewohnt hat.</li>"
    "<li>Ich war zu einer Zeit glücklich, als ich studiert habe.</li></ul>"
    "<h4>Beispiele</h4><ul><li>Da ist der Hund, den wir gefunden haben.</li><li>Ich kenne das Mädchen, das nebenan wohnt.</li>"
    "<li>Das ist ein schöner Park, wo du spazieren gehen kannst.</li><li>Das ist der Lehrer, dem ich ein Buch gegeben habe.</li>"
    "<li>Das ist eine Stadt, die viele Touristen besuchen.</li><li>Meine Schwester, deren Auto kaputt ist, kann nicht kommen.</li>"
    "<li>Das ist das Restaurant, in dem wir gestern gegessen haben.</li></ul>"
    "<h4>Weitere Strukturen</h4><ul><li>(Nomen), + Präposition + Relativpronomen + … : Das ist der Kollege, <strong>mit dem</strong> ich zusammenarbeite.</li>"
    "<li>(Nomen), + Genitiv: Das ist der Kollege, <strong>dessen</strong> Büro sehr groß ist.</li></ul>"
)

_REL = [  # (n, sentence, options as printed, answer, explanation)
    (1, "Das ist der Mann, ___ hier arbeitet.", ["der", "den", "dem"], "A", "Nominativ maskulin: der."),
    (2, "Ich habe ein Buch, ___ sehr interessant ist.", ["das", "dem", "den"], "A", "Nominativ neutrum: das."),
    (3, "Die Frau, ___ ich gestern gesehen habe, ist meine Lehrerin.", ["die", "der", "den"], "A", "Akkusativ feminin: die."),
    (4, "Das Kind, mit ___ ich spiele, ist sehr nett.", ["dem", "den", "das"], "A", "mit + Dativ neutrum: dem."),
    (5, "Der Schüler, ___ Hausaufgaben fehlen, ist krank.", ["dessen", "dem", "den"], "A", "Genitiv maskulin: dessen."),
    (6, "Die Tasche, ___ auf dem Tisch liegt, ist neu.", ["die", "der", "das"], "A", "Nominativ feminin: die."),
    (7, "Der Lehrer, ___ wir danken, ist sehr freundlich.", ["dem", "den", "der"], "A", "danken + Dativ: dem."),
    (8, "Das ist der Hund, ___ ich jeden Tag sehe.", ["der", "den", "dem"], "B", "Akkusativ maskulin: den."),
    (9, "Ich kenne die Frau, ___ Sohn Arzt ist.", ["deren", "die", "den"], "A", "Genitiv feminin: deren."),
    (10, "Das Auto, ___ vor dem Haus steht, ist teuer.", ["das", "dem", "den"], "A", "Nominativ neutrum: das."),
    (11, "Der Mann, mit ___ ich gesprochen habe, ist nett.", ["dem", "den", "der"], "A", "mit + Dativ maskulin: dem."),
    (12, "Die Kinder, ___ im Garten spielen, sind laut.", ["die", "denen", "den"], "A", "Nominativ Plural: die."),
    (13, "Das Mädchen, ___ ich helfe, ist dankbar.", ["dem", "das", "den"], "A", "helfen + Dativ: dem."),
    (14, "Der Kollege, ___ Büro neu ist, kommt aus Spanien.", ["dessen", "dem", "den"], "A", "Genitiv maskulin: dessen."),
    (15, "Ich habe einen Freund, ___ ich sehr vertraue.", ["dem", "den", "der"], "A", "vertrauen + Dativ: dem."),
    (16, "Die Stadt, in ___ ich wohne, ist groß.", ["der", "die", "den"], "A", "in (Wo?) + Dativ feminin: der."),
    (17, "Das ist das Haus, ___ Fenster kaputt sind.", ["dessen", "dem", "den"], "A", "Genitiv neutrum: dessen."),
    (18, "Der Lehrer, ___ wir sehen, ist streng.", ["den", "dem", "der"], "A", "Akkusativ maskulin: den."),
    (19, "Die Frau, ___ ich ein Geschenk gebe, ist meine Mutter.", ["der", "die", "den"], "A", "geben (wem?) + Dativ feminin: der."),
    (21, "Der Student, ___ ich gestern getroffen habe, kommt aus Italien.", ["den", "dem", "der"], "A", "Akkusativ maskulin: den."),
    (22, "Die Frau, ___ wir helfen, ist sehr freundlich.", ["der", "die", "den"], "A", "helfen + Dativ feminin: der."),
    (23, "Das Buch, ___ ich lese, ist spannend.", ["das", "dem", "den"], "A", "Akkusativ neutrum: das."),
    (24, "Der Mann, ___ Auto vor der Tür steht, ist mein Nachbar.", ["dessen", "dem", "den"], "A", "Genitiv maskulin: dessen."),
    (25, "Die Kinder, mit ___ wir spielen, sind sehr aktiv.", ["denen", "die", "den"], "A", "mit + Dativ Plural: denen."),
]
RELATIV = [mc(f"{n}. {s}", o, a, e) for n, s, o, a, e in _REL]

TEXT_T1 = (
    "„Computer und Freunde sind mir wichtig“\n\nPeter wohnt in Bremen, ist Schüler und geht in die 7. Klasse des Gymnasiums. Seine Lieblingsfächer sind Mathe "
    "und Englisch. Geschwister hat er keine. In seiner Freizeit gefällt es ihm, mit seinen Freunden, aber auch an seinem Computer zu spielen. Er hat nämlich "
    "seit der 5. Klasse einen eigenen PC. Das Geld für den Computer hat er selber gespart.\n\nWenn man seine Eltern fragt, dann hört man von ihnen nicht "
    "selten, dass sie es lieber sehen, wenn sich ihr Sohn nicht so viel am Computer beschäftigt, denn sie haben große Angst davor, dass er in der Schule "
    "schlechter wird. Peter ist aber in der Schule ganz gut und seine Lehrer sagen, dass er im Unterricht immer mitmacht.\n\n[…] natürlich kein Geld dafür "
    "ausgeben muss. Außerdem machen das auch meine Freunde!“ meint er.\n\nAls er noch in den Kindergarten ging, wollte er Pilot werden. Peter kann sich "
    "jetzt aber gut vorstellen Informatik zu studieren, weil er sehr gern am Computer sitzt und neue Sachen lernt.")
LESEN_T1 = [
    mc("1 Peter gefällt es, …", ["nur am Computer zu spielen.", "mit seinen Freunden zu spielen.",
                                  "sowohl am Computer als auch mit seinen Freunden zu spielen."], "C",
       "„In seiner Freizeit gefällt es ihm, mit seinen Freunden, aber auch an seinem Computer zu spielen.“"),
    mc("2 Peters Eltern möchten, …", ["dass sich Peter am Computer beschäftigt.", "dass Peter keine Angst vor dem Computer hat.",
                                      "dass er nicht zu lange am Computer sitzt."], "C", "„… dass sie es lieber sehen, wenn sich ihr Sohn nicht so viel am Computer beschäftigt …“"),
    mc("5 Peter möchte …", ["Informatik studieren.", "Pilot werden.", "als Kindergärtner arbeiten."], "A",
       "„Peter kann sich jetzt aber gut vorstellen Informatik zu studieren …“"),
]
TEXT_T2 = (
    "SAT 1 — Abendprogramm\n\n19:00 Uhr Mit den Noten spielen: Heute sehen Sie, wie man verschiedene Musikinstrumente spielen lernt. Neben Gitarre und "
    "Trompete stellen wir Ihnen auch das Klavier vor. Nichts macht mehr Spaß als Musik.\n19:30 Uhr Kein Problem für Flink: In dieser Episode ist Kommissar "
    "Flink hinter zwei Personen her, die in einem Park einen Mann überfallen haben. Wird es ihm gelingen, den Fall zu lösen?\n20:00 Uhr Lecker – Schmecker: "
    "Heute lernen Sie, wie man in sehr kurzer Zeit ein leckeres Essen kocht und wie man einen Apfelkuchen macht. Alle Rezepte der Sendung können Sie online "
    "downloaden.\n20:30 Uhr Der Spaßvogel: Der neue, nette Assistent von Professor Gruber ist immer zu Späßen aufgelegt. Ob das gut gehen wird? Wenn Sie Lust "
    "zum Lachen haben, dann müssen Sie sich diese Komödie unbedingt anschauen.\n21:00 Uhr Aktuelles vom Tage: Aktuelle Nachrichten nicht nur aus "
    "Deutschland, sondern auch aus dem Ausland. Heute im Studio: Bundesarbeitsminister Schaff im Interview über Maßnahmen zur Bekämpfung der "
    "Arbeitslosigkeit und mögliche Änderungen in der Sozialversicherung.\n21:30 Uhr Tor!: In der heutigen Sportschau informieren wir Sie über die Tennis-, "
    "Handball- und Fußballergebnisse. Außerdem blenden wir uns live in das Spiel von Borussia Dortmund gegen den Hamburger SV ein.")
LESEN_T2 = [
    mc("6 Du möchtest mit deinen Freunden einen lustigen Film sehen.", ["Lecker – Schmecker", "Aktuelles vom Tage", "andere Sendung"], "C",
       "Die Komödie „Der Spaßvogel“ (20:30 Uhr) steht nicht unter a / b → andere Sendung."),
    mc("7 Du möchtest wissen, was auf der Welt passiert.", ["Tor!", "Aktuelles vom Tage", "andere Sendung"], "B", "Aktuelle Nachrichten … auch aus dem Ausland."),
    mc("8 Du möchtest wissen, wie deine Fußballmannschaft gespielt hat.", ["Tor!", "Kein Problem für Flink", "andere Sendung"], "A", "Sportschau: Fußballergebnisse."),
    mc("9 Du spielst Klavier und möchtest eine passende Sendung sehen.", ["Der Spaßvogel", "Mit den Noten spielen", "andere Sendung"], "B",
       "„… stellen wir Ihnen auch das Klavier vor.“"),
    mc("10 Du möchtest wissen, wie man einen Kuchen backt.", ["Lecker – Schmecker", "Tor!", "andere Sendung"], "A", "„… und wie man einen Apfelkuchen macht.“"),
]
TEXT_T3 = (
    "Von: Nadine · An: Claudia · Betreff: Sommerferien\n\nLiebe Claudia,\nentschuldige bitte, dass ich mich erst heute melde, dabei gibt es so viel "
    "Interessantes zu berichten.\n\nIch möchte dir so gern über meine letzten Sommerferien erzählen. Jetzt sind wir schon drei Wochen wieder zu Hause und "
    "ich denke immer noch an die schöne Zeit, die ich mit meiner Familie in Griechenland verbracht habe.\n\nAm 1. August um 12:30 Uhr sind wir in Athen "
    "angekommen. Auf dem Flughafen waren sooo viele Menschen, voll beladen mit Koffern, Taschen, Kameras. Wir hatten zum Glück nicht so viel Gepäck. Mit "
    "einem Taxi sind wir ins Hotel gefahren, das außerhalb von Athen lag.\n\nUnser Hotelzimmer war groß, mit herrlichem Blick aufs Meer und auf die Inseln. "
    "Gleich am ersten Tag sind wir schwimmen gegangen. Das Wasser war schön warm und wir haben uns ein bisschen in die Sonne gelegt. Als es uns zu heiß "
    "wurde, gingen wir ins Hotel zurück.\n\nAn den anderen Tagen haben wir Sehenswürdigkeiten besichtigt und Souvenirs gekauft, jeden Tag was Neues. Für "
    "dich habe ich auch ein kleines Souvenir mitgebracht, das dir sicher gut gefallen wird.\n\nNatürlich haben wir auch die griechischen Spezialitäten "
    "probiert. Abends haben wir fast immer in Tavernen gegessen. Am besten hat uns „Souvlaki“ geschmeckt. Das ist gegrilltes Fleisch am Spieß. Aber auch "
    "die vielen bunten Salate waren lecker und überhaupt nicht teuer.\n\nDas waren fantastische Ferien! Nächstes Jahr wollen wir auf eine der vielen "
    "malerischen Inseln fahren.\n\nMelde dich!\nLiebe Grüße\nNadine")
LESEN_T3 = [
    mc("11 Nadine erzählt über …", ["die schöne Zeit zu Hause nach den Sommerferien.", "die Sommerferien, die sie letzten Sommer verbracht hat.",
                                    "die Sommerferien, die sie jetzt macht."], "B", "„Ich möchte dir … über meine letzten Sommerferien erzählen.“"),
    mc("12 Auf dem Flughafen …", ["hatten viele Menschen keine Koffer.", "waren sie kurz vor 12 Uhr.", "hatten sie wenig Gepäck."], "C",
       "„Wir hatten zum Glück nicht so viel Gepäck.“"),
    mc("13 Das Hotelzimmer …", ["war super, aber man konnte nicht aufs Meer sehen.", "hatte Blick aufs Meer.", "war zu heiß."], "B",
       "„… mit herrlichem Blick aufs Meer und auf die Inseln.“"),
    mc("14 Nadine hat …", ["viele Ausflüge gemacht.", "Sehenswürdigkeiten besichtigt.", "viele Souvenirs für ihre Freundin gekauft."], "B",
       "„An den anderen Tagen haben wir Sehenswürdigkeiten besichtigt …“"),
    mc("15 Die Familie hat …", ["nur griechische Spezialitäten probiert.", "gern Souvlaki gegessen.", "immer in derselben Taverne gegessen."], "B",
       "„Am besten hat uns „Souvlaki“ geschmeckt.“"),
]
TEXT_T4 = (
    "www.weltreisen.de — Wir bringen Sie überall hin!\n\na Aktivurlaub in Spanien – mal was anderes. In unserem 5-Sterne-Hotel in der Nähe von Barcelona "
    "können Sie einen unvergesslichen Urlaub verbringen, mit Schwimmen im Pool und viel Sport – von Fußball und Basketball bis Tennis oder Golf. Schauen Sie "
    "unter www.sportcatal.es nach und nutzen Sie unser Superangebot. Reservieren Sie jetzt!\n\nb Unzählige Sehenswürdigkeiten warten auf Sie. Wenn Sie nicht "
    "nur das Colosseum und den Petersdom besuchen wollen, dann kommen Sie zu uns, und wir suchen für Sie das passende Angebot zu einem besonders günstigen "
    "Preis aus. Reisebüro der Jugend – Öffnungszeiten: Montag–Freitag: 8:00 - 14:00 Uhr\n\nc Eine Sprachreise nach Deutschland lohnt sich. Wenn Sie ein "
    "bisschen Deutsch sprechen und noch besser Deutsch sprechen wollen, dann organisieren wir für Sie eine Sprachreise nach Deutschland. Preiswerte "
    "Unterkunft in Pensionen oder Gastfamilien, Unterricht durch muttersprachliche Lehrer.\n\nd Die Natur genießen. Ein sehr schönes Reiseziel sind die "
    "Berge. Im Dezember liegt viel Schnee, und Sie können die Alpen aus der Nähe sehen. Rufen Sie uns an! Wir bieten täglich supergünstige Schnäppchen an. "
    "Tel.: 0846/84736\n\ne Endloses Baden. Sommerzeit, Badezeit!!! Wollen Sie schwimmen und die Sonne genießen? Dann sollten Sie früh buchen. Wir haben "
    "Hotelzimmer und Ferienwohnungen in allen Preisklassen im Angebot. Unsere Adresse lautet: Brandenburger Straße 6, 70173 Stuttgart\n\nf Sport mal "
    "anders! Extremsport: der neue Trend, der absolute Liebling – besonders unter jungen Leuten. Probieren Sie in Ihrem Urlaub die eine oder andere Sportart "
    "aus, zum Beispiel Bungee-Jumping oder Paragliding. Sie werden nicht allein sein, sondern immer zusammen mit begeisterten Sportfreunden trainieren. "
    "Anklicken: www.sportextrem.com")
LESEN_T4 = [match(
    "Welche Anzeige passt zu welcher Person? (keine passende Anzeige: X)",
    ["Ulrike möchte im Winter in die Berge fahren.", "Markus möchte mit seiner Familie in den Norden fahren.", "Jörg will dieses Jahr seine Ferien am Meer verbringen.",
     "Klaus möchte nach Italien fahren und die vielen Sehenswürdigkeiten besichtigen.", "Jasmin möchte in den Ferien ihre Deutschkenntnisse verbessern."],
    ["Anzeige b) Unzählige Sehenswürdigkeiten", "Anzeige c) Sprachreise nach Deutschland", "Anzeige d) Die Natur genießen", "Anzeige e) Endloses Baden",
     "X – keine passende Anzeige"],
    {"1": "C", "2": "E", "3": "D", "4": "A", "5": "B"}, points=5,
    explanation="Ulrike → d (Berge, Schnee im Dezember), Markus → X (keine Anzeige für den Norden), Jörg → e (Baden), Klaus → b (Colosseum, Petersdom), "
                "Jasmin → c (Sprachreise).")]

HOEREN_T1 = [mc_pending(q, o) for q, o in [
    ("1 Wie ist das Zimmer von Anna?", ["Es ist alt und klein.", "Es ist neu und groß.", "Es ist hell und gemütlich."]),
    ("2 Welcher Tag ist heute?", ["Samstag.", "Sonntag.", "Montag."]), ("3 Wie viel kostet der Kugelschreiber?", ["2,20 Euro.", "0,90 Euro.", "2,90 Euro."]),
    ("4 Wen soll Markus abholen?", ["Seine Mutti.", "Seinen Bruder.", "Seinen Vater."]),
    ("5 Wie ist das Wetter im Norden?", ["Sonnig und warm.", "Zuerst Regen, dann Sonne.", "Es regnet."])]]
_KOFFER = ["a) Pullover", "b) Hemd", "c) Bikini", "d) Kleid", "e) Strandtasche", "f) CD", "g) T-Shirts", "i) Flip-Flops"]
HOEREN_T2 = [gap("Was kommt in den Koffer? Wähle das passende Bild (Beispiel: 0 Ralf → h kurze Jeans).", f"{name}: [[1]]",
                 {"1": {"accepted": [], "options": _KOFFER}}) for name in ("6 Erika", "7 Anna", "8 Markus", "9 Jürgen", "10 Udo")]
HOEREN_T3 = [mc_pending(q, o) for q, o in [
    ("11 Was möchte das Mädchen?", ["a) Apfelsaft (rote Flasche)", "b) Orangensaft", "c) Traubensaft"]),
    ("12 Wann schreibt Rainer die Mathearbeit?", ["a) Mittwoch, 9.", "b) Donnerstag, 10.", "c) Freitag, 11."]),
    ("13 Was nimmt der Junge?", ["a) Hustensaft", "b) Tee", "c) Tabletten aus dem Medizinschrank"]),
    ("14 Um wie viel Uhr gehen sie ins Kino?", ["a) 18:00", "b) 20:00", "c) 20:15"]),
    ("15 Was holt sich Hans von der Bäckerei?", ["a) Brötchen", "b) Baguette", "c) Kuchen"])]]
HOEREN_T4 = [{"type": "true_false", "question": q, "options": ["Ja", "Nein"], "points": 1, "passage": 1} for q in [
    "16 Sandra ist seit 12 Monaten in Italien.", "17 Sandra geht jetzt in die 8. Klasse.", "18 In Sandras Schule wird auf Englisch unterrichtet.",
    "19 Am Anfang hatte Sandra überhaupt keine Freunde.", "20 Das Essen, das Wetter und die Menschen in Italien sind toll, aber Sandras Vater verdient nicht viel."]]

VARIANTEN = {
    "Variante 1": ["das Fest", "die Tradition", "die Bräuche", "die Kultur", "die Gesellschaft", "die Werte"],
    "Variante 2": ["feiern", "bewahren", "weitergeben", "teilnehmen", "respektieren", "verbinden"],
    "Variante 3": ["die Familie", "die Gemeinschaft", "die Freundschaft", "die Nachbarn", "das Zusammenleben", "die Hilfe"],
    "Variante 4": ["die Vielfalt", "die Integration", "die Sprache", "die Identität", "die Unterschiede", "der Zusammenhalt"],
    "Variante 5": ["das Ehrenamt", "das Engagement", "die Verantwortung", "die Toleranz", "die Gleichberechtigung", "die Zukunft"],
}
WORTSCHATZ_HTML = ("<h3>Wort zu Wort Wortschatzmethode — Kultur, Tradition und Gesellschaft A2</h3>"
                   + "".join(f"<h4>{k}</h4>" + ul(v) for k, v in VARIANTEN.items())
                   + "<p>Formulieren Sie einen Text mit den Wörtern einer Variante (Aufgabe im Bereich Schreiben).</p>")


def _hoeren(n: int, title: str, page: int, instruction: str, questions: list[dict]) -> dict:
    return base(L, "hoeren", n, title, page=page, audio_file=AUDIO[f"vizu-a2-l12-hoeren-{n:02d}"], key_pending=True, instruction=instruction,
                questions=questions, metadata={"note": "Kitobda kalit va transkript yo'q — admin audioni tinglab javoblarni belgilaydi."})


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: A2 12. Unterricht", source="vizu", page=147, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Warum sind die Traditionen für eine Gesellschaft wichtig?", page=148,
             prompt="Warum sind die Traditionen für eine Gesellschaft wichtig?", min_duration=20, max_duration=120,
             metadata={"book_samples": [
                 "Traditionen verbinden die Menschen miteinander und schaffen ein Gefühl der Zugehörigkeit. Sie bewahren unsere Kultur und Werte und geben sie "
                 "an die nächste Generation weiter. Ohne Traditionen würden wir unsere Wurzeln verlieren.",
                 "Traditionen geben einer Gesellschaft Stabilität und Orientierung. Sie helfen uns, unsere Geschichte zu verstehen und aus der Vergangenheit zu "
                 "lernen. Außerdem machen sie Feste und Bräuche zu etwas Besonderem und bereichern unser Leben.",
                 "Ich denke, Traditionen fördern Respekt und Zusammenhalt in der Gesellschaft. Sie zeigen, wer wir sind, und stärken das Gemeinschaftsgefühl. "
                 "Natürlich können sich Traditionen auch verändern, aber ihr Kern bleibt wichtig."]}),
        base(L, "grammatik", 1, "Grammatik: Relativsätze", page="149-150", rules=[{"title": "Relativsätze (A2)", "html": GRAMMAR_HTML}],
             exercises=[exercise("Grammatik Aufgaben: Relativpronomen (24 von 25)", RELATIV,
                                 "Wähle das richtige Relativpronomen. (Aufgabe 20 ist im Buch fehlerhaft und wurde nicht übernommen.)")],
             metadata={"book_page": "149-150", "corrections": ["Relativpronomen-Tabelle korrigiert (Spalten im Buch vertauscht).",
                                                               "Aufgabe 20 „Das Kind, ___ Ball verloren hat“ — keine richtige Option, nicht übernommen."]}),
        base(L, "lesen", 1, "Lesen Teil 1: Computer und Freunde sind mir wichtig", page=151, instruction="Du liest einen Zeitungstext. Wähle a, b oder c.",
             passages=[{"title": "„Computer und Freunde sind mir wichtig“", "text": TEXT_T1}], questions=LESEN_T1, max_score=len(LESEN_T1),
             metadata={"note": "Kitobdagi matn ikki ustun orasida uzilgan — 3 va 4-savollarga javob matnda yo'q, olinmadi."}),
        base(L, "lesen", 2, "Lesen Teil 2: SAT 1 Abendprogramm", page=152,
             instruction="Du bist zu Hause und liest das Abendprogramm von SAT 1. Was schaust du dir an? Wähle a, b oder c.",
             passages=[{"title": "SAT 1 Abendprogramm", "text": TEXT_T2}], questions=LESEN_T2, max_score=5),
        base(L, "lesen", 3, "Lesen Teil 3: E-Mail von Nadine", page=153, instruction="Du liest eine E-Mail. Wähle für die Aufgaben 11 bis 15 a, b oder c.",
             passages=[{"title": "E-Mail: Sommerferien", "text": TEXT_T3}], questions=LESEN_T3, max_score=5),
        base(L, "lesen", 4, "Lesen Teil 4: Wir bringen Sie überall hin!", page=154,
             instruction="Sechs Jugendliche suchen im Internet nach Reisen. Welche Anzeige passt zu welcher Person?",
             passages=[{"title": "www.weltreisen.de", "text": TEXT_T4}], questions=LESEN_T4, max_score=5,
             metadata={"note": "Birgit (Sport) ga ikki e'lon (a va f) mos keladi — bir ma'noli emas, olinmadi."}),
        _hoeren(1, "Hören Teil 1: Fünf kurze Texte", 155, "Du hörst fünf kurze Texte. Du hörst jeden Text zweimal. Wähle a, b oder c.", HOEREN_T1),
        _hoeren(2, "Hören Teil 2: Was kommt in den Koffer?", 156, "Du hörst ein Gespräch einmal. Wähle für die Aufgaben 6 bis 10 ein passendes Bild (Bild im "
                                                                  "Abschnitt). Wähle jeden Buchstaben nur einmal.", HOEREN_T2),
        _hoeren(3, "Hören Teil 3: Fünf kurze Gespräche", 157, "Du hörst fünf kurze Gespräche einmal. Wähle a, b oder c (Bilder im Abschnitt).", HOEREN_T3),
        _hoeren(4, "Hören Teil 4: Interview mit Sandra", 158, "Du hörst ein Interview zweimal. Wähle „Ja“ oder „Nein“. (Beispiel: 0 Sandra ist Italienerin. → Nein)",
                HOEREN_T4),
        base(L, "schreiben", 1, "Schreiben Teil 1: SMS an Michael", page=159, task_type="message",
             prompt="Dein Freund Michael sendet dir eine SMS und lädt dich am kommenden Samstag um 10 Uhr zu einem Tennisspiel ein. Antworte Michael mit einer SMS.\n"
                    "• Entschuldige dich, dass du nicht kommen kannst.\n• Schreib warum.\n• Mach einen neuen Vorschlag (Tag und Uhrzeit) für euer Tennisspiel.\n\n"
                    "Schreib 20–30 Wörter. Schreib zu allen drei Punkten.",
             audience="Freund Michael (informell)", min_words=20, max_words=40, time_limit=10),
        base(L, "schreiben", 3, "Schreiben Teil 2: E-Mail an Herrn Stark", page=159, task_type="email",
             prompt="Der Vater von deinem Freund, Herr Stark, hat noch eine Karte für das Rockkonzert am Samstagabend und möchte sie dir schenken. Er weiß nämlich, "
                    "dass du ein großer Fan von „Rammstein“ bist. Schreib Herrn Stark eine E-Mail:\n• Bedanke dich und sage, dass du mitkommst.\n"
                    "• Informiere ihn, dass du nicht bis ganz spät auf dem Konzert bleiben kannst.\n• Frage nach der Uhrzeit fürs Treffen vor dem Konzert.\n\n"
                    "Schreib 30–40 Wörter. Schreib zu allen drei Punkten.",
             audience="Herr Stark (formell)", min_words=30, max_words=50, time_limit=15),
        base(L, "schreiben", 4, "Wortschatz-Aufgabe: Wort zu Wort Wortschatzmethode (Kultur, Tradition und Gesellschaft)", page=163, task_type="description",
             prompt="Formulieren Sie mit den Wörtern einer Variante einen Text.\n\n" + "\n".join(f"{k}: {', '.join(v)}" for k, v in VARIANTEN.items()),
             min_words=40, max_words=200, time_limit=25),
        base(L, "sprechen", 1, "Sprechen Teil 1: Fragen zur Person", page=160, topic="Fragen zur Person", response_type="dialog",
             prompt="Du nimmst vier Karten und stellst mit diesen Karten vier Fragen. Dein Partner / deine Partnerin antwortet.",
             questions=["Kandidat 1: Geschwister?", "Kandidat 1: Alter?", "Kandidat 1: Klasse?", "Kandidat 1: Fremdsprache?", "Kandidat 2: Hobby?",
                        "Kandidat 2: Lieblingsessen?", "Kandidat 2: Reisen?", "Kandidat 2: Freizeit?"],
             min_duration=30, max_duration=150, speech_goal="Zu jedem Stichwort eine korrekte Frage stellen und beantworten.",
             keywords=["Hast du", "Wie alt", "In welche Klasse", "Welche Sprache"]),
        base(L, "sprechen", 2, "Sprechen Teil 2: Von sich erzählen", page=161, topic="Von sich erzählen",
             prompt="Du bekommst eine Karte und erzählst etwas über dein Leben. Karte A: Möchtest du später studieren? Karte B: Was für Geschenke machst du?",
             questions=["Karte A: Bessere Chancen?", "Karte A: Was?", "Karte A: Inland oder Ausland?", "Karte A: nach dem Studium?", "Karte B: Preis?",
                        "Karte B: was?", "Karte B: wann?", "Karte B: für wen?"],
             response_type="monolog", min_duration=45, max_duration=150, speech_goal="Zu einer Aufgabenkarte zusammenhängend von sich erzählen.",
             keywords=["studieren", "weil", "Geschenk", "für"]),
        base(L, "sprechen", 3, "Sprechen Teil 3: Ins Kino gehen — einen Termin finden", page=162, topic="Einen Termin finden", response_type="dialog",
             prompt="Ihr wollt zusammen ins Kino gehen. Findet einen Termin.\n\nAufgabenblatt A: Mo Nachmittag Basketballtraining · Di Abend Englischunterricht · "
                    "Mi Abend Lieblingssendung im Fernsehen · Do Nachmittag mit Klaus für den Test lernen · Fr Nachmittag Oma besuchen · Sa Abend Annas "
                    "Geburtstagsparty · So Abend nichts tun!\nAufgabenblatt B: Mo Abend für den Mathe-Test lernen · Di Nachmittag neue Sportschuhe kaufen · "
                    "Mi Nachmittag Volleyballtraining · Do Abend Tante Gabi kommt · Fr Abend Marias Party · Sa Nachmittag Fahrrad reparieren · So Abend früh ins Bett!",
             questions=["Hast du am … Zeit?", "Am … kann ich nicht, weil …", "Wie wäre es mit …?", "Gut, dann gehen wir am … ins Kino."],
             min_duration=45, max_duration=180, speech_goal="Gemeinsam einen freien Termin aushandeln (Vorschlag, Ablehnung mit Grund, Zustimmung).",
             keywords=["Hast du Zeit", "am Nachmittag", "am Abend", "leider", "ins Kino"]),
        base(L, "kompetenz", 3, "Wortschatz: Kultur, Tradition und Gesellschaft (Wortschatzmethode)", page=163, competency="WORTSCHATZ", html=WORTSCHATZ_HTML,
             metadata={"note": "Kitobda tarjima berilmagan — so'z ro'yxati to'qib chiqarilmadi."}),
        base(L, "yakuniy", 1, "Abschlusstest: A2 12. Unterricht", source="vizu",
             instruction="Relativsätze va dars matnlari bo'yicha yakuniy test (dars materiali asosida).",
             questions=[
                 mc("Das ist die Frau, ___ ich geholfen habe.", ["der", "die", "den"], "A", "helfen + Dativ feminin."),
                 mc("Das ist der Film, ___ ich gestern gesehen habe.", ["den", "der", "dem"], "A", "Akkusativ maskulin."),
                 mc("Die Kinder, mit ___ ich spiele, sind nett.", ["denen", "die", "deren"], "A", "mit + Dativ Plural."),
                 mc("Ich kenne die Frau, ___ Sohn Arzt ist.", ["deren", "dessen", "die"], "A"),
                 mc("Wo steht das Verb im Relativsatz?", ["am Ende", "auf Position 2", "am Anfang"], "A"),
                 mc("Was möchte Peter später studieren?", ["Informatik", "Medizin", "Musik"], "A", "Lesen Teil 1."),
                 mc("Wo hat Nadine ihre Sommerferien verbracht?", ["in Griechenland", "in Italien", "in Spanien"], "A", "Lesen Teil 3."),
                 tf("Das Hotelzimmer von Nadine hatte Blick aufs Meer.", True, "Lesen Teil 3."),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: A2 12. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
