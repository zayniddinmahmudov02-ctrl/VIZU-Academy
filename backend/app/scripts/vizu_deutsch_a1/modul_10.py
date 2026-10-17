"""Modul 10 — Wir sind im Supermarkt — Grammatik: Adjektivdeklination (book pp. 98-107).

p.101 (30 questions): the answer sheet belongs to an older version and
contradicts the book's own declension table (p.100) in 8 items (1, 3, 6, 9,
17, 25, 27, …). The answers here follow the table on p.100. Items 21-30 drill
the table's "Artikelsiz" column; the explanation says that a singular
countable noun normally needs an article in a real sentence. Item 24 prints
no gap in the book ("das Haus guten Mannes"); the gap is set on "gut__"."""

from . import (
    forward_vocab_set,
    article_set, base, choice_gap, exercise, html_table, intro_html, match, mc, reverse_vocab_set, summary_html, tf, vocab_match_sets, words,
)

L = 10
LESSON_TITLE = "Wir sind im Supermarkt"
LESSON_DESCRIPTION = "Thema: Wir sind im Supermarkt · Grammatik: Adjektivdeklination"
IMAGES = [("01_cover.jpg", "EINFUEHRUNG", "Modul 10 — Wir sind im Supermarkt (Buch, S. 98)")]
RETIRED_IMAGE_TITLES: list[str] = []

EINFUEHRUNG_HTML = intro_html(
    10, "Wir sind im Supermarkt", "Adjektivdeklination (sifatlarning turlanishi)",
    ["sifat qo'shimchasini artikl, rod va kelishikka qarab tanlash: der gute Mann, ein guter Mann, guter Wein;",
     "aniq artikl bilan: Nominativda -e, qolgan joylarda ko'pincha -en;",
     "noaniq artikl bilan: ein guter Mann, ein gutes Kind, eine gute Frau;",
     "supermarket va kiyim do'koniga oid so'zlarni o'rganish: die Kasse, das Angebot, anprobieren."],
    ["„Ich kaufe frisches Brot und eine blaue Jacke.“ — xarid haqida sifatlar bilan gapirasiz;",
     "supermarketdagi xarid haqidagi ikki matnni o'qib, Richtig/Falsch topshirig'ini bajarasiz;",
     "supermarket va bozor haqidagi ikki matnni tinglab, savollarga javob berasiz;",
     "do'konda sotuvchi bilan dialog qurasiz."])

ZUSAMMENFASSUNG_HTML = summary_html(10, [
    "<strong>Aniq artikl bilan:</strong> der/die/das gute … (Nominativ), die gute Frau, das gute Kind (Akkusativ) — boshqa hamma joyda -en: den guten Mann, dem guten Kind, die guten Leute.",
    "<strong>Noaniq artikl bilan:</strong> ein guter Mann, ein gutes Kind, eine gute Frau · einen guten Mann · einem guten Freund · meine guten Leute.",
    "<strong>Artikelsiz:</strong> qo'shimcha artikl vazifasini bajaradi — frisches Brot, kalte Milch, guter Wein, mit gutem Freund, gute Leute.",
    "<strong>Einkaufen:</strong> Ich möchte … kaufen. Ich nehme … Was kostet …? Das macht zusammen … Euro. Ich bezahle mit Karte.",
])

