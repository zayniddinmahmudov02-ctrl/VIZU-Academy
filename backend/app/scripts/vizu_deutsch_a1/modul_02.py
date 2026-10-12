"""Modul 2 — Meine Familie — Grammatik: Präsens, Die Zahlen (book pp. 13-26)."""

from . import base, choice_gap, exercise, gap, gap_paragraphs, html_table, match, mc, text_gap, tf, ul, words

L = 2

_PRAESENS = (
    "<p><strong>Präsens (hozirgi zamon)</strong> — fe'llarning hozirgi paytdagi yoki doimiy takrorlanadigan harakatni bildiradi.</p>"
    "<h3>1. Kuchsiz fe'llar (Regelmäßige Verben)</h3>"
    "<p>Fe'lning asosi o'zgarmaydi, faqat shaxs qo'shimchalari qo'shiladi.</p>"
    + html_table(["Shaxs", "Qo'shimcha", "lernen (o'rganmoq)"],
                 [["ich (men)", "-e", "ich lerne"], ["du (sen)", "-st", "du lernst"], ["er / sie / es (u)", "-t", "er lernt"],
                  ["wir (biz)", "-en", "wir lernen"], ["ihr (sizlar)", "-t", "ihr lernt"], ["sie / Sie (ular / Siz)", "-en", "sie lernen"]])
    + "<p><strong>Misollar:</strong></p>"
    + ul(["Ich spiele Fußball. — Men futbol o'ynayman.", "Du gehst zur Schule. — Sen maktabga borasan.",
          "Wir lesen ein Buch. — Biz bir kitob o'qiymiz.", "Sie wohnen in Berlin. — Ular Berlinda yashashadi."])
    + "<h3>2. Kuchli fe'llar</h3><p>Unli harf faqat <strong>du</strong> va <strong>er / sie / es</strong> da o'zgaradi.</p>"
    + html_table(["Infinitiv", "du", "er / sie / es"],
                 [["fahren", "fährst", "fährt"], ["schlafen", "schläfst", "schläft"], ["tragen", "trägst", "trägt"],
                  ["waschen", "wäschst", "wäscht"], ["sprechen", "sprichst", "spricht"], ["helfen", "hilfst", "hilft"],
                  ["nehmen", "nimmst", "nimmt"], ["lesen", "liest", "liest"], ["essen", "isst", "isst"]])
    + ul(["Du fährst zur Schule. Er fährt zur Schule.", "Du sprichst Deutsch. Sie spricht Deutsch.", "Du liest ein Buch. Er liest ein Buch."])
    + "<h3>3. Ajraladigan fe'llar — Trennbare Verben</h3>"
    "<p>Asosiy fe'l odatda 2-o'rinda keladi, prefiks (old qo'shimcha) gap oxirida keladi.</p>"
    "<p><strong>aufstehen</strong> — turmoq / uyg'onmoq: ich stehe auf, du stehst auf, er steht auf, wir stehen auf, ihr steht auf, sie stehen auf.</p>"
    + ul(["Ich stehe jeden Morgen um 7 Uhr auf. — Men har kuni ertalab soat 7 da turaman.",
          "Wir gehen um 8 Uhr zur Schule los. — Biz 8 da maktabga yo'lga chiqamiz."])
)

