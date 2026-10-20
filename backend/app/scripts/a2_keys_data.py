"""Answer keys / verification notes of the A2 course with their source (see a2_keys.py).

Timestamps [m:ss] refer to the audio file of the task (the same file as on
the server, SHA-256 compared). "TR" = machine transcript of that file by two
models. "Blatt" = "Vizu-Antworten A2" (keys for some lessons only)."""

TR = "Audio-Transkript (Whisper large-v3 + medium)"
AUDIT = "VIZU-Audit 2026-10-21"


def one(answer: str) -> dict:
    """Key of a one-gap Lückentext / picture choice (dropdown option text)."""
    return {"1": [answer]}


def one_of(*answers: str) -> dict:
    """Key of a one-gap short answer with several accepted wordings."""
    return {"1": list(answers)}


# ============================================================ Hören
HOEREN: dict[str, dict] = {}

HOEREN["vizu-a2-l01-hoeren-01"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 1.Unterricht Hören.m4a“: Johann [0:08-0:32] „Mein Beruf ist Architekt, weil mein Vater auch "
                "Architekt war … als Kind … Häuser gezeichnet … Jetzt plane ich moderne Gebäude“; Julia [0:41-1:06] „Ärztin, weil ich schon als "
                "Kind Menschen helfen wollte … Puppen behandelt … Biologie sehr gemocht … arbeite ich im Krankenhaus“; Mikey [1:15-1:35] "
                "„Cristiano Ronaldo immer bewundert. Letztes Jahr … in einer Mannschaft trainiert. Jetzt trainiere ich hart und werde in "
                "Zukunft professionell Fußball spielen“. Bestehende Lösung (Blatt) bestätigt.",
    "keys": ["Weil sein Vater Architekt war", "Cristiano Ronaldo", "In einem Krankenhaus", "Er hat Häuser gezeichnet", "Menschen helfen",
             "Er wird professionell Fußball spielen", "Biologie", "Er plant moderne Gebäude", "Er hat in einer Mannschaft trainiert",
             "Weil sie schon als Kind helfen wollte", "Architekt", "Er trainiert hart"],
}

HOEREN["vizu-a2-l02-hoeren-01"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 2.Unterricht Hören.mp3“: Moderatorin eröffnet [0:00-0:42] und fragt „wie beeinflussen soziale "
                "Netzwerke unser Leben?“; Prof. Müller „arbeitet an der Universität München“ [0:22], „Für Studenten und Forscher … praktisch“, "
                "„Informationen und Nachrichten“, „zu viel Zeit online … weniger miteinander im echten Leben“ [0:43-1:10]; Frau Millner „Mutter "
                "von zwei Kindern“ [0:28], „Tipps über Schule, Gesundheit“, „zu Hause klare Regeln“ [1:11-1:41]; Moderatorin „ein wichtiger Teil "
                "unseres Lebens“ [1:46]. Bestehende Lösung bestätigt.",
    "keys": ["Professor Müller", "die Journalistin", "Professor Müller", "Frau Millner", "Professor Müller", "Frau Millner", "die Journalistin",
             "Frau Millner", "Professor Müller", "die Journalistin", "Professor Müller", "die Journalistin"],
}

HOEREN["vizu-a2-l03-hoeren-01"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2. 3.Unterricht Hören.mp3“: „Mein Name ist Dr. Martin Weber. Ich bin Arzt“ [0:11]; „bleiben Sie zuerst "
                "zu Hause und ruhen Sie sich aus … Gute Ruhe ist sehr wichtig“ [0:36-0:50]; „Trinken Sie Wasser oder warmen Tee“ [0:54]; „Essen Sie "
                "leichte und gesunde Nahrung“ [1:02]; „frische Luft und leichte Bewegung … spazieren“ [1:24]; „Stress zu vermeiden. Entspannen Sie "
                "sich“ [1:36]; „Wenn Sie sich nach einigen Tagen nicht besser fühlen, gehen Sie zum Arzt“ [1:49]. Bestehende Lösung bestätigt.",
    "keys": ["Richtig", "Falsch", "Richtig", "Richtig", "Falsch", "Richtig", "Richtig", "Richtig"],
}

