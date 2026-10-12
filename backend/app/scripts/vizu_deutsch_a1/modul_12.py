"""Modul 12 — Das Wetter in Berlin — Grammatik: Die Konjunktionen (book pp. 117-125).

p.120 ("6 Bog'lovchi — 60 topshiriq"): free sentence building with several
correct solutions (and no matching answer sheet) — imported as two Schreiben
tasks evaluated against the rubric, not as auto-graded items. A short
auto-graded conjunction exercise is added by VIZU. The Lesen texts (p.121)
have no questions in the book; the questions are created by VIZU."""

from . import base, choice_gap, exercise, gap, html_table, match, mc, tf, words

L = 12

_KONJ = html_table(
    ["Bog'lovchi", "Strukturasi", "Misollar"],
    [
        ["und — va", "Gap + und + gap", "Ich lerne Deutsch und Englisch. — Men nemis va ingliz tillarini o'rganaman. / Ich arbeite und lerne zu Hause. / "
                                        "Wir trinken Tee und Kaffee."],
        ["oder — yoki", "Gap + oder + gap", "Möchtest du Tee oder Kaffee? — Sen choy yoki qahva xohlaysanmi? / Kommst du heute oder morgen? / "
                                           "Wir lernen zu Hause oder in der Schule."],
        ["aber — lekin", "Gap, aber gap", "Die Wohnung ist klein, aber billig. — Kvartira kichkina, lekin arzon. / Ich bin müde, aber glücklich. / "
                                          "Er arbeitet viel, aber verdient wenig."],
        ["denn — chunki", "Gap, denn gap", "Ich gehe nicht zur Arbeit, denn ich bin krank. — Men ishga bormayman, chunki kasalman. / "
                                           "Wir bleiben zu Hause, denn es regnet. / Ich lerne Deutsch, denn es ist wichtig."],
        ["deshalb / deswegen / darum — shuning uchun", "Gap. Deshalb + fe'l + ega …", "Ich bin krank. Deshalb gehe ich nicht zur Arbeit. — "
                                                                                     "Men kasalman. Shuning uchun ishga bormayman. / Es ist kalt. Darum bleiben wir zu Hause. / "
                                                                                     "Ich habe viel Arbeit. Deswegen komme ich spät."],
        ["dann / danach — keyin", "Gap. Dann / Danach + fe'l + ega …", "Wir essen zu Mittag. Danach gehen wir spazieren. — Biz tushlik qilamiz. "
                                                                        "Keyin sayr qilamiz. / Ich lerne Deutsch. Dann mache ich Hausaufgaben. / "
                                                                        "Er arbeitet am Morgen. Danach ruht er sich aus."],
    ],
) + "<p><strong>E'tibor bering:</strong> und, oder, aber, denn dan keyin so'z tartibi o'zgarmaydi; deshalb / deswegen / darum va dann / danach dan " \
    "keyin fe'l 2-o'rinda keladi.</p>"

KONJ_EX = [
    choice_gap("Ich bin müde, ___ ich lerne Deutsch.", ["aber", "denn", "oder"], "aber"),
    choice_gap("Wir bleiben zu Hause, ___ es regnet.", ["denn", "deshalb", "und"], "denn"),
    choice_gap("Möchtest du Tee ___ Kaffee?", ["oder", "aber", "denn"], "oder"),
    choice_gap("Es ist kalt. ___ bleiben wir zu Hause.", ["Darum", "Denn", "Aber"], "Darum"),
    choice_gap("Wir essen zu Mittag. ___ gehen wir spazieren.", ["Danach", "Denn", "Oder"], "Danach"),
    choice_gap("Meine Mutter kocht ___ mein Vater arbeitet.", ["und", "deshalb", "dann"], "und"),
    mc("Welcher Satz ist richtig?", ["Ich bin krank. Deshalb ich gehe nicht zur Arbeit.", "Ich bin krank. Deshalb gehe ich nicht zur Arbeit.",
                                     "Ich bin krank, deshalb ich nicht gehe zur Arbeit."], "B", "Deshalb + Verb (Position 2) + Subjekt."),
    mc("Welcher Satz ist richtig?", ["Ich lerne Deutsch, denn es ist wichtig.", "Ich lerne Deutsch, denn ist es wichtig.",
                                     "Ich lerne Deutsch, denn es wichtig ist."], "A", "Nach „denn“ bleibt die normale Wortstellung."),
    mc("Welcher Satz ist richtig?", ["Ich stehe auf. Dann ich frühstücke.", "Ich stehe auf. Dann frühstücke ich.", "Ich stehe auf. Dann frühstücken ich."], "B"),
    tf("„deswegen“ bedeutet „shuning uchun“.", True),
]

