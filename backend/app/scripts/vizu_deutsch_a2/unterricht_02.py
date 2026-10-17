"""A2 2. Unterricht — Digitaler Alltag und soziale Medien — Grammatik: Konditionalsätze mit wenn (book pp. 19-30).

Book: Frage p.20, Grammatik p.21, Lückenübung (20 open sentence endings) p.22,
Lesen Aufgabe 1-3 (Lukas, Anna, Thomas; four Richtig/Falsch each) pp.23-25,
Hören (12 questions, no transcript in the book) p.26, Video-Pause p.27,
Schreiben (Thema + E-Mail) p.28, Sprechen p.29, Wortschatz (40 words) p.30.

Keys: Hören and the handout's 12 Lesen questions from "Vizu-Antworten A2";
the book's Richtig/Falsch statements are decided by the quoted sentence of
the text. The Lückenübung has open endings ("wird von dem Lehrer korrigiert")
and is a written task checked by the teacher. Typo fixed: "hlifreich" ->
"hilfreich" (Thomas, p.25)."""

from . import (
    article_set, base, exercise, forward_vocab_set, intro_html, mc, numbered_words, reverse_vocab_set, summary_html, tf, vocab_match_sets,
)

L = 2
LESSON_TITLE = "Digitaler Alltag und soziale Medien"
LESSON_DESCRIPTION = "Thema: Digitaler Alltag und soziale Medien · Grammatik: Konditionalsätze mit wenn"
AUDIO = {"vizu-a2-l02-hoeren-01": "A2 2.Unterricht Hören.mp3"}

EINFUEHRUNG_HTML = intro_html(
    2, "Digitaler Alltag und soziale Medien", "Konditionalsätze – wenn",
    ["„wenn“ bilan shart ergash gapini tuzish: Wenn ich Zeit habe, lerne ich Deutsch.;",
     "ergash gapda fe'l oxirda turishini qo'llash;",
     "ijtimoiy tarmoqlar va internet haqidagi so'zlarni o'rganish."],
    ["ijtimoiy tarmoqlardan nima uchun foydalanishingizni aytasiz;",
     "Lukas, Anna va Thomasning matnlarini o'qib tushunasiz;",
     "radio-ko'rsatuvni tinglab, kim nima deganini aniqlaysiz;",
     "do'stingizga o'tkazib yuborilgan qo'ng'iroq haqida e-mail yozasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(2, [
    "<strong>Konditionalsatz:</strong> Wenn + Nebensatz, Hauptsatz — Wenn ich Zeit habe, lerne ich Deutsch.",
    "<strong>Hauptsatz + wenn:</strong> Ich lerne Deutsch, wenn ich Zeit habe.",
    "<strong>Merke:</strong> Im Nebensatz (nach „wenn“) steht das Verb am Ende.",
    "<strong>Wortschatz:</strong> das soziale Netzwerk, posten, teilen, liken, folgen, herunterladen, hochladen, das Passwort, der Vorteil, der Nachteil.",
])

GRAMMAR_HTML = (
    "<h3>Die Konditionalsätze</h3>"
    "<h4>Erklärung</h4><p>Konditionalsätze zeigen eine Bedingung. Eine Handlung passiert <strong>nur wenn</strong> etwas passiert.</p>"
    "<h4>Struktur</h4><ol>"
    "<li><strong>Wenn + Nebensatz, Hauptsatz</strong> — <em>Wenn</em> ich Zeit <em>habe</em>, <strong>lerne</strong> ich Deutsch.</li>"
    "<li><strong>Hauptsatz + wenn + Nebensatz</strong> — Ich <strong>lerne</strong> Deutsch, <em>wenn</em> ich Zeit <em>habe</em>.</li></ol>"
    "<h4>Merke</h4><p>Im Nebensatz (nach „wenn“) steht das <strong>Verb am Ende</strong>.</p>"
    "<h4>Beispiele</h4><ul><li>Wenn ich Zeit habe, besuche ich meine Freunde.</li><li>Wenn ich Geld hätte, würde ich reisen.</li>"
    "<li>Wenn das Wetter schön ist, gehe ich spazieren.</li><li>Ich würde mich freuen, wenn du mir hilfst.</li></ul>"
)