_ADJ = (
    "<p>Sifat ot oldida kelganda kelishik, rod va artiklga qarab qo'shimcha oladi.</p>"
    + html_table(["Kelishik + rod", "Aniq artikel bilan", "Noaniq artikel bilan", "Artikelsiz"],
                 [["Mask. Nominativ", "der gute Mann", "ein guter Mann", "guter Mann"], ["Mask. Genitiv", "des guten Mannes", "eines guten Mannes", "guten Mannes"],
                  ["Mask. Dativ", "dem guten Mann", "einem guten Mann", "gutem Mann"], ["Mask. Akkusativ", "den guten Mann", "einen guten Mann", "guten Mann"],
                  ["Fem. Nominativ", "die gute Frau", "eine gute Frau", "gute Frau"], ["Fem. Genitiv", "der guten Frau", "einer guten Frau", "guter Frau"],
                  ["Fem. Dativ", "der guten Frau", "einer guten Frau", "guter Frau"], ["Fem. Akkusativ", "die gute Frau", "eine gute Frau", "gute Frau"],
                  ["Neut. Nominativ", "das gute Kind", "ein gutes Kind", "gutes Kind"], ["Neut. Genitiv", "des guten Kindes", "eines guten Kindes", "guten Kindes"],
                  ["Neut. Dativ", "dem guten Kind", "einem guten Kind", "gutem Kind"], ["Neut. Akkusativ", "das gute Kind", "ein gutes Kind", "gutes Kind"],
                  ["Pl. Nominativ", "die guten Leute", "meine guten Leute", "gute Leute"], ["Pl. Genitiv", "der guten Leute", "meiner guten Leute", "guter Leute"],
                  ["Pl. Dativ", "den guten Leuten", "meinen guten Leuten", "guten Leuten"], ["Pl. Akkusativ", "die guten Leute", "meine guten Leute", "gute Leute"]])
    + "<p>Tarjima: der gute Mann — yaxshi erkak; des guten Mannes — yaxshi erkakning; dem guten Mann — yaxshi erkakka; den guten Mann — yaxshi erkakni.</p>"
    + "<h3>Qo'shimchalar jadvali</h3>"
    + html_table(["Kelishik + rod", "Aniq artikel bilan", "Noaniq artikel bilan", "Artikelsiz"],
                 [["Mask. Nominativ (der)", "der -e", "ein -er", "-er"], ["Mask. Genitiv (des)", "des -en", "eines -en", "-en"],
                  ["Mask. Dativ (dem)", "dem -en", "einem -en", "-em"], ["Mask. Akkusativ (den)", "den -en", "einen -en", "-en"],
                  ["Fem. Nominativ (die)", "die -e", "eine -e", "-e"], ["Fem. Genitiv (der)", "der -en", "einer -en", "-er"],
                  ["Fem. Dativ (der)", "der -en", "einer -en", "-er"], ["Fem. Akkusativ (die)", "die -e", "eine -e", "-e"],
                  ["Neut. Nominativ (das)", "das -e", "ein -es", "-es"], ["Neut. Genitiv (des)", "des -en", "eines -en", "-en"],
                  ["Neut. Dativ (dem)", "dem -en", "einem -en", "-em"], ["Neut. Akkusativ (das)", "das -e", "ein -es", "-es"],
                  ["Pl. Nominativ (die)", "die -en", "meine -en", "-e"], ["Pl. Genitiv (der)", "der -en", "meiner -en", "-er"],
                  ["Pl. Dativ (den)", "den -en", "meinen -en", "-en"], ["Pl. Akkusativ (die)", "die -en", "meine -en", "-e"]])
)

_T = [("Der gut__ Mann arbeitet im Büro.", ["-er", "-e", "-en"], "B"), ("Die schön__ Frau wohnt in Berlin.", ["-e", "-er", "-en"], "A"),
      ("Das klein__ Kind schläft jetzt.", ["-es", "-e", "-en"], "B"), ("Ich sehe den alt__ Mann im Park.", ["-er", "-en", "-e"], "B"),
      ("Ich helfe dem gut__ Freund heute.", ["-em", "-en", "-er"], "B"), ("Das Dach der neu__ Schule ist groß.", ["-e", "-er", "-en"], "C"),
      ("Die jung__ Leute lernen Deutsch.", ["-e", "-er", "-en"], "C"), ("Ich spreche mit den gut__ Kindern.", ["-e", "-en", "-er"], "B"),
      ("Das groß__ Haus steht am See.", ["-e", "-es", "-en"], "A"), ("Die alt__ Bücher liegen auf dem Tisch.", ["-e", "-er", "-en"], "C"),
      ("Ein gut__ Mann hilft mir.", ["-e", "-er", "-en"], "B"), ("Eine schön__ Stadt gefällt mir.", ["-e", "-er", "-en"], "A"),
      ("Ein klein__ Kind spielt draußen.", ["-e", "-es", "-en"], "B"), ("Das Auto eines alt__ Mannes ist blau.", ["-er", "-en", "-em"], "B"),
      ("Ich danke einem gut__ Freund.", ["-en", "-em", "-er"], "A"), ("Ich kenne einen jung__ Lehrer.", ["-e", "-er", "-en"], "C"),
      ("Ich spreche mit meiner gut__ Mutter.", ["-e", "-er", "-en"], "C"), ("Mein neu__ Auto ist schnell.", ["-e", "-es", "-en"], "B"),
      ("Meine alt__ Tasche ist kaputt.", ["-e", "-er", "-en"], "A"), ("Ich besuche meinen klein__ Bruder.", ["-e", "-en", "-er"], "B"),
      ("Gut__ Mann arbeitet viel.", ["-er", "-e", "-en"], "A"), ("Schön__ Frau kommt heute.", ["-e", "-er", "-en"], "A"),
      ("Klein__ Kind lacht laut.", ["-e", "-es", "-en"], "B"), ("Das ist das Haus gut__ Mannes.", ["-er", "-en", "-em"], "B"),
      ("Ich helfe gut__ Freund.", ["-em", "-en", "-er"], "A"), ("Alt__ Haus steht im Dorf.", ["-e", "-es", "-en"], "B"),
      ("Jung__ Leute reisen viel.", ["-e", "-er", "-en"], "A"), ("Ich spreche mit gut__ Kindern.", ["-e", "-en", "-er"], "B"),
      ("Neu__ Bücher sind interessant.", ["-e", "-er", "-en"], "A"), ("Groß__ Stadt liegt am Fluss.", ["-e", "-er", "-en"], "A")]