_PRAESENS_2 = (
    "<h3>Präsensda qo'shimcha -e</h3>"
    "<p>Fe'l asosi <strong>-t, -d, -gn, -ffn, -tm</strong> bilan tugasa, du / er / sie / es / ihr shakllarida talaffuz oson "
    "bo'lishi uchun <strong>-e</strong> qo'shiladi. ich / wir / sie / Sie oddiy qo'shimchalar bilan qoladi.</p>"
    + html_table(["Tugashi", "Fe'l", "du", "er", "ihr"],
                 [["-t / -d", "arbeiten, warten, reden", "du arbeitest, du wartest, du redest", "er arbeitet, er wartet, er redet",
                   "ihr arbeitet, ihr wartet, ihr redet"],
                  ["-gn", "regnen", "—", "es regnet", "—"],
                  ["-ffn", "öffnen", "du öffnest", "er öffnet", "ihr öffnet"],
                  ["-tm", "atmen", "du atmest", "er atmet", "ihr atmet"]])
    + "<h3>du shaklida -s qo'shilmaydi</h3>"
    "<p>Fe'l asosi <strong>-s, -ß, -z</strong> bilan tugasa, du shaklida faqat <strong>-t</strong> qo'shiladi:</p>"
    + ul(["heißen: du heißt — er heißt — ihr heißt (Ich heiße Max.)", "tanzen: du tanzt — er tanzt — ihr tanzt (Ich tanze gern.)"])
    + "<p><em>Eslatma:</em> Präsensda fe'lning oxiriga qo'shimcha talaffuzni osonlashtirish uchun qo'shiladi, ammo ma'no o'zgarmaydi.</p>"
)

_ZAHLEN = (
    "<h3>Die Zahlen 1–12</h3>"
    + html_table(["Zahl", "Wort", "Zahl", "Wort", "Zahl", "Wort"],
                 [["1", "eins", "5", "fünf", "9", "neun"], ["2", "zwei", "6", "sechs", "10", "zehn"], ["3", "drei", "7", "sieben", "11", "elf"],
                  ["4", "vier", "8", "acht", "12", "zwölf"]])
    + "<h3>Die Zahlen 13–19 (mit „zehn“ am Ende)</h3>"
    + html_table(["Zahl", "Wort", "Zahl", "Wort"],
                 [["13", "dreizehn", "17", "siebzehn"], ["14", "vierzehn", "18", "achtzehn"], ["15", "fünfzehn", "19", "neunzehn"], ["16", "sechzehn", "", ""]])
    + "<h3>Zehner</h3>"
    + html_table(["Zahl", "Wort", "Zahl", "Wort"],
                 [["20", "zwanzig", "60", "sechzig"], ["30", "dreißig", "70", "siebzig"], ["40", "vierzig", "80", "achtzig"], ["50", "fünfzig", "90", "neunzig"],
                  ["100", "hundert", "", ""]])
    + "<h3>Höhere Zahlen — 21 bis 99 mit „und“</h3>"
    + ul(["21 einundzwanzig, 22 zweiundzwanzig, 23 dreiundzwanzig, 24 vierundzwanzig, 25 fünfundzwanzig, 26 sechsundzwanzig, "
          "27 siebenundzwanzig, 28 achtundzwanzig, 29 neunundzwanzig",
          "31 einunddreißig, 32 zweiunddreißig, 33 dreiunddreißig, 34 vierunddreißig, 35 fünfunddreißig, 39 neununddreißig",
          "41 einundvierzig, 42 zweiundvierzig, 49 neunundvierzig, 51 einundfünfzig, 59 neunundfünfzig, 61 einundsechzig, "
          "69 neunundsechzig, 71 einundsiebzig, 99 neunundneunzig"])
    + "<h3>Hunderter und Tausender</h3>"
    + ul(["100 einhundert, 200 zweihundert, 300 dreihundert, 350 dreihundertfünfzig, 900 neunhundert",
          "1.000 eintausend, 1.500 eintausendfünfhundert, 2.000 zweitausend"])
    + "<p><strong>TIPP:</strong> Die Zahlen 1–12 sind einfach. Die Zahlen 13–19 haben „zehn“ am Ende. "
      "Ab 21 benutzen wir „und“ zwischen Zehner und Einer.</p>"
)

