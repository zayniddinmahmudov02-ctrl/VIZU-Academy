"""Modul 1 — Herzlich Willkommen! — Grammatik: Deutsches Alphabet (book pp. 3-12).

Book pages: 3 cover (Mavzu / Grammatik), 4 Frage des Themas, 5 alphabet,
6 important letters, 7 letter combinations and diphthongs, 8 Lesen (three
texts with Uzbek translations), 9 Hören (the park text + translation, audio
A1-1.mp3), 10 Schreiben (four fill-in tasks with word banks), 11 Sprechen,
12 Wortschatz.

The book has no questions for its Lesen / Hören texts and no exercises for
the alphabet or the words: those are created by VIZU strictly from the
book's own texts, tables and word list (source "vizu"); every answer can be
found in the book material."""

from . import base, choice_gap, exercise, gap, html_table, match, mc, tf, ul, words

L = 1
LESSON_TITLE = "Herzlich Willkommen!"
LESSON_DESCRIPTION = "Thema: Herzlich Willkommen! · Grammatik: Das deutsche Alphabet"

# book page images (app/data/vizu_deutsch_a1/images/modul_01) -> competency
IMAGES = [
    ("01_cover.jpg", "EINFUEHRUNG", "Modul 1 — Herzlich Willkommen! (Buch, S. 3)"),
    ("02_frage.jpg", "EINFUEHRUNG", "Frage des Themas: Nima uchun nemis tili? (Buch, S. 4)"),
    ("03_alphabet.jpg", "GRAMMATIK", "Nemis tili alifbosi (Buch, S. 5)"),
    ("04_harflar.jpg", "GRAMMATIK", "Muhim harflar va ularning o'qilishi (Buch, S. 6)"),
    ("05_birikmalar.jpg", "GRAMMATIK", "Harf birikmalari va diftonglar (Buch, S. 7)"),
    ("06_lesen.jpg", "LESEN", "Lesen — Tom und Anna (Buch, S. 8)"),
    ("07_schreiben.jpg", "SCHREIBEN", "Schreiben — Aufgaben 1-4 (Buch, S. 10)"),
    ("08_sprechen.jpg", "SPRECHEN", "Sprechen — Stellen Sie sich vor! (Buch, S. 11)"),
    ("09_wortschatz.jpg", "WORTSCHATZ", "Wortschatz Modul 1 (Buch, S. 12)"),
]

# ============================================================
# Einführung / Zusammenfassung (competency texts)
# ============================================================

EINFUEHRUNG_HTML = (
    "<h3>Modul 1 — Herzlich Willkommen!</h3>"
    "<p><strong>Mavzu:</strong> Herzlich Willkommen · <strong>Grammatik:</strong> Das deutsche Alphabet (nemis alifbosi)</p>"
    "<h4>Dars maqsadlari</h4>"
    + ul([
        "nemis alifbosidagi 26 harf, Ä Ö Ü va ß ni tanish va ularning nomini aytish;",
        "muhim harflar (C, H, J, Q, R, S, V, W, Y, Z) va harf birikmalari (ch, sch, sp, st, ei, eu, ie …) qanday o'qilishini bilish;",
        "o'zingiz haqingizda oddiy gaplar tuzish: ism, yosh, qayerdan ekanligingiz, qayerda yashashingiz, nima yoqishi;",
        "1-modul so'zlarini (shaxs olmoshlari, maktab, oila, hobbilar, kunlar, ob-havo) o'rganish.",
    ])
    + "<h4>Dars oxirida siz quyidagilarni bajara olasiz</h4>"
    + ul([
        "„Hallo! Ich heiße … Ich bin … Jahre alt. Ich komme aus … und wohne in …“ — o'zingizni nemis tilida tanishtirasiz;",
        "ismingizni harflab aytasiz (buchstabieren);",
        "Tom va Anna haqidagi qisqa matnlarni o'qib, savollarga javob berasiz;",
        "parkdagi kun haqidagi matnni tinglab tushunasiz.",
    ])
    + "<h4>Darsning tuzilishi</h4>"
    + "<p>Einführung → Wortschatz → Grammatik → Lesen → Hören → Sprechen → Schreiben → Übungen → Abschlusstest → Zusammenfassung</p>"
)

ZUSAMMENFASSUNG_HTML = (
    "<h3>Modul 1 — qisqacha</h3>"
    + ul([
        "<strong>Alphabet:</strong> A–Z, Umlaute Ä Ö Ü va ß (Eszett). W = [v], V = ko'pincha [f], Z = [ts], J = [y], Qu = [kv].",
        "<strong>Birikmalar:</strong> sch = [sh], sp/st (so'z boshida) = [shp]/[sht], ch = [ç]/[x], ei = [ay], eu/äu = [oy], ie = [i:].",
        "<strong>O'zini tanishtirish:</strong> Ich heiße … · Ich bin … Jahre alt. · Ich komme aus … · Ich wohne in … · Ich lerne Deutsch. · Ich mag …",
        "<strong>Wortschatz:</strong> ich, du, er, sie, wir, ihr · die Schule, das Buch, das Heft · die Familie · Montag … Sonntag · sonnig, warm, kalt.",
    ])
    + "<p>Natijalaringiz pastda — tugallanmagan bo'limlarni yakunlang, so'ng keyingi darsga o'ting.</p>"
)

# ============================================================
# Grammatik — Das deutsche Alphabet (pp. 5-7)
# ============================================================

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
        ["Ü ü", "Ü (uuh)", "Ö ö", "Ö (ouh)", "ß", "Eszett (ess-set)"],
    ],
)