TEST = [mc(q.replace("__", "___"), o, a, "Jadval (S. 100) bo'yicha." + (
    " (Jadvalning „Artikelsiz“ ustuni; birlikdagi sanaladigan ot odatda gapda artikl bilan keladi: ein guter Mann.)"
    if i >= 20 and not any(w in q for w in ("Leute", "Kindern", "Bücher")) else "")) for i, (q, o, a) in enumerate(_T)]

TEXT_1 = ("Ich heiße Herr Julian und ich kaufe oft im Supermarkt für meine Familie ein. Heute gehe ich nach der Arbeit einkaufen. Ich nehme meinen "
          "Einkaufswagen und gehe zuerst zu Brot und Milch. Ich kaufe frisches Brot, Milch, Eier und Käse. Für meine Kinder kaufe ich Äpfel, "
          "Bananen und Saft. Meine Frau möchte Reis, Nudeln und Gemüse. Manchmal gibt es Rabatte auf Obst und Gemüse, und heute gibt es 10% Rabatt "
          "auf Äpfel, das ist gut für meine Familie.\n\nIm Supermarkt ist es sauber und groß. Die Preise sind gut, besonders die Angebote an der "
          "Kasse. Ich bezahle mit Karte und bekomme eine Einkaufsquittung. Danach gehe ich nach Hause. Meine Kinder freuen sich über die Früchte "
          "und meine Frau kocht ein gesundes Abendessen. Ich mag den Einkauf im Supermarkt, weil er schnell und einfach ist und es immer viele "
          "gute Angebote gibt.")
TEXT_2 = ("Max und Alex sind gute Freunde und wohnen zusammen in einer Wohnung. Am Samstag gehen sie zusammen in den Supermarkt. Max kauft Brot, "
          "Butter und Käse, und Alex kauft Nudeln, Tomaten und Fleisch. Sie schauen auch auf Sonderangebote, zum Beispiel gibt es 2 zum Preis "
          "von 1 auf Cola. Sie kaufen außerdem Wasser, Kekse und Snacks, weil sie heute Abend zusammen kochen wollen.\n\nDer Supermarkt ist groß "
          "und modern, aber es sind viele Menschen da. Die Freunde sprechen und lachen viel. Sie achten auf die Preise und vergleichen Angebote. "
          "Am Ende bezahlen sie zusammen an der Kasse. Zu Hause kochen sie leckeres Abendessen und genießen es. Der Einkauf macht Spaß, besonders "
          "wenn es gute Rabatte und frische Lebensmittel gibt.")
LESEN = [
    tf("Herr Julian kauft oft im Supermarkt für seine Familie ein.", True, passage=1),
    tf("Heute kauft er nur Süßigkeiten für sich selbst.", False, passage=1),
    tf("Er kauft Brot, Milch, Eier und Käse.", True, passage=1),
    tf("Seine Kinder bekommen Äpfel, Bananen und Saft.", True, passage=1),
    tf("Im Supermarkt gibt es keine Rabatte auf Obst und Gemüse.", False, "„… heute gibt es 10% Rabatt auf Äpfel.“", passage=1),
    tf("Herr Julian bezahlt an der Kasse mit Karte.", True, passage=1),
    tf("Max und Alex sind gute Freunde und wohnen zusammen.", True, passage=2),
    tf("Sie gehen am Samstag alleine spazieren, nicht einkaufen.", False, passage=2),
    tf("Max kauft Brot, Butter und Käse, Alex kauft Nudeln, Tomaten und Fleisch.", True, passage=2),
    tf("Sie schauen auf Sonderangebote, z. B. 2 zum Preis von 1 auf Cola.", True, passage=2),
    tf("Der Supermarkt ist leer und es sind keine anderen Kunden da.", False, "„… es sind viele Menschen da.“", passage=2),
    tf("Am Ende bezahlen sie zusammen an der Kasse und kochen zu Hause.", True, passage=2),
]

