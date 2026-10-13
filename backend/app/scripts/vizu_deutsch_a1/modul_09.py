"""Modul 9 — Meine Reise nach Deutschland — Grammatik: Lokalangaben (book pp. 89-97).

p.92 (30 questions): the answer sheet contradicts the book's own rules on
p.91 in two places (3: "bei der Arbeit"; 24: "in die Schweiz"); the book's
rule is used there.

p.93 Brief 3 question 3 "Paul fährt jeden Tag mit dem Zug in die Berge" is
left out: the letter says he takes the train every day and sees the
mountains — that he goes INTO the mountains is neither stated nor denied, so
no Richtig/Falsch answer can be proven from the text. Hören gap 5 ("…ist er
___ Markt gegangen") accepts "auf den" and "zum" (both correct German)."""

from . import (
    article_set, base, choice_gap, exercise, gap, html_table, intro_html, match, mc, reverse_vocab_set, summary_html, tf, ul, vocab_match_sets,
    words,
)

L = 9
LESSON_TITLE = "Meine Reise nach Deutschland"
LESSON_DESCRIPTION = "Thema: Meine Reise nach Deutschland · Grammatik: Lokalangaben (wo? wohin?)"
IMAGES = [("01_cover.jpg", "EINFUEHRUNG", "Modul 9 — Meine Reise nach Deutschland (Buch, S. 89)")]
RETIRED_IMAGE_TITLES: list[str] = []

EINFUEHRUNG_HTML = intro_html(
    9, "Meine Reise nach Deutschland", "Lokalangaben — wo? (qayerda?) va wohin? (qayerga?)",
    ["„qayerga?“ (wohin?): nach Berlin, in die Stadt, ins Kino, zum Arzt, auf den Markt;",
     "„qayerda?“ (wo?): in der Stadt, im Kino, beim Arzt, auf dem Markt, am Meer, zu Hause;",
     "wohin? — Akkusativ, wo? — Dativ farqini tushunish;",
     "sayohatga oid so'zlarni o'rganish: die Reise, das Hotel, die Gastfamilie, besichtigen."],
    ["„Ich bin nach Italien gefahren. Ich war in Rom.“ — qayerga borganingiz va qayerda bo'lganingizni aytasiz;",
     "Max, Lisa va Paulning sayohat xatlarini o'qib, Richtig/Falsch topshirig'ini bajarasiz;",
     "uch do'stning sayohati haqidagi matnni tinglab, predloglarni yozasiz;",
     "do'stingizga sayohatingiz haqida xat yozasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(9, [
    "<strong>Wohin? (Akkusativ):</strong> nach Deutschland / Berlin / Hause · in die Schule, in den Park, ins Kino · zur Arbeit, zum Arzt · auf den Markt, ans Meer.",
    "<strong>Wo? (Dativ):</strong> in Deutschland · in der Schule, im Park, im Kino · bei der Arbeit, beim Arzt · auf dem Markt, am Meer · zu Hause.",
    "<strong>Länder mit Artikel:</strong> in die Türkei / in der Türkei, in die Schweiz / in der Schweiz.",
    "<strong>Reise:</strong> Ich bin nach … gefahren. Ich habe in einem Hotel / bei einer Gastfamilie gewohnt. Ich habe … besichtigt.",
])

