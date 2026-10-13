"""Modul 2 — Meine Familie — Grammatik: Präsens, Die Zahlen (book pp. 13-26).

Book pages: 13 cover (Mavzu / Grammatik), 14 Frage des Moduls, 15-16
Präsens rules, 17 "Yozma mashqlar (20 ta)", 18 "Test mashqlar (20 ta)",
19-20 Lesen (four texts with Uzbek translations), 21 Lesen Test (15
questions), 22 Hören (Lückentext + word list, audio A1-2.mp3), 23 Die
Zahlen 1-100, 24 Schreiben (introduce your family), 25 Sprechen, 26
Wortschatz.

Corrections of the book (the rule is taught correctly, the book's wording
is noted): p.16 lists "stauchen — du stauchest" under -chn (stauchen ends in
-ch: du stauchst) and "reden" under -dm (reden ends in -d). p.18 question 9
"Sie ___ gern Fußball" is right with spielt (sie = u) and spielen (sie / Sie
= ular / Siz): both are accepted.

The Hören gaps can only be decided from the audio (one answer — "Ich ___ in
Berlin" — is not even in the book's word list): only the family words that
the text itself determines are keyed, the task stays key_pending until an
admin has listened to A1-2.mp3 and set the remaining answers."""

from . import base, choice_gap, exercise, gap, gap_paragraphs, html_table, match, mc, text_gap, tf, ul, words

L = 2
LESSON_TITLE = "Meine Familie"
LESSON_DESCRIPTION = "Thema: Meine Familie · Grammatik: Präsens, Die Zahlen"

IMAGES = [
    ("01_cover.jpg", "EINFUEHRUNG", "Modul 2 — Meine Familie (Buch, S. 13)"),
]
RETIRED_IMAGE_TITLES: list[str] = []


def _pairs(n: int) -> dict:
    return {str(i): "ABCDEFGHIJKL"[i - 1] for i in range(1, n + 1)}


# ============================================================
# Einführung / Zusammenfassung
# ============================================================

EINFUEHRUNG_HTML = (
    "<h3>Modul 2 — Meine Familie</h3>"
    "<p><strong>Mavzu:</strong> Meine Familie (mening oilam) · <strong>Grammatik:</strong> Präsens (hozirgi zamon), Die Zahlen (raqamlar)</p>"
    "<h4>Dars maqsadlari</h4>"
    + ul([
        "fe'llarni hozirgi zamonda (Präsens) barcha shaxslarda tuslash: ich lerne, du lernst, er lernt …;",
        "kuchli fe'llarda unlining o'zgarishini bilish: fahren → du fährst, sprechen → du sprichst, lesen → du liest;",
        "ajraladigan fe'llarni gapda to'g'ri ishlatish: Ich stehe um 7 Uhr auf.;",
        "1 dan 100 gacha va undan katta raqamlarni aytish va yozish;",
        "oila a'zolari nomlarini (Vater, Mutter, Bruder, Schwester, Großvater …) o'rganish.",
    ])
    + "<h4>Dars oxirida siz quyidagilarni bajara olasiz</h4>"
    + ul([
        "oilangizni tanishtirasiz: „Das ist mein Vater. Er heißt … und er ist … Jahre alt.“;",
        "Müller oilasi haqidagi matnlarni o'qib, savollarga javob berasiz;",
        "oila haqidagi matnni tinglab, bo'sh joylarni to'ldirasiz;",
        "yoshingizni, telefon raqamingizni va boshqa sonlarni nemischa aytasiz.",
    ])
    + "<h4>Darsning tuzilishi</h4>"
    + "<p>Einführung → Wortschatz → Grammatik → Lesen → Hören → Sprechen → Schreiben → Übungen → Abschlusstest → Zusammenfassung</p>"
)

ZUSAMMENFASSUNG_HTML = (
    "<h3>Modul 2 — qisqacha</h3>"
    + ul([
        "<strong>Präsens:</strong> ich -e · du -st · er/sie/es -t · wir -en · ihr -t · sie/Sie -en (ich lerne, du lernst, er lernt …).",
        "<strong>Kuchli fe'llar:</strong> a → ä (fahren: du fährst), e → i (sprechen: du sprichst), e → ie (lesen: du liest) — faqat du va er/sie/es da.",
        "<strong>-e qo'shiladi:</strong> du arbeitest, er wartet, ihr öffnet · <strong>-s qo'shilmaydi:</strong> du heißt, du tanzt.",
        "<strong>Ajraladigan fe'llar:</strong> Ich stehe um 7 Uhr auf. Wir fangen die Arbeit an.",
        "<strong>Zahlen:</strong> 13–19 „-zehn“ (dreizehn), 21–99 „und“ bilan (einundzwanzig), 30 = dreißig, 100 = hundert.",
        "<strong>Familie:</strong> der Vater, die Mutter, der Sohn, die Tochter, der Bruder, die Schwester, der Großvater, die Großmutter …",
    ])
    + "<p>Natijalaringiz pastda — tugallanmagan bo'limlarni yakunlang, so'ng keyingi darsga o'ting.</p>"
)

# ============================================================
# Grammatik — Präsens (pp. 15-18), Die Zahlen (p. 23)
# ============================================================

