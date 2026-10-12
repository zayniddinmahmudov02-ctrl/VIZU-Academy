"""Modul 1 — Herzlich Willkommen! — Grammatik: Deutsches Alphabet (book pp. 3-12).

The book has no Hören task and no grammar exercises in this module. The
Lesen questions and the alphabet exercise are the ones already used on the
platform (source "vizu", created from the book texts / alphabet rules)."""

from . import base, exercise, html_table, match, mc, tf, ul, words

L = 1

_ALPHABET = html_table(
    ["Harf", "Nomi", "Harf", "Nomi", "Harf", "Nomi"],
    [
        ["A a", "A (ah)", "B b", "Be (bay)", "C c", "Ce (tsay)"],
        ["D d", "De (day)", "E e", "E (ay)", "F f", "Ef (eff)"],
        ["G g", "Ge (gay)", "H h", "Ha (hah)", "I i", "I (eeh)"],
        ["J j", "Jott / Je (yot)", "K k", "Ka (kah)", "L l", "El (ell)"],
        ["M m", "Em (em)", "N n", "En (en)", "O o", "O (oh)"],
        ["P p", "Pe (pay)", "Q q", "Qu / Que (koo)", "R r", "Er (err)"],
        ["S s", "Es (es)", "T t", "Te (tay)", "U u", "U (ooh)"],
        ["V v", "Vau (fow)", "W w", "We (vay)", "X x", "Ix (iks)"],
        ["Y y", "Ypsilon (oopsilohn)", "Z z", "Zett (tset)", "Ä ä", "Ä (eh)"],
        ["Ö ö", "Ö (ouh)", "Ü ü", "Ü (uuh)", "ß", "Eszett (ess-set)"],
    ],
)

_IMPORTANT = html_table(
    ["Harf", "Qoida", "Misollar"],
    [
        ["C c", "a, o, u yoki undoshdan oldin — [k]; e, i, ä, ö, ü oldidan — [ts]", "Café [kafe], Clown [klawn]; Cent [tsent], Cinema [tsinema]"],
        ["H h", "So'z boshida yoki unli oldida [h]; ikki unli orasida talaffuz qilinmaydi, oldingi unlini cho'zadi", "Haus [haus] (uy), heute [hoyte] (bugun); sehen [ze:en] (ko'rmoq), gehen [ge:en] (bormoq); Uhr [u:a] (soat), Zahn [tsa:n] (tish)"],
        ["J j", "Asli nemischa so'zlarda [y]; xorijiy so'zlarda [ʒ] (o'zbekcha J)", "Jahr [ya:r] (yil), Junge [yunge] (bola); Job (ish), Joggen (yugurish), Jeans (jinsi)"],
        ["Q q", "Har doim [kv]", "Qualität [kvali'te:t] (sifat), Quelle [kvele] (manba)"],
        ["R r", "So'z boshida yoki undoshdan keyin tomoqdan chiqadigan [ʁ]; so'z yoki bo'g'in oxirida ko'pincha [ɐ] ga yaqin", "Rot (qizil), Brief (xat); Lehrer (o'qituvchi), Mutter (ona)"],
        ["S s", "So'z boshida unli oldidan [z]; so'z oxiri yoki undosh oldidan [s]; sp — [shp], st — [sht]", "Sonne [zone] (quyosh), sieben [zi:ben] (yetti); Haus [haus], ist [ist]; Sport [shport], Straße [shtra:se], Student [shtudent]"],
        ["V v", "Ko'pincha [f]; ba'zi xorijiy so'zlarda [v]", "Vater [fa:ter] (ota), Volk [folk] (xalq); Video, Virus"],
        ["W w", "Har doim [v]", "Wasser [vaser] (suv), Winter [vinter] (qish)"],
        ["Y y", "Ko'pincha [ü] yoki [i]; ba'zi xorijiy so'zlarda [y]", "Physik [füzik] (fizika), Psychologie (psixologiya); Yoga [jo:ga]"],
        ["Z z", "Har doim [ts]", "Zeit [tsayt] (vaqt), Zimmer [tsimmer] (xona)"],
        ["Ä ä", "„a“ va „e“ oralig'idagi tovush", "Mädchen [me:dchen] (qizcha)"],
        ["Ö ö", "„o“ va „e“ aralash tovush", "schön [shø:n] (chiroyli)"],
        ["Ü ü", "„u“ va „i“ aralash tovush", "Tür [ty:r] (eshik)"],
        ["ß", "Eszett („scharfes S“) — har doim [s]", "Straße [shtra:se] (ko'cha), Fußball [fu:sbal] (futbol)"],
    ],
)