LUECKEN = [
    "Wenn ich Zeit habe, …", "Ich gehe spazieren, wenn …", "Wenn es regnet, …", "Ich trinke Tee, wenn …", "Wenn ich müde bin, …",
    "Ich höre Musik, wenn …", "Wenn ich Geld habe, …", "Ich lerne Deutsch, wenn …", "Wenn ich krank bin, …", "Ich kaufe Obst, wenn …",
    "Wenn ich frei habe, …", "Ich rufe meine Freunde an, wenn …", "Wenn ich Hunger habe, …", "Ich bleibe zu Hause, wenn …",
    "Wenn ich in den Urlaub fahre, …", "Ich spiele Fußball, wenn …", "Wenn ich früh aufstehe, …", "Ich lese ein Buch, wenn …",
    "Wenn ich im Supermarkt bin, …", "Ich sehe fern, wenn …",
]

# ---------- Lesen (pp.23-25) ----------
TEXT_LUKAS = (
    "Ich nutze soziale Netzwerke, weil ich dort mit meinen Freunden sprechen kann.\n\nNach der Schule schreibe ich oft Nachrichten oder schicke "
    "lustige Bilder.\n\nManchmal spielen wir auch zusammen Online-Spiele.\n\nIch sehe auch kurze Videos über Fußball oder Tiere. Das macht mir Spaß."
    "\n\nMeine Eltern sagen, ich soll nicht zu lange am Handy bleiben. Deshalb nutze ich soziale Netzwerke nur ein bisschen am Abend.\n\nFür mich "
    "sind soziale Netzwerke interessant, weil ich dort meine Freunde sehe und neue Dinge lernen kann.")
TEXT_ANNA = (
    "Ich nutze soziale Netzwerke jeden Tag.\nDort kann ich mit meinen Freunden und meiner Familie Kontakt halten.\nViele meiner Freunde wohnen in "
    "anderen Städten, deshalb schreiben wir oft Nachrichten oder schicken Fotos.\nAußerdem sehe ich gern Videos über Reisen, Mode oder Essen.\n"
    "Manchmal bekomme ich dort auch neue Ideen für mein Studium oder meine Freizeit.\n\nSoziale Netzwerke sind für mich praktisch, weil ich schnell "
    "Informationen finden und mit vielen Menschen sprechen kann.\nAber ich versuche auch, nicht zu viel Zeit online zu verbringen.")
TEXT_THOMAS = (
    "Ich nutze soziale Netzwerke aus verschiedenen Gründen. Erstens bleibe ich so mit meinen Freunden und Kollegen in Kontakt.\n\nViele Menschen "
    "arbeiten heute in verschiedenen Städten, deshalb ist das Internet sehr hilfreich.\n\nZweitens bekomme ich dort Nachrichten und Informationen "
    "über Politik, Wirtschaft oder Kultur. Das ist für mich interessant und wichtig.\n\nManchmal teile ich auch Fotos von meiner Familie oder von "
    "Reisen. So können meine Freunde sehen, was ich mache.\n\nTrotzdem finde ich, dass man soziale Netzwerke mit Maß nutzen soll, damit man auch "
    "genug Zeit für das echte Leben hat.")
