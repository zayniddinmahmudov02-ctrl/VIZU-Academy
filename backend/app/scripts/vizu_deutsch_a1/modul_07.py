"""Modul 7 — Meine letzte Woche — Grammatik: Präteritum (book pp. 70-79).

p.73 task 3 ("Was passt zusammen? Verbinde!") is not imported as an
auto-graded task: its verb column has no form for "du" (warst / hattest), so
the book gives no unambiguous solution. p.73 task 2 (Bilde Sätze) is a
choice between the correct sentence and two wrong word orders. p.74 question
1 "Wo ist Lili?" is asked about the writer (Lili receives the letter). The
Hören word list (war ×4, ging ×3, aß ×2, …) decides every gap."""

from . import (
    forward_vocab_set,
    article_set, base, choice_gap, exercise, gap, html_table, intro_html, match, mc, reverse_vocab_set, short, summary_html, text_gap, tf, ul,
    vocab_match_sets, word_order_mc, words,
)

L = 7
LESSON_TITLE = "Meine letzte Woche"
LESSON_DESCRIPTION = "Thema: Meine letzte Woche · Grammatik: Präteritum"
IMAGES = [("01_cover.jpg", "EINFUEHRUNG", "Modul 7 — Meine letzte Woche (Buch, S. 70)")]
RETIRED_IMAGE_TITLES: list[str] = []

EINFUEHRUNG_HTML = intro_html(
    7, "Meine letzte Woche", "Präteritum (o'tgan zamon)",
    ["haben va sein ning o'tgan zamon shakllari: ich hatte, ich war, du hattest, du warst …;",
     "kuchsiz fe'llarning Präteritumi: spielen → spielte, machen → machte;",
     "kuchli fe'llarning Präteritumi: sehen → sah, gehen → ging, essen → aß;",
     "hafta kunlari, oy nomlari va vaqt iboralarini o'rganish: gestern, letzte Woche, am Wochenende."],
    ["„Letzte Woche war ich in Taschkent. Am Montag ging ich ins Kino.“ — o'tgan haftangiz haqida aytasiz;",
     "Parijdan yozilgan ikki xatni o'qib, hozirgi va o'tgan zamonni farqlaysiz;",
     "Toshkentdagi kun haqidagi matnni tinglab, fe'llarni to'ldirasiz;",
     "bolaligingiz haqida qisqa hikoya qilasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(7, [
    "<strong>haben / sein:</strong> ich hatte / war, du hattest / warst, er hatte / war, wir hatten / waren, ihr hattet / wart, sie hatten / waren.",
    "<strong>Schwache Verben:</strong> spielen → ich spielte, du spieltest, wir spielten · machen → machte, arbeiten → arbeitete.",
    "<strong>Starke Verben:</strong> sehen → sah, gehen → ging, kommen → kam, essen → aß, trinken → trank, schreiben → schrieb, aufstehen → stand auf.",
    "<strong>Zeit:</strong> gestern, letzte Woche, letztes Jahr, am Wochenende, am Montag … · Monate: Januar … Dezember.",
])