_AUFGABE_1 = (
    "Gap tuzish mashqlari (Buch S. 120). Schreiben Sie zu jeder Zeile einen vollständigen deutschen Satz.\n\n"
    "UND — va: 1. ich / Deutsch lernen / Englisch lernen  2. meine Mutter / kochen / mein Vater / arbeiten  3. ich / Kaffee trinken / Musik hören  "
    "4. wir / Fußball spielen / Tennis spielen  5. Anna / lesen / Peter / schreiben  6. ich / in Berlin wohnen / Deutsch studieren  "
    "7. er / früh aufstehen / zur Arbeit gehen  8. wir / am Wochenende lernen / Freunde treffen  9. sie / Brot kaufen / Milch kaufen  "
    "10. ich / ein Buch lesen / einen Film sehen\n\n"
    "ODER — yoki: 1. Tee / Kaffee trinken  2. heute / morgen kommen  3. zu Hause / in der Schule lernen  4. mit dem Bus / mit dem Zug fahren  "
    "5. Pizza / Hamburger essen  6. Deutsch / Englisch sprechen  7. am Samstag / am Sonntag arbeiten  8. einen Film / eine Serie sehen  "
    "9. im Sommer / im Winter reisen  10. morgens / abends lernen\n\n"
    "ABER — lekin: 1. die Wohnung ist klein / sie ist schön  2. ich bin müde / ich lerne Deutsch  3. das Wetter ist schlecht / wir gehen spazieren  "
    "4. der Kaffee ist teuer / er schmeckt gut  5. ich habe wenig Zeit / ich helfe dir  6. er arbeitet viel / er verdient wenig  "
    "7. Deutsch ist schwierig / ich lerne es gern  8. das Auto ist alt / es funktioniert gut  9. sie ist krank / sie geht zur Arbeit  "
    "10. der Film ist lang / er ist interessant"
)
_AUFGABE_2 = (
    "Gap tuzish mashqlari (Buch S. 120). Verbinden Sie die zwei Sätze. Achten Sie auf die Wortstellung.\n\n"
    "DENN — chunki: 1. ich gehe nicht zur Arbeit / ich bin krank  2. wir bleiben zu Hause / es regnet  3. ich lerne Deutsch / Deutsch ist wichtig  "
    "4. er geht früh ins Bett / er ist müde  5. sie kauft einen Regenschirm / es regnet  6. ich trinke keinen Kaffee / ich mag Kaffee nicht  "
    "7. wir fahren nicht mit dem Auto / das Auto ist kaputt  8. er lernt jeden Tag / er möchte die Prüfung bestehen  9. ich esse jetzt / ich habe Hunger  "
    "10. sie bleibt heute zu Hause / sie fühlt sich nicht gut\n\n"
    "DESHALB / DESWEGEN / DARUM — shuning uchun (Verb auf Position 2): 1. ich bin krank / ich gehe nicht zur Arbeit  2. es ist kalt / wir bleiben zu Hause  "
    "3. ich habe viel Arbeit / ich komme spät  4. er ist müde / er geht früh ins Bett  5. es regnet / wir nehmen einen Regenschirm  "
    "6. sie hat Hunger / sie macht ein Sandwich  7. Deutsch ist wichtig / ich lerne jeden Tag  8. das Auto ist kaputt / wir fahren mit dem Bus  "
    "9. morgen ist eine Prüfung / ich lerne heute viel  10. ich habe keine Zeit / ich kann dir nicht helfen\n\n"
    "DANN / DANACH — keyin: 1. ich stehe auf / ich frühstücke  2. ich frühstücke / ich gehe zur Arbeit  3. wir essen zu Mittag / wir gehen spazieren  "
    "4. ich lerne Deutsch / ich mache Hausaufgaben  5. er arbeitet am Morgen / er ruht sich aus  6. sie macht Sport / sie duscht  "
    "7. ich komme nach Hause / ich esse zu Abend  8. wir sehen einen Film / wir gehen ins Bett  9. er kauft ein Buch / er liest das Buch  "
    "10. ich mache meine Hausaufgaben / ich treffe meine Freunde"
)
_RUBRIC = [{"key": "task", "name": "Topshiriqni bajarish (barcha gaplar)", "max": 30},
           {"key": "grammar", "name": "Bog'lovchi va so'z tartibi", "max": 40},
           {"key": "vocabulary", "name": "Fe'l shakllari", "max": 20},
           {"key": "spelling", "name": "Imlo va tinish belgilari", "max": 10}]
