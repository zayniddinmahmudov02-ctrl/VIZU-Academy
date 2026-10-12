"""Modul 4 — Mein Zimmer ist gemütlich — Grammatik: Possessivpronomen (book pp. 38-46).

Hören (p.43): the book has the questions but neither transcript nor a valid
answer sheet, so only question 1 has a key (the name, given by question 2);
an admin sets the other answers after listening to the audio. The Wortschatz
page announces 40 words but its section B (Möbel) is missing in the book —
the 16 printed words and the new words of the Schreiben page are imported."""

from . import base, choice_gap, exercise, html_table, match, mc, mc_pending, tf, words

L = 4

_POSS = (
    "<h3>1. Possessivpronomen — Grundformen</h3>"
    + html_table(["Person", "Possessivpronomen", "Beispielsatz"],
                 [["ich", "mein", "Das ist mein Buch."], ["du", "dein", "Ist das dein Zimmer?"], ["er", "sein", "Das ist sein Auto."],
                  ["sie (fem.)", "ihr", "Das ist ihr Fahrrad."], ["es", "sein", "Das ist sein Spielzeug."], ["wir", "unser", "Das ist unser Haus."],
                  ["ihr", "euer", "Das ist euer Hund."], ["sie (pl.)", "ihr", "Das ist ihr Garten."], ["Sie (formell)", "Ihr", "Ist das Ihr Auto?"]])
    + "<h3>2. Deklination (nach Kasus und Genus) — am Beispiel „mein“</h3>"
    + html_table(["Kasus", "Maskulin (der)", "Feminin (die)", "Neutrum (das)", "Plural (die)"],
                 [["Nominativ (Wer? Was?)", "mein", "meine", "mein", "meine"], ["Genitiv (Wessen?)", "meines", "meiner", "meines", "meiner"],
                  ["Dativ (Wem?)", "meinem", "meiner", "meinem", "meinen"], ["Akkusativ (Wen? Was?)", "meinen", "meine", "mein", "meine"]])
    + "<p><strong>Merke:</strong> Possessivpronomen zeigen, wem eine Person oder Sache gehört. Sie stehen immer vor dem Nomen. "
      "Die Endungen (Suffixe) hängen vom Kasus und Genus ab.</p>"
)

_Q = "Wähle die richtige Form des Possessivpronomens."
TEST = [
    mc("Das ist ___ Buch.", ["mein", "meine", "meines", "meinen"], "A"),
    mc("Ist das ___ Handy?", ["dein", "deine", "deines", "deinen"], "A"),
    mc("Hier ist ___ Schlüssel.", ["sein", "seine", "seines", "seinen"], "A"),
    mc("Das ist ___ Fahrrad.", ["ihr", "ihre", "ihres", "ihren"], "A"),
    mc("Ich sehe ___ Bruder.", ["mein", "meine", "meines", "meinen"], "D", "Akkusativ maskulin: meinen."),
    mc("Wir besuchen ___ Oma.", ["unser", "unsere", "unseres", "unseren"], "B"),
    mc("Das ist ___ Haus.", ["euer", "eure", "eures", "euren"], "A"),
    mc("Er zeigt ___ Auto.", ["sein", "seine", "seines", "seinen"], "A"),
    mc("Ich putze ___ Zimmer.", ["mein", "meine", "meines", "meinen"], "A"),
    mc("Sie liest ___ Buch.", ["ihr", "ihre", "ihres", "ihren"], "A"),
    mc("Das ist ___ Hund.", ["unser", "unsere", "unseres", "unseren"], "A"),
    mc("Ist das ___ Stift?", ["dein", "deine", "deines", "deinen"], "A"),
    mc("Das sind ___ Eltern.", ["sein", "seine", "seines", "seinen"], "B"),
    mc("Ich nehme ___ Tasche.", ["mein", "meine", "meines", "meinen"], "B"),
    mc("Wir machen ___ Hausaufgaben.", ["unser", "unsere", "unseres", "unseren"], "B"),
    mc("Das ist ___ Idee.", ["euer", "eure", "eures", "euren"], "B"),
    mc("Er trägt ___ Jacke.", ["sein", "seine", "seines", "seinen"], "B"),
    mc("Sie öffnet ___ Tür.", ["ihr", "ihre", "ihres", "ihren"], "B"),
    mc("Ich habe ___ Ball.", ["mein", "meine", "meines", "meinen"], "D", "Akkusativ maskulin: meinen."),
    mc("Das sind ___ Freunde.", ["unser", "unsere", "unseres", "unseren"], "B"),
]