_PRAET = (
    "<p><strong>Präteritum</strong> — o'tgan zamon shakli. Asosan hikoya va yozma matnlarda ishlatiladi. Kuchli fe'llar shakli o'zgaradi. "
    "Sein va haben — yordamchi fe'llar.</p>"
    "<h3>haben — Präteritum (hatte) / sein — Präteritum (war)</h3>"
    + html_table(["Shaxs", "haben", "Misol", "sein", "Misol"],
                 [["ich", "hatte", "Ich hatte Zeit. (Mening vaqtim bor edi.)", "war", "Ich war müde. (Men charchagan edim.)"],
                  ["du", "hattest", "Du hattest Hunger. (Sening ochliging bor edi.)", "warst", "Du warst zu Hause. (Sen uyda eding.)"],
                  ["er / sie / es", "hatte", "Er hatte ein Auto. (Uning mashinasi bor edi.)", "war", "Er war krank. (U kasal edi.)"],
                  ["wir", "hatten", "Wir hatten Unterricht. (Bizda dars bor edi.)", "waren", "Wir waren im Park. (Biz parkda edik.)"],
                  ["ihr", "hattet", "Ihr hattet Glück. (Sizlarda omad bor edi.)", "wart", "Ihr wart pünktlich. (Sizlar o'z vaqtida edingiz.)"],
                  ["sie / Sie", "hatten", "Sie hatten Probleme. (Ularda muammo bor edi.)", "waren", "Sie waren glücklich. (Ular xursand edilar.)"]])
    + "<h3>Schwache Verben / kuchsiz fe'llar — spielen</h3>"
    + html_table(["Shaxs", "Präsens", "Präteritum", "Tarjima"],
                 [["ich", "spiele", "spielte", "Men o'ynayman / Men o'ynadim"], ["du", "spielst", "spieltest", "Sen o'ynaysan / Sen o'ynading"],
                  ["er / sie / es", "spielt", "spielte", "U o'ynaydi / U o'ynadi"], ["wir", "spielen", "spielten", "Biz o'ynaymiz / Biz o'ynadik"],
                  ["ihr", "spielt", "spieltet", "Sizlar o'ynaysizlar / Sizlar o'ynadingiz"], ["sie / Sie", "spielen", "spielten", "Ular o'ynaydilar / Ular o'ynadilar"]])
    + "<h3>Starke Verben / kuchli fe'llar — sehen</h3>"
    + html_table(["Shaxs", "Präsens", "Präteritum", "Tarjima"],
                 [["ich", "sehe", "sah", "Men ko'ryapman / Men ko'rdim"], ["du", "siehst", "sahst", "Sen ko'ryapsan / Sen ko'rding"],
                  ["er / sie / es", "sieht", "sah", "U ko'ryapti / U ko'rdi"], ["wir", "sehen", "sahen", "Biz ko'ryapmiz / Biz ko'rdik"],
                  ["ihr", "seht", "saht", "Sizlar ko'ryapsizlar / Sizlar ko'rdingiz"], ["sie / Sie", "sehen", "sahen", "Ular ko'ryaptilar / Ular ko'rdilar"]])
    + "<h3>Präsens → Präteritum: machen / aufstehen</h3>"
    + html_table(["Shaxs", "Präsens", "Präteritum"],
                 [["ich", "mache / stehe auf", "machte / stand auf"], ["du", "machst / stehst auf", "machtest / standst auf"],
                  ["er / sie / es", "macht / steht auf", "machte / stand auf"], ["wir", "machen / stehen auf", "machten / standen auf"],
                  ["ihr", "macht / steht auf", "machtet / standet auf"], ["sie / Sie", "machen / stehen auf", "machten / standen auf"]])
    + "<p><strong>Beispiele:</strong> Gestern spielte ich Fußball. Er sah einen Film. Wir machten Hausaufgaben. Ich war zu Hause.</p>"
    + "<p><strong>Tipp:</strong> Ko'proq misollar bilan mashq qiling. Shakllarni yodlab oling!</p>"
)

_Q1 = "Setze die richtige Form im Präteritum ein!"
_FILL = [("Gestern ___ ich viel zu tun. (haben)", ["hatte"]), ("Letzte Woche ___ meine Eltern im Urlaub. (sein)", ["waren"]),
         ("Wir ___ Fußball im Park. (spielen)", ["spielten"]), ("Ich ___ gestern einen Brief. (schreiben)", ["schrieb"]),
         ("Du ___ spät nach Hause. (kommen)", ["kamst"]), ("Er ___ einen Film im Fernsehen. (sehen)", ["sah"]),
         ("Wir ___ letzte Nacht lange wach. (bleiben)", ["blieben"]), ("Ihr ___ gestern Pizza zum Mittagessen. (essen)", ["aßt"]),
         ("Sie ___ mir beim Umzug. (helfen)", ["halfen", "half"]), ("Ich ___ gestern früh auf. (aufstehen)", ["stand"]),
         ("Letztes Wochenende ___ ich viel Hausaufgaben. (machen)", ["machte"]), ("Du ___ gestern einen Freund an. (anrufen)", ["riefst"]),
         ("Er ___ letzte Woche krank. (sein)", ["war"]), ("Wir ___ gestern eine schöne Wanderung. (machen)", ["machten"]),
         ("Ihr ___ am Samstag im Kino. (sein)", ["wart"]), ("Sie ___ gestern das neue Buch. (lesen)", ["lasen", "las"]),
         ("Ich ___ gestern spät ins Bett. (gehen)", ["ging"]), ("Du ___ gestern deine Hausaufgaben. (machen)", ["machtest"]),
         ("Er ___ am Sonntag im Garten. (arbeiten)", ["arbeitete"]), ("Wir ___ gestern einen tollen Film. (sehen)", ["sahen"])]