_LOKAL = (
    "<h3>WOHIN? (Qayerga?) — yo'nalish</h3>"
    + html_table(["Qoida", "Misollar"],
                 [["1. nach + shahar / davlat (artiklsiz)", "nach Deutschland — Germaniyaga, nach Usbekistan — O'zbekistonga, nach Berlin — Berlinga, "
                   "nach Hause — uyga (maxsus holat)"],
                  ["2. in + Akkusativ — artiklli joylar yoki ichiga kirish", "in die Schule — maktabga, in die Stadt — shaharga, in den Park — parkka, "
                   "ins Kino (in das Kino) — kinoga, ins Krankenhaus — kasalxonaga, in die Türkei — Turkiyaga, in die Schweiz — Shveysariyaga, "
                   "in den Iran — Eronga"],
                  ["3. zu + Dativ — odamga, ishga, maqsadga (ichiga kirish emas)", "zur Arbeit — ishga, zum Arzt — shifokorga, zur Schule — maktabga "
                   "(umumiy maqsad), zum Freund — do'stimnikiga, zur Party — bazmga"],
                  ["4. auf + Akkusativ — tadbirlar, ochiq joylar", "auf den Markt — bozorga, auf die Party — bazmga, aufs Konzert — konsertga, "
                   "auf die Messe — ko'rgazmaga"]])
    + "<h3>WO? (Qayerda?) — joy</h3>"
    + html_table(["Qoida", "Misollar"],
                 [["1. in + Dativ — ichida, hududda", "in der Schule — maktabda, in der Küche — oshxonada, in der Stadt — shaharda, "
                   "in Deutschland — Germaniyada (artiklsiz), in der Türkei, in der Schweiz (artiklli)"],
                  ["2. bei + Dativ — yonida, ish / holat paytida", "bei der Arbeit — ishda, beim Arzt — shifokor huzurida, bei meiner Mutter — onamnikida, "
                   "beim Freund — do'stimnikida, zu Hause — uyda (maxsus holat!)"],
                  ["3. auf + Dativ — ustida / tadbirda, ochiq joyda", "auf der Straße — ko'chada, auf dem Markt — bozorda, auf der Party — ziyofatda, "
                   "auf der Arbeit (ba'zan ishlatiladi)"],
                  ["4. an + Dativ — yonida, chetida (suv, devor, chegara)", "am Fenster — deraza yonida, an der Wand — devorda, am Meer — dengiz bo'yida, "
                   "an der Grenze — chegarada"],
                  ["5. von … aus — joydan turib", "von zu Hause aus — uydan turib, von hier aus — shu yerdan"]])
)

_Q = "Wählen Sie die richtige Präposition."
_MC = [("Ich bin ___ Schule.", ["in die", "in der", "zur"], "B"), ("Ich gehe ___ Schule.", ["in der", "zur", "bei der"], "B"),
       ("Er arbeitet ___ Arbeit.", ["in der", "bei der", "zur"], "B"), ("Wir gehen ___ Arbeit.", ["bei der", "zur", "in der"], "B"),
       ("Sie lebt ___ Deutschland.", ["nach", "in", "zu"], "B"), ("Er fährt ___ Deutschland.", ["zu", "in", "nach"], "C"),
       ("Das Buch liegt ___ Tisch.", ["auf den", "auf dem", "in dem"], "B"), ("Ich lege das Buch ___ Tisch.", ["auf dem", "auf den", "in den"], "B"),
       ("Die Kinder sind ___ Park.", ["in dem", "in den", "zu dem"], "A"), ("Die Kinder gehen ___ Park.", ["in dem", "zu dem", "in den"], "C"),
       ("Meine Mutter ist ___ Küche.", ["in die", "in der", "zur"], "B"), ("Meine Mutter geht ___ Küche.", ["in der", "zu der", "in die"], "C"),
       ("Wir sind ___ Markt.", ["auf dem", "auf den", "in den"], "A"), ("Wir gehen ___ Markt.", ["auf dem", "auf den", "bei dem"], "B"),
       ("Er ist ___ Arzt.", ["beim", "zum", "bei den"], "A"), ("Er geht ___ Arzt.", ["beim", "zum", "bei dem"], "B"),
       ("Sie sind ___ Party.", ["auf der", "auf die", "zur"], "A"), ("Sie gehen ___ Party.", ["auf der", "zur", "auf die"], "C"),
       ("Ich bin ___ Hause.", ["in", "nach", "zu"], "C"), ("Ich gehe ___ Hause.", ["zu", "nach", "in"], "B"),
       ("Das Bild hängt ___ Wand.", ["an der", "an die", "auf der"], "A"), ("Ich hänge das Bild ___ Wand.", ["an der", "auf die", "an die"], "C"),
       ("Wir sind ___ Schweiz.", ["in die", "in der", "nach"], "B"), ("Wir fahren ___ Schweiz.", ["nach", "in der", "in die"], "C"),
       ("Er ist ___ Meer.", ["am", "an das", "im"], "A"), ("Wir fahren ___ Meer.", ["am", "an das", "ans"], "C"),
       ("Sie arbeitet ___ Hause aus.", ["von zu", "von dem", "bei"], "A"), ("Er sitzt ___ Fenster.", ["an dem", "am", "bei dem"], "B"),
       ("Ich gehe ___ Kino.", ["im", "ins", "in dem"], "B"), ("Wir sind ___ Kino.", ["im", "ins", "zum"], "A")]