_Q = "Setzen Sie das Verb im Präsens ein."
WRITTEN = [
    text_gap("Ich ___ (arbeiten) jeden Tag.", ["arbeite"], _Q),
    text_gap("Du ___ (warten) auf den Bus.", ["wartest"], _Q),
    text_gap("Er ___ (reden) mit seiner Freundin.", ["redet"], _Q),
    text_gap("Wir ___ (lernen) Deutsch.", ["lernen"], _Q),
    text_gap("Ihr ___ (tanzen) gern.", ["tanzt"], _Q),
    text_gap("Sie ___ (öffnen) die Tür.", ["öffnen", "öffnet"], _Q, explanation="Sie (Siz / ular) öffnen; sie (u) öffnet."),
    text_gap("Ich ___ (atmen) tief.", ["atme"], _Q),
    text_gap("Du ___ (stauchen) die Hand.", ["stauchst"], _Q),
    text_gap("Er ___ (regnen) oft hier.", ["regnet"], _Q, explanation="regnen → es / er regnet (-e qo'shiladi)."),
    text_gap("Wir ___ (heißen) Anna und Tom.", ["heißen"], _Q),
    text_gap("Du ___ (fahren) nach Berlin.", ["fährst"], _Q),
    text_gap("Er ___ (schlafen) lange.", ["schläft"], _Q),
    text_gap("Ich ___ (lesen) ein Buch.", ["lese"], _Q),
    text_gap("Du ___ (sehen) den Film.", ["siehst"], _Q),
    text_gap("Wir ___ (anfangen) die Arbeit.", ["fangen an", "fangen … an", "fangen ... an"], _Q,
             explanation="Trennbares Verb: Wir fangen die Arbeit an."),
    text_gap("Ihr ___ (mitkommen) zur Party.", ["kommt mit", "kommt … mit", "kommt ... mit"], _Q, explanation="Ihr kommt zur Party mit."),
    text_gap("Er ___ (tanzen) auf dem Fest.", ["tanzt"], _Q),
    text_gap("Du ___ (heißen) Markus.", ["heißt"], _Q),
    text_gap("Ich ___ (machen) die Hausaufgaben.", ["mache"], _Q),
    text_gap("Sie ___ (öffnen) das Fenster.", ["öffnen", "öffnet"], _Q),
]

TEST = [
    mc("Du ___ (o'rganmoq) Deutsch.", ["lerne", "lernst", "lernt"], "B"),
    mc("Er ___ (ochmoq) die Tür.", ["öffnet", "öffnen", "öffnest"], "A"),
    mc("Ihr ___ (ishlamoq) am Montag.", ["arbeitet", "arbeitest", "arbeite"], "A"),
    mc("Ich ___ (o'qimoq) ein Buch.", ["lese", "liest", "lesen"], "A"),
    mc("Du ___ (haydamoq) nach Hause.", ["fährt", "fahren", "fährst"], "C"),
    mc("Er ___ (uxlamoq) lange.", ["schläfst", "schläft", "schlafen"], "B"),
    mc("Wir ___ (boshlamoq) jetzt.", ["fängst an", "fangt an", "fangen an"], "C"),
    mc("Du ___ (o'qimoq) das Buch.", ["lesen", "liest", "ließt"], "B"),
    mc("Sie ___ (o'ynamoq) gern Fußball.", ["spielst", "spielt", "spielen"], "C", "Kitob kaliti: Sie (Siz / ular) → spielen."),
    mc("Ich ___ (ko'rmoq) dich.", ["sieht", "sehe", "siehst"], "B"),
    mc("Du ___ (kesib o'tmoq) die Straße.", ["überquert", "überquerst", "überquere"], "B"),
    mc("Er ___ (qilmoq) die Hausaufgaben.", ["macht", "machst", "machen"], "A"),
    mc("Ihr ___ (eshitmoq) Musik.", ["hören", "hört", "hörst"], "B"),
    mc("Wir ___ (haydamoq) nach Deutschland.", ["fährt", "fahrst", "fahren"], "C"),
    mc("Du ___ (ko'rmoq) den Film.", ["sieht", "siehst", "sehen"], "B"),
    mc("Ich ___ (qilmoq) die Aufgabe.", ["machst", "mache", "macht"], "B"),
    mc("Du ___ (yordam bermoq) mir.", ["hilft", "hilfst", "helfen"], "B"),
    mc("Er ___ (qoplamoq) den Tisch.", ["deckst", "deckt", "decke"], "B"),
    mc("Wir ___ (ochmoq) die Fenster.", ["öffnest", "öffnen", "öffnet"], "B"),
    mc("Ihr ___ (raqsga tushmoq) am Samstag.", ["tanztet", "tanze", "tanzt"], "C"),
]