FILL = [text_gap(s, a, _Q1, explanation=f"Javob: {a[0]}" + (f" (sie — u: {a[1]})" if len(a) > 1 else "")) for s, a in _FILL]

_BILDE = [("ich / gestern / Schule / haben", ["Ich hatte gestern Schule.", "Gestern hatte ich Schule."]),
          ("wir / am Wochenende / Ausflug / machen", ["Wir machten am Wochenende einen Ausflug.", "Am Wochenende machten wir einen Ausflug.",
                                                     "Wir machten am Wochenende Ausflug."]),
          ("du / spät / nach Hause / kommen", ["Du kamst spät nach Hause."]),
          ("er / ein Buch / lesen", ["Er las ein Buch."]),
          ("sie / im Park / sitzen", ["Sie saß im Park.", "Sie saßen im Park."]),
          ("ihr / am Abend / fernsehen", ["Ihr saht am Abend fern.", "Am Abend saht ihr fern."])]
BILDE = [word_order_mc(w, acc[0], "Bilde einen Satz im Präteritum") for w, acc in _BILDE]
_WANDLE = [("Ich habe einen Hund.", ["Ich hatte einen Hund."]), ("Wir gehen ins Kino.", ["Wir gingen ins Kino."]),
           ("Er spielt Gitarre.", ["Er spielte Gitarre."]), ("Sie macht Hausaufgaben.", ["Sie machte Hausaufgaben."]),
           ("Du hilfst mir.", ["Du halfst mir."]), ("Ihr seid müde.", ["Ihr wart müde."])]
WANDLE = [short(f"Wandle den Satz in das Präteritum um: {s}", acc, max_length=120) for s, acc in _WANDLE]

BRIEF_1 = ("Liebe Lili,\n\nich bin heute in Paris. Das Wetter ist schön. Ich gehe spazieren und sehe viele schöne Gebäude. Ich esse Croissants "
           "und trinke Kaffee. Ich besuche den Eiffelturm und mache Fotos. Ich kaufe auch Souvenirs für dich.\n\nViele Grüße\n[Name]")
BRIEF_2 = ("Liebe Lili,\n\nich war gestern in Paris. Das Wetter war schön. Ich ging spazieren und sah viele schöne Gebäude. Ich aß Croissants "
           "und trank Kaffee. Ich besuchte den Eiffelturm und machte Fotos. Ich kaufte auch Souvenirs für dich.\n\nViele Grüße\n[Name]")
BRIEF_1_UZ = ("Aziz Lili, men bugun Parijdaman. Ob-havo chiroyli. Men sayr qilaman va ko'p chiroyli binolarni ko'raman. Men kruassan yeyman va "
              "qahva ichaman. Men Eyfel minorasiga boraman va suratlar olaman. Men sen uchun sovg'alar ham sotib olaman. Ko'p salomlar bilan …")
BRIEF_2_UZ = ("Aziz Lili, men kecha Parijda edim. Ob-havo chiroyli edi. Men sayr qildim va ko'p chiroyli binolarni ko'rdim. Men kruassan yedim va "
              "qahva ichdim. Men Eyfel minorasiga bordim va suratlar oldim. Men sen uchun sovg'alar ham sotib oldim. Ko'p salomlar bilan …")