_PRAESENS = (
    "<p><strong>Präsens (hozirgi zamon)</strong> — fe'llarning hozirgi paytdagi yoki doimiy takrorlanadigan harakatini bildiradi.</p>"
    "<h3>1. Kuchsiz fe'llar (Regelmäßige Verben)</h3>"
    "<p>Fe'lning asosi o'zgarmaydi, faqat shaxs qo'shimchalari qo'shiladi.</p>"
    + html_table(["Shaxs", "Qo'shimcha", "lernen (o'rganmoq)"],
                 [["ich (men)", "-e", "ich lerne"], ["du (sen)", "-st", "du lernst"], ["er / sie / es (u)", "-t", "er lernt"],
                  ["wir (biz)", "-en", "wir lernen"], ["ihr (sizlar)", "-t", "ihr lernt"], ["sie / Sie (ular / Siz)", "-en", "sie lernen"]])
    + "<p><strong>Misollar:</strong></p>"
    + ul(["Ich spiele Fußball. — Men futbol o'ynayman.", "Du gehst zur Schule. — Sen maktabga borasan.",
          "Wir lesen ein Buch. — Biz bir kitob o'qiymiz.", "Sie wohnen in Berlin. — Ular Berlinda yashashadi."])
    + "<h3>2. Kuchli fe'llar</h3><p>Unli harf faqat <strong>du</strong> va <strong>er / sie / es</strong> da o'zgaradi.</p>"
    + html_table(["O'zgarish", "Infinitiv", "du", "er / sie / es"],
                 [["a → ä", "fahren", "fährst", "fährt"], ["a → ä", "schlafen", "schläfst", "schläft"], ["a → ä", "tragen", "trägst", "trägt"],
                  ["a → ä", "waschen", "wäschst", "wäscht"], ["e → i", "sprechen", "sprichst", "spricht"], ["e → i", "helfen", "hilfst", "hilft"],
                  ["e → i", "essen", "isst", "isst"], ["e → i", "nehmen", "nimmst", "nimmt"], ["e → ie", "lesen", "liest", "liest"]])
    + ul(["Du fährst zur Schule. Er fährt zur Schule.", "Du sprichst Deutsch. Sie spricht Deutsch.", "Du liest ein Buch. Er liest ein Buch."])
    + "<h3>3. Ajraladigan fe'llar — Trennbare Verben</h3>"
    "<p>Asosiy fe'l odatda 2-o'rinda keladi, prefiks (old qo'shimcha) gap oxirida keladi.</p>"
    + html_table(["aufstehen (turmoq / uyg'onmoq)", "", ""],
                 [["ich stehe auf", "wir stehen auf", ""], ["du stehst auf", "ihr steht auf", ""], ["er steht auf", "sie stehen auf", ""]])
    + ul(["Ich stehe jeden Morgen um 7 Uhr auf. — Men har kuni ertalab soat 7 da turaman.",
          "Wir gehen um 8 Uhr zur Schule los. — Biz 8 da maktabga yo'lga chiqamiz."])
)

_PRAESENS_2 = (
    "<h3>Präsensda qo'shimcha -e (qisqaroq)</h3>"
    "<p>Fe'l asosi quyidagi tovushlar bilan tugasa, <strong>du / er / sie / es / ihr</strong> shakllarida talaffuz oson bo'lishi uchun "
    "<strong>-e</strong> qo'shiladi. <strong>ich / wir / sie / Sie</strong> oddiy qo'shimchalar bilan qoladi.</p>"
    + html_table(["Asos tugashi", "Fe'l", "du", "er / sie / es", "ihr"],
                 [["-t", "arbeiten", "du arbeitest", "er arbeitet", "ihr arbeitet"],
                  ["-d", "warten", "du wartest", "er wartet", "ihr wartet"],
                  ["-d", "reden", "du redest", "er redet", "ihr redet"],
                  ["-gn", "regnen", "du regnest", "es regnet", "ihr regnet"],
                  ["-ffn", "öffnen", "du öffnest", "er öffnet", "ihr öffnet"],
                  ["-tm", "atmen", "du atmest", "er atmet", "ihr atmet"]])
    + "<p><em>Izoh:</em> kitobda „stauchen — du stauchest“ (-chn) misoli berilgan. „stauchen“ ning asosi <strong>-ch</strong> bilan tugaydi, "
      "shuning uchun -e qo'shilmaydi: <strong>du stauchst, er staucht</strong>. „reden“ esa -d bilan tugaydi (yuqoridagi jadvalda).</p>"
    + "<h3>du shaklida -s qo'shilmaydi (oxiri ß va z bilan tugagan fe'llar)</h3>"
    + html_table(["Fe'l", "du", "er / sie / es", "ihr", "Misol"],
                 [["heißen", "du heißt", "er heißt", "ihr heißt", "Ich heiße Max."],
                  ["tanzen", "du tanzt", "er tanzt", "ihr tanzt", "Ich tanze gern."]])
    + "<p><strong>Eslatma:</strong> Präsensda fe'lning oxiriga qo'shimcha talaffuzni osonlashtirish uchun qo'shiladi, ammo ma'no o'zgarmaydi.</p>"
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
    + "<h3>Die Zahlen 21–99 (mit „und“)</h3>"
    + html_table(["Zahl", "Wort", "Zahl", "Wort"],
                 [["21", "einundzwanzig", "35", "fünfunddreißig"], ["22", "zweiundzwanzig", "39", "neununddreißig"],
                  ["23", "dreiundzwanzig", "41", "einundvierzig"], ["24", "vierundzwanzig", "49", "neunundvierzig"],
                  ["25", "fünfundzwanzig", "51", "einundfünfzig"], ["26", "sechsundzwanzig", "59", "neunundfünfzig"],
                  ["27", "siebenundzwanzig", "61", "einundsechzig"], ["28", "achtundzwanzig", "69", "neunundsechzig"],
                  ["29", "neunundzwanzig", "71", "einundsiebzig"], ["31", "einunddreißig", "99", "neunundneunzig"],
                  ["32", "zweiunddreißig", "", ""], ["33", "dreiunddreißig", "", ""], ["34", "vierunddreißig", "", ""]])
    + "<h3>Höhere Zahlen — Hunderter und Tausender</h3>"
    + html_table(["Zahl", "Wort"],
                 [["100", "einhundert"], ["200", "zweihundert"], ["300", "dreihundert"], ["350", "dreihundertfünfzig"], ["900", "neunhundert"],
                  ["1.000", "eintausend"], ["1.500", "eintausendfünfhundert"], ["2.000", "zweitausend"]])
    + "<p><strong>TIPP:</strong> Die Zahlen 1–12 sind einfach. Die Zahlen 13–19 haben „zehn“ am Ende. "
      "Ab 21 benutzen wir „und“ zwischen Zehner und Einer.</p>"
)