_IMPORTANT = html_table(
    ["Harf", "Qoida", "Misollar"],
    [
        ["C c", "a, o, u yoki undoshdan oldin — [k]; e, i, ä, ö, ü oldidan — [ts]", "Cafe [kafe], Clown [klawn]; Cent [tsent], Cinema [tsinema]"],
        ["H h", "So'z boshida yoki unli oldida [h]; ikki unli orasida talaffuz qilinmaydi va oldingi unlini cho'zadi; ba'zi so'zlarda faqat unlining uzunligini bildiradi",
         "Haus [haus] (uy), heute [hoyte] (bugun); sehen [ze:en] (ko'rmoq), gehen [ge:en] (bormoq); Uhr [u:a] (soat), Zahn [tsa:n] (tish)"],
        ["J j", "Asli nemischa so'zlarda [y]; xorijiy so'zlarda [ʒ] (o'zbekcha J)", "Jahr [ya:r] (yil), Junge [yunge] (bola); Job (ish), Joggen (yugurish), Jeans (jinsi)"],
        ["Q q", "Har doim [kv]", "Qualität [kvali'te:t] (sifat), Quelle [kvelə] (manba)"],
        ["R r", "So'z boshida yoki undoshdan keyin tomoqdan chiqadigan [ʁ]; so'z yoki bo'g'in oxirida ko'pincha [ɐ] ga yaqin",
         "Rot [ʁo:t] (qizil), Brief [bʁi:f] (xat); Lehrer [le:ʁɐ] (o'qituvchi), Mutter [mutɐ] (ona)"],
        ["S s", "So'z boshida unli oldidan [z]; so'z oxiri yoki undosh oldidan [s]; sp — [shp], st — [sht]",
         "Sonne [zonə] (quyosh), sieben [zi:bən] (yetti); Haus [haus] (uy), ist [ist] (dir); Sport [shport], sprechen [shprechen]; Straße [shtra:se], Student [shtudent]"],
        ["V v", "Ko'pincha [f]; ba'zi xorijiy so'zlarda [v]", "Vater [fa:ter] (ota), Volk [folk] (xalq); Video [video], Virus [virus]"],
        ["W w", "Har doim [v]", "Wasser [vaser] (suv), Winter [vinter] (qish)"],
        ["Y y", "Ko'pincha [ü] yoki [i] tovushiga yaqin; ba'zi xorijiy so'zlarda [y]", "Physik [füzik] (fizika), Psychologie [psüxolo'gi:] (psixologiya); Yoga [jo:ga]"],
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
            ["ch", "[ç]; a, o, u, au dan keyin [x]; ba'zi xorijiy so'zlarda [k]", "ich [ix] (men), Küche [kyxə] (oshxona); Bach [bax] (soy), Buch [bux] (kitob); Charakter [karakter] (xarakter)"],
            ["sch", "[sh]", "Schule [shu:lə] (maktab), Schnee [shne:] (qor)"],
            ["sp", "[shp]", "Sport [shport] (sport), Sprache [shpra:xə] (til)"],
            ["st", "[sht]", "Student [shtudent] (talaba), Stadt [shtat] (shahar)"],
            ["ph", "[f]", "Philosophie [filozofi:] (falsafa), Physik [fizik] (fizika)"],
            ["th", "[t]", "Theater [teater] (teatr), Thema [tema] (mavzu)"],
            ["ck", "[k]", "Jacke [yaka] (kurtka), Zucker [tsuker] (shakar)"],
            ["ng", "[ŋ]", "singen [ziŋən] (kuylamoq), Finger (barmoq)"],
        ],
    )
    + "<h3>B. Diftonglar (ikki unli tovush birikmasi)</h3>"
    + html_table(
        ["Diftong", "O'qilishi", "Misollar"],
        [
            ["ei / ai", "[ay]", "mein [mayn] (mening), Kaiser (imperator)"],
            ["eu / äu", "[oy]", "neu [noy] (yangi), Häuser [hoyzer] (uylar)"],
            ["au", "[au]", "Haus [haus] (uy), Auto [auto] (mashina)"],
            ["ie", "[i:] (cho'ziq i)", "Liebe [li:bə] (muhabbat), vier [fi:r] (to'rt)"],
            ["eu (xorijiy so'zlarda)", "[oy] yoki [eü]", "Europa [oyropa] (Yevropa), Eule (boyo'g'li)"],
        ],
    )
)