_AI = ("Bu gap tuzish mashqi. Har bir satr uchun talaba bitta to'liq nemischa gap yozishi kerak. Bog'lovchi to'g'ri ishlatilganini, "
       "so'z tartibini (deshalb/deswegen/darum va dann/danach dan keyin fe'l 2-o'rinda; und/oder/aber/denn dan keyin oddiy tartib) va fe'l "
       "shakllarini tekshir. Mazmunan boshqacha, lekin grammatik jihatdan to'g'ri variantlarni to'g'ri deb hisobla. Yo'q gaplarni 'task' "
       "mezonida kamaytir.")

TEXTS = {
    "Winter in Deutschland": ("Im Winter ist das Wetter in Deutschland sehr kalt. Die Temperaturen sind oft unter null Grad und es schneit viel. Die Tage "
                              "sind kurz und die Nächte sind lang. Viele Menschen bleiben gern zu Hause, trinken heißen Tee oder Kaffee und verbringen "
                              "Zeit mit der Familie. Im Winter kann man Nürnberg besuchen. Die Stadt ist bekannt für ihren großen Weihnachtsmarkt. Dort "
                              "gibt es viele Lichter, Musik und traditionelles Essen. Auch Dresden ist im Winter sehr beliebt, weil der Weihnachtsmarkt "
                              "dort alt und sehr schön ist. Der Winter ist kalt, aber ideal für Weihnachtsmärkte, Kultur und gemütliche Zeit."),
    "Frühling in Deutschland": ("Im Frühling wird das Wetter langsam wärmer. Die Sonne scheint öfter und die Natur wird grün. Blumen blühen überall und "
                                "die Menschen sind wieder mehr draußen. Es regnet manchmal, aber die Luft ist frisch und angenehm. Im Frühling ist Bonn "
                                "sehr schön, weil viele Bäume und Blumen blühen. Besonders die Kirschblüten sind sehr bekannt. Auch Freiburg ist im "
                                "Frühling beliebt, denn die Stadt ist sonnig und liegt nah an der Natur. Der Frühling ist perfekt für Spaziergänge, "
                                "Natur und frische Luft."),
    "Sommer in Deutschland": ("Im Sommer ist es in Deutschland warm oder manchmal sehr heiß. Die Tage sind lang und viele Menschen haben Urlaub. Man reist "
                              "viel, geht schwimmen oder sitzt draußen im Café. Parks und Seen sind sehr beliebt. Im Sommer fahren viele Leute nach "
                              "Berlin, weil es dort viele Feste, Parks und Seen gibt. Auch Hamburg ist im Sommer interessant, denn der Hafen, die Alster "
                              "und die Spaziergänge am Wasser sind sehr schön. Der Sommer ist die beste Zeit für Reisen, Freizeit und Aktivitäten im Freien."),
    "Herbst in Deutschland": ("Im Herbst wird das Wetter kühler. Die Blätter werden gelb, rot und braun. Es regnet öfter und die Tage werden kürzer. "
                              "Viele Menschen trinken gern warmen Tee und genießen ruhige Abende. Im Herbst kann man Heidelberg besuchen, weil die Stadt "
                              "ruhig und romantisch ist. Auch Weimar ist im Herbst gut zu besuchen, denn dort gibt es viel Kultur und Geschichte. Der "
                              "Herbst ist ruhig und ideal für Kultur, Natur und Entspannung."),
}
LESEN = [
    mc("Wie ist das Wetter im Winter?", ["Sehr kalt, es schneit viel", "Warm und sonnig", "Heiß"], "A", passage=1),
    mc("Wofür ist Nürnberg bekannt?", ["Für den Hafen", "Für den großen Weihnachtsmarkt", "Für die Kirschblüten"], "B", passage=1),
    tf("Im Winter sind die Tage lang und die Nächte kurz.", False, "„Die Tage sind kurz und die Nächte sind lang.“", passage=1),
    mc("Warum ist Bonn im Frühling schön?", ["Weil es dort viele Feste gibt", "Weil viele Bäume und Blumen blühen", "Weil es dort schneit"], "B", passage=2),
    tf("Freiburg ist sonnig und liegt nah an der Natur.", True, passage=2),
    mc("Was machen viele Menschen im Sommer?", ["Sie bleiben zu Hause.", "Sie reisen, gehen schwimmen oder sitzen im Café.", "Sie fahren Ski."], "B", passage=3),
    mc("Warum fahren viele Leute im Sommer nach Berlin?", ["Wegen der Feste, Parks und Seen", "Wegen des Weihnachtsmarkts", "Wegen der Berge"], "A", passage=3),
    mc("Welche Farben haben die Blätter im Herbst?", ["Grün und blau", "Gelb, rot und braun", "Weiß"], "B", passage=4),
    tf("Weimar ist im Herbst gut zu besuchen, denn es gibt dort viel Kultur und Geschichte.", True, passage=4),
    mc("Welche Jahreszeit ist ideal für Weihnachtsmärkte?", ["Der Sommer", "Der Herbst", "Der Winter"], "C", passage=1),
]