_COMBINATIONS = (
    "<h3>A. Harf birikmalari (undoshlar birikmasi)</h3>"
    + html_table(
        ["Birikma", "O'qilishi", "Misollar"],
        [
            ["ch", "[ç] (ich); a, o, u, au dan keyin [x]; ba'zi xorijiy so'zlarda [k]", "ich (men), Küche (oshxona); Bach (soy), Buch (kitob); Charakter (xarakter)"],
            ["sch", "[sh]", "Schule [shu:le] (maktab), Schnee [shne:] (qor)"],
            ["sp", "[shp]", "Sport [shport] (sport), Sprache [shpra:xe] (til)"],
            ["st", "[sht]", "Student [shtudent] (talaba), Stadt [shtat] (shahar)"],
            ["ph", "[f]", "Philosophie (falsafa), Physik (fizika)"],
            ["th", "[t]", "Theater [teater] (teatr), Thema [tema] (mavzu)"],
            ["ck", "[k]", "Jacke [yake] (kurtka), Zucker [tsuker] (shakar)"],
            ["ng", "[ŋ]", "singen (kuylamoq), Finger (barmoq)"],
        ],
    )
    + "<h3>B. Diftonglar (ikki unli tovush birikmasi)</h3>"
    + html_table(
        ["Diftong", "O'qilishi", "Misollar"],
        [
            ["ei / ai", "[ay]", "mein [mayn] (mening), Kaiser (imperator)"],
            ["eu / äu", "[oy]", "neu [noy] (yangi), Häuser [hoyzer] (uylar), Europa, Eule (boyo'g'li)"],
            ["au", "[au]", "Haus [haus] (uy), Auto [auto] (mashina)"],
            ["ie", "[i:] (cho'ziq i)", "Liebe [li:be] (muhabbat), vier [fi:r] (to'rt)"],
        ],
    )
)

GRAMMAR_QUIZ = [
    mc("Nemis alifbosida nechta asosiy harf bor?", ["24", "26", "28", "30"], "B"),
    mc("Nemis tilida nechta Umlaut harfi bor?", ["2", "3", "4", "5"], "B", explanation="Ä, Ö, Ü"),
    mc("„sch“ harf birikmasi o'zbekchaga yaqin qanday o'qiladi?", ["ch", "sh", "s", "k"], "B"),
    mc("„sp“ so'z boshida qanday o'qiladi?", ["sp", "shp", "sht", "sh"], "B"),
    mc("„st“ so'z boshida qanday o'qiladi?", ["st", "sht", "shp", "ts"], "B"),
    mc("„ch“ „ich“ so'zida qanday tovush beradi?", ["[k]", "[ç]", "[sh]", "[t]"], "B"),
    mc("Nemis tilida „ß“ qanday ataladi?", ["Umlaut", "Eszett", "Zett", "Ypsilon"], "B"),
    mc("„z“ harfi nemis tilida qanday o'qiladi?", ["z", "ts", "s", "sh"], "B"),
    mc("„w“ harfi nemis tilida qanday o'qiladi?", ["w", "v", "f", "y"], "B"),
    mc("„v“ ko'p nemis so'zlarida qanday o'qiladi?", ["v", "f", "b", "w"], "B", explanation="Vater [fa:ter]"),
    mc("„j“ nemischa so'zlarda ko'pincha qanday o'qiladi?", ["j", "y", "sh", "ts"], "B", explanation="Jahr [ya:r]"),
    mc("„qu“ qanday o'qiladi?", ["ku", "kv", "shu", "tsu"], "B"),
    mc("„ei“ qanday o'qiladi?", ["ey", "ay", "iy", "oy"], "B", explanation="mein [mayn]"),
    mc("„eu“ qanday o'qiladi?", ["ay", "oy", "au", "iy"], "B", explanation="neu [noy]"),
    mc("„au“ qanday o'qiladi?", ["ay", "oy", "au", "u"], "C"),
    mc("„ie“ qanday o'qiladi?", ["[i:] (cho'ziq i)", "ay", "oy", "e"], "A"),
    mc("„ph“ qanday o'qiladi?", ["p", "f", "h", "v"], "B"),
    mc("„th“ qanday o'qiladi?", ["t", "th", "f", "s"], "A"),
    mc("„ck“ qanday o'qiladi?", ["k", "ts", "sh", "g"], "A"),
    mc("„ng“ qanday tovush beradi?", ["n", "[ŋ]", "g", "nk"], "B"),
]