_Q = "Setzen Sie das Verb im Präsens ein."
WRITTEN = [
    text_gap("Ich ___ (arbeiten) jeden Tag.", ["arbeite"], _Q),
    text_gap("Du ___ (warten) auf den Bus.", ["wartest"], _Q, explanation="-d: du wartest (-e qo'shiladi)."),
    text_gap("Er ___ (reden) mit seiner Freundin.", ["redet"], _Q, explanation="-d: er redet (-e qo'shiladi)."),
    text_gap("Wir ___ (lernen) Deutsch.", ["lernen"], _Q),
    text_gap("Ihr ___ (tanzen) gern.", ["tanzt"], _Q),
    text_gap("Sie ___ (öffnen) die Tür.", ["öffnen", "öffnet"], _Q, explanation="Sie (Siz / ular) öffnen; sie (u) öffnet."),
    text_gap("Ich ___ (atmen) tief.", ["atme"], _Q),
    text_gap("Du ___ (stauchen) die Hand.", ["stauchst"], _Q, explanation="stauchen asosi -ch bilan tugaydi, -e qo'shilmaydi: du stauchst."),
    text_gap("Er ___ (regnen) oft hier.", ["regnet"], _Q, explanation="regnen → es / er regnet (-e qo'shiladi)."),
    text_gap("Wir ___ (heißen) Anna und Tom.", ["heißen"], _Q),
    text_gap("Du ___ (fahren) nach Berlin.", ["fährst"], _Q, explanation="a → ä: du fährst."),
    text_gap("Er ___ (schlafen) lange.", ["schläft"], _Q, explanation="a → ä: er schläft."),
    text_gap("Ich ___ (lesen) ein Buch.", ["lese"], _Q),
    text_gap("Du ___ (sehen) den Film.", ["siehst"], _Q, explanation="e → ie: du siehst."),
    text_gap("Wir ___ (anfangen) die Arbeit.", ["fangen an", "fangen … an", "fangen ... an"], _Q,
             explanation="Trennbares Verb: Wir fangen die Arbeit an."),
    text_gap("Ihr ___ (mitkommen) zur Party.", ["kommt mit", "kommt … mit", "kommt ... mit"], _Q, explanation="Ihr kommt zur Party mit."),
    text_gap("Er ___ (tanzen) auf dem Fest.", ["tanzt"], _Q),
    text_gap("Du ___ (heißen) Markus.", ["heißt"], _Q, explanation="heißen: du heißt (-s qo'shilmaydi)."),
    text_gap("Ich ___ (machen) die Hausaufgaben.", ["mache"], _Q),
    text_gap("Sie ___ (öffnen) das Fenster.", ["öffnen", "öffnet"], _Q, explanation="Sie (Siz / ular) öffnen; sie (u) öffnet."),
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
    gap("Sie ___ (o'ynamoq) gern Fußball.", "Sie [[1]] gern Fußball.", {"1": {"accepted": ["spielen", "spielt"], "options": ["spielst", "spielt", "spielen"]}},
        explanation="Ikkala javob ham to'g'ri: sie (u) spielt, sie / Sie (ular / Siz) spielen."),
    mc("Ich ___ (ko'rmoq) dich.", ["sieht", "sehe", "siehst"], "B"),
    mc("Du ___ (kesib o'tmoq) die Straße.", ["überquert", "überquerst", "überquere"], "B"),
    mc("Er ___ (qilmoq) die Hausaufgaben.", ["macht", "machst", "machen"], "A"),
    mc("Ihr ___ (eshitmoq) Musik.", ["hören", "hört", "hörst"], "B"),
    mc("Wir ___ (haydamoq) nach Deutschland.", ["fährt", "fahrst", "fahren"], "C"),
    mc("Du ___ (ko'rmoq) den Film.", ["sieht", "siehst", "sehen"], "B"),
    mc("Ich ___ (qilmoq) die Aufgabe.", ["machst", "mache", "macht"], "B"),
    mc("Du ___ (yordam berish) mir.", ["hilft", "hilfst", "helfen"], "B"),
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
    match("Zahl und Wort: Was passt zusammen?", ["11", "20", "60", "100", "1.000"],
          ["elf", "zwanzig", "sechzig", "hundert", "eintausend", "zwölf"], _pairs(5), points=5),
]

# ============================================================
# Lesen (pp. 19-21) — the book's texts, translations and 15 questions
# ============================================================