PASSAGES = [
    {"title": "Lukas Schneider (12 Jahre): Warum nutze ich soziale Netzwerke?", "text": TEXT_LUKAS},
    {"title": "Anna Müller (20 Jahre): Warum nutze ich soziale Netzwerke?", "text": TEXT_ANNA},
    {"title": "Thomas Becker (35 Jahre): Warum nutze ich soziale Netzwerke?", "text": TEXT_THOMAS},
]
LESEN_BOOK = [
    tf("Lukas schreibt nach der Schule oft Nachrichten.", True, "„Nach der Schule schreibe ich oft Nachrichten …“", passage=1),
    tf("Lukas spielt nie Online-Spiele.", False, "„Manchmal spielen wir auch zusammen Online-Spiele.“", passage=1),
    tf("Seine Eltern möchten, dass er nicht zu lange am Handy bleibt.", True, "„Meine Eltern sagen, ich soll nicht zu lange am Handy bleiben.“",
       passage=1),
    tf("Lukas findet soziale Netzwerke langweilig.", False, "„Für mich sind soziale Netzwerke interessant …“", passage=1),
    tf("Anna nutzt soziale Netzwerke jeden Tag.", True, "„Ich nutze soziale Netzwerke jeden Tag.“", passage=2),
    tf("Ihre Freunde wohnen alle in derselben Stadt.", False, "„Viele meiner Freunde wohnen in anderen Städten …“", passage=2),
    tf("Anna sieht gern Videos über Reisen und Essen.", True, "„Außerdem sehe ich gern Videos über Reisen, Mode oder Essen.“", passage=2),
    tf("Anna möchte den ganzen Tag online sein.", False, "„Aber ich versuche auch, nicht zu viel Zeit online zu verbringen.“", passage=2),
    tf("Thomas bleibt über soziale Netzwerke mit seinen Kollegen in Kontakt.", True,
       "„Erstens bleibe ich so mit meinen Freunden und Kollegen in Kontakt.“", passage=3),
    tf("Thomas interessiert sich nicht für Nachrichten.", False,
       "„… bekomme ich dort Nachrichten und Informationen … Das ist für mich interessant und wichtig.“", passage=3),
    tf("Manchmal teilt Thomas Fotos von seiner Familie oder von Reisen.", True, "„Manchmal teile ich auch Fotos von meiner Familie oder von Reisen.“",
       passage=3),
    tf("Thomas findet, dass man soziale Netzwerke immer benutzen soll.", False, "„… dass man soziale Netzwerke mit Maß nutzen soll …“", passage=3),
]
_K = "Javob: Vizu-Antworten A2 (2. Unterricht, Lesen)."
LESEN_HANDOUT = [
    mc("Lukas nutzt soziale Netzwerke vor allem, um …", ["neue Spiele zu kaufen", "mit seinen Freunden zu kommunizieren", "Schulbücher zu lesen"],
       "B", _K, passage=1),
    mc("Thomas findet soziale Netzwerke hilfreich, weil …", ["viele Menschen in verschiedenen Städten arbeiten", "dort viele Filme gezeigt werden",
                                                             "man dort Sport machen kann"], "A", _K, passage=3),
    mc("Anna nutzt soziale Netzwerke auch, weil …", ["sie dort Nachrichten liest", "sie Kontakt mit Familie und Freunden halten kann",
                                                     "sie dort arbeitet"], "B", _K, passage=2),
    mc("Lukas schaut manchmal Videos im Internet, weil …", ["sie ihm Spaß machen", "seine Lehrer das sagen", "er dafür Geld bekommt"], "A", _K, passage=1),
    mc("Thomas bekommt über soziale Netzwerke oft …", ["Nachrichten über Politik, Wirtschaft oder Kultur", "neue Computerspiele", "Musikunterricht"],
       "A", _K, passage=3),
    mc("Anna findet soziale Netzwerke praktisch, weil sie …", ["schnell Informationen finden kann", "dort Sport treiben kann", "dort einkaufen muss"],
       "A", _K, passage=2),
    mc("Lukas nutzt soziale Netzwerke am Abend nur kurz, weil …", ["seine Eltern eine Regel haben", "sein Internet langsam ist",
                                                                   "seine Freunde schlafen"], "A", _K, passage=1),
    mc("Thomas teilt manchmal Fotos, damit …", ["seine Freunde sehen, was er macht", "er Geld verdient", "er berühmt wird"], "A", _K, passage=3),
    mc("Anna bekommt durch soziale Netzwerke manchmal …", ["neue Ideen für Studium oder Freizeit", "neue Arbeit im Ausland", "neue Bücher"],
       "A", _K, passage=2),
    mc("Lukas kann durch soziale Netzwerke auch …", ["neue Dinge lernen", "eine Wohnung finden", "ein Auto kaufen"], "A", _K, passage=1),
    mc("Thomas denkt, soziale Netzwerke soll man …", ["sehr viel nutzen", "mit Maß nutzen", "gar nicht nutzen"], "B", _K, passage=3),
    mc("Anna sieht online gern Inhalte über …", ["Reisen, Mode oder Essen", "Politik und Geschichte", "Autos und Technik"], "A", _K, passage=2),
]