TRANSCRIPT = (
    "Text 1 — Wir sind im Supermarkt: Heute sind wir mit unserem Deutschlehrer in den Supermarkt gegangen. Der Lehrer hat uns mitgenommen, um neue "
    "Wörter zu lernen. Unsere Aufgabe war, 20 neue Wörter zu schreiben. Wir mussten die Namen von Produkten auf Deutsch und auf Usbekisch "
    "aufschreiben, die wir noch nicht kannten. Im Supermarkt haben wir viele neue Sachen gesehen und viel gelernt. Am Ende hat unser Lehrer jedem "
    "von uns ein kleines Geschenk gekauft. Wir haben uns sehr gefreut. Heute haben wir 20 neue Wörter gelernt und Geschenke bekommen. Vielen Dank "
    "an unseren Lehrer!\n\n"
    "O'zbekcha tarjima — Biz supermarketdamiz: Bugun biz nemis tili ustozimiz bilan supermarketga bordik. Ustoz bizni yangi so'zlarni o'rganish "
    "uchun olib bordi. Bizning vazifamiz 20 ta yangi so'zni yozish edi. Biz hali bilmagan mahsulotlarning nomlarini nemischa va o'zbekcha qilib "
    "yozishimiz kerak edi. Supermarketda biz juda ko'p yangi narsalarni ko'rdik va ko'p bilim oldik. Oxirida ustozimiz har birimizga kichkina "
    "sovg'a olib berdi. Biz juda xursand bo'ldik. Bugun biz 20 ta yangi so'z o'rgandik va sovg'alarga ega bo'ldik. Ustozimizga katta rahmat!\n\n"
    "Text 2 — Wir sind im Markt: Ich heiße Zayd und ich bin 12 Jahre alt. Heute sind wir als Familie in den Markt gegangen. Wir wollten Kleidung "
    "für die Schule kaufen. Meine Mutter hat schöne Kleidung für uns Kinder gekauft. Für meine Mutter haben wir auch ein Kopftuch gekauft. Wir "
    "waren alle glücklich. Aber mein Vater hat für sich selbst nichts gekauft. Er hat nur auf uns geachtet. Er hat immer gesagt: „Das ist nicht "
    "wichtig.“ Als wir nach Hause gekommen sind, habe ich gesehen, dass mein Vater keine neuen Kleider hat. Ich war traurig und habe geweint. Ich "
    "habe gesagt: „Papa, du hast für alle Kleidung gekauft, aber für dich nichts.“ Mein Vater hat mich umarmt und gelächelt. Er hat gesagt, dass "
    "unsere Freude für ihn das Wichtigste ist. Ich liebe meinen Vater sehr.\n\n"
    "O'zbekcha tarjima — Biz bozordamiz: Mening ismim Zayd, men 12 yoshdaman. Bugun biz oilamiz bilan bozorga bordik. Biz maktab uchun kiyim "
    "sotib olmoqchi edik. Onam biz bolalar uchun chiroyli kiyimlar oldi. Onam uchun ham bosh kiyim sotib oldik. Biz hammamiz xursand edik. Lekin "
    "dadam o'zi uchun hech narsa olmadi. U faqat bizni o'yladi. U doim: «Bu muhim emas», derdi. Uyga qaytganimizda dadamning yangi kiyimi "
    "yo'qligini ko'rdim. Men xafa bo'ldim va yig'ladim. Men dedim: «Dada, siz hammaga kiyim oldingiz, lekin o'zingizga hech narsa olmadingiz». "
    "Dadam meni quchoqladi va kulib dedi: bizning quvonchimiz u uchun eng muhim narsa ekan. Men dadamni juda yaxshi ko'raman."
)
TRANSCRIPT_1, _rest = TRANSCRIPT.split("\n\nText 2 — ")
TRANSCRIPT_2 = "Text 2 — " + _rest
HOEREN = [
    mc("Text 1: Wohin sind die Schüler heute gegangen?", ["In die Schule", "In den Supermarkt", "In den Park"], "B"),
    mc("Text 1: Mit wem sind die Schüler in den Supermarkt gegangen?", ["Mit ihren Eltern", "Mit ihrem Freund", "Mit ihrem Deutschlehrer"], "C"),
    mc("Text 1: Was war die Aufgabe der Schüler?", ["10 neue Wörter schreiben", "20 neue Wörter schreiben", "30 neue Wörter schreiben"], "B"),
    mc("Text 1: Was mussten die Schüler aufschreiben?", ["Nur deutsche Wörter", "Nur usbekische Wörter", "Deutsche und usbekische Wörter"], "C"),
    mc("Text 1: Was hat der Lehrer am Ende gemacht?", ["Er hat Hausaufgaben gegeben.", "Er hat einen Test geschrieben.", "Er hat Geschenke gekauft."], "C"),
    mc("Text 1: Wie fühlen sich die Schüler am Ende?", ["Sie sind müde.", "Sie sind traurig.", "Sie freuen sich."], "C"),
    mc("Text 2: Wie alt ist Zayd?", ["10 Jahre alt", "12 Jahre alt", "14 Jahre alt"], "B"),
    mc("Text 2: Warum ist die Familie in den Markt gegangen?", ["Um Essen zu kaufen", "Um Kleidung für die Schule zu kaufen", "Um Geschenke zu kaufen"], "B"),
    mc("Text 2: Für wen hat die Mutter Kleidung gekauft?", ["Nur für sich selbst", "Für die Kinder und für sich selbst", "Nur für die Kinder"], "C"),
    mc("Text 2: Was hat die Familie für die Mutter gekauft?", ["Eine Jacke", "Ein Kopftuch", "Schuhe"], "B"),
    mc("Text 2: Was hat der Vater für sich selbst gekauft?", ["Kleidung", "Schuhe", "Nichts"], "C"),
    mc("Text 2: Wie reagiert Zayd zu Hause?", ["Er lacht.", "Er ist wütend.", "Er weint."], "C"),
]