TEXT_VATER = ("Das ist Herr Müller, der Vater von Tom und Anna. Er arbeitet als Ingenieur in einer Firma. Seine Muttersprache ist Deutsch. "
              "Er spricht auch Englisch. Herr Müller ist verheiratet und liebt seine Familie sehr. In seiner Freizeit liest er gern Zeitung "
              "und fährt Fahrrad.")
TEXT_VATER_UZ = ("Bu Herr Müller, Tom va Annaning otasi. U bir firmada muhandis bo'lib ishlaydi. Uning ona tili nemis tili. U ingliz tilida ham "
                 "gapira oladi. Herr Müller uylangan va oilasini juda yaxshi ko'radi. Bo'sh vaqtida gazeta o'qishni va velosiped haydashni yaxshi ko'radi.")
TEXT_MUTTER = ("Das ist Frau Müller, die Mutter von Tom und Anna. Sie arbeitet als Ärztin in einem Krankenhaus. Ihre Muttersprache ist Deutsch. "
               "Sie spricht auch ein bisschen Französisch. Frau Müller kocht gern und hört abends gern ruhige Musik. Sie liebt ihre Kinder sehr.")
TEXT_MUTTER_UZ = ("Bu Frau Müller, Tom va Annaning onasi. U shifoxonada shifokor bo'lib ishlaydi. Uning ona tili nemis tili. U fransuz tilini ham "
                  "ozgina biladi. Frau Müller ovqat pishirishni yaxshi ko'radi va kechqurun sokin musiqa tinglaydi. U bolalarini juda yaxshi ko'radi.")
TEXT_TOM = ("Das ist Tom, der Sohn von Herr und Frau Müller und der Bruder von Anna. Er ist 14 Jahre alt und geht in die Schule. "
            "Tom spielt gern Fußball und hört gern Popmusik. Seine Lieblingsfächer sind Sport und Englisch. Er hilft seinem Vater oft im Garten.")
TEXT_TOM_UZ = ("Bu Tom, Herr va Frau Müllerning o'g'li va Annaning akasi. U 14 yoshda va maktabga boradi. Tom futbol o'ynashni va pop musiqa "
               "tinglashni yaxshi ko'radi. Uning sevimli fanlari sport va ingliz tili. U ko'pincha otasiga bog'da yordam beradi.")
TEXT_ANNA = ("Das ist Anna, die Tochter von Herr und Frau Müller und die Schwester von Tom. Sie ist 11 Jahre alt und geht auch in die Schule. "
             "Anna malt gern und liest gern Märchen. Sie spielt gern mit ihrer Katze und hilft ihrer Mutter in der Küche.")
TEXT_ANNA_UZ = ("Bu Anna, Herr va Frau Müllerning qizi va Tomning singlisi. U 11 yoshda va u ham maktabga boradi. Anna rasm chizishni va ertak "
                "o'qishni yaxshi ko'radi. U mushugi bilan o'ynashni yaxshi ko'radi va onasiga oshxonada yordam beradi.")


def _with_translation(de: str, uz: str) -> str:
    return f"{de}\n\nO'zbekcha tarjima: {uz}"


LESEN = [
    mc("Wer ist Herr Müller?", ["Der Bruder von Tom", "Der Vater von Tom und Anna", "Der Lehrer"], "B", "„Das ist Herr Müller, der Vater von Tom und Anna.“", passage=1),
    mc("Wo arbeitet Herr Müller?", ["In einer Schule", "In einer Firma", "Im Krankenhaus"], "B", "„Er arbeitet als Ingenieur in einer Firma.“", passage=1),
    mc("Welche Sprachen spricht Herr Müller?", ["Deutsch und Englisch", "Deutsch und Französisch", "Nur Deutsch"], "A",
       "„Seine Muttersprache ist Deutsch. Er spricht auch Englisch.“", passage=1),
    mc("Ist Herr Müller verheiratet?", ["Ja", "Nein", "Weiß nicht"], "A", "„Herr Müller ist verheiratet …“", passage=1),
    mc("Was macht Herr Müller gern in seiner Freizeit?", ["Kochen", "Zeitung lesen und Fahrrad fahren", "Fußball spielen"], "B",
       "„In seiner Freizeit liest er gern Zeitung und fährt Fahrrad.“", passage=1),
    mc("Wer ist Frau Müller?", ["Die Schwester von Tom", "Die Mutter von Tom und Anna", "Die Lehrerin"], "B", "„Das ist Frau Müller, die Mutter von Tom und Anna.“", passage=2),
    mc("Wo arbeitet Frau Müller?", ["In einer Firma", "In einem Krankenhaus", "In der Schule"], "B", "„Sie arbeitet als Ärztin in einem Krankenhaus.“", passage=2),
    mc("Welche Fremdsprache spricht Frau Müller?", ["Englisch", "Französisch", "Italienisch"], "B", "„Sie spricht auch ein bisschen Französisch.“", passage=2),
    mc("Was macht Frau Müller gern?", ["Musik hören und kochen", "Fußball spielen", "Zeitung lesen"], "A",
       "„Frau Müller kocht gern und hört abends gern ruhige Musik.“", passage=2),
    mc("Wie alt ist Tom?", ["14 Jahre", "12 Jahre", "10 Jahre"], "A", "„Er ist 14 Jahre alt.“", passage=3),
    mc("Was macht Tom gern?", ["Fußball spielen und Musik hören", "Malen", "Lesen"], "A", "„Tom spielt gern Fußball und hört gern Popmusik.“", passage=3),
    mc("Welche Lieblingsfächer hat Tom?", ["Sport und Englisch", "Mathematik und Deutsch", "Musik und Kunst"], "A",
       "„Seine Lieblingsfächer sind Sport und Englisch.“", passage=3),
    mc("Wer ist Anna?", ["Die Schwester von Tom", "Die Mutter von Tom", "Die Lehrerin"], "A", "„… und die Schwester von Tom.“", passage=4),
    mc("Wie alt ist Anna?", ["11 Jahre", "12 Jahre", "10 Jahre"], "A", "„Sie ist 11 Jahre alt.“", passage=4),
    mc("Was macht Anna gern in ihrer Freizeit?", ["Computerspiele spielen", "Malen und Märchen lesen", "Fußball spielen"], "B",
       "„Anna malt gern und liest gern Märchen.“", passage=4),
]