ZAHLEN_EX = [
    mc("Wie schreibt man 13?", ["dreizehn", "dreißig", "dreiundzehn"], "A"),
    mc("Wie schreibt man 30?", ["dreizig", "dreißig", "dreizehn"], "B"),
    mc("Wie schreibt man 21?", ["zwanzigeins", "einundzwanzig", "einszwanzig"], "B"),
    mc("Wie schreibt man 16?", ["sechzehn", "sechszehn", "sechzig"], "A"),
    mc("Wie schreibt man 70?", ["siebenzig", "siebzig", "siebzehn"], "B"),
    mc("„fünfundvierzig“ ist …", ["54", "45", "405"], "B"),
    mc("„neunundneunzig“ ist …", ["99", "19", "90"], "A"),
    mc("Wie schreibt man 350?", ["dreihundertfünfzig", "dreifünfzighundert", "dreihundertfünfzehn"], "A"),
    tf("12 heißt „zwölf“.", True),
    tf("17 heißt „siebenzehn“.", False, "17 — siebzehn."),
]

TEXT_VATER = ("Das ist Herr Müller, der Vater von Tom und Anna. Er arbeitet als Ingenieur in einer Firma. Seine Muttersprache ist Deutsch. "
              "Er spricht auch Englisch. Herr Müller ist verheiratet und liebt seine Familie sehr. In seiner Freizeit liest er gern Zeitung "
              "und fährt Fahrrad.")
TEXT_MUTTER = ("Das ist Frau Müller, die Mutter von Tom und Anna. Sie arbeitet als Ärztin in einem Krankenhaus. Ihre Muttersprache ist Deutsch. "
               "Sie spricht auch ein bisschen Französisch. Frau Müller kocht gern und hört abends gern ruhige Musik. Sie liebt ihre Kinder sehr.")
TEXT_TOM = ("Das ist Tom, der Sohn von Herr und Frau Müller und der Bruder von Anna. Er ist 14 Jahre alt und geht in die Schule. "
            "Tom spielt gern Fußball und hört gern Popmusik. Seine Lieblingsfächer sind Sport und Englisch. Er hilft seinem Vater oft im Garten.")
TEXT_ANNA = ("Das ist Anna, die Tochter von Herr und Frau Müller und die Schwester von Tom. Sie ist 11 Jahre alt und geht auch in die Schule. "
             "Anna malt gern und liest gern Märchen. Sie spielt gern mit ihrer Katze und hilft ihrer Mutter in der Küche.")