_T = lambda n: [str(n), f"{n} Grad"]  # noqa: E731
HOEREN_TEXT = ("Wetterbericht 1: Guten Morgen! Hier ist der Wetterbericht für heute in Deutschland. Heute ist das Wetter kalt und wechselhaft. Am Morgen "
               "ist es bewölkt und es regnet leicht. In [[1]] sind es am Morgen [[2]] Grad. In [[3]] sind es nur [[4]] Grad und es ist windig. Am "
               "Mittag steigen die Temperaturen ein bisschen. Am Nachmittag bleibt es kühl. In [[5]] sind es [[6]] Grad und es gibt wenig Regen. "
               "Am Abend wird es wieder kälter. Ziehen Sie eine warme Jacke an.\n"
               "Wetterbericht 2: Guten Tag! Hier ist der Wetterbericht für morgen in Deutschland. Morgen ist das Wetter sehr schön und sonnig. Am "
               "Morgen scheint die Sonne. In [[7]] sind es [[8]] Grad. In [[9]] sind es [[10]] Grad. Am Mittag wird es warm. Am Nachmittag ist das "
               "Wetter angenehm. In [[11]] steigen die Temperaturen auf [[12]] Grad. Am Abend bleibt es mild. Ein perfekter Tag für einen Spaziergang.")
HOEREN_GAPS = {"1": ["Berlin"], "2": _T(8), "3": ["Hamburg"], "4": _T(7), "5": ["Köln"], "6": _T(12), "7": ["München"], "8": _T(16),
               "9": ["Stuttgart"], "10": _T(17), "11": ["Frankfurt"], "12": _T(24)}

_V = [("regnen", "yomg'ir yog'moq"), ("schneien", "qor yog'moq"), ("scheinen", "porlamoq (quyosh)"), ("wehen", "esmoq (shamol)"), ("frieren", "sovqotmoq"),
      ("schwitzen", "terlamoq"), ("steigen", "ko'tarilmoq"), ("sinken", "pasaymoq"), ("blitzen", "chaqmoq chaqmoq"), ("donnern", "momaqaldiroq gumburlamoq"),
      ("bewölkt sein", "bulutli bo'lmoq"), ("aufklaren", "ochilmoq (osmon)"), ("hageln", "do'l yog'moq"), ("tauen", "erimoq"), ("sich ändern", "o'zgarmoq")]