TEXT_1 = "Hallo! Ich heiße Tom und ich bin 10 Jahre alt. Ich komme aus Usbekistan und wohne in Taschkent. Ich gehe in die Schule und lerne Deutsch. Ich mag Fußball. Danke!"
TEXT_2 = "Hallo! Ich heiße Anna und ich bin 9 Jahre alt. Ich komme aus Usbekistan und wohne in Taschkent. Ich gehe in die Schule und lerne Deutsch. Ich mag Malen und Musik. Danke!"
TEXT_3 = ("Hallo! Wir heißen Tom und Anna. Wir sind 10 und 9 Jahre alt. Wir kommen aus Usbekistan und wohnen in Taschkent. "
          "Wir gehen in die Schule und lernen Deutsch. Wir mögen Fußball, Malen und Musik. Danke!")
TEXT_4 = ("Es ist Samstag. Tom und Anna gehen in den Park. Es ist sonnig und warm. Tom spielt Fußball und Anna liest ein Buch. "
          "Ein Hund kommt und läuft zu ihnen. Sie lachen und spielen mit dem Hund. Nach zwei Stunden gehen sie nach Hause. "
          "Sie sind müde, aber glücklich.")

LESEN_QUESTIONS = [
    mc("Wie alt ist Tom?", ["8 Jahre", "10 Jahre", "12 Jahre"], "B", "Matnda: „Ich bin 10 Jahre alt.“", passage=1),
    mc("Wo wohnt Tom?", ["In Berlin", "In München", "In Taschkent"], "C", "Matnda: „Ich wohne in Taschkent.“", passage=1),
    tf("Tom kommt aus Usbekistan.", True, "Matnda: „Ich komme aus Usbekistan.“", passage=1),
    mc("Was lernt Tom in der Schule?", ["Englisch", "Deutsch", "Russisch"], "B", "Matnda: „Ich gehe in die Schule und lerne Deutsch.“", passage=1),
    mc("Was mag Tom?", ["Malen", "Fußball", "Musik"], "B", "Matnda: „Ich mag Fußball.“", passage=1),
    tf("Anna ist 9 Jahre alt.", True, "Matnda: „Ich bin 9 Jahre alt.“", passage=2),
    mc("Was mag Anna?", ["Fußball und Tennis", "Malen und Musik", "Lesen und Schwimmen"], "B", "Matnda: „Ich mag Malen und Musik.“", passage=2),
    mc("Woher kommt Anna?", ["Aus Deutschland", "Aus Usbekistan", "Aus Österreich"], "B", "Matnda: „Ich komme aus Usbekistan.“", passage=2),
    tf("Anna wohnt in Berlin.", False, "Noto'g'ri — matnda: „Ich wohne in Taschkent.“", passage=2),
    mc("Was lernt Anna?", ["Deutsch", "Französisch", "Englisch"], "A", "Matnda: „Ich gehe in die Schule und lerne Deutsch.“", passage=2),
    tf("Tom und Anna kommen aus Deutschland.", False, "Noto'g'ri — matnda: „Wir kommen aus Usbekistan.“", passage=3),
    mc("Wie alt sind Tom und Anna?", ["10 und 9 Jahre", "9 und 8 Jahre", "11 und 10 Jahre"], "A", "Matnda: „Wir sind 10 und 9 Jahre alt.“", passage=3),
    mc("Wo wohnen Tom und Anna?", ["In Samarkand", "In Taschkent", "In Buchara"], "B", "Matnda: „Wir wohnen in Taschkent.“", passage=3),
    tf("Tom und Anna gehen in die Schule.", True, "Matnda: „Wir gehen in die Schule.“", passage=3),
    mc("Was mögen Tom und Anna?", ["Fußball, Malen und Musik", "Tennis und Schwimmen", "Lesen und Kochen"], "A",
       "Matnda: „Wir mögen Fußball, Malen und Musik.“", passage=3),
    mc("Welcher Tag ist es?", ["Sonntag", "Samstag", "Montag"], "B", "Matnda: „Es ist Samstag.“", passage=4),
    mc("Wohin gehen Tom und Anna?", ["In die Schule", "In den Park", "Nach Hause"], "B", "Matnda: „Tom und Anna gehen in den Park.“", passage=4),
    mc("Was macht Anna im Park?", ["Sie spielt Fußball.", "Sie liest ein Buch.", "Sie malt."], "B", "Matnda: „Anna liest ein Buch.“", passage=4),
    tf("Ein Hund kommt und spielt mit Tom und Anna.", True, "Matnda: „Ein Hund kommt … Sie lachen und spielen mit dem Hund.“", passage=4),
    mc("Wie sind Tom und Anna am Ende?", ["Müde, aber glücklich", "Traurig", "Krank"], "A", "Matnda: „Sie sind müde, aber glücklich.“", passage=4),
]