# ============================================================
# Hören (p. 22) — Lückentext; answers come from the audio A1-2.mp3
# ============================================================

HOEREN_WORDLIST = ("Familie (oila), Vater (ota), Mutter (ona), Bruder (aka), Schwester (singil), Haus (uy), Berlin (Berlin), Peter (Peter), "
                   "Tom (Tom), Anna (Anna), spielt (o'ynaydi), Fußball (futbol), Kuchen (pirogi), freundlich (do'stona), liest (o'qiydi), "
                   "arbeitet (ishlaydi), Lehrerin (o'qituvchi), Musik (musiqa), malt (chizadi), hilft (yordam beradi), Garten (bog'), "
                   "Ausflüge (sayrlar), Geburtstage (tug'ilgan kunlar)")
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
# Keyed: only the gaps the text itself decides (family members by name / age
# and role, the house "mit einem Garten", the fixed phrases). The rest — the
# speaker's name, the verbs, the hobbies — is set by an admin after listening.
HOEREN_GAPS = {str(i): [] for i in range(1, 26)}
HOEREN_GAPS.update({"3": ["Familie"], "4": ["Vater"], "9": ["Mutter"], "10": ["Lehrerin"], "14": ["Bruder"], "17": ["Garten"],
                    "18": ["Schwester"], "22": ["Haus"], "23": ["Familie"], "24": ["Ausflüge"], "25": ["Geburtstage"]})

# ============================================================
# Schreiben (p. 24) — introduce your family (free, teacher-graded) + VIZU practice
# ============================================================

SCHREIBEN_SETS = [
    exercise("Oilani tanishtirish: Mein oder meine?", [
        choice_gap("___ Großvater heißt Karl.", ["Mein", "Meine"], "Mein", explanation="der Großvater → mein Großvater"),
        choice_gap("___ Großmutter heißt Erika.", ["Mein", "Meine"], "Meine", explanation="die Großmutter → meine Großmutter"),
        choice_gap("___ Vater heißt Peter.", ["Mein", "Meine"], "Mein"),
        choice_gap("___ Mutter heißt Maria.", ["Mein", "Meine"], "Meine"),
        choice_gap("___ Bruder heißt Tom.", ["Mein", "Meine"], "Mein"),
        choice_gap("___ Schwester heißt Anna.", ["Mein", "Meine"], "Meine"),
        choice_gap("___ Onkel heißt Max.", ["Mein", "Meine"], "Mein"),
        choice_gap("___ Tante heißt Laura.", ["Mein", "Meine"], "Meine"),
    ], "der → mein, die → meine (kitobdagi 24-bet namunasi: Mein Großvater heißt …, Meine Großmutter heißt …). VIZU mashqi.", source="vizu"),
    exercise("Oilani tanishtirish: er oder sie?", [
        choice_gap("Mein Vater heißt Peter und ___ ist 45 Jahre alt.", ["er", "sie"], "er"),
        choice_gap("Meine Mutter heißt Maria und ___ ist 42 Jahre alt.", ["er", "sie"], "sie"),
        choice_gap("Mein Sohn heißt Ali und ___ ist 8 Jahre alt.", ["er", "sie"], "er"),
        choice_gap("Meine Tochter heißt Lola und ___ ist 6 Jahre alt.", ["er", "sie"], "sie"),
        choice_gap("Meine Cousine heißt Nora und ___ ist 15 Jahre alt.", ["er", "sie"], "sie"),
        choice_gap("Mein Neffe heißt Jan und ___ ist 3 Jahre alt.", ["er", "sie"], "er"),
    ], "Erkak — er, ayol — sie. VIZU mashqi.", source="vizu"),
    exercise("Sätze bauen: Meine Familie", [
        mc("Welcher Satz ist richtig? (heißt / Mein Bruder / Tom)", ["Mein Bruder heißt Tom.", "Heißt Tom mein Bruder.", "Tom mein Bruder heißt."], "A"),
        mc("Welcher Satz ist richtig? (ist / 14 Jahre alt / er)", ["Er 14 Jahre alt ist.", "Er ist 14 Jahre alt.", "Ist er alt 14 Jahre."], "B"),
        mc("Welcher Satz ist richtig? (möchte / meine Familie / vorstellen / ich)",
           ["Ich möchte meine Familie vorstellen.", "Ich vorstellen möchte meine Familie.", "Meine Familie ich möchte vorstellen."], "A"),
        mc("Welcher Satz ist richtig? (wohnen / in Berlin / wir)", ["In wohnen wir Berlin.", "Wir in Berlin wohnen.", "Wir wohnen in Berlin."], "C"),
    ], "So'zlardan to'g'ri gapni tanlang. VIZU mashqi.", source="vizu"),
]