_EXPL = {3: "Kitob qoidasi (S. 91): bei der Arbeit — ishda.", 18: "auf die Party (zur Party ham ishlatiladi).",
         24: "Kitob qoidasi (S. 91): in die Schweiz — Shveysariyaga.", 26: "ans = an das.", 28: "am = an dem."}
AUFGABEN = [mc(q, o, a, _EXPL.get(i)) for i, (q, o, a) in enumerate(_MC, start=1)]

BRIEF_MAX = ("Lieber Tom,\n\nwie geht es dir? Ich hoffe, es geht dir gut. Mir geht es sehr gut.\n\nIch bin jetzt in Italien, in Rom. Die Stadt ist "
             "sehr alt und schön. Ich wohne in einem kleinen Hotel im Zentrum. Jeden Tag gehe ich durch die Stadt spazieren.\n\nIch besuche Museen "
             "und alte Gebäude. Das Kolosseum gefällt mir sehr. Ich esse Pizza und Pasta und trinke Kaffee. Das Essen ist lecker.\n\nAm Abend "
             "sitze ich in einem Café und höre Musik. Das Wetter ist warm und sonnig. Die Reise macht mir viel Spaß.\n\nViele Grüße\nMax")
BRIEF_LISA = ("Liebe Schwester Anna,\n\nwie geht es dir? Ich hoffe, du bist gesund.\n\nIch bin jetzt in der Türkei, in Istanbul. Die Stadt ist sehr groß "
              "und lebendig. Ich wohne bei einer Gastfamilie. Die Leute sind freundlich.\n\nAm Morgen gehe ich in die Stadt. Ich besichtige Moscheen "
              "und alte Häuser. Ich mache viele Fotos. Am Mittag esse ich türkisches Essen und trinke Tee.\n\nAm Abend gehe ich am Meer spazieren. "
              "Das Wetter ist schön, aber manchmal heiß. Die Reise ist sehr interessant.\n\nLiebe Grüße\nLisa")
BRIEF_PAUL = ("Sehr geehrter Herr Müller,\n\nwie geht es Ihnen? Mir geht es gut, vielen Dank.\n\nIch bin zurzeit in der Schweiz, in Zürich. Die Stadt ist "
              "sehr sauber und ruhig. Ich wohne in einem kleinen Hostel.\n\nJeden Tag fahre ich mit dem Zug. Ich sehe die Berge und die Natur. Ich gehe "
              "viel spazieren und mache Notizen. Ich lerne neue Wörter und übe Deutsch.\n\nAm Nachmittag lese ich ein Buch oder schreibe E-Mails. "
              "Die Reise ist sehr schön und lehrreich. Vielen Dank für Ihren Unterricht.\n\nMit freundlichen Grüßen\nPaul Schneider")
LESEN = [
    tf("Max ist in Rom.", True, passage=1), tf("Er wohnt in einem kleinen Hotel im Zentrum.", True, passage=1),
    tf("Max besucht Museen und hört Musik im Café.", True, passage=1), tf("Er isst Pizza und Pasta und trinkt Kaffee.", True, passage=1),
    tf("Das Wetter ist warm und sonnig.", True, passage=1),
    tf("Lisa ist in Istanbul.", True, passage=2), tf("Sie wohnt bei einer Gastfamilie.", True, passage=2),
    tf("Lisa macht viele Fotos in der Stadt.", True, passage=2), tf("Sie trinkt Tee zum Mittagessen.", True, passage=2),
    tf("Am Abend geht sie am Meer spazieren.", True, passage=2),
    tf("Paul ist in Zürich.", True, passage=3), tf("Er wohnt in einem großen Hotel.", False, "„Ich wohne in einem kleinen Hostel.“", passage=3),
    tf("Paul liest Bücher und schreibt E-Mails.", True, passage=3), tf("Die Reise ist langweilig.", False, "„Die Reise ist sehr schön und lehrreich.“", passage=3),
]