LESEN = [
    mc("Wer ist Herr Müller?", ["Der Bruder von Tom", "Der Vater von Tom und Anna", "Der Lehrer"], "B", passage=1),
    mc("Wo arbeitet Herr Müller?", ["In einer Schule", "In einer Firma", "Im Krankenhaus"], "B", "„Er arbeitet als Ingenieur in einer Firma.“", passage=1),
    mc("Welche Sprachen spricht Herr Müller?", ["Deutsch und Englisch", "Deutsch und Französisch", "Nur Deutsch"], "A", passage=1),
    mc("Ist Herr Müller verheiratet?", ["Ja", "Nein", "Weiß nicht"], "A", passage=1),
    mc("Was macht Herr Müller gern in seiner Freizeit?", ["Kochen", "Zeitung lesen und Fahrrad fahren", "Fußball spielen"], "B", passage=1),
    mc("Wer ist Frau Müller?", ["Die Schwester von Tom", "Die Mutter von Tom und Anna", "Die Lehrerin"], "B", passage=2),
    mc("Wo arbeitet Frau Müller?", ["In einer Firma", "In einem Krankenhaus", "In der Schule"], "B", passage=2),
    mc("Welche Fremdsprache spricht Frau Müller?", ["Englisch", "Französisch", "Italienisch"], "B", "„Sie spricht auch ein bisschen Französisch.“", passage=2),
    mc("Was macht Frau Müller gern?", ["Musik hören und kochen", "Fußball spielen", "Zeitung lesen"], "A", passage=2),
    mc("Wie alt ist Tom?", ["14 Jahre", "12 Jahre", "10 Jahre"], "A", "„Er ist 14 Jahre alt.“", passage=3),
    mc("Was macht Tom gern?", ["Fußball spielen und Musik hören", "Malen", "Lesen"], "A", passage=3),
    mc("Welche Lieblingsfächer hat Tom?", ["Sport und Englisch", "Mathematik und Deutsch", "Musik und Kunst"], "A", passage=3),
    mc("Wer ist Anna?", ["Die Schwester von Tom", "Die Mutter von Tom", "Die Lehrerin"], "A", passage=4),
    mc("Wie alt ist Anna?", ["11 Jahre", "12 Jahre", "10 Jahre"], "A", "„Sie ist 11 Jahre alt.“", passage=4),
    mc("Was macht Anna gern in ihrer Freizeit?", ["Computerspiele spielen", "Malen und Märchen lesen", "Fußball spielen"], "B", passage=4),
]

HOEREN_TEXT = (
    "Hallo! Ich heiße [[1]]. Ich bin 12 Jahre alt. Ich [[2]] in Berlin.\n"
    "Ich möchte euch meine [[3]] vorstellen. Das ist mein [[4]]. Er heißt Peter. Er arbeitet als [[5]] in einer großen Firma. "
    "Er ist sehr [[6]] und liest gern [[7]]. Am Wochenende spielt er oft mit mir [[8]].\n"
    "Das ist meine [[9]]. Sie heißt Maria. Sie arbeitet als [[10]] in einer Schule. Sie [[11]] gern und hört gern [[12]]. "
    "Jeden Samstag [[13]] sie Kuchen für uns.\n"
    "Das ist mein [[14]]. Er heißt Tom. Er ist 14 Jahre alt. Tom spielt gern [[15]] und hört gern [[16]]. Er hilft oft meinem Vater im [[17]].\n"
    "Das ist meine [[18]]. Sie heißt Anna. Sie ist 10 Jahre alt. Anna [[19]] gern und liest gern [[20]]. Sie spielt gern mit unserer [[21]].\n"
    "Wir wohnen zusammen in einem großen [[22]] mit einem Garten. Ich liebe meine [[23]] sehr! "
    "Wir machen oft [[24]] und feiern zusammen [[25]] und Weihnachten."
)
# Only the gaps the text itself decides are prefilled; the rest is taken
# from the audio by an admin (the book's answer sheet belongs to an older
# version of this text).
HOEREN_GAPS = {str(i): [] for i in range(1, 26)}
HOEREN_GAPS.update({"3": ["Familie"], "4": ["Vater"], "9": ["Mutter"], "10": ["Lehrerin"], "14": ["Bruder"], "17": ["Garten"],
                    "18": ["Schwester"], "22": ["Haus"], "23": ["Familie"], "24": ["Ausflüge"], "25": ["Geburtstage"]})