# ============================================================
# Wortschatz (p. 26) — 16 verbs + 22 family words (book translations)
# ============================================================

WORDS = (
    words([("wohnen", "yashamoq"), ("gehen", "bormoq, yurmoq"), ("kommen", "kelmoq"), ("arbeiten", "ishlamoq"), ("lernen", "o'rganmoq"),
           ("lesen", "o'qimoq"), ("spielen", "o'ynamoq"), ("essen", "yeyish"), ("trinken", "ichmoq"), ("kochen", "pishirmoq"),
           ("schlafen", "uxlamoq"), ("sehen", "ko'rmoq"), ("sprechen", "gapirmoq"), ("lieben", "sevmoq"), ("helfen", "yordam berish"),
           ("tanzen", "raqsga tushmoq")], "A1 daraja fe'llari")
    + words([("der", "Vater", "ota"), ("die", "Mutter", "ona"), ("der", "Sohn", "o'g'il bola"), ("die", "Tochter", "qiz bola"),
             ("der", "Bruder", "aka / uka"), ("die", "Schwester", "opa / singil"), ("der", "Großvater", "bobo (Opa)"),
             ("die", "Großmutter", "buvi (Oma)"), ("der", "Onkel", "amaki / tog'a"), ("die", "Tante", "xola / amma"),
             ("der", "Cousin", "amaki / xola o'g'li"), ("die", "Cousine", "amaki / xola qizi"), ("der", "Neffe", "jiyan o'g'il"),
             ("die", "Nichte", "jiyan qiz"), ("der", "Ehemann", "er"), ("die", "Ehefrau", "xotin"), ("die", "Schwiegermutter", "qaynona"),
             ("der", "Schwiegervater", "qaynota"), ("die", "Schwägerin", "qaynisingil"), ("der", "Schwager", "qayni aka / qayni uka"),
             ("der", "Enkel", "nabira o'g'il"), ("die", "Enkelin", "nabira qiz")], "Oila a'zolari")
)

WORTSCHATZ_SETS = [
    exercise("Zuordnung 1: A1-Verben", [
        match("Was passt zusammen?", ["wohnen", "gehen", "kommen", "arbeiten", "lernen", "lesen"],
              ["yashamoq", "bormoq, yurmoq", "kelmoq", "ishlamoq", "o'rganmoq", "o'qimoq", "uxlamoq"], _pairs(6), points=6),
        match("Was passt zusammen?", ["spielen", "essen", "trinken", "kochen", "schlafen"],
              ["o'ynamoq", "yeyish", "ichmoq", "pishirmoq", "uxlamoq", "sevmoq"], _pairs(5), points=5),
        match("Was passt zusammen?", ["sehen", "sprechen", "lieben", "helfen", "tanzen"],
              ["ko'rmoq", "gapirmoq", "sevmoq", "yordam berish", "raqsga tushmoq", "kelmoq"], _pairs(5), points=5),
    ], "Fe'lni tarjimasi bilan moslashtiring.", source="vizu"),
    exercise("Zuordnung 2: Familie", [
        match("Was passt zusammen?", ["der Vater", "die Mutter", "der Sohn", "die Tochter", "der Großvater", "die Großmutter"],
              ["ota", "ona", "o'g'il bola", "qiz bola", "bobo (Opa)", "buvi (Oma)", "amaki / tog'a"], _pairs(6), points=6),
        match("Was passt zusammen?", ["der Onkel", "die Tante", "der Cousin", "die Cousine", "der Neffe", "die Nichte"],
              ["amaki / tog'a", "xola / amma", "amaki / xola o'g'li", "amaki / xola qizi", "jiyan o'g'il", "jiyan qiz", "nabira qiz"], _pairs(6), points=6),
        match("Was passt zusammen?", ["der Ehemann", "die Ehefrau", "die Schwiegermutter", "der Schwiegervater", "der Enkel", "die Enkelin"],
              ["er", "xotin", "qaynona", "qaynota", "nabira o'g'il", "nabira qiz", "qaynisingil"], _pairs(6), points=6),
    ], "Oila a'zosini tarjimasi bilan moslashtiring.", source="vizu"),
    exercise("Der oder die?", [
        choice_gap("___ Vater (ota)", ["der", "die", "das"], "der"),
        choice_gap("___ Tochter (qiz bola)", ["der", "die", "das"], "die"),
        choice_gap("___ Onkel (amaki / tog'a)", ["der", "die", "das"], "der"),
        choice_gap("___ Tante (xola / amma)", ["der", "die", "das"], "die"),
        choice_gap("___ Neffe (jiyan o'g'il)", ["der", "die", "das"], "der"),
        choice_gap("___ Nichte (jiyan qiz)", ["der", "die", "das"], "die"),
        choice_gap("___ Schwager (qayni aka / qayni uka)", ["der", "die", "das"], "der"),
        choice_gap("___ Schwägerin (qaynisingil)", ["der", "die", "das"], "die"),
    ], "Oila so'zlarining artiklini tanlang (erkak — der, ayol — die).", source="vizu"),
    exercise("Wer ist das?", [
        mc("Der Vater von meinem Vater ist mein …", ["Onkel", "Großvater", "Bruder"], "B"),
        mc("Der Bruder von meiner Mutter ist mein …", ["Onkel", "Cousin", "Neffe"], "A"),
        mc("Die Tochter von meiner Tante ist meine …", ["Nichte", "Cousine", "Schwester"], "B"),
        mc("Der Sohn von meinem Bruder ist mein …", ["Neffe", "Enkel", "Cousin"], "A"),
        mc("Die Tochter von meinem Sohn ist meine …", ["Nichte", "Enkelin", "Tochter"], "B"),
        mc("Die Mutter von meinem Ehemann ist meine …", ["Schwiegermutter", "Großmutter", "Tante"], "A"),
    ], "Oila a'zolari o'rtasidagi qarindoshlikni toping.", source="vizu"),
]