TEXT_NIKO = ("Hallo! Ich heiße Niko. Das ist mein Zimmer. Mein Zimmer ist klein, aber gemütlich. In meinem Zimmer gibt es ein Bett, "
             "einen Tisch und einen Stuhl. Auf meinem Tisch liegen meine Bücher und mein Heft. Neben meinem Bett steht meine Lampe. "
             "Mein Fenster ist groß. Ich lerne und lese gern in meinem Zimmer. Mein Zimmer gefällt mir sehr.")
TEXT_MARIA = ("Maria ist meine Schwester. Das ist ihr Zimmer. Ihr Zimmer ist schön und sauber. In ihrem Zimmer gibt es ein Bett, einen Tisch "
              "und einen Schrank. Auf ihrem Tisch liegen ihre Bücher und ihr Handy. An ihrer Wand hängen Fotos. Maria liest gern in ihrem "
              "Zimmer. Ihr Zimmer gefällt ihr sehr.")
TEXT_ALBERT = ("Albert ist mein Bruder. Das ist sein Zimmer. Sein Zimmer ist groß und modern. In seinem Zimmer gibt es ein Bett, einen Tisch "
               "und einen Computer. Auf seinem Tisch stehen sein Computer und seine Bücher. Sein Fenster ist groß. Albert macht seine "
               "Hausaufgaben in seinem Zimmer. Sein Zimmer gefällt ihm sehr.")
LESEN = [
    mc("Wie ist Nikos Zimmer?", ["Groß und modern", "Klein, aber gemütlich", "Schön und sauber"], "B", passage=1),
    mc("Was liegt auf Nikos Tisch?", ["Seine Bücher und sein Heft", "Sein Computer", "Sein Handy"], "A", passage=1),
    tf("Neben Nikos Bett steht seine Lampe.", True, passage=1),
    mc("Wer ist Maria?", ["Nikos Mutter", "Nikos Schwester", "Nikos Freundin"], "B", passage=2),
    mc("Was gibt es in Marias Zimmer?", ["Ein Bett, einen Tisch und einen Schrank", "Ein Bett und einen Computer", "Nur einen Tisch"], "A", passage=2),
    tf("An Marias Wand hängen Fotos.", True, passage=2),
    mc("Wie ist Alberts Zimmer?", ["Klein und dunkel", "Groß und modern", "Alt"], "B", passage=3),
    mc("Was steht auf Alberts Tisch?", ["Seine Lampe", "Sein Computer und seine Bücher", "Seine Fotos"], "B", passage=3),
    tf("Albert macht seine Hausaufgaben in der Küche.", False, "„Albert macht seine Hausaufgaben in seinem Zimmer.“", passage=3),
    mc("Wer liest gern in ihrem Zimmer?", ["Maria", "Albert", "Niemand"], "A", passage=2),
]