# ---------- Hören (p.26), key: Vizu-Antworten A2 ----------
_JMF = ["die Journalistin", "Professor Müller", "Frau Millner"]
HOEREN = [
    mc("Wer arbeitet an der Universität München?", ["Professor Müller", "Frau Millner", "die Journalistin"], "A"),
    mc("Wer eröffnet die Sendung „Gemeinschaftskreis“?", ["Frau Millner", "Professor Müller", "die Journalistin"], "C"),
    mc("Wer sagt, dass soziale Netzwerke für Studenten und Forscher praktisch sind?", _JMF, "B"),
    mc("Wer hat zwei Kinder?", ["Frau Millner", "Professor Müller", "die Journalistin"], "A"),
    mc("Wer sagt, dass manche Menschen zu viel Zeit online verbringen?", ["Frau Millner", "Professor Müller", "die Journalistin"], "B"),
    mc("Wer bekommt durch soziale Netzwerke Tipps über Schule oder Gesundheit?", ["Professor Müller", "Frau Millner", "die Journalistin"], "B"),
    mc("Wer stellt die Frage: „Wie beeinflussen soziale Netzwerke unser Leben?“", _JMF, "A"),
    mc("Wer spricht über Regeln für Kinder zu Hause?", ["Professor Müller", "Frau Millner", "die Journalistin"], "B"),
    mc("Wer spricht über Informationen und Nachrichten im Internet?", ["Frau Millner", "Professor Müller", "die Journalistin"], "B"),
    mc("Wer sagt, dass soziale Netzwerke Teil unseres Lebens sind?", ["die Journalistin", "Frau Millner", "Professor Müller"], "A"),
    mc("Wer spricht über Kommunikation im echten Leben?", ["Frau Millner", "Professor Müller", "die Journalistin"], "B"),
    mc("Wer moderiert die Sendung im Studio?", _JMF, "A"),
]

WORDS = numbered_words([
    ("das soziale Netzwerk", "ijtimoiy tarmoq"), ("das Internet", "internet"), ("die Nachricht", "xabar"), ("die Information", "ma’lumot"),
    ("der Benutzer", "foydalanuvchi"), ("der Account", "akkaunt"), ("das Profil", "profil"), ("das Foto", "rasm"), ("das Video", "video"),
    ("der Kommentar", "izoh"), ("posten", "joylashtirmoq"), ("teilen", "ulashmoq"), ("liken", "layk bosmoq"), ("folgen", "kuzatmoq"),
    ("der Freund / die Freundin", "do‘st"), ("die Freundschaft", "do‘stlik"), ("der Chat", "chat"), ("schreiben", "yozmoq"), ("sprechen", "gaplashmoq"),
    ("telefonieren", "telefon qilmoq"), ("online", "onlayn"), ("offline", "oflayn"), ("die App", "ilova"), ("herunterladen", "yuklab olmoq"),
    ("hochladen", "yuklamoq"), ("das Passwort", "parol"), ("die Sicherheit", "xavfsizlik"), ("die Zeit", "vaqt"), ("die Unterhaltung", "ko‘ngilocharlik"),
    ("die Kommunikation", "muloqot"), ("die Gruppe", "guruh"), ("der Beitrag", "post"), ("der Link", "havola"), ("suchen", "qidirmoq"),
    ("finden", "topmoq"), ("lernen", "o‘rganmoq"), ("informieren", "ma’lumot bermoq"), ("das Problem", "muammo"), ("der Vorteil", "afzallik"),
    ("der Nachteil", "kamchilik")], "Internet und soziale Medien")