# ============================================================
# Übungen — review (VIZU, from the lesson material)
# ============================================================

UEBUNGEN_SETS = [
    exercise("Präsens: ich, du, er …", [
        match("Welche Form passt? (wohnen)", ["ich", "du", "er", "wir"], ["wohne", "wohnst", "wohnt", "wohnen", "wohnest"], _pairs(4), points=4,
              explanation="ich wohne, du wohnst, er wohnt, wir wohnen (ihr wohnt)"),
        choice_gap("Tom ___ gern Fußball.", ["spielt", "spielst", "spiele"], "spielt", explanation="Lesen: „Tom spielt gern Fußball …“"),
        choice_gap("Frau Müller ___ gern.", ["kocht", "kochst", "kochen"], "kocht", explanation="Lesen: „Frau Müller kocht gern …“"),
        choice_gap("Herr Müller ___ auch Englisch.", ["spricht", "sprecht", "sprichst"], "spricht", explanation="e → i: er spricht."),
        choice_gap("Anna ___ gern Märchen.", ["liest", "lest", "lesen"], "liest", explanation="e → ie: sie liest."),
        choice_gap("Du ___ deiner Mutter in der Küche.", ["hilfst", "helfst", "hilft"], "hilfst", explanation="e → i: du hilfst."),
        choice_gap("Er ___ Fahrrad.", ["fährt", "fahrt", "fährst"], "fährt", explanation="a → ä: er fährt."),
        choice_gap("Ihr ___ jeden Tag.", ["arbeitet", "arbeitt", "arbeitest"], "arbeitet", explanation="-t: ihr arbeitet (-e qo'shiladi)."),
    ], "Darsdagi fe'llar bilan Präsensni takrorlang.", source="vizu"),
    exercise("Zahlen im Alltag", [
        choice_gap("Tom ist ___ Jahre alt. (14)", ["vierzehn", "vierzig", "vierundzehn"], "vierzehn", explanation="Lesen: Tom ist 14 Jahre alt."),
        choice_gap("Anna ist ___ Jahre alt. (11)", ["elf", "eins", "zwölf"], "elf", explanation="Lesen: Anna ist 11 Jahre alt."),
        choice_gap("Mein Großvater ist ___ Jahre alt. (78)", ["achtundsiebzig", "siebenundachtzig", "achtzehnsiebzig"], "achtundsiebzig"),
        choice_gap("Meine Mutter ist ___ Jahre alt. (42)", ["zweiundvierzig", "vierundzwanzig", "zweivierzig"], "zweiundvierzig"),
        choice_gap("Das kostet ___ Euro. (15)", ["fünfzehn", "fünfzig", "fünfundzehn"], "fünfzehn"),
        choice_gap("Wir wohnen in Haus Nummer ___. (60)", ["sechzig", "sechszig", "sechzehn"], "sechzig"),
    ], "Raqamni so'z bilan tanlang.", source="vizu"),
]

# ============================================================
# Abschlusstest
# ============================================================