_N = [("der", "Regen", "yomg'ir"), ("der", "Schnee", "qor"), ("die", "Sonne", "quyosh"), ("der", "Wind", "shamol"), ("die", "Kälte", "sovuq"),
      ("die", "Hitze", "issiq"), ("die", "Temperatur", "harorat"), ("die", "Wolke", "bulut"), ("das", "Gewitter", "momaqaldiroq"), ("der", "Sturm", "bo'ron"),
      ("der", "Nebel", "tuman"), ("der", "Himmel", "osmon"), ("der", "Hagel", "do'l"), ("das", "Eis", "muz"), ("das", "Klima", "iqlim")]
_A = [("kalt", "sovuq"), ("warm", "iliq"), ("heiß", "issiq"), ("kühl", "salqin"), ("sonnig", "quyoshli"), ("windig", "shamolli"), ("regnerisch", "yomg'irli"),
      ("neblig", "tumanli"), ("trocken", "quruq"), ("nass", "ho'l"), ("bewölkt", "bulutli"), ("stürmisch", "bo'ronli"), ("angenehm", "yoqimli"),
      ("mild", "yumshoq (ob-havo)"), ("wechselhaft", "o'zgaruvchan")]
_R = [("heute", "bugun"), ("morgen", "ertaga"), ("gestern", "kecha"), ("draußen", "tashqarida"), ("drinnen", "ichkarida"), ("überall", "hamma joyda"),
      ("manchmal", "ba'zan"), ("oft", "tez-tez"), ("selten", "kamdan-kam"), ("plötzlich", "to'satdan"), ("langsam", "sekin"), ("schnell", "tez"),
      ("tagsüber", "kunduz kuni"), ("nachts", "tunda")]
WORDS = words(_V, "Verben") + words(_N, "Nomen") + words(_A, "Adjektive") + words(_R, "Adverbien")