LESEN = [
    mc("Wo ist die Person im ersten Brief?", ["In Berlin", "In Paris", "In Rom"], "B",
       "Brief 1: „ich bin heute in Paris.“ (Kitobda: „Wo ist Lili?“ — Lili xatni oluvchi, Parijda xat yozuvchi.)"),
    mc("Wie ist das Wetter?", ["Schön", "Kalt und regnerisch", "Windig"], "A"),
    mc("Was isst sie?", ["Pizza", "Croissants", "Kuchen"], "B"),
    mc("Was trinkt sie?", ["Tee", "Saft", "Kaffee"], "C"),
    mc("Was besucht sie?", ["Den Eiffelturm", "Ein Museum", "Einen Park"], "A"),
    mc("Was macht sie am Eiffelturm?", ["Sie macht Fotos.", "Sie isst.", "Sie schläft."], "A"),
    mc("Was kauft sie?", ["Bücher", "Souvenirs für Lili", "Kleidung"], "B"),
    mc("Wann war sie im zweiten Brief in Paris?", ["Heute", "Gestern", "Morgen"], "B", "Brief 2: „ich war gestern in Paris.“", passage=2),
    tf("Brief 2: Das Wetter war schlecht.", False, "Brief 2: „Das Wetter war schön.“", passage=2),
    mc("Brief 2: „Ich ___ viele schöne Gebäude.“ — welches Wort steht im Brief?", ["sah", "sehe", "sehen"], "A",
       "Brief 2: „Ich ging spazieren und sah viele schöne Gebäude.“", passage=2),
    tf("Brief 2: Die Person kaufte Souvenirs für Lili.", True, "Brief 2: „Ich kaufte auch Souvenirs für dich.“", passage=2),
]

HOEREN_TEXT = ("Gestern [[1]] ich in Taschkent. Ich [[2]] am Morgen an und das Wetter [[3]] schön. Zuerst [[4]] ich in einem kleinen Café. "
               "Ich [[5]] ein Brötchen und [[6]] einen Tee. Danach [[7]] ich in die Stadt und [[8]] viele interessante Gebäude. "
               "Ich [[9]] den Amir-Timur-Platz und [[10]] viele Fotos. Später [[11]] ich in einen Park und [[12]] mich ein bisschen aus. "
               "Ich [[13]] auch Souvenirs für meine Familie und meine Freunde. Am Abend [[14]] ich in einem Restaurant und [[15]] usbekisches "
               "Essen. Danach [[16]] ich zurück nach Hause und ich [[17]] müde, aber glücklich. Es [[18]] ein sehr schöner Tag in Taschkent.")
_KEY = ["war", "kam", "war", "frühstückte", "aß", "trank", "ging", "sah", "besuchte", "machte", "ging", "ruhte", "kaufte", "aß", "probierte",
        "ging", "war", "war"]
HOEREN_GAPS = {str(i): [w] for i, w in enumerate(_KEY, start=1)}

WORDS = (
    words([("die", "Stadt", "shahar"), ("das", "Gebäude", "bino"), ("der", "Eiffelturm", "Eyfel minorasi"), ("der", "Amir-Timur-Platz", "Amir Temur maydoni"),
           ("die", "Großeltern", "buvi va bobo"), ("der", "Hund", "it"), ("das", "Eis", "muzqaymoq"), ("der", "Saft", "sharbat"),
           ("das", "Restaurant", "restoran"), ("der", "Tag", "kun"), ("die", "Woche", "hafta"), ("die", "Kindheit", "bolalik"), ("gestern", "kecha"),
           ("heute", "bugun"), ("morgen", "ertaga"), ("am Morgen", "ertalab"), ("am Abend", "kechqurun"), ("letzte Woche", "o'tgan hafta"),
           ("letztes Jahr", "o'tgan yil"), ("am Wochenende", "hafta oxiri"), ("vorher", "oldin"), ("danach", "keyin")], "Wörter")
    + words([("Montag", "dushanba"), ("Dienstag", "seshanba"), ("Mittwoch", "chorshanba"), ("Donnerstag", "payshanba"), ("Freitag", "juma"),
             ("Samstag", "shanba"), ("Sonntag", "yakshanba")], "Wochentage — hafta kunlari")
    + words([("Januar", "yanvar"), ("Februar", "fevral"), ("März", "mart"), ("April", "aprel"), ("Mai", "may"), ("Juni", "iyun"), ("Juli", "iyul"),
             ("August", "avgust"), ("September", "sentyabr"), ("Oktober", "oktyabr"), ("November", "noyabr"), ("Dezember", "dekabr")],
            "Monate — oy nomlari")
    + words([("spazieren", "sayr qilmoq"), ("Fotos machen", "suratlar olish"), ("die", "Croissants", "kruassanlar"), ("die", "Souvenirs", "esdalik sovg'alar"),
             ("besuchen", "bormoq, tashrif buyurmoq"), ("kaufen", "sotib olmoq")], "Lesen: Wörter-Hilfe")
)