ABSCHLUSSTEST = [
    mc("Er ___ jeden Tag im Büro.", ["arbeitet", "arbeitest", "arbeite"], "A"),
    mc("Du ___ gern Bücher.", ["liest", "lest", "lesen"], "A"),
    mc("Wir ___ in Berlin.", ["wohnt", "wohnen", "wohnst"], "B"),
    mc("Anna ___ Deutsch.", ["sprecht", "sprichst", "spricht"], "C"),
    choice_gap("Ich ___ jeden Morgen um 7 Uhr auf.", ["stehe", "stehst", "aufstehe"], "stehe", explanation="aufstehen: Ich stehe … auf."),
    choice_gap("Du ___ Markus.", ["heißt", "heißst", "heiße"], "heißt"),
    choice_gap("Er ___ lange.", ["schläft", "schlaft", "schläfst"], "schläft"),
    mc("Wie schreibt man 47?", ["vierundsiebzig", "siebenundvierzig", "vierzigsieben"], "B"),
    mc("Wie schreibt man 19?", ["neunzehn", "neunzig", "neunzehnzig"], "A"),
    mc("Wie schreibt man 1.000?", ["eintausend", "einhundert", "zehnhundert"], "A"),
    mc("„die Tochter“ — o'zbekchasi qaysi?", ["qiz bola", "o'g'il bola", "xola"], "A"),
    mc("Die Mutter von meinem Vater ist meine …", ["Tante", "Großmutter", "Cousine"], "B"),
    tf("„der Onkel“ bedeutet „amaki / tog'a“.", True),
    tf("Herr Müller arbeitet als Arzt. (Lesen)", False, "Lesen: „Er arbeitet als Ingenieur in einer Firma.“ Frau Müller ist Ärztin."),
    mc("Wo arbeitet Frau Müller? (Lesen)", ["In einem Krankenhaus", "In einer Firma", "In einer Schule"], "A"),
    match("Was passt zusammen?", ["der Bruder", "die Schwester", "der Sohn", "die Enkelin"],
          ["aka / uka", "opa / singil", "o'g'il bola", "nabira qiz", "qaynona"], _pairs(4), points=4),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: Modul 2", source="vizu", page=13, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Moduls: Germaniyada hayot qanday?", page=14,
             prompt="Germaniyada hayot qanday? Germaniyadagi hayot haqida nimalarni bilasiz? Fikringizni ovozli yuboring (nemischa yoki o'zbekcha).",
             min_duration=10, max_duration=120),
        base(L, "wortschatz", 1, "Wortschatz Modul 2", page=26, words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False),
        base(L, "grammatik", 1, "Grammatik: Präsens und Die Zahlen", page="15-18, 23",
             rules=[
                 {"title": "Präsens — Hozirgi zamon", "html": _PRAESENS},
                 {"title": "Präsens — Qoidalar davomi", "html": _PRAESENS_2},
                 {"title": "Die Zahlen — Raqamlar 1–100", "html": _ZAHLEN},
             ],
             exercises=[
                 exercise("Yozma mashqlar (20 ta): Präsens", WRITTEN, "Fe'lni to'g'ri shaklga keltiring (Präsens). Kitob, 17-bet."),
                 exercise("Test mashqlar (20 ta): Präsens", TEST, "To'g'ri javobni tanlang. Kitob, 18-bet."),
                 exercise("Übung: Die Zahlen", ZAHLEN_EX, "Raqamlarning to'g'ri yozilishini tanlang (kitob, 23-bet).", source="vizu"),
             ]),
        base(L, "lesen", 1, "Lesen: Familie Müller", page="19-21",
             instruction="Lesen Sie die Texte. Antworten Sie, indem Sie A, B oder C wählen.",
             passages=[{"title": "Herr Müller", "text": _with_translation(TEXT_VATER, TEXT_VATER_UZ)},
                       {"title": "Frau Müller", "text": _with_translation(TEXT_MUTTER, TEXT_MUTTER_UZ)},
                       {"title": "Tom", "text": _with_translation(TEXT_TOM, TEXT_TOM_UZ)},
                       {"title": "Anna", "text": _with_translation(TEXT_ANNA, TEXT_ANNA_UZ)}],
             questions=LESEN, max_score=len(LESEN)),
        base(L, "hoeren", 1, "Hören: Meine Familie (Lückentext)", page=22, audio_file="A1-2.mp3", key_pending=True,
             instruction=f"Hören Sie den Text und ergänzen Sie die Lücken. Passende Wörter — mos keladigan so'zlar: {HOEREN_WORDLIST}.",
             metadata={"book_page": 22, "note": "Bo'sh joylarning bir qismi faqat audiodan aniqlanadi — admin audio (A1-2.mp3) ni tinglab javoblarni belgilaydi."},
             questions=gap_paragraphs("Meine Familie — ergänzen Sie die Lücken", HOEREN_TEXT, HOEREN_GAPS)),
        base(L, "sprechen", 1, "Sprechen Sie über Ihre Familie!", page=25, topic="Meine Familie",
             prompt="Sprechen Sie über Ihre Familie. Benutzen Sie die Sätze.",
             questions=["Meine Familie besteht aus … Personen.", "In meiner Familie gibt es …", "Mein Vater heißt …", "Meine Mutter heißt …",
                        "Ich habe … Geschwister.", "Mein Bruder / Meine Schwester heißt …", "Wir wohnen in …",
                        "Am Wochenende … wir gerne zusammen.", "Ich liebe meine Familie, weil …"],
             response_type="monolog", min_duration=20, max_duration=90,
             speech_goal="Familienmitglieder mit Namen nennen, Wohnort und gemeinsame Aktivitäten beschreiben, einen Grund nennen (weil …).",
             keywords=["Familie", "Vater", "Mutter", "Geschwister", "wohnen"]),
        base(L, "schreiben_uebungen", 1, "Schreiben: Meine Familie — Übungen", page=24, source="vizu", exercises=SCHREIBEN_SETS),
        base(L, "schreiben", 1, "Schreiben: Meine Familie vorstellen", page=24,
             prompt="Nemis tilida: Oilani tanishtirish. Stellen Sie Ihre Familie vor. Schreiben Sie über 5–8 Familienmitglieder:\n\n"
                    "Hallo! Ich möchte meine Familie vorstellen.\n"
                    "Mein Großvater (bobom) heißt … und er ist … Jahre alt.\nMeine Großmutter (buvim) heißt … und sie ist … Jahre alt.\n"
                    "Mein Vater / Meine Mutter / Mein Bruder / Meine Schwester / Mein Onkel / Meine Tante / Mein Cousin / Meine Cousine / "
                    "Mein Sohn / Meine Tochter / Mein Enkel / Meine Enkelin / Mein Neffe / Meine Nichte … heißt … und er/sie ist … Jahre alt.",
             task_type="description", min_words=30, max_words=100, time_limit=15,
             support_phrases=["Ich möchte meine Familie vorstellen.", "Mein Vater heißt …", "Meine Mutter heißt …", "… und er ist … Jahre alt.",
                              "… und sie ist … Jahre alt."]),
        base(L, "uebungen", 1, "Übungen Modul 2", exercises=UEBUNGEN_SETS, source="vizu"),
        base(L, "yakuniy", 1, "Abschlusstest: Modul 2", source="vizu",
             instruction="Präsens, raqamlar, oila so'zlari va Lesen matnlari bo'yicha yakuniy test.", questions=ABSCHLUSSTEST),
        base(L, "kompetenz", 2, "Zusammenfassung: Modul 2", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