_W = [("der", "Supermarkt", "supermarket"), ("der", "Laden", "do'kon"), ("der", "Verkäufer", "sotuvchi"), ("die", "Verkäuferin", "sotuvchi ayol"),
      ("der", "Kunde", "mijoz"), ("die", "Kundin", "mijoz ayol"), ("einkaufen", "xarid qilmoq"), ("der", "Einkaufswagen", "savat"),
      ("die", "Tasche", "sumka"), ("das", "Brot", "non"), ("das", "Weißbrot", "oq non"), ("das", "Vollkornbrot", "to'liq donli non"), ("die", "Milch", "sut"),
      ("die", "Butter", "sariyog'"), ("der", "Käse", "pishloq"), ("die", "Eier", "tuxum"), ("das", "Obst", "meva"), ("der", "Apfel", "olma"),
      ("die", "Banane", "banan"), ("die", "Tomate", "pomidor"), ("die", "Gurke", "bodring"), ("das", "Gemüse", "sabzavot"), ("der", "Reis", "guruch"),
      ("die", "Nudeln", "makaron"), ("das", "Fleisch", "go'sht"), ("das", "Wasser", "suv"), ("der", "Saft", "sharbat"), ("die", "Cola", "kola"),
      ("der", "Snack", "gazak / atirli taom"), ("das", "Angebot", "aksiya, chegirma"), ("die", "Kasse", "kassa"), ("bezahlen", "to'lash"), ("die", "Karte", "karta (to'lov)"),
      ("der", "Preis", "narx"), ("das", "Produkt", "mahsulot"), ("frisch", "yangi"), ("alt", "eski"), ("groß", "katta"), ("klein", "kichik"), ("blau", "ko'k"),
      ("schwarz", "qora"), ("rot", "qizil"), ("die", "Jacke", "kurtka"), ("die", "Hose", "shim"), ("das", "T-Shirt", "futbolka"), ("die", "Schuhe", "poyabzal"),
      ("anprobieren", "kiyib ko'rmoq"), ("die", "Umkleidekabine", "kiyinish xonasi"), ("gesund", "sog'lom"), ("lecker", "mazali")]