WORDS = (
    words([("ich", "men"), ("du", "sen"), ("er", "u (erkak)"), ("sie", "u (ayol)"), ("wir", "biz"), ("ihr", "siz (sizlar)"), ("sie", "ular")],
          "Personen")
    + words([("die", "Schule", "maktab"), ("lernen", "o'rganmoq"), ("der", "Deutschunterricht", "nemis tili darsi"), ("das", "Buch", "kitob"),
             ("das", "Heft", "daftar"), ("der", "Stift", "ruchka")], "Schule und Lernen")
    + words([("die", "Mutter", "ona"), ("der", "Vater", "ota"), ("der", "Bruder", "aka / uka"), ("die", "Schwester", "opa / singil"),
             ("die", "Familie", "oila"), ("der", "Freund", "do'st (o'g'il)"), ("die", "Freundin", "do'st (qiz)")], "Familie")
    + words([("Fußball spielen", "futbol o'ynamoq"), ("malen", "rasm chizmoq"), ("Musik hören", "musiqa tinglamoq"), ("lesen", "o'qimoq"),
             ("schwimmen", "suzmoq"), ("Rad fahren", "velosiped haydamoq")], "Hobbys und Freizeit")
    + words([("der", "Morgen", "tong"), ("der", "Tag", "kun"), ("der", "Abend", "kechqurun"), ("die", "Nacht", "tun"), ("Montag", "dushanba"),
             ("Dienstag", "seshanba"), ("Mittwoch", "chorshanba"), ("Donnerstag", "payshanba"), ("Freitag", "juma"), ("Samstag", "shanba"),
             ("Sonntag", "yakshanba")], "Tageszeiten und Tage")
    + words([("sonnig", "quyoshli"), ("warm", "iliq"), ("kalt", "sovuq"), ("regnerisch", "yomg'irli"), ("windig", "shamolli"),
             ("der", "Frühling", "bahor"), ("der", "Sommer", "yoz"), ("der", "Herbst", "kuz"), ("der", "Winter", "qish")], "Wetter und Jahreszeiten")
    + words([("kommen", "kelmoq"), ("wohnen", "yashamoq"), ("gehen", "bormoq"), ("mögen", "yoqtirmoq"), ("danke", "rahmat"),
             ("bitte", "iltimos"), ("ja", "ha"), ("nein", "yo'q")], "Wichtige Wörter")
)