HOEREN_TEXT = ("Letzten Sommer haben drei Freunde aus Deutschland eine Reise gemacht. Max, Lisa und Paul haben neue Länder gesehen und viele Dinge "
               "erlebt. Max ist [[1]] Italien gefahren. Er war [[2]] Rom und hat in einem kleinen Hotel [[3]] Zentrum gewohnt. Die Stadt war sehr "
               "alt und schön. Max hat viele Museen besucht und Musik [[4]] Café gehört. Er hat Pizza und Pasta gegessen und Kaffee getrunken. "
               "Am Nachmittag ist er [[5]] Markt gegangen und hat Fotos gemacht. Am Abend ist er noch [[6]] Straße spazieren gegangen.\n"
               "Lisa ist [[7]] Türkei gefahren. Sie war [[8]] Istanbul und hat bei einer Gastfamilie gewohnt. Die Stadt war groß und lebendig. "
               "Sie hat viele Fotos gemacht und alte Häuser besichtigt. Lisa hat türkisches Essen gegessen und Tee getrunken. Am Abend ist sie "
               "[[9]] Meer spazieren gegangen. Am Wochenende ist sie noch [[10]] Party gegangen.\n"
               "Paul ist [[11]] Schweiz gefahren. Er war [[12]] Zürich und hat in einem kleinen Hostel gewohnt. Die Stadt war sauber und ruhig. "
               "Paul hat jeden Tag mit dem Zug die Berge gesehen. Er hat viele Notizen geschrieben und Deutsch geübt. Am Morgen ist er [[13]] "
               "Messe gegangen und hat etwas Neues gelernt. Alle drei Freunde haben eine schöne Reise gehabt. Sie haben viel gesehen, gegessen "
               "und fotografiert. Sie haben neue Länder, Städte und Kulturen kennengelernt. Sie sind oft [[14]] Straße, [[15]] Kino oder [[16]] "
               "Park gegangen.")
HOEREN_GAPS = {"1": ["nach"], "2": ["in"], "3": ["im"], "4": ["im"], "5": ["auf den", "zum"], "6": ["auf der"], "7": ["in die"], "8": ["in"],
               "9": ["am"], "10": ["auf die", "zur"], "11": ["in die"], "12": ["in"], "13": ["zur", "auf die"], "14": ["auf die"], "15": ["ins"],
               "16": ["in den"]}

_W = [("die", "Reise", "sayohat"), ("reisen", "sayohat qilmoq"), ("der", "Tourist", "sayyoh"), ("der", "Tourismus", "turizm"), ("das", "Land", "mamlakat"),
      ("die", "Stadt", "shahar"), ("das", "Zentrum", "markaz"), ("das", "Hotel", "mehmonxona"), ("das", "Hostel", "xostel"), ("die", "Gastfamilie", "mehmon oila"),
      ("wohnen", "yashamoq, qolmoq"), ("fahren", "bormoq (transport bilan)"), ("gehen", "piyoda bormoq"), ("ankommen", "yetib kelmoq"), ("bleiben", "qolmoq"),
      ("besuchen", "tashrif buyurmoq"), ("besichtigen", "tomosha qilmoq"), ("das", "Museum", "muzey"), ("der", "Markt", "bozor"), ("der", "Park", "park"),
      ("die", "Straße", "ko'cha"), ("das", "Café", "kafe"), ("das", "Kino", "kino"), ("das", "Meer", "dengiz"), ("die", "Berge", "tog'lar"),
      ("spazieren gehen", "sayr qilmoq"), ("Fotos machen", "suratga tushirmoq"), ("essen", "yemoq"), ("trinken", "ichmoq"), ("das", "Essen", "ovqat"),
      ("der", "Tee", "choy"), ("der", "Kaffee", "qahva"), ("die", "Pizza", "pitsa"), ("die", "Pasta", "pasta"), ("das", "Wetter", "ob-havo"),
      ("sonnig", "quyoshli"), ("warm", "iliq"), ("schön", "chiroyli"), ("ruhig", "tinch"), ("lebendig", "jonli"), ("lernen", "o'rganmoq"),
      ("kennenlernen", "tanishib olmoq"), ("erleben", "boshdan kechirmoq"), ("die", "Kultur", "madaniyat"), ("die", "Party", "bazm"),
      ("die", "Messe", "ko'rgazma"), ("der", "Zug", "poyezd"), ("die", "Sehenswürdigkeit", "diqqatga sazovor joy"), ("der", "Urlaub", "ta'til"),
      ("die", "Erinnerung", "xotira")]