HOEREN = [
    mc("Wie heißt die Person?", ["Max", "Alex", "Tom"], "B", "Frage 2: „Wie alt ist Alex?“"),
    mc_pending("Wie alt ist Alex?", ["19 Jahre alt", "20 Jahre alt", "21 Jahre alt"]),
    mc_pending("Wie ist sein Zimmer?", ["Schön, sauber und hell", "Klein und dunkel", "Alt und schmutzig"]),
    mc_pending("Was steht auf dem Tisch?", ["Ein Fernseher", "Ein Computer", "Eine Lampe"]),
    mc_pending("Was hat Alex für seine Kleidung?", ["Einen Schrank", "Ein Regal", "Einen Koffer"]),
    mc_pending("Was gibt es in seinem Zimmer?", ["Ein großes Fenster", "Zwei Türen", "Einen Balkon"]),
    mc_pending("Was hängt an der Wand?", ["Uhren", "Bilder", "Spiegel"]),
    mc_pending("Was macht Alex oft in seinem Zimmer?", ["Er schläft.", "Er lernt.", "Er kocht."]),
    mc_pending("Was macht Alex manchmal?", ["Bücher lesen oder Musik hören", "Fußball spielen", "Einkaufen gehen"]),
    mc_pending("Warum mag Alex sein Zimmer?", ["Es ist sehr groß.", "Es ist sein Lieblingsplatz zu Hause.", "Es hat einen Fernseher."]),
]

WORDS = (
    words([("das", "Schlafzimmer", "yotoqxona"), ("das", "Wohnzimmer", "mehmonxona"), ("die", "Küche", "oshxona"), ("das", "Badezimmer", "hammom"),
           ("das", "Kinderzimmer", "bolalar xonasi"), ("das", "Arbeitszimmer", "ish xonasi"), ("der", "Flur", "yo'lak"),
           ("das", "Esszimmer", "ovqatlanish xonasi"), ("der", "Balkon", "balkon"), ("der", "Garten", "bog'")], "Zimmer — xonalar")
    + words([("schön", "chiroyli"), ("sauber", "toza"), ("groß", "katta"), ("klein", "kichik"), ("hell", "yorug'"), ("gemütlich", "qulay")],
            "Nützliche Wörter — foydali so'zlar")
    + words([("modern", "zamonaviy"), ("der", "Kleiderschrank", "kiyim shkafi"), ("das", "Regal", "javon"), ("der", "Schreibtisch", "yozuv stoli"),
             ("der", "Rucksack", "ryukzak"), ("der", "Kalender", "taqvim"), ("die", "Trophäe", "sovrin (kubok)"), ("ruhig", "tinch")],
            "Schreiben: yangi so'zlar")
)