HOEREN["vizu-a2-l04-hoeren-01"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 4.Unterricht Text 1/2/3.mp3“ (im Server-Audio nacheinander): Johan „45 Jahre alt … Am Vormittag "
                "arbeite ich manchmal im Garten … Am Sonntag besuche ich oft meine Freunde oder lese ein Buch“; Anna „40 Jahre … bereite ich das "
                "Frühstück für meine Familie vor … am Vormittag mache ich oft Hausarbeit … am Abend koche ich gern ein leckeres Abendessen … Am "
                "Sonntag machen wir oft einen Familienausflug“; Julio „18 Jahre alt … am (Samstag-)Vormittag treffe ich oft meine Freunde, wir "
                "spielen Fußball … am Abend gehe ich manchmal mit meinen Freunden ins Kino“. Frage 5 hieß „am Wochenende“ — das traf auch auf "
                "Johan zu (sonntags Freunde besuchen); jetzt „am Samstagvormittag“ wie im Audio, damit sie eindeutig ist.",
    "text_fixes": {5: [("Wer trifft sich am Wochenende oft mit Freunden?", "Wer trifft sich am Samstagvormittag oft mit Freunden?")]},
    "keys": ["Johan Mannsberg", "Anna Mannsberg", "Johan Mannsberg", "Julio Mannsberg", "Julio Mannsberg", "Anna Mannsberg", "Julio Mannsberg",
             "Johan Mannsberg", "Anna Mannsberg", "Julio Mannsberg", "Johan Mannsberg", "Anna Mannsberg"],
}