WORDS = words(_W, "Im Supermarkt")


WORTSCHATZ_SETS = [*vocab_match_sets(WORDS, per_set=4), article_set(WORDS), forward_vocab_set(WORDS)]

UEBUNGEN_SETS = [
    exercise("Adjektivendungen in den Texten", [
        choice_gap("Herr Julian kauft ___ Brot, Milch, Eier und Käse.", ["frisches", "frische", "frischen"], "frisches",
                   explanation="Lesen: „Ich kaufe frisches Brot …“ — artikelsiz, das Brot, Akkusativ: -es."),
        choice_gap("Seine Frau kocht ein ___ Abendessen.", ["gesundes", "gesunde", "gesunden"], "gesundes", explanation="ein + das Abendessen (Akkusativ): -es."),
        choice_gap("Max und Alex sind ___ Freunde.", ["gute", "guten", "guter"], "gute", explanation="artikelsiz, Plural Nominativ: -e."),
        choice_gap("Zu Hause kochen sie ___ Abendessen.", ["leckeres", "leckere", "leckeren"], "leckeres", explanation="artikelsiz, das Abendessen (Akkusativ): -es."),
        choice_gap("Der Lehrer hat jedem Schüler ein ___ Geschenk gekauft.", ["kleines", "kleine", "kleinen"], "kleines", explanation="Hören: „ein kleines Geschenk“."),
        choice_gap("Die Mutter hat ___ Kleidung für die Kinder gekauft.", ["schöne", "schönen", "schöner"], "schöne", explanation="artikelsiz, die Kleidung (Akkusativ): -e."),
        choice_gap("Der Vater hat keine ___ Kleider.", ["neuen", "neue", "neuer"], "neuen", explanation="keine + Plural: -en (meine guten Leute kabi)."),
    ], "O'qish va tinglash matnlaridagi sifatlarning to'g'ri shaklini tanlang.", source="vizu"),
    reverse_vocab_set(WORDS),
]