WORDS = (
    words([("wohnen", "yashamoq"), ("gehen", "bormoq, yurmoq"), ("kommen", "kelmoq"), ("arbeiten", "ishlamoq"), ("lernen", "o'rganmoq"),
           ("lesen", "o'qimoq"), ("spielen", "o'ynamoq"), ("essen", "yemoq"), ("trinken", "ichmoq"), ("kochen", "pishirmoq"),
           ("schlafen", "uxlamoq"), ("sehen", "ko'rmoq"), ("sprechen", "gapirmoq"), ("lieben", "sevmoq"), ("helfen", "yordam bermoq"),
           ("tanzen", "raqsga tushmoq")], "A1 daraja fe'llari")
    + words([("der", "Vater", "ota"), ("die", "Mutter", "ona"), ("der", "Sohn", "o'g'il bola"), ("die", "Tochter", "qiz bola"),
             ("der", "Bruder", "aka / uka"), ("die", "Schwester", "opa / singil"), ("der", "Großvater", "bobo (Opa)"),
             ("die", "Großmutter", "buvi (Oma)"), ("der", "Onkel", "amaki / tog'a"), ("die", "Tante", "xola / amma"),
             ("der", "Cousin", "amaki / xola o'g'li"), ("die", "Cousine", "amaki / xola qizi"), ("der", "Neffe", "jiyan (o'g'il)"),
             ("die", "Nichte", "jiyan (qiz)"), ("der", "Ehemann", "er"), ("die", "Ehefrau", "xotin"), ("die", "Schwiegermutter", "qaynona"),
             ("der", "Schwiegervater", "qaynota"), ("die", "Schwägerin", "qaynisingil"), ("der", "Schwager", "qayni aka / qayni uka"),
             ("der", "Enkel", "nabira (o'g'il)"), ("die", "Enkelin", "nabira (qiz)")], "Oila a'zolari")
)