WORDS = words(_W, "Reise")


WORTSCHATZ_SETS = [*vocab_match_sets(WORDS, per_set=4), article_set(WORDS)]

UEBUNGEN_SETS = [
    exercise("Wo? oder Wohin? (Lesen)", [
        choice_gap("Max ist jetzt ___ Italien.", ["in", "nach", "zu"], "in", explanation="Brief 1: „Ich bin jetzt in Italien, in Rom.“"),
        choice_gap("Max wohnt in einem kleinen Hotel ___ Zentrum.", ["im", "ins", "zum"], "im"),
        choice_gap("Lisa ist jetzt ___ Türkei.", ["in der", "in die", "nach"], "in der", explanation="die Türkei — Wo? in der Türkei."),
        choice_gap("Am Morgen geht Lisa ___ Stadt.", ["in die", "in der", "nach"], "in die", explanation="Brief 2: „Am Morgen gehe ich in die Stadt.“"),
        choice_gap("Am Abend geht Lisa ___ Meer spazieren.", ["am", "ans", "im"], "am"),
        choice_gap("Paul ist zurzeit ___ Schweiz.", ["in der", "in die", "nach"], "in der"),
        choice_gap("Lisa wohnt ___ einer Gastfamilie.", ["bei", "zu", "in"], "bei"),
        choice_gap("Am Abend sitzt Max ___ einem Café.", ["in", "auf", "nach"], "in"),
    ], "Xatlardagi gaplarda to'g'ri predlogni tanlang.", source="vizu"),
    reverse_vocab_set(WORDS),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: Modul 9", source="vizu", page=89, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage: Wie ist der Tourismus in Deutschland?", page=90,
             prompt="Wie ist der Tourismus in Deutschland? (Beliebte Reiseziele, Natur, Kultur, Infrastruktur …) Welche Stadt oder welchen Ort "
                    "in Deutschland möchten Sie besuchen und warum?",
             min_duration=10, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Lokalangaben (wo? wohin?)", page="91-92",
             rules=[{"title": "Lokalangaben — wo? wohin?", "html": _LOKAL}],
             exercises=[exercise("Aufgaben: Präpositionen (30)", AUFGABEN, _Q + " Ergänzen Sie die Sätze.")]),
        base(L, "lesen", 1, "Lesen: Briefe von der Reise", page=93,
             instruction="Lesen Sie die Texte und entscheiden Sie: Richtig oder Falsch?",
             passages=[{"title": "Brief 1 — Max (Italien)", "text": BRIEF_MAX}, {"title": "Brief 2 — Lisa (Türkei)", "text": BRIEF_LISA},
                       {"title": "Brief 3 — Paul (Schweiz)", "text": BRIEF_PAUL}],
             questions=LESEN, max_score=len(LESEN)),
        base(L, "hoeren", 1, "Hören: Reise der Freunde", page=94, audio_file="A1-9.mp3",
             instruction="Hören Sie den Text und ergänzen Sie die Lücken (Präpositionen).",
             questions=[gap("Reise der Freunde — ergänzen Sie die Präpositionen.", HOEREN_TEXT, HOEREN_GAPS, points=16)]),
        base(L, "schreiben", 1, "Schreiben: Brief — Meine Reise", page=95,
             prompt="Schreiben Sie einen Brief an Alex / Alexandra über Ihre Reise. Nutzen Sie die Stichwörter:\n"
                    "1. Wann und wohin? Mit wem? (Letzten Sommer habe ich eine Reise gemacht. Ich bin mit meinen Freunden gereist.)\n"
                    "2. Wohin? (Ich bin nach Berlin gefahren. Ich war in der Stadt …)\n3. Wo haben Sie gewohnt? (in + Dativ)\n"
                    "4. Was haben Sie gemacht? (mit Ortsangaben)\n5. Essen und Trinken\n6. Wetter und Atmosphäre\n7. Besondere Erlebnisse\n"
                    "8. Fazit (Meine Reise war sehr schön …)\nAnrede: Liebe/r Alex/Alexandra, … Gruß: Liebe Grüße / Mit freundlichen Grüßen, (Name)",
             task_type="letter", audience="Alex / Alexandra (Freund / Freundin)", min_words=60, max_words=150, time_limit=25,
             support_phrases=["Liebe/r …,", "Ich bin nach … gefahren.", "Ich habe in einem … gewohnt.", "Am Abend bin ich am Meer spazieren gegangen.",
                              "Liebe Grüße"]),
        base(L, "sprechen", 1, "Sprechen: Über die Reise erzählen", page=96, topic="Meine Reise",
             prompt="Sprechen Sie über Ihre Reise nach dem Plan. Beispiel: „Guten Tag! Heute möchte ich über meine Reise erzählen. …“",
             questions=["Wann war die Reise?", "Mit wem bist du gereist?", "Wohin bist du gefahren?", "Wo hast du gewohnt?", "Was hast du gemacht?",
                        "Wo hast du diese Dinge gemacht?", "Wie war das Wetter?", "Wie war die Reise?"],
             response_type="monolog", min_duration=40, max_duration=180,
             speech_goal="Eine Reise im Perfekt mit Ortsangaben (nach, in, am, auf …) erzählen.",
             keywords=["Ich bin nach … gefahren", "in einem Hotel", "am Meer", "auf den Markt"]),
        base(L, "wortschatz", 1, "Wortschatz Modul 9: Reise", page=97, words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False),
        base(L, "uebungen", 1, "Übungen Modul 9", exercises=UEBUNGEN_SETS, source="vizu"),
        base(L, "yakuniy", 1, "Abschlusstest: Modul 9", source="vizu",
             instruction="Lokalangaben (wo? wohin?) va sayohat so'zlari bo'yicha yakuniy test.",
             questions=[
                 choice_gap("Ich fahre ___ Berlin.", ["nach", "in", "zu"], "nach"),
                 choice_gap("Wir wohnen ___ Deutschland.", ["in", "nach", "zu"], "in"),
                 choice_gap("Meine Schwester geht ___ Zahnarzt.", ["zum", "beim", "im"], "zum"),
                 choice_gap("Sie ist ___ Arbeit.", ["bei der", "zur", "nach"], "bei der"),
                 choice_gap("Wir gehen heute Abend ___ Theater.", ["ins", "im", "zum"], "ins", explanation="in + das (Akkusativ) = ins."),
                 choice_gap("Wir sind ___ Meer.", ["am", "ans", "nach"], "am"),
                 mc("Wohin? oder Wo?: „in die Schule“", ["Wohin?", "Wo?"], "A"),
                 mc("Welcher Satz ist richtig?", ["Ich bin zu Hause.", "Ich bin nach Hause.", "Ich bin in Hause."], "A"),
                 mc("„die Sehenswürdigkeit“ — o'zbekchasi qaysi?", ["diqqatga sazovor joy", "ko'rgazma", "mehmon oila"], "A"),
                 tf("„ankommen“ bedeutet „yetib kelmoq“.", True),
                 match("Was passt zusammen?", ["der Markt", "das Meer", "die Messe", "der Zug"], ["bozor", "dengiz", "ko'rgazma", "poyezd", "tog'"],
                       {"1": "A", "2": "B", "3": "C", "4": "D"}),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: Modul 9", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