def items() -> list[dict]:
    return [
        base(L, "kompetenz", 1, "Einführung: Modul 10", source="vizu", page=98, competency="EINFUEHRUNG", html=EINFUEHRUNG_HTML),
        base(L, "frage", 1, "Frage: Wie kaufen die Deutschen ein?", page=99,
             prompt="Wie kaufen die Deutschen ein? (Supermarkt, Qualität, Angebote, regional & Bio, Einkaufsliste) Und wie kaufen Sie ein?",
             min_duration=10, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Adjektivdeklination", page="100-101",
             rules=[{"title": "Adjektivdeklination", "html": _ADJ}],
             exercises=[exercise("Grammatik-Aufgaben: Adjektivendungen (30)", TEST, "Wählen Sie die richtige Endung.")]),
        base(L, "lesen", 1, "Lesen: Einkaufen im Supermarkt", page=102,
             instruction="Lesen Sie die Texte und entscheiden Sie: Richtig oder Falsch?",
             passages=[{"title": "Mein Einkauf im Supermarkt (Familie)", "text": TEXT_1}, {"title": "Mein Einkauf für Wochenende", "text": TEXT_2}],
             questions=LESEN, max_score=len(LESEN)),
        # one task per audio file (A1-10.1.mp3, A1-10.2.mp3): a task holds one audio
        base(L, "hoeren", 1, "Hören: Wir sind im Supermarkt (Text 1)", page="103-104", audio_file="A1-10.1.mp3",
             instruction="Hören Sie Text 1 und wählen Sie die richtige Antwort (A, B, C).",
             transcript=TRANSCRIPT_1, questions=HOEREN[:6], max_score=6),
        base(L, "hoeren", 2, "Hören: Wir sind im Markt (Text 2)", page="103-104", audio_file="A1-10.2.mp3",
             instruction="Hören Sie Text 2 und wählen Sie die richtige Antwort (A, B, C).",
             transcript=TRANSCRIPT_2, questions=HOEREN[6:], max_score=6),
        base(L, "schreiben", 1, "Schreiben: Ich gehe einkaufen", page=105,
             prompt="Schreiben Sie einen Text über einen Einkauf:\n1. Matnni boshlash: Ich möchte einkaufen gehen. Heute gehe ich in den Supermarkt.\n"
                    "2. Mit wem? Ich gehe mit meinem Freund einkaufen.\n3. Was möchten Sie kaufen? Ich kaufe Brot, Milch und Obst.\n"
                    "4. Einkauf: Ich gehe zum Obststand und kaufe Äpfel.\n5. Gefühle: Ich freue mich, weil …\n6. Schluss / Dank: Danke an … für die Hilfe.",
             task_type="description", min_words=40, max_words=120, time_limit=20,
             support_phrases=["Heute gehe ich in den Supermarkt.", "Ich gehe mit … einkaufen.", "Ich kaufe …", "Ich freue mich, weil …"]),
        base(L, "sprechen", 1, "Dialog: Im Geschäft", page=106, topic="Einkaufen",
             prompt="Spielen Sie den Kunden. Sprechen Sie einen der Dialoge (Bäckerei / Lebensmittel oder Kleidung).",
             questions=["Kunde: Guten Tag! Ich möchte Brot und Milch kaufen. — Verkäufer: Welches Brot möchten Sie? Weißbrot oder Vollkornbrot?",
                        "Kunde: Ich nehme das Vollkornbrot, bitte. — Verkäufer: Möchten Sie noch Milch?",
                        "Kunde: Ja, zwei Liter Milch, bitte. — Verkäufer: Möchten Sie auch Obst oder Gemüse?",
                        "Kunde: Ja, ich nehme Äpfel und Tomaten. — Verkäufer: Das macht zusammen 15 Euro, bitte.",
                        "Kunde: Guten Tag! Ich möchte eine neue Jacke kaufen. — Verkäufer: Welche Größe haben Sie?",
                        "Kunde: Ich habe Größe M. — Verkäufer: Möchten Sie eine blaue oder schwarze Jacke?",
                        "Kunde: Ich nehme die blaue Jacke, bitte. — Verkäufer: Möchten Sie die Kleidung anprobieren?",
                        "Kunde: Ja, gern. Wo ist die Umkleidekabine? — Verkäufer: Das macht zusammen 75 Euro, bitte."],
             response_type="dialog", min_duration=30, max_duration=150,
             speech_goal="Im Geschäft höflich Waren verlangen, Größe/Farbe nennen und bezahlen.",
             keywords=["Ich möchte", "Ich nehme", "bitte", "Das macht zusammen"]),
        base(L, "wortschatz", 1, "Wortschatz Modul 10: Im Supermarkt", page=107, words=WORDS, exercises=WORTSCHATZ_SETS, auto_practice=False),
        base(L, "uebungen", 1, "Übungen Modul 10", exercises=UEBUNGEN_SETS, source="vizu"),
        base(L, "yakuniy", 1, "Abschlusstest: Modul 10", source="vizu",
             instruction="Sifatlarning turlanishi va xarid so'zlari bo'yicha yakuniy test.",
             questions=[
                 choice_gap("Das ist ein ___ Apfel.", ["roter", "rote", "rotes"], "roter"),
                 choice_gap("Ich kaufe eine ___ Jacke.", ["blaue", "blauen", "blauer"], "blaue"),
                 choice_gap("Der ___ Käse ist lecker.", ["frische", "frischer", "frischen"], "frische"),
                 choice_gap("Ich sehe den ___ Supermarkt.", ["großen", "große", "großer"], "großen"),
                 choice_gap("Wir kaufen ___ Brot. (artikelsiz)", ["frisches", "frische", "frischen"], "frisches"),
                 mc("„mit dem neu__ Auto“", ["-en", "-e", "-es"], "A"),
                 mc("„die Kasse“ — o'zbekchasi qaysi?", ["kassa", "narx", "sumka"], "A"),
                 mc("„anprobieren“ — o'zbekchasi qaysi?", ["kiyib ko'rmoq", "to'lamoq", "xarid qilmoq"], "A"),
                 tf("„das Angebot“ bedeutet „aksiya, chegirma“.", True),
                 match("Was passt zusammen?", ["der Preis", "die Hose", "die Schuhe", "gesund"], ["narx", "shim", "poyabzal", "sog'lom", "sumka"],
                       {"1": "A", "2": "B", "3": "C", "4": "D"}),
             ]),
        base(L, "kompetenz", 2, "Zusammenfassung: Modul 10", source="vizu", competency="ZUSAMMENFASSUNG", html=ZUSAMMENFASSUNG_HTML),
    ]