WORTSCHATZ_SETS = [*vocab_match_sets(WORDS), article_set(WORDS), forward_vocab_set(WORDS)]

UEBUNGEN_SETS = [
    exercise("Präsens → Präteritum (Lesen)", [
        choice_gap("Ich bin heute in Paris. → Ich ___ gestern in Paris.", ["war", "bin", "wurde"], "war", explanation="Brief 2: „ich war gestern in Paris.“"),
        choice_gap("Ich gehe spazieren. → Ich ___ spazieren.", ["ging", "gehte", "gang"], "ging", explanation="Brief 2: „Ich ging spazieren …“"),
        choice_gap("Ich sehe viele Gebäude. → Ich ___ viele Gebäude.", ["sah", "sehte", "sahe"], "sah"),
        choice_gap("Ich esse Croissants. → Ich ___ Croissants.", ["aß", "esste", "ass"], "aß"),
        choice_gap("Ich trinke Kaffee. → Ich ___ Kaffee.", ["trank", "trinkte", "trunk"], "trank"),
        choice_gap("Ich besuche den Eiffelturm. → Ich ___ den Eiffelturm.", ["besuchte", "besuch", "besuchten"], "besuchte"),
        choice_gap("Ich kaufe Souvenirs. → Ich ___ Souvenirs.", ["kaufte", "kauf", "kaufen"], "kaufte"),
    ], "Brief 1 dagi gaplarni Präteritumga o'tkazing (Brief 2 bilan solishtiring).", source="vizu"),
    exercise("Wann war das?", [
        mc("Heute ist Mittwoch. Gestern war …", ["Dienstag", "Donnerstag", "Montag"], "A"),
        mc("Jetzt ist März. Letzten Monat war …", ["Februar", "April", "Januar"], "A"),
        mc("Welcher Monat kommt nach Juni?", ["Juli", "Mai", "August"], "A"),
        mc("„vorher“ bedeutet …", ["oldin", "keyin", "kecha"], "A"),
    ], "Kunlar, oylar va vaqt so'zlari.", source="vizu"),
    reverse_vocab_set(WORDS),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: Modul 7", source="vizu", page=70, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage des Themas: Wie ist die Geschichte von Deutschland?", page=71,
             prompt="Wie ist die Geschichte von Deutschland? Was weißt du über die Geschichte von Deutschland? "
                    "(früher viele Königreiche, 1871 Kaiserreich, 1914–1945 zwei Weltkriege, 1949 zwei Teile, 1990 wieder ein Land)",
             min_duration=10, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Präteritum", page="72-73",
             rules=[{"title": "Präteritum", "html": _PRAET}],
             exercises=[
                 exercise("Aufgabe 1: Präteritum einsetzen (20)", FILL, _Q1 + " (haben, sein, spielen, schreiben, kommen, sehen, bleiben, essen, "
                          "helfen, aufstehen, machen, anrufen, lesen, gehen, arbeiten)"),
                 exercise("Aufgabe 2: Bilde Sätze im Präteritum (6)", BILDE, "Bilde Sätze im Präteritum!"),
                 exercise("Aufgabe 4: Wandle die Sätze in das Präteritum um (6)", WANDLE, "Wandle die Sätze in das Präteritum um!"),
             ]),
        base(L, "lesen", 1, "Lesen: Mein Tag in Paris", page=74,
             instruction="Lies die beiden Briefe und beantworte die Fragen.",
             metadata={"book_page": "74-75", "note": "Savollar kitobdan (javob variantlari VIZU tomonidan)."},
             passages=[{"title": "Brief 1: Mein erster Tag in Paris", "text": f"{BRIEF_1}\n\nO'zbekcha tarjima: {BRIEF_1_UZ}"},
                       {"title": "Brief 2: Mein Tag in Paris", "text": f"{BRIEF_2}\n\nO'zbekcha tarjima: {BRIEF_2_UZ}"}],
             questions=LESEN, max_score=sum(q["points"] for q in LESEN)),
        base(L, "hoeren", 1, "Hören: Mein Tag in Taschkent", page=76, audio_file="A1-7.mp3",
             instruction="Höre den Text und ergänze die Lücken mit den passenden Wörtern: sah, aß, ging, war, kaufte, probierte, machte, trank, "
                         "frühstückte, besuchte, ruhte, kam, war, ging, aß, ging, war, war.",
             questions=[gap("Mein Tag in Taschkent — ergänze die Lücken.", HOEREN_TEXT, HOEREN_GAPS, points=18)]),
        base(L, "schreiben", 1, "Schreiben: Meine letzte Woche", page=77,
             prompt="Schreibe einen kurzen Text über deine letzte Woche. Benutze die Struktur:\n"
                    "Einleitung: Letzte Woche war ich sehr beschäftigt. / Letzte Woche war meine Woche interessant.\n"
                    "Hauptteil: Am Montag ging ich zur Schule und lernte Deutsch. Am Dienstag arbeitete ich zu Hause und machte meine "
                    "Hausaufgaben. Am Mittwoch besuchte ich meine Freunde und spielte Fußball. … (die ganze Woche)\n"
                    "Schluss: Es war eine schöne Woche. / Ich freute mich über meine Woche. / Ich war müde, aber glücklich.",
             task_type="description", min_words=40, max_words=120, time_limit=20,
             support_phrases=["Letzte Woche war ich …", "Am Montag ging ich …", "Am Dienstag …", "Es war eine schöne Woche."]),
        base(L, "sprechen", 1, "Sprechen: Meine Kindheit", page=78, topic="Meine Kindheit",
             prompt="Sprich über deine Kindheit. Benutze die Fragen und den Beispieltext (Als Kind war ich sehr glücklich. Ich wurde in "
                    "Taschkent geboren und wuchs dort auf. Ich spielte gern mit meinen Freunden im Park …).",
             questions=["Wann bist du geboren?", "Wo bist du aufgewachsen?", "Was hast du als Kind gern gemacht?", "Hattest du Geschwister?"],
             response_type="monolog", min_duration=30, max_duration=150,
             speech_goal="Über die eigene Kindheit im Präteritum erzählen: Geburtsort, Spiele, Familie, Schule.",
             keywords=["Als Kind", "war", "hatte", "spielte"]),
        base(L, "wortschatz", 1, "Wortschatz Modul 7", page="74, 79", words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False),
        base(L, "uebungen", 1, "Übungen Modul 7", exercises=UEBUNGEN_SETS, source="vizu"),
        base(L, "yakuniy", 1, "Abschlusstest: Modul 7", source="vizu",
             instruction="Präteritum va darsdagi so'zlar bo'yicha yakuniy test.",
             questions=[
                 choice_gap("Gestern ___ ich krank.", ["war", "bin", "warst"], "war"),
                 choice_gap("Wir ___ keine Zeit.", ["hatten", "hattet", "hatte"], "hatten"),
                 choice_gap("Du ___ gestern zu Hause.", ["warst", "wart", "war"], "warst"),
                 choice_gap("Er ___ einen Film.", ["sah", "sieht", "sahen"], "sah"),
                 choice_gap("Ich ___ Fußball. (spielen)", ["spielte", "spielt", "spielten"], "spielte"),
                 mc("Präteritum von „gehen“ (ich):", ["ging", "gehte", "gang"], "A"),
                 mc("Präteritum von „essen“ (er):", ["aß", "esste", "isst"], "A"),
                 mc("Präteritum von „aufstehen“ (ich):", ["stand auf", "stehte auf", "aufstand"], "A"),
                 mc("„letzte Woche“ — o'zbekchasi qaysi?", ["o'tgan hafta", "keyingi hafta", "hafta oxiri"], "A"),
                 tf("„die Kindheit“ bedeutet „bolalik“.", True),
                 match("Was passt zusammen?", ["Januar", "Juli", "Oktober", "gestern"], ["yanvar", "iyul", "oktyabr", "kecha", "ertaga"],
                       {"1": "A", "2": "B", "3": "C", "4": "D"}),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: Modul 7", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