def items() -> list[dict]:
    return [
        base(L, "frage", 1, "Frage des Themas: Nima uchun nemis tili?", page=4,
             prompt="Nima uchun nemis tili? Nima uchun aynan nemis tilini o'rganmoqchisiz? Fikringizni 2–3 gap bilan ovozli yuboring "
                    "(nemischa yoki o'zbekcha).",
             min_duration=10, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Das deutsche Alphabet", page="5-7",
             rules=[
                 {"title": "Das deutsche Alphabet", "html": "<h3>Nemis tili alifbosi</h3>" + _ALPHABET},
                 {"title": "Nemis alifbosidagi muhim harflar", "html": _IMPORTANT},
                 {"title": "Harf birikmalari va diftonglar", "html": _COMBINATIONS},
             ],
             exercises=[exercise("Übung: Alphabet und Aussprache", GRAMMAR_QUIZ,
                                 "Alifbo va talaffuz qoidalari bo'yicha to'g'ri javobni tanlang.", source="vizu")]),
        base(L, "lesen", 1, "Lesen: Tom und Anna", page="8-9", source="vizu",
             instruction="Lesen Sie die Texte und beantworten Sie die Fragen.",
             metadata={"book_page": "8-9", "note": "Matnlar kitobdan; savollar VIZU tomonidan matn asosida tuzilgan (kitobda savol yo'q)."},
             passages=[
                 {"title": "Text 1: Tom", "text": TEXT_1},
                 {"title": "Text 2: Anna", "text": TEXT_2},
                 {"title": "Text 3: Tom und Anna", "text": TEXT_3},
                 {"title": "Text 4: Im Park", "text": TEXT_4},
             ],
             questions=LESEN_QUESTIONS, max_score=len(LESEN_QUESTIONS)),
        base(L, "schreiben", 1, "Topshiriq 1", page=10,
             prompt="Schreiben Sie über sich. Ergänzen Sie den Text mit Ihren Informationen:\n\n"
                    "Hallo! Ich heiße ____, ich bin ____ Jahre alt, ich komme aus ____ und wohne in ____.\n"
                    "Ich gehe in die Schule und lerne ____. Ich mag ____.\n\n"
                    "Beispiel (Tom): 10, Fußball, Usbekistan, Tom, Taschkent, Deutsch",
             task_type="description", min_words=20, max_words=60, time_limit=10,
             support_phrases=["Ich heiße …", "Ich bin … Jahre alt.", "Ich komme aus …", "Ich wohne in …", "Ich lerne …", "Ich mag …"]),
        base(L, "schreiben", 2, "Topshiriq 3", page=10,
             prompt="Schreiben Sie über Ihren Freund / Ihre Freundin:\n\n"
                    "Das ist mein Freund / meine Freundin ____. Er/Sie ist ____ Jahre alt, er/sie kommt aus ____ und wohnt in ____.\n"
                    "Er/Sie geht in die Schule und lernt ____. Er/Sie mag ____.\n\n"
                    "Beispiel (Anna): Usbekistan, Anna, Malen und Musik, Taschkent, 9, Deutsch",
             task_type="description", audience="Freund / Freundin", min_words=20, max_words=60, time_limit=10,
             support_phrases=["Das ist mein Freund …", "Er/Sie ist … Jahre alt.", "Er/Sie kommt aus …", "Er/Sie wohnt in …", "Er/Sie mag …"]),
        base(L, "sprechen", 1, "Stellen Sie sich vor!", page=11, topic="Sich vorstellen – Erzählen Sie über sich!",
             prompt="Sich vorstellen — Erzählen Sie über sich! Sprechen Sie mit diesen Sätzen.",
             questions=["Hallo! Ich heiße … , ich bin … Jahre alt.", "Ich komme aus … und wohne in …", "Ich gehe in die Schule und lerne …",
                        "Ich mag … (z. B. Fußball, Musik, Bücher).", "Meine Hobbys sind …", "Mein Lieblingsfach ist …",
                        "Ich habe … Bruder / … Schwester.", "Meine Familie ist …", "Ich freue mich, Deutsch zu lernen!"],
             response_type="monolog", min_duration=20, max_duration=90,
             speech_goal="Name, Alter, Herkunft, Wohnort, Schule/Deutsch, Hobbys und Familie in einfachen Sätzen nennen.",
             keywords=["Ich heiße", "Jahre alt", "Ich komme aus", "Ich wohne in", "Ich mag"]),
        base(L, "wortschatz", 1, "Wortschatz Modul 1", page=12, words=WORDS),
        base(L, "yakuniy", 1, "Yakuniy Test: Modul 1", source="vizu",
             instruction="Alifbo, talaffuz va darsdagi so'zlar bo'yicha yakuniy test.",
             questions=[
                 mc("Wie spricht man „W“ in „Wasser“ aus?", ["[v]", "[w]", "[f]"], "A"),
                 mc("Wie heißt der Buchstabe „ß“?", ["Eszett", "Umlaut", "Ypsilon"], "A"),
                 mc("Welches Wort beginnt mit [sht]?", ["Straße", "Sonne", "Zimmer"], "A"),
                 mc("„ei“ in „mein“ klingt wie …", ["[ay]", "[ey]", "[i:]"], "A"),
                 mc("„die Schwester“ — o'zbekchasi qaysi?", ["ota", "opa / singil", "aka / uka"], "B"),
                 mc("„Mittwoch“ — o'zbekchasi qaysi?", ["seshanba", "chorshanba", "payshanba"], "B"),
                 mc("„der Herbst“ — o'zbekchasi qaysi?", ["kuz", "bahor", "qish"], "A"),
                 tf("„sonnig“ bedeutet „quyoshli“.", True),
                 tf("„nein“ bedeutet „ha“.", False, "„nein“ — yo'q, „ja“ — ha."),
                 match("Was passt zusammen?", ["ich", "du", "wir", "ihr"], ["men", "sen", "biz", "siz (sizlar)", "ular"],
                       {"1": "A", "2": "B", "3": "C", "4": "D"}),
             ]),
    ]