WORTSCHATZ_SETS = [s for s in (*vocab_match_sets(WORDS), article_set(WORDS), forward_vocab_set(WORDS)) if s]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: A2 2. Unterricht", source="vizu", page=19, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Wie beeinflusst das Internet unseren Alltag?", page=20,
             prompt="Wie beeinflusst das Internet unseren Alltag? Deine Meinung zählt!",
             questions=["Das Internet spart uns Zeit.", "Das Internet verbindet uns mit der Welt.", "Das Internet hilft uns beim Lernen.",
                        "Das Internet macht das Einkaufen leichter."],
             min_duration=10, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Konditionalsätze mit wenn", page="21-22", rules=[{"title": "Die Konditionalsätze", "html": GRAMMAR_HTML}]),
        base(L, "schreiben", 2, "Grammatik-Aufgabe: Konditionalsatz mit WENN – Lückenübung", page=22, task_type="other",
             prompt="Ergänzen Sie die Sätze mit passenden Enden (Konditionalsatz mit WENN). Schreiben Sie alle 20 Sätze vollständig.\n\n"
                    + "\n".join(f"{i}. {s}" for i, s in enumerate(LUECKEN, start=1))
                    + "\n\nMerke: Im Nebensatz (nach „wenn“) steht das Verb am Ende. — Wenn ich Zeit habe, lerne ich Deutsch.",
             min_words=60, max_words=300, time_limit=25,
             metadata={"note": "Ochiq javobli mashq — Vizu-Antworten: „wird von dem Lehrer korrigiert“."},
             support_phrases=["Wenn ich Zeit habe, lerne ich Deutsch.", "Ich gehe spazieren, wenn das Wetter schön ist."]),
        base(L, "lesen", 1, "Lesen: Warum nutze ich soziale Netzwerke? (Aufgabe 1-3)", page="23-25",
             instruction="Lesen Sie die Texte. Richtig oder Falsch? Danach: Kreuzen Sie die richtige Antwort an (a, b oder c).",
             passages=PASSAGES, questions=LESEN_BOOK + LESEN_HANDOUT, max_score=len(LESEN_BOOK) + len(LESEN_HANDOUT),
             metadata={"note": "Kitobdagi Richtig/Falsch (javob matndan iqtibos bilan) + dars varag'idagi 12 savol (javob: Vizu-Antworten A2). "
                               "„hlifreich“ → „hilfreich“ tuzatildi."}),
        base(L, "hoeren", 1, "Hören: Sendung „Gemeinschaftskreis“ — soziale Netzwerke", page=26, audio_file="A2 2.Unterricht Hören.mp3",
             instruction="Hören Sie die 12 Fragen. Kreuzen Sie die richtige Antwort an.", questions=HOEREN, max_score=len(HOEREN)),
        base(L, "schreiben", 1, "Schreiben: Warum nutze ich soziale Netzwerke?", page=28, task_type="description",
             prompt="Warum nutze ich soziale Netzwerke? Schreiben Sie einen kurzen Text über das Thema. Schreiben Sie ca. 30–40 Wörter.\n\nPunkte:\n"
                    "• Welche sozialen Netzwerke nutzen Sie?\n• Warum nutzen Sie soziale Netzwerke?\n• Was machen Sie dort normalerweise?\n"
                    "• Wie oft nutzen Sie soziale Netzwerke?",
             min_words=30, max_words=60, time_limit=15),
        base(L, "schreiben", 3, "Schreiben: E-Mail — Verpasster Anruf", page=28, task_type="email",
             prompt="Situation: Ihr Freund hat Sie über Skype angerufen. Sie konnten den Videoanruf nicht beantworten. Schreiben Sie Ihrem Freund "
                    "eine E-Mail.\n\nPunkte:\n• Entschuldigen Sie sich für den verpassten Anruf.\n• Erklären Sie kurz, warum Sie nicht antworten "
                    "konnten.\n• Fragen Sie, wann Sie wieder telefonieren können.\n• Machen Sie einen Vorschlag für einen neuen Termin.",
             audience="Ihr Freund (informell)", min_words=30, max_words=80, time_limit=20,
             support_phrases=["Hallo …,", "Es tut mir leid, dass …", "Ich konnte nicht antworten, weil …", "Wann können wir wieder telefonieren?",
                              "Hast du am … Zeit?", "Viele Grüße"]),
        base(L, "sprechen", 1, "Sprechen: Welche Rolle spielt Internet in meinem Leben?", page=29, topic="Internet in meinem Leben",
             prompt="Sprechen Sie über das Thema. Sprechen Sie ca. 1–2 Minuten. Tipps: Sprechen Sie über alle Punkte. Begründen Sie Ihre Meinung.",
             questions=["Wofür verwenden Sie das Internet?", "Wie oft nutzen Sie das Internet?", "Welche Informationen suchen Sie online?",
                        "Gibt es auch Nachteile?"],
             response_type="monolog", min_duration=60, max_duration=150,
             speech_goal="Über die eigene Internetnutzung sprechen: wofür, wie oft, welche Informationen, Nachteile — mit Begründung (weil, wenn).",
             keywords=["Internet", "nutzen", "wenn", "weil", "Nachteile"]),
        base(L, "wortschatz", 1, "Wortschatz: Internet und soziale Medien", page=30, words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False),
        base(L, "uebungen", 1, "Übungen: A2 2. Unterricht", source="vizu", exercises=[s for s in (reverse_vocab_set(WORDS),) if s]),
        base(L, "yakuniy", 1, "Abschlusstest: A2 2. Unterricht", source="vizu",
             instruction="Konditionalsätze va internet so'zlari bo'yicha yakuniy test (dars materiali asosida).",
             questions=[
                 mc("Wenn ich Zeit ___, lerne ich Deutsch.", ["habe", "hat", "haben"], "A"),
                 mc("Welcher Satz ist richtig?", ["Wenn es regnet, ich bleibe zu Hause.", "Wenn es regnet, bleibe ich zu Hause.",
                                                  "Wenn regnet es, bleibe ich zu Hause."], "B", "Nach dem Nebensatz kommt im Hauptsatz zuerst das Verb."),
                 mc("Ich gehe spazieren, wenn das Wetter schön ___.", ["ist", "sein", "war ist"], "A", "Im Nebensatz steht das Verb am Ende."),
                 mc("Wo steht das Verb im Nebensatz mit „wenn“?", ["Am Anfang", "Auf Position 2", "Am Ende"], "C"),
                 tf("Lukas nutzt soziale Netzwerke nur ein bisschen am Abend.", True, "Lesen, Aufgabe 1."),
                 tf("Thomas teilt nie Fotos.", False, "Lesen, Aufgabe 3: „Manchmal teile ich auch Fotos …“"),
                 mc("„herunterladen“ — o'zbekchasi?", ["yuklab olmoq", "yuklamoq", "ulashmoq"], "A"),
                 mc("„der Nachteil“ — o'zbekchasi?", ["kamchilik", "afzallik", "muammo"], "A"),
                 mc("„teilen“ — o'zbekchasi?", ["ulashmoq", "kuzatmoq", "qidirmoq"], "A"),
                 mc("Ich rufe dich an, wenn ich nach Hause ___.", ["komme", "kommen", "kam ich"], "A"),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: A2 2. Unterricht", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