def items() -> list[dict]:
    return [
        base(L, "frage", 1, "Frage: Ist Deutschland regnerisch?", page=118,
             prompt="Ist Deutschland regnerisch? Wie oft regnet es in Deutschland? (Norden und Westen, Süden, Herbst und Winter) "
                    "Wie ist das Wetter in Ihrer Stadt?",
             min_duration=10, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Die Konjunktionen", page="119-120",
             rules=[{"title": "Die Konjunktionen", "html": _KONJ}],
             exercises=[exercise("Übung: Konjunktionen", KONJ_EX, "Wählen Sie die richtige Konjunktion bzw. den richtigen Satz.", source="vizu")]),
        base(L, "lesen", 1, "Lesen: Die Jahreszeiten in Deutschland", page=121, source="vizu",
             instruction="Lesen Sie die Texte und beantworten Sie die Fragen.",
             metadata={"book_page": 121, "note": "Matnlar kitobdan; savollar VIZU tomonidan matn asosida tuzilgan."},
             passages=[{"title": t, "text": x} for t, x in TEXTS.items()], questions=LESEN, max_score=len(LESEN)),
        base(L, "hoeren", 1, "Hören: Wetterberichte", page=122, audio_file="A1-12.1.mp3 / A1-12.2.mp3",
             instruction="Hören Sie die Wetterberichte und ergänzen Sie die Städte und die Temperaturen.",
             metadata={"book_page": 122, "note": "Javoblar kitobning javoblar varag'idan; audio yuklanganda admin tekshirsin."},
             questions=[gap("Wetterbericht — Städte und Temperaturen.", HOEREN_TEXT, HOEREN_GAPS, points=12)]),
        base(L, "schreiben", 1, "Schreiben: Mein Lieblingswetter", page=123,
             prompt="Was ist dein Lieblingswetter? Warum? Beschreibe das Wetter und was du gern bei diesem Wetter machst. Schreibe 4–5 Sätze.",
             task_type="description", min_words=25, max_words=80, time_limit=10,
             support_phrases=["Mein Lieblingswetter ist …", "…, denn …", "Bei diesem Wetter gehe ich gern …"]),
        base(L, "schreiben", 2, "Schreiben: Mein Lieblingsmonat", page=123,
             prompt="Welcher ist dein Lieblingsmonat? Beschreibe den Monat, das Wetter, die Feste oder Aktivitäten. Schreibe 4–5 Sätze.",
             task_type="description", min_words=25, max_words=80, time_limit=10,
             support_phrases=["Mein Lieblingsmonat ist …", "Im … ist das Wetter …", "Im … feiern wir …"]),
        base(L, "schreiben", 3, "Gap tuzish: und, oder, aber (30 Sätze)", page=120,
             prompt=_AUFGABE_1, task_type="other", min_words=150, max_words=400, time_limit=40, rubric=_RUBRIC, max_score=100, ai_instructions=_AI),
        base(L, "schreiben", 4, "Gap tuzish: denn, deshalb, dann (30 Sätze)", page=120,
             prompt=_AUFGABE_2, task_type="other", min_words=150, max_words=400, time_limit=40, rubric=_RUBRIC, max_score=100, ai_instructions=_AI),
        base(L, "sprechen", 1, "Sprechen: Mein Lieblingsmonat und meine Lieblingsjahreszeit", page=124, topic="Wetter und Jahreszeiten",
             prompt="Beantworte die Fragen in ganzen Sätzen. Beispiel: Mein Lieblingsmonat ist Juli. Im Juli haben wir Sommerferien. Im Juli gehe ich "
                    "gerne schwimmen.",
             questions=["Welcher ist dein Lieblingsmonat?", "Warum ist es dein Lieblingsmonat?", "Was machst du dann gerne?",
                        "Welche ist deine Lieblingsjahreszeit?", "Warum ist das deine Lieblingsjahreszeit?", "Was machst du gerne in der Jahreszeit?"],
             response_type="monolog", min_duration=30, max_duration=120,
             speech_goal="Lieblingsmonat und Lieblingsjahreszeit nennen, begründen und Aktivitäten beschreiben.",
             keywords=["Mein Lieblingsmonat ist", "Meine Lieblingsjahreszeit ist", "Im Sommer / Winter …", "gerne"]),
        base(L, "wortschatz", 1, "Wortschatz Modul 12: Wetter", page=125, words=WORDS),
        base(L, "yakuniy", 1, "Yakuniy Test: Modul 12", source="vizu",
             instruction="Bog'lovchilar va ob-havo so'zlari bo'yicha yakuniy test.",
             questions=[
                 choice_gap("Es regnet, ___ bleiben wir zu Hause.", ["deshalb", "denn", "aber"], "deshalb"),
                 choice_gap("Ich gehe spazieren, ___ das Wetter ist schön.", ["denn", "deshalb", "oder"], "denn"),
                 choice_gap("Das Wetter ist kalt, ___ sonnig.", ["aber", "denn", "dann"], "aber"),
                 choice_gap("Wir frühstücken. ___ gehen wir zur Schule.", ["Danach", "Denn", "Aber"], "Danach"),
                 mc("Welcher Satz ist richtig?", ["Es ist kalt. Darum wir bleiben zu Hause.", "Es ist kalt. Darum bleiben wir zu Hause."], "B"),
                 mc("„neblig“ — o'zbekchasi qaysi?", ["tumanli", "shamolli", "quruq"], "A"),
                 mc("„der Schnee“ — o'zbekchasi qaysi?", ["qor", "yomg'ir", "do'l"], "A"),
                 mc("„Die Sonne ___.“", ["scheint", "schneit", "regnet"], "A"),
                 tf("„wechselhaft“ bedeutet „o'zgaruvchan“.", True),
                 match("Was passt zusammen?", ["der Wind", "das Gewitter", "heiß", "selten"], ["shamol", "momaqaldiroq", "issiq", "kamdan-kam", "tuman"],
                       {"1": "A", "2": "B", "3": "C", "4": "D"}),
             ]),
    ]