ALPHABET_NAMES = exercise("Übung 1: Buchstaben und ihre Namen", [
    match("Welcher Name gehört zu welchem Buchstaben?",
          ["B", "C", "H", "J", "Q", "V"],
          ["Be (bay)", "Ce (tsay)", "Ha (hah)", "Jott / Je (yot)", "Qu / Que (koo)", "Vau (fow)", "We (vay)"],
          {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E", "6": "F"}, points=6,
          explanation="Buch, S. 5: B — Be, C — Ce, H — Ha, J — Jott, Q — Qu, V — Vau."),
    match("Welcher Name gehört zu welchem Buchstaben?",
          ["W", "Y", "Z", "ß", "X", "R"],
          ["Ix (iks)", "Er (err)", "We (vay)", "Ypsilon (oopsilohn)", "Zett (tset)", "Eszett (ess-set)", "Vau (fow)"],
          {"1": "C", "2": "D", "3": "E", "4": "F", "5": "A", "6": "B"}, points=6,
          explanation="Buch, S. 5: W — We, Y — Ypsilon, Z — Zett, ß — Eszett, X — Ix, R — Er."),
], "Harfni uning nemischa nomi bilan moslashtiring (kitob, 5-bet).", source="vizu")

ALPHABET_CASE = exercise("Übung 2: Groß- und Kleinbuchstaben", [
    match("Großbuchstabe — Kleinbuchstabe: Was passt zusammen?",
          ["A", "B", "D", "E", "G", "Q"],
          ["a", "b", "d", "e", "g", "q", "p"],
          {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E", "6": "F"}, points=6),
    match("Großbuchstabe — Kleinbuchstabe: Was passt zusammen?",
          ["R", "T", "Ä", "Ö", "Ü", "N"],
          ["ü", "ö", "ä", "r", "t", "n", "u"],
          {"1": "D", "2": "E", "3": "C", "4": "B", "5": "A", "6": "F"}, points=6),
    mc("Welcher Buchstabe hat keinen Großbuchstaben im Alphabet der Buchseite?", ["ß", "ä", "z", "y"], "A",
       "Buch, S. 5: „ß“ steht im Alphabet nur klein (Eszett)."),
], "Katta va kichik harflarni moslashtiring.", source="vizu")

ALPHABET_RULES = exercise("Übung 3: Wie liest man das?", [
    mc("Nemis alifbosida (Ä, Ö, Ü, ß dan tashqari) nechta harf bor?", ["24", "26", "28", "30"], "B", "Buch, S. 5: A dan Z gacha 26 harf."),
    mc("Nemis tilida nechta Umlaut harfi bor?", ["2", "3", "4", "5"], "B", "Ä, Ö, Ü"),
    mc("„sch“ harf birikmasi qanday o'qiladi?", ["[ch]", "[sh]", "[s]", "[k]"], "B", "Schule [shu:lə]"),
    mc("„sp“ (Sport) qanday o'qiladi?", ["[sp]", "[shp]", "[sht]", "[sh]"], "B"),
    mc("„st“ (Student) qanday o'qiladi?", ["[st]", "[sht]", "[shp]", "[ts]"], "B"),
    mc("„ch“ „ich“ so'zida qanday tovush beradi?", ["[k]", "[ç]", "[sh]", "[t]"], "B"),
    mc("„ch“ „Buch“ so'zida (u dan keyin) qanday o'qiladi?", ["[ç]", "[x]", "[k]", "[sh]"], "B", "a, o, u, au dan keyin [x]: Bach, Buch."),
    mc("„ß“ qanday ataladi?", ["Umlaut", "Eszett", "Zett", "Ypsilon"], "B"),
    mc("„z“ qanday o'qiladi?", ["[z]", "[ts]", "[s]", "[sh]"], "B", "Zeit [tsayt]"),
    mc("„w“ qanday o'qiladi?", ["[w]", "[v]", "[f]", "[y]"], "B", "Wasser [vaser]"),
    mc("„v“ ko'pincha qanday o'qiladi?", ["[v]", "[f]", "[b]", "[w]"], "B", "Vater [fa:ter]"),
    mc("„j“ asli nemischa so'zlarda qanday o'qiladi?", ["[j]", "[y]", "[sh]", "[ts]"], "B", "Jahr [ya:r]"),
    mc("„qu“ qanday o'qiladi?", ["[ku]", "[kv]", "[shu]", "[tsu]"], "B", "Qualität [kvali'te:t]"),
    mc("„ei“ qanday o'qiladi?", ["[ey]", "[ay]", "[iy]", "[oy]"], "B", "mein [mayn]"),
    mc("„eu“ qanday o'qiladi?", ["[ay]", "[oy]", "[au]", "[iy]"], "B", "neu [noy]"),
    mc("„ie“ qanday o'qiladi?", ["[i:] (cho'ziq i)", "[ay]", "[oy]", "[e]"], "A", "vier [fi:r]"),
    mc("„ph“ qanday o'qiladi?", ["[p]", "[f]", "[h]", "[v]"], "B", "Physik"),
    mc("„th“ qanday o'qiladi?", ["[t]", "[th]", "[f]", "[s]"], "A", "Theater [teater]"),
    mc("„ck“ qanday o'qiladi?", ["[k]", "[ts]", "[sh]", "[g]"], "A", "Zucker [tsuker]"),
    mc("„s“ so'z boshida unli oldidan („Sonne“) qanday o'qiladi?", ["[s]", "[z]", "[sh]", "[ts]"], "B", "Sonne [zonə]"),
    mc("„c“ „Cafe“ so'zida (a oldidan) qanday o'qiladi?", ["[ts]", "[k]", "[s]", "[ch]"], "B", "a, o, u oldidan [k]."),
    mc("„c“ „Cent“ so'zida (e oldidan) qanday o'qiladi?", ["[k]", "[ts]", "[s]", "[ch]"], "B", "e, i, ä, ö, ü oldidan [ts]."),
], "Alifbo va talaffuz qoidalari bo'yicha to'g'ri javobni tanlang (kitob, 5-7-betlar).", source="vizu")

# ============================================================
# Lesen (p. 8) — three texts with the book's Uzbek translation
# ============================================================

TEXT_1 = "Hallo! Ich heiße Tom und ich bin 10 Jahre alt. Ich komme aus Usbekistan und wohne in Taschkent. Ich gehe in die Schule und lerne Deutsch. Ich mag Fußball. Danke!"
TEXT_1_UZ = "Salom! Mening ismim Tom va men 10 yoshdaman. Men O'zbekistondan va Toshkentda yashayman. Men maktabga boraman va nemis tilini o'rganaman. Menga futbol yoqadi. Rahmat!"
TEXT_2 = "Hallo! Ich heiße Anna und ich bin 9 Jahre alt. Ich komme aus Usbekistan und wohne in Taschkent. Ich gehe in die Schule und lerne Deutsch. Ich mag Malen und Musik. Danke!"
TEXT_2_UZ = "Salom! Mening ismim Anna va men 9 yoshdaman. Men O'zbekistondan va Toshkentda yashayman. Men maktabga boraman va nemis tilini o'rganaman. Menga rasm chizish va musiqa yoqadi. Rahmat!"
TEXT_3 = ("Hallo! Wir heißen Tom und Anna. Wir sind 10 und 9 Jahre alt. Wir kommen aus Usbekistan und wohnen in Taschkent. "
          "Wir gehen in die Schule und lernen Deutsch. Wir mögen Fußball, Malen und Musik. Danke!")
TEXT_3_UZ = ("Salom! Bizning ismimiz Tom va Anna. Biz 10 va 9 yoshdamiz. Biz O'zbekistonlikmiz va Toshkentda yashaymiz. "
             "Biz maktabga boramiz va nemis tilini o'rganamiz. Bizga futbol, rasm chizish va musiqa yoqadi. Rahmat!")


def _with_translation(de: str, uz: str) -> str:
    return f"{de}\n\nO'zbekcha tarjima: {uz}"


LESEN_QUESTIONS = [
    mc("Wie alt ist Tom?", ["8 Jahre", "10 Jahre", "12 Jahre"], "B", "Matnda: „Ich bin 10 Jahre alt.“", passage=1),
    mc("Wo wohnt Tom?", ["In Berlin", "In München", "In Taschkent"], "C", "Matnda: „Ich … wohne in Taschkent.“", passage=1),
    tf("Tom kommt aus Usbekistan.", True, "Matnda: „Ich komme aus Usbekistan.“", passage=1),
    mc("Was lernt Tom in der Schule?", ["Englisch", "Deutsch", "Russisch"], "B", "Matnda: „Ich gehe in die Schule und lerne Deutsch.“", passage=1),
    mc("Was mag Tom?", ["Malen", "Fußball", "Musik"], "B", "Matnda: „Ich mag Fußball.“", passage=1),
    gap("Ergänzen Sie den Text über Tom.", "Ich heiße Tom und ich bin [[1]] Jahre alt. Ich komme aus [[2]].",
        {"1": {"accepted": ["10"], "options": ["9", "10", "12"]}, "2": {"accepted": ["Usbekistan"], "options": ["Deutschland", "Usbekistan", "Taschkent"]}},
        points=2, explanation="Matnda: „Ich heiße Tom und ich bin 10 Jahre alt. Ich komme aus Usbekistan …“", passage=1),
    tf("Anna ist 9 Jahre alt.", True, "Matnda: „Ich bin 9 Jahre alt.“", passage=2),
    mc("Was mag Anna?", ["Fußball und Tennis", "Malen und Musik", "Lesen und Schwimmen"], "B", "Matnda: „Ich mag Malen und Musik.“", passage=2),
    mc("Woher kommt Anna?", ["Aus Deutschland", "Aus Usbekistan", "Aus Österreich"], "B", "Matnda: „Ich komme aus Usbekistan.“", passage=2),
    tf("Anna wohnt in Berlin.", False, "Noto'g'ri — matnda: „… und wohne in Taschkent.“", passage=2),
    gap("Ergänzen Sie den Text über Anna.", "Ich gehe in die [[1]] und lerne [[2]].",
        {"1": {"accepted": ["Schule"], "options": ["Schule", "Familie", "Musik"]}, "2": {"accepted": ["Deutsch"], "options": ["Englisch", "Deutsch", "Malen"]}},
        points=2, explanation="Matnda: „Ich gehe in die Schule und lerne Deutsch.“", passage=2),
    tf("Tom und Anna kommen aus Deutschland.", False, "Noto'g'ri — matnda: „Wir kommen aus Usbekistan.“", passage=3),
    mc("Wie alt sind Tom und Anna?", ["10 und 9 Jahre", "9 und 8 Jahre", "11 und 10 Jahre"], "A", "Matnda: „Wir sind 10 und 9 Jahre alt.“", passage=3),
    mc("Wo wohnen Tom und Anna?", ["In Samarkand", "In Taschkent", "In Buchara"], "B", "Matnda: „… und wohnen in Taschkent.“", passage=3),
    tf("Tom und Anna gehen in die Schule.", True, "Matnda: „Wir gehen in die Schule …“", passage=3),
    mc("Was mögen Tom und Anna?", ["Fußball, Malen und Musik", "Tennis und Schwimmen", "Lesen und Kochen"], "A",
       "Matnda: „Wir mögen Fußball, Malen und Musik.“", passage=3),
    gap("Ergänzen Sie den Text.", "Wir [[1]] Tom und Anna. Wir [[2]] in die Schule und lernen Deutsch.",
        {"1": {"accepted": ["heißen"], "options": ["heißen", "heiße", "heißt"]}, "2": {"accepted": ["gehen"], "options": ["gehe", "gehen", "geht"]}},
        points=2, explanation="Matnda: „Wir heißen Tom und Anna. … Wir gehen in die Schule …“", passage=3),
]

# ============================================================
# Hören (p. 9) — the park text; audio A1-1.mp3 is uploaded by an admin
# ============================================================

HOEREN_TEXT = ("Es ist Samstag. Tom und Anna gehen in den Park. Es ist sonnig und warm. Tom spielt Fußball und Anna liest ein Buch. "
               "Ein Hund kommt und läuft zu ihnen. Sie lachen und spielen mit dem Hund. Nach zwei Stunden gehen sie nach Hause. "
               "Sie sind müde, aber glücklich.")
HOEREN_TEXT_UZ = ("Shanba kuni. Tom va Anna parkka borishadi. Quyoshli va iliq kun. Tom futbol o'ynaydi, Anna esa kitob o'qiydi. "
                  "Bir it kelib ularga qo'shiladi. Ular kulib, it bilan o'ynashadi. Ikki soatdan so'ng uyga ketishadi. "
                  "Ular charchagan, lekin baxtli.")

HOEREN_QUESTIONS = [
    mc("Welcher Tag ist es?", ["Sonntag", "Samstag", "Montag"], "B", "Audio: „Es ist Samstag.“"),
    mc("Wohin gehen Tom und Anna?", ["In die Schule", "In den Park", "Nach Hause"], "B", "Audio: „Tom und Anna gehen in den Park.“"),
    tf("Es ist kalt und regnerisch.", False, "Noto'g'ri — audio: „Es ist sonnig und warm.“"),
    mc("Was macht Tom im Park?", ["Er liest ein Buch.", "Er spielt Fußball.", "Er malt."], "B", "Audio: „Tom spielt Fußball …“"),
    mc("Was macht Anna im Park?", ["Sie spielt Fußball.", "Sie liest ein Buch.", "Sie hört Musik."], "B", "Audio: „… und Anna liest ein Buch.“"),
    tf("Ein Hund kommt und läuft zu Tom und Anna.", True, "Audio: „Ein Hund kommt und läuft zu ihnen.“"),
    tf("Tom und Anna spielen mit dem Hund.", True, "Audio: „Sie lachen und spielen mit dem Hund.“"),
    mc("Wann gehen sie nach Hause?", ["Nach einer Stunde", "Nach zwei Stunden", "Nach drei Stunden"], "B", "Audio: „Nach zwei Stunden gehen sie nach Hause.“"),
    gap("Ergänzen Sie, was Sie hören.", "Es ist [[1]] und [[2]].",
        {"1": {"accepted": ["sonnig"], "options": ["sonnig", "kalt", "windig"]}, "2": {"accepted": ["warm"], "options": ["regnerisch", "warm", "kalt"]}},
        points=2, explanation="Audio: „Es ist sonnig und warm.“"),
    gap("Ergänzen Sie, was Sie hören.", "Sie sind [[1]], aber [[2]].",
        {"1": {"accepted": ["müde"], "options": ["müde", "traurig", "krank"]}, "2": {"accepted": ["glücklich"], "options": ["glücklich", "kalt", "böse"]}},
        points=2, explanation="Audio: „Sie sind müde, aber glücklich.“"),
]

# ============================================================
# Schreiben (p. 10) — the book's four fill-in tasks (word banks)
# ============================================================

_BANK_1 = ["10", "Fußball", "Usbekistan", "Tom", "Taschkent", "Deutsch"]
_BANK_2 = ["10", "futbol", "Usbekiston", "Tom", "Toshkentda", "nemis"]
_BANK_3 = ["Usbekistan", "Anna", "Malen und Musik", "Taschkent", "9", "Deutsch"]
_BANK_4 = ["Anna", "9", "Usbekistondan", "Toshkentda", "nemis", "Malen va musiqa"]


def _bank_gaps(answers: list[str], bank: list[str]) -> dict:
    return {str(n): {"accepted": [a], "options": bank} for n, a in enumerate(answers, start=1)}


SCHREIBEN_SETS = [
    exercise("Aufgabe 1: Tom (Lückentext)", [
        gap("Ergänzen Sie den Text mit den Wörtern aus dem Kasten.",
            "Hallo! Ich heiße [[1]], ich bin [[2]] Jahre alt, ich komme aus [[3]] und wohne in [[4]]. Ich gehe in die Schule und lerne [[5]]. Ich mag [[6]].",
            _bank_gaps(["Tom", "10", "Usbekistan", "Taschkent", "Deutsch", "Fußball"], _BANK_1), points=6,
            explanation="Hallo! Ich heiße Tom, ich bin 10 Jahre alt, ich komme aus Usbekistan und wohne in Taschkent. Ich gehe in die Schule und lerne Deutsch. Ich mag Fußball."),
    ], "Wörter: 10, Fußball, Usbekistan, Tom, Taschkent, Deutsch (kitob, 10-bet).", source="book"),
    exercise("Aufgabe 2: Tom (o'zbekcha)", [
        gap("Bo'sh joylarni qutidagi so'zlar bilan to'ldiring.",
            "Salom! Mening ismim [[1]], men [[2]] yoshdaman, men [[3]]danman va [[4]] yashayman. Men maktabga boraman va [[5]] tilini o'rganaman. Menga [[6]] yoqadi.",
            _bank_gaps(["Tom", "10", "Usbekiston", "Toshkentda", "nemis", "futbol"], _BANK_2), points=6,
            explanation="Salom! Mening ismim Tom, men 10 yoshdaman, men Usbekistondanman va Toshkentda yashayman. Men maktabga boraman va nemis tilini o'rganaman. Menga futbol yoqadi."),
    ], "So'zlar: 10, futbol, Usbekiston, Tom, Toshkentda, nemis (kitob, 10-bet).", source="book"),
    exercise("Aufgabe 3: Anna (Lückentext)", [
        gap("Ergänzen Sie den Text mit den Wörtern aus dem Kasten.",
            "Das ist mein Freund / meine Freundin [[1]]. Er/Sie ist [[2]] Jahre alt, er/sie kommt aus [[3]] und wohnt in [[4]]. Er/Sie geht in die Schule und lernt [[5]]. Er/Sie mag [[6]].",
            _bank_gaps(["Anna", "9", "Usbekistan", "Taschkent", "Deutsch", "Malen und Musik"], _BANK_3), points=6,
            explanation="Das ist meine Freundin Anna. Sie ist 9 Jahre alt, sie kommt aus Usbekistan und wohnt in Taschkent. Sie geht in die Schule und lernt Deutsch. Sie mag Malen und Musik."),
    ], "Wörter: Usbekistan, Anna, Malen und Musik, Taschkent, 9, Deutsch (kitob, 10-bet).", source="book"),
    exercise("Aufgabe 4: Anna (o'zbekcha)", [
        gap("Bo'sh joylarni qutidagi so'zlar bilan to'ldiring.",
            "Bu mening do'stim [[1]]. U [[2]] yoshda, u [[3]] va [[4]] yashaydi. U maktabga boradi va [[5]] tilini o'rganadi. Uga [[6]] yoqadi.",
            _bank_gaps(["Anna", "9", "Usbekistondan", "Toshkentda", "nemis", "Malen va musiqa"], _BANK_4), points=6,
            explanation="Bu mening do'stim Anna. U 9 yoshda, u Usbekistondan va Toshkentda yashaydi. U maktabga boradi va nemis tilini o'rganadi. Uga Malen va musiqa yoqadi."),
    ], "So'zlar: Anna, 9, Usbekistondan, Toshkentda, nemis, Malen va musiqa (kitob, 10-bet).", source="book"),
    exercise("Sätze bauen", [
        mc("Welcher Satz ist richtig? (heiße / Ich / Tom)", ["Ich heiße Tom.", "Heiße Tom ich.", "Tom ich heiße."], "A", "Ich heiße Tom."),
        mc("Welcher Satz ist richtig? (bin / 10 Jahre alt / ich)", ["Ich bin 10 Jahre alt.", "Bin ich alt 10 Jahre.", "10 Jahre ich bin alt."], "A"),
        mc("Welcher Satz ist richtig? (komme / aus Usbekistan / Ich)", ["Aus ich komme Usbekistan.", "Ich komme aus Usbekistan.", "Komme Usbekistan ich aus."], "B"),
        mc("Welcher Satz ist richtig? (wohne / in Taschkent / Ich)", ["Ich wohne in Taschkent.", "In wohne ich Taschkent.", "Wohne Taschkent ich in."], "A"),
        mc("Welcher Satz ist richtig? (mag / Ich / Musik)", ["Musik mag ich ich.", "Mag ich Musik ich.", "Ich mag Musik."], "C"),
    ], "So'zlardan to'g'ri gap tanlang (kitobdagi gaplar asosida, VIZU mashqi).", source="vizu"),
]

# ============================================================
# Wortschatz (p. 12) — 61 words in the book's groups
# ============================================================

WORDS = (
    words([("ich", "men"), ("du", "sen"), ("er", "u"), ("sie", "u"), ("wir", "biz"), ("ihr", "siz"), ("sie", "ular")], "Personen")
    + words([("die", "Schule", "maktab"), ("lernen", "o'rganmoq"), ("der", "Deutschunterricht", "nemis tili darsi"), ("das", "Buch", "kitob"),
             ("das", "Heft", "daftar"), ("der", "Stift", "ruchka")], "Schule und Lernen")
    + words([("die", "Mutter", "ona"), ("der", "Vater", "ota"), ("der", "Bruder", "aka / uka"), ("die", "Schwester", "opa / singil"),
             ("die", "Familie", "oila"), ("der", "Freund", "do'st (o'g'il)"), ("die", "Freundin", "do'st (qiz)")], "Familie")
    + words([("Fußball spielen", "futbol o'ynamoq"), ("Malen", "rasm chizmoq"), ("Musik hören", "musiqa tinglamoq"), ("lesen", "o'qimoq"),
             ("schwimmen", "suzmoq"), ("Rad fahren", "velosiped haydamoq")], "Hobbys und Freizeit")
    + words([("der", "Morgen", "tong"), ("der", "Tag", "kun"), ("der", "Abend", "kechqurun"), ("die", "Nacht", "tun"), ("Montag", "dushanba"),
             ("Dienstag", "seshanba"), ("Mittwoch", "chorshanba"), ("Donnerstag", "payshanba"), ("Freitag", "juma"), ("Samstag", "shanba"),
             ("Sonntag", "yakshanba")], "Tageszeiten und Tage")
    + words([("sonnig", "quyoshli"), ("warm", "iliq"), ("kalt", "sovuq"), ("regnerisch", "yomg'irli"), ("windig", "shamolli"),
             ("der", "Frühling", "bahor"), ("der", "Sommer", "yoz"), ("der", "Herbst", "kuz"), ("der", "Winter", "qish")], "Wetter und Jahreszeiten")
    + words([("kommen", "kelmoq"), ("wohnen", "yashamoq (yashash)"), ("gehen", "bormoq"), ("mögen", "yoqtirmoq"), ("danke", "rahmat"),
             ("bitte", "iltimos"), ("ja", "ha"), ("nein", "yo'q")], "Wichtige Wörter")
)


def _pairs(n: int) -> dict:
    return {str(i): "ABCDEFGHIJKL"[i - 1] for i in range(1, n + 1)}


WORTSCHATZ_SETS = [
    exercise("Zuordnung 1: Personen, Schule, Familie", [
        match("Was passt zusammen? (Personen)", ["ich", "du", "wir", "ihr"], ["men", "sen", "biz", "siz", "ular"], _pairs(4), points=4),
        match("Was passt zusammen? (Schule und Lernen)", ["die Schule", "lernen", "das Buch", "das Heft", "der Stift"],
              ["maktab", "o'rganmoq", "kitob", "daftar", "ruchka", "oila"], _pairs(5), points=5),
        match("Was passt zusammen? (Familie)", ["die Mutter", "der Vater", "der Bruder", "die Schwester", "die Familie"],
              ["ona", "ota", "aka / uka", "opa / singil", "oila", "do'st (qiz)"], _pairs(5), points=5),
    ], "Nemischa so'zni tarjimasi bilan moslashtiring.", source="vizu"),
    exercise("Zuordnung 2: Hobbys, Tage, Wetter", [
        match("Was passt zusammen? (Hobbys)", ["Fußball spielen", "Musik hören", "lesen", "schwimmen", "Rad fahren"],
              ["futbol o'ynamoq", "musiqa tinglamoq", "o'qimoq", "suzmoq", "velosiped haydamoq", "rasm chizmoq"], _pairs(5), points=5),
        match("Was passt zusammen? (Wochentage)", ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
              ["dushanba", "seshanba", "chorshanba", "payshanba", "juma", "shanba", "yakshanba"], _pairs(7), points=7),
        match("Was passt zusammen? (Wetter und Jahreszeiten)", ["sonnig", "kalt", "windig", "der Frühling", "der Sommer", "der Winter"],
              ["quyoshli", "sovuq", "shamolli", "bahor", "yoz", "qish", "kuz"], _pairs(6), points=6),
    ], "Nemischa so'zni tarjimasi bilan moslashtiring.", source="vizu"),
    exercise("Lückentext: Wörter im Satz", [
        choice_gap("Ich gehe in die ___ und lerne Deutsch.", ["Schule", "Familie", "Nacht"], "Schule", explanation="Lesen, Text 1: „Ich gehe in die Schule und lerne Deutsch.“"),
        choice_gap("Ich ___ aus Usbekistan.", ["komme", "wohne", "mag"], "komme", explanation="„Ich komme aus Usbekistan.“ — kommen = kelmoq"),
        choice_gap("Ich ___ in Taschkent.", ["wohne", "komme", "gehe"], "wohne", explanation="„Ich wohne in Taschkent.“ — wohnen = yashamoq"),
        choice_gap("Ich ___ Fußball.", ["mag", "wohne", "komme"], "mag", explanation="„Ich mag Fußball.“ — mögen = yoqtirmoq"),
        choice_gap("Anna liest ein ___.", ["Buch", "Stift", "Tag"], "Buch", explanation="Hören: „Anna liest ein Buch.“"),
        choice_gap("Es ist ___ und warm.", ["sonnig", "Montag", "danke"], "sonnig", explanation="Hören: „Es ist sonnig und warm.“"),
        choice_gap("___ ist der Tag nach Freitag.", ["Samstag", "Sonntag", "Montag"], "Samstag", explanation="Freitag → Samstag → Sonntag"),
        choice_gap("Hallo! ___! — Rahmat!", ["Danke", "Bitte", "Nein"], "Danke", explanation="danke = rahmat"),
    ], "Bo'sh joyga mos so'zni tanlang.", source="vizu"),
    exercise("Der, die oder das?", [
        choice_gap("___ Schule (maktab)", ["der", "die", "das"], "die"),
        choice_gap("___ Buch (kitob)", ["der", "die", "das"], "das"),
        choice_gap("___ Heft (daftar)", ["der", "die", "das"], "das"),
        choice_gap("___ Stift (ruchka)", ["der", "die", "das"], "der"),
        choice_gap("___ Mutter (ona)", ["der", "die", "das"], "die"),
        choice_gap("___ Vater (ota)", ["der", "die", "das"], "der"),
        choice_gap("___ Familie (oila)", ["der", "die", "das"], "die"),
        choice_gap("___ Nacht (tun)", ["der", "die", "das"], "die"),
        choice_gap("___ Sommer (yoz)", ["der", "die", "das"], "der"),
        choice_gap("___ Morgen (tong)", ["der", "die", "das"], "der"),
    ], "So'zning artiklini tanlang (kitobdagi lug'at bo'yicha).", source="vizu"),
    exercise("Nemischa qanday?", [
        mc("„kitob“ — nemischa qanday?", ["das Buch", "das Heft", "der Stift"], "A"),
        mc("„oila“ — nemischa qanday?", ["die Schule", "die Familie", "die Freundin"], "B"),
        mc("„chorshanba“ — nemischa qanday?", ["Dienstag", "Mittwoch", "Donnerstag"], "B"),
        mc("„kuz“ — nemischa qanday?", ["der Herbst", "der Winter", "der Frühling"], "A"),
        mc("„yomg'irli“ — nemischa qanday?", ["windig", "regnerisch", "sonnig"], "B"),
        mc("„iltimos“ — nemischa qanday?", ["danke", "bitte", "nein"], "B"),
        mc("„kechqurun“ — nemischa qanday?", ["der Abend", "der Morgen", "die Nacht"], "A"),
        mc("„suzmoq“ — nemischa qanday?", ["lesen", "schwimmen", "Rad fahren"], "B"),
    ], "O'zbekcha so'zning nemischasini tanlang.", source="vizu"),
]

# ============================================================
# Übungen — review of alphabet + words (VIZU, from the book material)
# ============================================================

UEBUNGEN_SETS = [
    exercise("Buchstabieren", [
        mc("Te – O – Em: Welches Wort ist das?", ["Tom", "Tim", "Ton"], "A"),
        mc("A – En – En – A: Welches Wort ist das?", ["Anja", "Anna", "Hanna"], "B"),
        mc("Be – U – Ce – Ha: Welches Wort ist das?", ["Bach", "Buch", "Busch"], "B"),
        mc("Ha – E – Ef – Te: Welches Wort ist das?", ["Heft", "Haft", "Hund"], "A"),
        mc("Vau – A – Te – E – Er: Welches Wort ist das?", ["Wasser", "Vater", "Winter"], "B", "V = Vau, wird [f] gesprochen: Vater [fa:ter]."),
        mc("We – I – En – Te – E – Er: Welches Wort ist das?", ["Winter", "Wetter", "Vater"], "A", "W = We, wird [v] gesprochen: Winter [vinter]."),
        mc("Zett – E – I – Te: Welches Wort ist das?", ["Zeit", "Seit", "Zett"], "A", "Z = Zett [ts]: Zeit [tsayt]."),
        mc("Es – Ce – Ha – U – El – E: Welches Wort ist das?", ["Schule", "Schale", "Stuhl"], "A"),
    ], "Harflab aytilgan so'zni toping (alifbo nomlari, kitob 5-bet).", source="vizu"),
    exercise("Wiederholung: Laute und Wörter", [
        mc("In welchem Wort hört man [sht]?", ["Student", "Sonne", "Zimmer"], "A", "st — [sht]: Student, Stadt."),
        mc("In welchem Wort hört man [shp]?", ["Sport", "Haus", "Zeit"], "A", "sp — [shp]: Sport, Sprache."),
        mc("In welchem Wort hört man [ay]?", ["mein", "neu", "vier"], "A", "ei — [ay]: mein."),
        mc("In welchem Wort hört man [oy]?", ["neu", "Haus", "Liebe"], "A", "eu — [oy]: neu."),
        tf("„Wasser“ spricht man [vaser].", True, "W — har doim [v]."),
        tf("„Vater“ spricht man [vater] mit [v].", False, "V — ko'pincha [f]: Vater [fa:ter]."),
        match("Was passt zusammen?", ["der Morgen", "der Abend", "die Nacht", "der Tag"], ["tong", "kechqurun", "tun", "kun", "yil"], _pairs(4), points=4),
        choice_gap("Hallo! Ich ___ Tom.", ["heiße", "komme", "mag"], "heiße", explanation="Ich heiße … — mening ismim …"),
        choice_gap("Wir ___ in die Schule und lernen Deutsch.", ["gehen", "gehe", "geht"], "gehen", explanation="Lesen, Text 3: „Wir gehen in die Schule …“"),
    ], "Darsdagi tovushlar, so'zlar va gaplar bo'yicha takrorlash.", source="vizu"),
]

# ============================================================
# Abschlusstest
# ============================================================

ABSCHLUSSTEST = [
    mc("Wie spricht man „W“ in „Wasser“ aus?", ["[v]", "[w]", "[f]"], "A"),
    mc("Wie heißt der Buchstabe „ß“?", ["Eszett", "Umlaut", "Ypsilon"], "A"),
    mc("Wie heißt der Buchstabe „J“?", ["Ge", "Jott", "Ja"], "B"),
    mc("Welches Wort beginnt mit [sht]?", ["Straße", "Sonne", "Zimmer"], "A"),
    mc("„ei“ in „mein“ klingt wie …", ["[ay]", "[ey]", "[i:]"], "A"),
    mc("„ie“ in „vier“ klingt wie …", ["[i:]", "[ay]", "[ie]"], "A"),
    mc("Welche Buchstaben sind Umlaute?", ["Ä, Ö, Ü", "A, O, U", "ß, Y, Z"], "A"),
    mc("„die Schwester“ — o'zbekchasi qaysi?", ["ota", "opa / singil", "aka / uka"], "B"),
    mc("„Mittwoch“ — o'zbekchasi qaysi?", ["seshanba", "chorshanba", "payshanba"], "B"),
    mc("„der Herbst“ — o'zbekchasi qaysi?", ["kuz", "bahor", "qish"], "A"),
    tf("„sonnig“ bedeutet „quyoshli“.", True),
    tf("„nein“ bedeutet „ha“.", False, "„nein“ — yo'q, „ja“ — ha."),
    match("Was passt zusammen?", ["ich", "du", "wir", "ihr"], ["men", "sen", "biz", "siz", "ular"], _pairs(4), points=4),
    choice_gap("Hallo! Ich ___ Anna und ich bin 9 Jahre alt.", ["heiße", "wohne", "lerne"], "heiße"),
    choice_gap("Ich komme aus Usbekistan und ___ in Taschkent.", ["wohne", "heiße", "mag"], "wohne"),
    mc("Tom mag … (Lesen, Text 1)", ["Fußball", "Malen", "Musik"], "A", "„Ich mag Fußball.“"),
    tf("Anna lernt in der Schule Deutsch. (Lesen, Text 2)", True, "„Ich gehe in die Schule und lerne Deutsch.“"),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: Modul 1", source="vizu", page=3, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Nima uchun nemis tili?", page=4,
             prompt="Nima uchun nemis tili? Nima uchun aynan nemis tilini o'rganmoqchisiz? Fikringizni 2–3 gap bilan ovozli yuboring "
                    "(nemischa yoki o'zbekcha).",
             min_duration=10, max_duration=120),
        base(L, "wortschatz", 1, "Wortschatz Modul 1", page=12, words=WORDS, exercises=WORTSCHATZ_SETS),
        base(L, "grammatik", 1, "Grammatik: Das deutsche Alphabet", page="5-7",
             rules=[
                 {"title": "Das deutsche Alphabet", "html": "<h3>Nemis tili alifbosi</h3>" + _ALPHABET},
                 {"title": "Nemis alifbosidagi muhim harflar", "html": "<h3>Muhim harflar va ularning o'qilishi</h3>" + _IMPORTANT},
                 {"title": "Harf birikmalari va diftonglar", "html": _COMBINATIONS},
             ],
             exercises=[ALPHABET_NAMES, ALPHABET_CASE, ALPHABET_RULES]),
        base(L, "lesen", 1, "Lesen: Tom und Anna", page=8, source="vizu",
             instruction="Lesen Sie die Texte und beantworten Sie die Fragen.",
             metadata={"book_page": 8, "note": "Matnlar va tarjimalar kitobdan; savollar VIZU tomonidan matn asosida tuzilgan (kitobda savol yo'q)."},
             passages=[
                 {"title": "Text 1: Tom", "text": _with_translation(TEXT_1, TEXT_1_UZ)},
                 {"title": "Text 2: Anna", "text": _with_translation(TEXT_2, TEXT_2_UZ)},
                 {"title": "Text 3: Tom und Anna", "text": _with_translation(TEXT_3, TEXT_3_UZ)},
             ],
             questions=LESEN_QUESTIONS, max_score=sum(q["points"] for q in LESEN_QUESTIONS)),
        base(L, "hoeren", 1, "Hören: Im Park", page=9, source="vizu",
             instruction="Hören Sie den Text und beantworten Sie die Fragen.",
             metadata={"book_page": 9, "note": "Matn kitobdan (audio A1-1.mp3); savollar VIZU tomonidan matn asosida tuzilgan."},
             audio_file="A1-1.mp3", transcript=f"{HOEREN_TEXT}\n\nO'zbekcha tarjima: {HOEREN_TEXT_UZ}",
             questions=HOEREN_QUESTIONS, max_score=sum(q["points"] for q in HOEREN_QUESTIONS)),
        base(L, "sprechen", 1, "Stellen Sie sich vor!", page=11, topic="Sich vorstellen – Erzählen Sie über sich!",
             prompt="Sich vorstellen — Erzählen Sie über sich! Sprechen Sie mit diesen Sätzen. Tipp: Sprich über dich selbst! Sei mutig und lächle!",
             questions=["Hallo! Ich heiße … , ich bin … Jahre alt.", "Ich komme aus … und wohne in …", "Ich gehe in die Schule und lerne …",
                        "Ich mag … (z. B. Fußball, Musik, Bücher).", "Meine Hobbys sind …", "Mein Lieblingsfach ist …",
                        "Ich habe … Bruder / … Schwester.", "Meine Familie ist …", "Ich freue mich, Deutsch zu lernen!"],
             response_type="monolog", min_duration=20, max_duration=90,
             speech_goal="Name, Alter, Herkunft, Wohnort, Schule/Deutsch, Hobbys und Familie in einfachen Sätzen nennen.",
             keywords=["Ich heiße", "Jahre alt", "Ich komme aus", "Ich wohne in", "Ich mag"]),
        base(L, "schreiben_uebungen", 1, "Schreiben: Aufgaben 1–4 und Sätze bauen", page=10, exercises=SCHREIBEN_SETS),
        base(L, "schreiben", 1, "Über mich", page=10, source="vizu",
             prompt="Schreiben Sie über sich — wie in Aufgabe 1, aber mit Ihren eigenen Informationen:\n\n"
                    "Hallo! Ich heiße ____, ich bin ____ Jahre alt, ich komme aus ____ und wohne in ____.\n"
                    "Ich gehe in die Schule und lerne ____. Ich mag ____.",
             task_type="description", min_words=20, max_words=60, time_limit=10,
             support_phrases=["Ich heiße …", "Ich bin … Jahre alt.", "Ich komme aus …", "Ich wohne in …", "Ich lerne …", "Ich mag …"]),
        base(L, "uebungen", 1, "Übungen Modul 1", exercises=UEBUNGEN_SETS, source="vizu"),
        base(L, "yakuniy", 1, "Abschlusstest: Modul 1", source="vizu",
             instruction="Alifbo, talaffuz, darsdagi so'zlar va Lesen matnlari bo'yicha yakuniy test.", questions=ABSCHLUSSTEST),
        base(L, "kompetenz", 2, "Zusammenfassung: Modul 1", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