def items() -> list[dict]:
    return [
        base(L, "frage", 1, "Frage des Moduls: Germaniyada hayot qanday?", page=14,
             prompt="Germaniyada hayot qanday? Germaniyadagi hayot haqida nimalarni bilasiz? Fikringizni ovozli yuboring.",
             min_duration=10, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Präsens und Die Zahlen", page="15-18, 23",
             rules=[
                 {"title": "Präsens — Hozirgi zamon", "html": _PRAESENS},
                 {"title": "Präsens — Qoidalar davomi", "html": _PRAESENS_2},
                 {"title": "Die Zahlen — Raqamlar", "html": _ZAHLEN},
             ],
             exercises=[
                 exercise("Yozma mashqlar (20 ta): Präsens", WRITTEN, "Fe'lni to'g'ri shaklga keltiring (Präsens)."),
                 exercise("Test mashqlar (20 ta): Präsens", TEST, "To'g'ri javobni tanlang."),
                 exercise("Übung: Die Zahlen", ZAHLEN_EX, "Raqamlarni to'g'ri yozilishini tanlang.", source="vizu"),
             ]),
        base(L, "lesen", 1, "Lesen: Familie Müller", page="19-21",
             instruction="Lesen Sie die Texte. Antworten Sie, indem Sie A, B oder C wählen.",
             passages=[{"title": "Herr Müller", "text": TEXT_VATER}, {"title": "Frau Müller", "text": TEXT_MUTTER},
                       {"title": "Tom", "text": TEXT_TOM}, {"title": "Anna", "text": TEXT_ANNA}],
             questions=LESEN, max_score=len(LESEN)),
        base(L, "hoeren", 1, "Hören: Meine Familie (Lückentext)", page=22, audio_file="A1-2.mp3", key_pending=True,
             instruction="Hören Sie den Text und ergänzen Sie die Lücken. Passende Wörter: Familie, Vater, Mutter, Bruder, Schwester, Haus, "
                         "Berlin, Peter, Tom, Anna, spielt, Fußball, Kuchen, freundlich, liest, arbeitet, Lehrerin, Musik, malt, hilft, "
                         "Garten, Ausflüge, Geburtstage.",
             questions=gap_paragraphs("Meine Familie — ergänzen Sie die Lücken", HOEREN_TEXT, HOEREN_GAPS)),
        base(L, "schreiben", 1, "Schreiben: Meine Familie vorstellen", page=24,
             prompt="Stellen Sie Ihre Familie vor. Schreiben Sie über 5–8 Familienmitglieder:\n\n"
                    "Hallo! Ich möchte meine Familie vorstellen.\n"
                    "Mein Großvater (bobom) heißt … und er ist … Jahre alt.\nMeine Großmutter (buvim) heißt … und sie ist … Jahre alt.\n"
                    "Mein Vater / Meine Mutter / Mein Bruder / Meine Schwester / Mein Onkel / Meine Tante / Mein Cousin / Meine Cousine … heißt … "
                    "und er/sie ist … Jahre alt.",
             task_type="description", min_words=30, max_words=100, time_limit=15,
             support_phrases=["Ich möchte meine Familie vorstellen.", "Mein Vater heißt …", "Meine Mutter heißt …", "… und er ist … Jahre alt.",
                              "… und sie ist … Jahre alt."]),
        base(L, "sprechen", 1, "Sprechen Sie über Ihre Familie!", page=25, topic="Meine Familie",
             prompt="Sprechen Sie über Ihre Familie. Benutzen Sie die Sätze.",
             questions=["Meine Familie besteht aus … Personen.", "In meiner Familie gibt es …", "Mein Vater heißt …", "Meine Mutter heißt …",
                        "Ich habe … Geschwister.", "Mein Bruder / Meine Schwester heißt …", "Wir wohnen in …",
                        "Am Wochenende … wir gerne zusammen.", "Ich liebe meine Familie, weil …"],
             response_type="monolog", min_duration=20, max_duration=90,
             speech_goal="Familienmitglieder mit Namen nennen, Wohnort und gemeinsame Aktivitäten beschreiben, einen Grund nennen (weil …).",
             keywords=["Familie", "Vater", "Mutter", "Geschwister", "wohnen"]),
        base(L, "wortschatz", 1, "Wortschatz Modul 2", page=26, words=WORDS),
        base(L, "yakuniy", 1, "Yakuniy Test: Modul 2", source="vizu",
             instruction="Präsens, raqamlar va oila so'zlari bo'yicha yakuniy test.",
             questions=[
                 mc("Er ___ jeden Tag im Büro.", ["arbeitet", "arbeitest", "arbeite"], "A"),
                 mc("Du ___ gern Bücher.", ["liest", "lest", "lesen"], "A"),
                 mc("Wir ___ in Berlin.", ["wohnt", "wohnen", "wohnst"], "B"),
                 mc("Anna ___ Deutsch.", ["sprecht", "sprichst", "spricht"], "C"),
                 mc("Ich ___ jeden Morgen um 7 Uhr ___.", ["stehe … auf", "aufstehe … (—)", "stehst … auf"], "A"),
                 choice_gap("Du ___ Markus.", ["heißt", "heißst", "heiße"], "heißt"),
                 mc("Wie schreibt man 47?", ["vierundsiebzig", "siebenundvierzig", "vierzigsieben"], "B"),
                 mc("Wie schreibt man 19?", ["neunzehn", "neunzig", "neunzehnzig"], "A"),
                 mc("„die Tochter“ — o'zbekchasi qaysi?", ["qiz bola", "o'g'il bola", "xola"], "A"),
                 mc("Die Mutter von meinem Vater ist meine …", ["Tante", "Großmutter", "Cousine"], "B"),
                 tf("„der Onkel“ bedeutet „amaki / tog'a“.", True),
                 match("Was passt zusammen?", ["der Bruder", "die Schwester", "der Sohn", "die Enkelin"],
                       ["aka / uka", "opa / singil", "o'g'il bola", "nabira (qiz)", "qaynona"], {"1": "A", "2": "B", "3": "C", "4": "D"}),
             ]),
    ]