HOEREN["vizu-a2-l05-hoeren-01"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 5.Unterricht Hören.mp3“ + Buchseite „TEST: Steigende Mieten in Deutschland!“ (Lektions-PDF S. 7, "
                "8 Fragen: 1–4, 7–10): 1 [0:04] „die steigenden Mieten in Deutschland“; 2 [0:09] „stark gestiegen“; 3 [0:14] „Besonders in großen "
                "Städten“; 4 [0:23] München „zwischen 1.500 und 2.100 Euro pro Monat“ — das Blatt (800–1000) widerspricht dem Audio und der "
                "Buchoption C; 7 [0:50] „dass viele Menschen in die Städte ziehen“; 8 [0:40] Berlin „etwa 1.000 bis 1.200 Euro“; 9 [1:02] „In "
                "kleineren Städten ist das Leben günstiger“; 10 [1:09] „nur 450 bis 700 Euro im Monat“. Die importierten Zusatzfragen „Berlin / "
                "Fahrrad“ und „5 Arbeitstage“ stehen weder auf der Buchseite noch im Audio (sie stammen aus dem Lesetext) und werden entfernt.",
    "remove_questions": ["Was machen viele Menschen in Berlin?", "Wie viele Tage arbeiten viele Menschen?"],
    "keys": ["Mieten in Deutschland", "Sie steigen", "In großen Städten", "1500–2100 Euro", "Viele ziehen in Städte", "1000–1200 Euro", "Günstiger",
             "450–700 Euro"],
}

_L6_OPEN = ("Prüfung nötig: offene Frage (Buch: „beantworten Sie die Fragen kurz“). Die Antwort ist laut Audio eindeutig, aber Freitext wird "
            "wörtlich verglichen — bitte die Lösungsvarianten prüfen/ergänzen oder die Frage in Multiple Choice umwandeln. Audio: ")

HOEREN["vizu-a2-l06-hoeren-01"] = {
    "evidence": f"Antworten aus {TR}, „A2 6.Unterricht.mp3“.",
    "keys": [
        one_of("im Sommerlager", "Sommerlager", "in einem Sommerlager", "im Lager"),
        one_of("Fußball gespielt", "Fußball", "Fußball spielen", "zusammen Fußball gespielt", "sie haben Fußball gespielt"),
        one_of("Jonas hat einen Fehler gemacht und Lukas wurde wütend", "Lukas wurde wütend", "Lukas war wütend"),
        one_of("traurig", "er war traurig", "Jonas war traurig"),
        one_of("Er hat sich entschuldigt", "sich entschuldigt", "Es tut mir leid gesagt", "er hat gesagt: es tut mir leid"),
        one_of("Respekt ist in einer Freundschaft sehr wichtig", "Respekt ist wichtig", "Respekt"),
        one_of("Brüder", "sie sind Brüder"),
        one_of("in Deutschland", "Deutschland", "im Ausland", "im Ausland in Deutschland"),
        one_of("Er musste viel lernen", "viel lernen", "er hatte viel zu lernen"),
        one_of("traurig", "er war traurig", "allein", "traurig und allein"),
        one_of("Er hat viel Stress im Studium, aber Paul ist ihm sehr wichtig", "viel Stress im Studium", "dass Paul ihm wichtig ist"),
        one_of("Man muss immer miteinander sprechen", "miteinander sprechen", "man muss miteinander sprechen"),
    ],
    "review": {
        1: _L6_OPEN + "[0:04] „Problem … im Sommerlager“.", 2: _L6_OPEN + "[0:09] „haben immer zusammen gespielt, besonders Fußball“.",
        3: _L6_OPEN + "[0:21] „Als Jonas einen Fehler gemacht hat, wurde Lukas wütend“.", 4: _L6_OPEN + "[0:26] „Jonas war traurig“.",
        5: _L6_OPEN + "[0:39] „Er ist zu Jonas gegangen und hat gesagt, es tut mir leid“.",
        6: _L6_OPEN + "[0:53] „dass Respekt in einer Freundschaft sehr wichtig ist“.", 7: _L6_OPEN + "[1:06] „Sie sind Brüder“.",
        8: _L6_OPEN + "[1:08] „Leon studiert im Ausland in Deutschland“.", 9: _L6_OPEN + "[1:13] „weil er viel lernen musste“.",
        10: _L6_OPEN + "[1:20] „Paul war traurig“, [1:27] „dass er sich allein fühlt“.",
        11: _L6_OPEN + "[1:31] „dass er viel Stress im Studium hat, aber dass Paul ihm sehr wichtig ist“.",
        12: _L6_OPEN + "[1:51] „dass man immer miteinander sprechen muss“.",
    },
}

HOEREN["vizu-a2-l07-hoeren-01"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 7.Unterricht Text 1.mp3“ (Max) + „Text 2.mp3“ (Sara), im Server-Audio nacheinander: Max „25 Jahre "
                "… aus Madrid“, „mit dem Auto begonnen“, „Mein erstes Ziel war Berlin“, „mit dem Bus nach Hamburg“, „In Hamburg … den Hafen "
                "gesehen“, „Der Bus ist günstig, aber langsam“ (Reise nach Deutschland); Sara „35 Jahre alt … aus München“, „Reise durch Europa“, "
                "„im Zug Musik gehört“, „nach Paris“, „mit dem Flugzeug nach Rom“. Buchseite: Frage 7 und 8 sind im Buch identisch („Wer fährt "
                "mit dem Bus?“, beide Max); die letzte Frage hieß im Buch „16.“ und ist jetzt Frage 15.",
    "text_fixes": {15: [("16. Wer hört Musik im Zug?", "15. Wer hört Musik im Zug?")]},
    "keys": ["Max", "Sara", "Max", "Sara", "Max", "Sara", "Max", "Max", "Sara", "Sara", "Max", "Sara", "Max", "Max", "Sara"],
}

HOEREN["vizu-a2-l08-hoeren-01"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 8.Unterricht.mp3“: Susanna „kauft oft im Supermarkt oder online ein … ungefähr 80 bis 100 Euro "
                "… zwei Liter Milch“ [0:12-0:20], „2 bis 3 Tassen Kaffee“ [0:41], „zwei bis drei Fertiggerichte pro Woche“ [0:57], „manchmal … "
                "Süßigkeiten … 1–2 Tafeln Schokolade“ [1:00] (das „am Wochenende“ der Frage nennt das Audio nicht; Schokolade ist das einzige "
                "„manchmal“-Produkt); Johann „geht gern auf den Markt … 60 bis 70 Euro … 2 Kilogramm Kartoffeln … etwa 500 g Fleisch … trinkt "
                "hauptsächlich Wasser … Am Sonntag kauft er … einen Kuchen oder backt selbst“ [1:23-2:19]. Bestehende Lösung bestätigt.",
    "keys": ["im Supermarkt oder online", "80–100 Euro", "2 Liter", "Kaffee", "2–3", "Schokolade", "auf dem Markt", "60–70 Euro", "2 kg", "500 g",
             "Wasser", "Er kauft oder backt Kuchen."],
}

HOEREN["vizu-a2-l09-hoeren-01"] = {
    "verify_only": True,
    "questions": 1,
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 9.Unterricht Hören.mp3“: Text 1 „aus Papier … jeden Morgen“ → F Zeitung; Text 2 „kann man hören … "
                "oft wie ein Gespräch“ → A Podcast; Text 3 „nur Ton … Musik, Nachrichten … im Auto“ → D Radio; Text 4 „online … Kommentare … "
                "Meinung“ → B Internet / soziale Medien; Text 5 „Bilder und Videos … am Abend … Familien“ → C Fernsehen; Text 6 „direkt sprechen "
                "… zwei Personen“ → E Telefon. Bestehende Zuordnung (1-F 2-A 3-D 4-B 5-C 6-E) bestätigt.",
    "keys": ["(Zuordnung unverändert)"],
}

HOEREN["vizu-a2-l10-hoeren-01"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 10.Unterricht Teil 1.m4a“: 1 [1:01] „Ich lasse mir mittellange Haare schneiden“; 2 [2:09] „Nur mein "
                "Vater versteht mich“; 3 [3:13] „am besten passt mir der Frühling“; 4 [4:53] „Bayern München gewinnt gegen Atletico Madrid 2 zu 1“; "
                "5 [5:45] „Jeanshosen, beste Qualität, nur 17 Euro“. Beide Modelle gleich.",
    "keys": ["Eine mittellange Frisur.", "Mit ihrem Vater.", "Den Frühling.", "Bayern München hat 2:1 gewonnen.", "17 Euro."],
}

HOEREN["vizu-a2-l10-hoeren-02"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 10.Unterricht Teil 2.m4a“ [1:36-2:13]: „Anne hat … eine karierte Tischdecke … mitgebracht“; "
                "„Olaf hat eine große Kiste Äpfel mitgebracht“; „Harry hat seine ganzen Legos mitgebracht“; „Niki ihre alten Puppen“; Martin: "
                "„Mein Rad. Ich habe ja zum Geburtstag ein Moped geschenkt bekommen“ (das Mofa wurde nicht verkauft). Beispiel Anton → a Poster.",
    "keys": [one("c) Tischdecke"), one("i) Kiste mit Äpfeln"), one("d) Bausteine (Lego)"), one("f) Puppen"), one("g) Fahrrad")],
}

HOEREN["vizu-a2-l10-hoeren-03"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 10.Unterricht Teil 3.m4a“: 11 [0:56] „Diesmal habe ich mich mit meiner Mutter gestritten“ (Bild a: "
                "Frau); 12 [1:38] „da brauche ich … geeignete Tennisschuhe“ (Schläger hat er schon); 13 [2:49] „Dann doch lieber das Top“; 14 [3:43] "
                "„dass ein Computerspiel genau das Richtige für ihn ist“; 15 [4:44] „wenn ich mich als Krankenschwester verkleide“ — Bild b zeigt "
                "die Figur im weißen Kittel; die bisherige Beschriftung „als Arzt“ widersprach dem Audio und wurde angepasst.",
    "option_fixes": {5: [("b) als Arzt", "b) als Krankenschwester (weißer Kittel, Bild b)")]},
    "keys": ["a) mit der Frau (Bild a)", "a) Tennisschuhe", "c) ein Top", "b) ein Computerspiel", "b) als Krankenschwester (weißer Kittel, Bild b)"],
}

HOEREN["vizu-a2-l10-hoeren-04"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 10.Unterricht Teil 4.m4a“: 16 [1:38] „Feriencamps für Jugendliche ab 14“; 17 [2:02] „Ich war im "
                "Feriencamp in Italien“; 18 [2:05] „jeden Vormittag von 10 bis 12 einen Sprachkurs“; 19 [2:33] „Im Juli und August“; 20 [2:46-2:55] "
                "„Man bezahlt nur sein Ticket … Natürlich braucht man auch etwas Taschengeld“ (man bekommt keines).",
    "keys": ["Ja", "Nein", "Ja", "Nein", "Nein"],
}

HOEREN["vizu-a2-l11-hoeren-01"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 11.Unterricht Teil_1.m4a“: 1 [1:01] „Mein Vater hat eine neue Arbeit bekommen. Deshalb müssen wir "
                "jetzt aufs Land umziehen“ (Haus gekauft / gesünder werden nur nebenbei genannt); 2 [2:20] „Diesmal möchte ich unbedingt das "
                "Olympiastadion besuchen … bitte keine Museen“; 3 [3:28] „Immer muss ich das Geschirr spülen. Das macht mir überhaupt keinen "
                "Spaß“; 4 [4:55] „ein bisschen Sport machen, weil ich nicht so fit bin“; 5 [6:15] „fürs Wochenende … sonnig und schön warm“.",
    "keys": ["Weil ihr Vater dort arbeiten wird.", "Er möchte das Olympiastadion besuchen.", "Das Geschirr spülen.", "Weil er fit werden möchte.",
             "Die Sonne wird scheinen."],
}

HOEREN["vizu-a2-l11-hoeren-02"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 11.Unterricht Teil_2.m4a“: 6 [1:27] „Um sieben Uhr klingelte also der Wecker und ich bin "
                "aufgestanden“; 7 [1:31] „Fabian hörte den Wecker und fing gleich an zu weinen“; 8 [1:40] „Viola hat Frühstück gemacht“; 9 [1:52] "
                "„Marie … hat uns leckere Burger gebracht“; 10 [2:03] „Jakob … seine Mutter hat Kuchen gebacken und er hat uns welche gebracht“ — "
                "einziges Gebäck-Bild ist f (gezeichnet als Waffeln); die Auswahl hieß „f) Waffeln“ und heißt jetzt „f) Gebäck (Kuchen)“.",
    "gap_option_renames": [("f) Waffeln", "f) Gebäck (Kuchen)")],
    "keys": [one("a) aufwachen / ausschlafen"), one("e) weinender Junge"), one("i) Frühstück"), one("d) Hamburger"), one("f) Gebäck (Kuchen)")],
}

HOEREN["vizu-a2-l11-hoeren-03"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 11.Unterricht Teil_3.m4a“: 11 [1:12] „Da lern ich lieber Spanisch“; 12 [2:00] „Wie wär's mit Fisch? "
                "… Das ist super“ (er isst kein Fleisch); 13 [2:45] „ich möchte mir einen Laptop kaufen“; 14 [3:33] „Warum gehen wir nicht ins "
                "Schwimmbad? Da können wir auch Eis essen … Klasse Idee“; 15 [4:35] „Ich habe viele alte Jeans … für das Spielzeug und die Bücher "
                "bekommen wir ja sowieso nicht so viel Geld“.",
    "keys": ["a) Spanisch", "c) Fisch", "a) für einen Laptop", "a) ins Schwimmbad", "b) mit Jeans"],
}

HOEREN["vizu-a2-l11-hoeren-04"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 11.Unterricht Teil_4.m4a“: 16 [1:19] „für Schülerinnen und Schüler von 12 bis 16 Jahren“; 17 [1:30] "
                "„Der Preis des Gewinners waren Hilfeleistungen im Wert von 1000 Euro an Kinder, die in Not sind“; 18 [1:53] „lachende Kinder im "
                "Regen“; 19 [2:03] „im Netz gesurft und in einem Blog gelesen“; 20 [2:17] „möchte Ärztin werden … für ein paar Jahre in Afrika "
                "arbeiten“ (nicht studieren).",
    "keys": ["Nein", "Ja", "Nein", "Ja", "Nein"],
}

HOEREN["vizu-a2-l12-hoeren-01"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 12.Unterricht Teil_1.m4a“: 1 [1:04] „nicht sehr groß und auch nicht neu, aber hell und gemütlich“; "
                "2 [2:09] „einen wunderschönen Montagmorgen“; 3 [3:37] „der Kugelschreiber kostet 2,90 Euro“; 4 [5:15] „Bitte hol deinen Bruder um "
                "17.30 Uhr vom Fußballtraining ab“; 5 [6:43] „Nur im Norden Regen bei 15 Grad“.",
    "keys": ["Es ist hell und gemütlich.", "Montag.", "2,90 Euro.", "Seinen Bruder.", "Es regnet."],
}

HOEREN["vizu-a2-l12-hoeren-02"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 12.Unterricht Teil_2.m4a“ [1:28-2:08]: Ralf „meine kurze Hose“ (Beispiel h); Erika „Und ich mein "
                "schwarzes Kleid“; „Anna … braucht ihren Bikini“; „Markus möchte unbedingt seine Flipflops“; „Jürgen will sicher sein kariertes Hemd "
                "einpacken“; „Udo wollte sein weißes und sein rotes T-Shirt mitnehmen“ (Bild g: weißes + rotes T-Shirt).",
    "keys": [one("d) Kleid"), one("c) Bikini"), one("i) Flip-Flops"), one("b) Hemd"), one("g) T-Shirts")],
}

HOEREN["vizu-a2-l12-hoeren-03"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 12.Unterricht Teil_3.m4a“: 11 [1:06-1:09] „Haben Sie vielleicht einen Apfelsaft? — Ja, Apfelsaft "
                "habe ich noch“ (Trauben-/Orangensaft abgelehnt bzw. nicht da); 12 [1:51] „Wann schreibst du die Arbeit? — Am Freitag“ (Donnerstag "
                "= Lerntermin); 13 [2:45] „Probier erstmal den Tee“ (Sirup/Tabletten erst später); 14 [3:32] „wir können sicher auch um 20 Uhr ins "
                "Kino gehen … Ja, das geht“; 15 [4:11] „Ich hätte gern fünf Brötchen“ (Apfelkuchen nur für Dienstag bestellt).",
    "keys": ["a) Apfelsaft (rote Flasche)", "c) Freitag, 11.", "b) Tee", "b) 20:00", "a) Brötchen"],
}

HOEREN["vizu-a2-l12-hoeren-04"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 12.Unterricht Teil_4.m4a“: 16 [1:18] „jetzt bin ich seit einem Jahr in Italien“; 17 [1:40] „Dieses "
                "Jahr gehe ich in die achte Klasse“; 18 [1:50] „Europaschule. Da findet der Unterricht auf Englisch statt“; 19 [2:01] „Vom ersten "
                "Moment an hatte ich Freunde“; 20 [1:27, 2:17] „einen gut bezahlten Job in Rom … Mein Vater hat eine gute Arbeitsstelle“.",
    "keys": ["Ja", "Ja", "Ja", "Nein", "Nein"],
}

# ============================================================ Lesen
# every question re-read against its text; the key was confirmed by the text
# passage quoted in the question's explanation (or found in the text)
_LESEN_EVIDENCE = (f"Geprüft ({AUDIT}): Lösung mit dem Lesetext abgeglichen — die Antwort steht im Text (Textstelle in der Erklärung der "
                   "Frage). Lösung unverändert.")

_LESEN_COUNTS = {
    "vizu-a2-l01-lesen-01#1": 11, "vizu-a2-l01-lesen-01#2": 12, "vizu-a2-l01-lesen-01#3": 12,
    "vizu-a2-l02-lesen-01#1": 8, "vizu-a2-l02-lesen-01#2": 8, "vizu-a2-l02-lesen-01#3": 8,
    "vizu-a2-l03-lesen-01#1": 6, "vizu-a2-l03-lesen-01#2": 6,
    "vizu-a2-l04-lesen-01#1": 6, "vizu-a2-l04-lesen-01#2": 6, "vizu-a2-l04-lesen-01#3": 6,
    "vizu-a2-l05-lesen-01#1": 16,
    "vizu-a2-l06-lesen-01#1": 12, "vizu-a2-l06-lesen-01#2": 11,
    "vizu-a2-l07-lesen-01#1": 12,
    "vizu-a2-l08-lesen-01#1": 10,
    "vizu-a2-l09-lesen-01#1": 8,
    "vizu-a2-l10-lesen-01#1": 5, "vizu-a2-l10-lesen-02#1": 5, "vizu-a2-l10-lesen-03#1": 5, "vizu-a2-l10-lesen-04#1": 1,
    "vizu-a2-l11-lesen-01#1": 4, "vizu-a2-l11-lesen-02#1": 5, "vizu-a2-l11-lesen-03#1": 5, "vizu-a2-l11-lesen-04#1": 1,
    "vizu-a2-l12-lesen-01#1": 3, "vizu-a2-l12-lesen-02#1": 5, "vizu-a2-l12-lesen-03#1": 5, "vizu-a2-l12-lesen-04#1": 1,
    "vizu-a2-l13-lesen-01#1": 5, "vizu-a2-l13-lesen-02#1": 5, "vizu-a2-l13-lesen-03#1": 5, "vizu-a2-l13-lesen-04#1": 1,
}

LESEN: dict[str, dict] = {cid: {"questions": n, "evidence": _LESEN_EVIDENCE} for cid, n in _LESEN_COUNTS.items()}
# Notes for the admin where the check found something worth knowing (key still correct):
LESEN["vizu-a2-l09-lesen-01#1"]["evidence"] += (" Frage 6 („Weniger als 30 % … problematisch“ → Richtig) beruht auf „fast 30 %“ im Text — "
                                                "sachlich richtig, aber knifflig formuliert.")
LESEN["vizu-a2-l11-lesen-01#1"]["evidence"] += " Buchaufgabe 5 fehlt bewusst: der Bungee-Preis steht auch im Buchtext nicht (PDF S. 5–6 geprüft)."