def items() -> list[dict]:
    return [
        base(L, "frage", 1, "Frage: Wie ist die Wohnung von Deutschen?", page=39,
             prompt="Wie ist die Wohnung von Deutschen? Was wissen Sie über moderne Wohnungen in Deutschland "
                    "(Ausstattung, Größe und Stil, Komfort und Gemütlichkeit)?",
             min_duration=10, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Possessivpronomen", page="40-41",
             rules=[{"title": "Possessivpronomen", "html": _POSS}],
             exercises=[exercise("Test: Possessivpronomen (20)", TEST, _Q + " Tipp: Achte auf den Besitzer und den Kasus!")]),
        base(L, "lesen", 1, "Lesen: Mein Zimmer", page=42, source="vizu",
             instruction="Lesen Sie die Texte und beantworten Sie die Fragen.",
             metadata={"book_page": 42, "note": "Matnlar kitobdan; savollar VIZU tomonidan matn asosida tuzilgan."},
             passages=[{"title": "Mein Zimmer (Niko)", "text": TEXT_NIKO}, {"title": "Das Zimmer von Maria", "text": TEXT_MARIA},
                       {"title": "Das Zimmer von Albert", "text": TEXT_ALBERT}],
             questions=LESEN, max_score=len(LESEN)),
        base(L, "hoeren", 1, "Hören: Alex und sein Zimmer", page=43, audio_file="A1-4.mp3", key_pending=True,
             instruction="Höre den Text und kreuze die richtige Antwort an.", questions=HOEREN),
        base(L, "schreiben", 1, "Schreiben: Mein Zimmer", page=44,
             prompt="Beschreiben Sie Ihr Zimmer (O'z xonangizni tasvirlang!). Schreiben Sie einfache Sätze:\n"
                    "1. Kirish: Ich heiße … Das ist mein Zimmer.\n2. Mein Zimmer ist … (groß / klein / schön / gemütlich / modern).\n"
                    "3. In meinem Zimmer gibt es … (ein Bett, einen Tisch, einen Schrank …).\n"
                    "4. Mein Bett steht … Auf meinem Tisch liegen … Neben … steht … Über … hängt …\n"
                    "5. Die Wände sind … An der Wand hängen … Mein Zimmer ist hell / bunt / modern.\n"
                    "6. Ich lerne / lese / höre Musik / spiele … in meinem Zimmer.\n7. Ich mag mein Zimmer sehr, weil …\n"
                    "8. Das ist mein Zimmer. Ich bin gern in meinem Zimmer.",
             task_type="description", min_words=40, max_words=120, time_limit=20,
             support_phrases=["In meinem Zimmer gibt es …", "Auf meinem Tisch liegen …", "Neben meinem Bett steht …", "An der Wand hängen …",
                              "Ich mag mein Zimmer sehr, weil …"]),
        base(L, "sprechen", 1, "Sprechen: Mein Zimmer", page=45, topic="Mein Zimmer",
             prompt="Beantworten Sie die Fragen. Sprechen Sie in vollständigen Sätzen.",
             questions=["Wie ist dein Zimmer?", "Was gibt es in deinem Zimmer?", "Wo stehen die Möbel in deinem Zimmer?",
                        "Was hast du in deinem Zimmer?", "Welche Farben hat dein Zimmer?", "Warum magst du dein Zimmer?"],
             response_type="monolog", min_duration=30, max_duration=120,
             speech_goal="Das eigene Zimmer beschreiben: Größe, Möbel und ihr Ort (neben / auf / an), Farben und einen Grund (weil …).",
             keywords=["mein", "in meinem Zimmer", "es gibt", "neben", "auf", "weil"]),
        base(L, "wortschatz", 1, "Wortschatz Modul 4: Zimmer & Möbel", page="44, 46", words=WORDS),
        base(L, "yakuniy", 1, "Yakuniy Test: Modul 4", source="vizu",
             instruction="Possessivpronomen va xona so'zlari bo'yicha yakuniy test.",
             questions=[
                 choice_gap("Das ist ___ Zimmer. (mening)", ["mein", "meine", "meinen"], "mein"),
                 choice_gap("Ist das ___ Tasche? (sening)", ["dein", "deine", "deinen"], "deine"),
                 choice_gap("Ich sehe ___ Vater. (uning — er)", ["sein", "seine", "seinen"], "seinen"),
                 choice_gap("Das ist ___ Wohnung. (bizning)", ["unser", "unsere", "unseren"], "unsere"),
                 choice_gap("Wo ist ___ Auto? (sizlarning)", ["euer", "eure", "euren"], "euer"),
                 mc("Anna liest ___ Buch.", ["ihr", "ihre", "ihren"], "A"),
                 mc("Ich wohne in ___ Haus. (Dativ)", ["meinem", "meinen", "meine"], "A"),
                 mc("„die Küche“ — o'zbekchasi qaysi?", ["oshxona", "hammom", "yo'lak"], "A"),
                 mc("„gemütlich“ — o'zbekchasi qaysi?", ["qulay", "katta", "toza"], "A"),
                 tf("„das Schlafzimmer“ bedeutet „yotoqxona“.", True),
                 match("Was passt zusammen?", ["der Flur", "das Badezimmer", "der Balkon", "hell"],
                       ["yo'lak", "hammom", "balkon", "yorug'", "kichik"], {"1": "A", "2": "B", "3": "C", "4": "D"}),
             ]),
    ]
