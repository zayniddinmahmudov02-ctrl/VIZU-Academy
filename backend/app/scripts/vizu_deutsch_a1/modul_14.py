"""Modul 14 — Gesundheit und Krankheit — Grammatik: Futur I (book pp. 136-143).

Hören (p.140): the answer sheet contradicts the page (e.g. question 9 asks
about "ihre Freundin" — the sheet says Alex), so the answers are set by an
admin after listening to the audio. The Lesen questions are the book's open
questions with answer options added by VIZU."""

from . import base, choice_gap, exercise, html_table, match, mc, mc_pending, short, text_gap, tf, ul, words

L = 14

_FUTUR = (
    "<p><strong>Futur I (kelasi zamon)</strong> — kelajakda bo'ladigan ish-harakatni bildiradi.</p>"
    + ul(["<strong>werden</strong> 2-o'rinda turadi.", "Asosiy fe'l oxirida turadi.", "Infinitiv shakli o'zgarmaydi (lernen, gehen, machen)."])
    + html_table(["Shaxs", "werden", "Misol", "Tarjima"],
                 [["ich", "werde", "Ich werde morgen lernen.", "Men ertaga o'qiyman."], ["du", "wirst", "Du wirst Deutsch sprechen.", "Sen nemis tilida gapirasan."],
                  ["er / sie / es", "wird", "Er wird nach Berlin fahren.", "U Berlinga boradi."], ["wir", "werden", "Wir werden zu Hause bleiben.", "Biz uyda qolamiz."],
                  ["ihr", "werdet", "Ihr werdet morgen abfahren.", "Sizlar ertaga jo'nab ketasizlar."],
                  ["sie / Sie", "werden", "Sie werden später kommen.", "Ular keyinroq kelishadi."]])
)

_Q1 = "Setzen Sie die richtige Form von „werden“ ein."
WERDEN = [text_gap(s, a, _Q1) for s, a in [
    ("Ich ___ morgen nach Berlin fahren.", ["werde"]), ("Du ___ heute Abend lernen.", ["wirst"]), ("Er ___ später kommen.", ["wird"]),
    ("Wir ___ am Wochenende Fußball spielen.", ["werden"]), ("Ihr ___ Deutsch sprechen.", ["werdet"]), ("Sie (Plural) ___ das Buch lesen.", ["werden"]),
    ("Maria ___ ihre Oma besuchen.", ["wird"]), ("Thomas und Ali ___ im Sommer reisen.", ["werden"]), ("Du ___ mir helfen.", ["wirst"]),
    ("Ich ___ das nicht machen.", ["werde"])]]
_ORD = [("morgen / ich / lernen / werde", ["Ich werde morgen lernen.", "Morgen werde ich lernen."]),
        ("wird / er / kommen / später", ["Er wird später kommen.", "Später wird er kommen."]),
        ("wir / bleiben / zu Hause / werden", ["Wir werden zu Hause bleiben."]),
        ("du / machen / wirst / was", ["Was wirst du machen?"]),
        ("fahren / sie / nach Deutschland / werden", ["Sie werden nach Deutschland fahren."]),
        ("das Buch / lesen / ich / werde", ["Ich werde das Buch lesen.", "Das Buch werde ich lesen."]),
        ("arbeiten / ihr / morgen / werdet", ["Ihr werdet morgen arbeiten.", "Morgen werdet ihr arbeiten."]),
        ("wird / sie / nicht / kommen", ["Sie wird nicht kommen."]),
        ("am Wochenende / spielen / wir / werden / Tennis", ["Wir werden am Wochenende Tennis spielen.", "Am Wochenende werden wir Tennis spielen."]),
        ("helfen / wirst / du / mir", ["Du wirst mir helfen.", "Wirst du mir helfen?"])]
ORDNUNG = [short(f"Bilden Sie einen Satz im Futur I: {w}", acc, max_length=120, explanation="Kitob kaliti: " + acc[0]) for w, acc in _ORD]

TEXT_1 = ("Ich möchte immer gesund werden und gesund bleiben. Gesundheit ist für mich sehr wichtig, denn ohne Gesundheit ist alles schwer. Jeden Morgen "
          "stehe ich um sieben Uhr auf. Zuerst öffne ich das Fenster und atme frische Luft. Danach mache ich zehn Minuten Sport. Manchmal gehe ich im "
          "Park joggen, manchmal mache ich Yoga oder einfache Übungen zu Hause.\n\nZum Frühstück esse ich Obst, Eier und Brot. Ich trinke Tee oder "
          "Wasser, aber keine süßen Getränke. In der Schule oder bei der Arbeit esse ich auch gesund. Ich nehme oft einen Apfel oder einen Salat mit. "
          "Am Mittag esse ich nicht zu fett und nicht zu viel.\n\nAm Abend gehe ich spazieren oder fahre Fahrrad. Das hilft meinem Körper und meinem "
          "Kopf. Ich schlafe jeden Tag acht Stunden, weil Schlaf sehr wichtig ist. Wenn ich Stress habe, höre ich Musik oder lese ein Buch. Ich denke "
          "positiv und lache viel. So fühle ich mich stark und glücklich. Ich hoffe, ich werde immer gesund bleiben und ein langes Leben haben.")
TEXT_2 = ("Ich bin leider krank und fühle mich nicht gut. Seit einer Woche habe ich Husten, Schnupfen und Fieber. Mein Hals tut weh und ich habe "
          "Kopfschmerzen. Ich bin sehr müde und habe keine Energie. Deshalb bleibe ich zu Hause und gehe nicht zur Schule oder zur Arbeit.\n\nIch liege "
          "viel im Bett und schlafe. Meine Familie hilft mir. Meine Mutter kocht Suppe und mein Bruder kauft Medikamente in der Apotheke. Ich trinke "
          "viel Tee mit Honig und Zitrone. Das hilft meinem Hals. Ich esse wenig, aber ich versuche Obst zu essen.\n\nVor zwei Tagen war ich beim Arzt. "
          "Der Arzt hat mich untersucht und gesagt: „Sie müssen viel schlafen und viel trinken.“ Er hat mir Tabletten gegeben. Ich nehme die "
          "Medikamente jeden Tag. Ich hoffe, ich werde bald wieder gesund. Ich vermisse meine Freunde und möchte wieder nach draußen gehen. "
          "Gesundheit ist wirklich sehr wichtig.")
LESEN = [
    mc("Warum ist Gesundheit für die Person sehr wichtig?", ["Denn ohne Gesundheit ist alles schwer.", "Denn sie möchte viel Geld haben.",
                                                            "Denn sie hat keine Zeit."], "A", passage=1),
    mc("Was macht die Person jeden Morgen nach dem Aufstehen?", ["Sie öffnet das Fenster, atmet frische Luft und macht zehn Minuten Sport.",
                                                                 "Sie sieht fern.", "Sie trinkt süße Getränke."], "A", passage=1),
    mc("Was macht die Person gegen Stress?", ["Sie hört Musik oder liest ein Buch.", "Sie isst Schokolade.", "Sie schläft nicht."], "A",
       "„Wenn ich Stress habe, höre ich Musik oder lese ein Buch.“", passage=1),
    mc("Welche Symptome hat die Person?", ["Husten, Schnupfen, Fieber, Halsschmerzen und Kopfschmerzen", "Nur Bauchschmerzen", "Keine Symptome"], "A", passage=2),
    mc("Was sagt der Arzt?", ["„Sie müssen viel schlafen und viel trinken.“", "„Sie müssen viel Sport machen.“", "„Sie können morgen arbeiten.“"], "A", passage=2),
    mc("Warum möchte die Person schnell gesund werden?", ["Sie vermisst ihre Freunde und möchte wieder nach draußen gehen.",
                                                         "Sie möchte in den Urlaub fahren.", "Sie muss eine Prüfung schreiben."], "A", passage=2),
]

_AA = ["Alisa", "Alex"]
HOEREN = [mc_pending(q, _AA) for q in [
    "Wer macht am Morgen Gymnastik und atmet frische Luft?", "Wer geht drei Mal pro Woche ins Fitnessstudio?", "Wer isst am Abend Salat oder Suppe?",
    "Wer spielt am Wochenende Basketball?", "Wer geht oft zu Fuß zur Arbeit?", "Wer trainiert eine Stunde im Fitnessstudio?",
    "Wer liest vor dem Schlafen ein Buch?", "Wer isst viel Gemüse und Fisch?", "Wer trifft am Nachmittag ihre Freundin im Park?",
    "Wer möchte stark und aktiv bleiben?"]]

_W = [("die", "Gesundheit", "sog'liq"), ("gesund", "sog'lom"), ("krank", "kasal"), ("die", "Krankheit", "kasallik"), ("das", "Fieber", "isitma"),
      ("der", "Husten", "yo'tal"), ("der", "Schnupfen", "shamollash (tumov)"), ("die", "Kopfschmerzen", "bosh og'rig'i"), ("die", "Halsschmerzen", "tomoq og'rig'i"),
      ("müde", "charchagan"), ("der", "Arzt", "shifokor"), ("die", "Ärztin", "ayol shifokor"), ("die", "Praxis", "klinika"), ("das", "Krankenhaus", "shifoxona"),
      ("die", "Tablette", "dori (tabletka)"), ("das", "Medikament", "dori"), ("die", "Apotheke", "dorixona"), ("der", "Patient", "bemor"),
      ("die", "Patientin", "ayol bemor"), ("der", "Termin", "uchrashuv"), ("das", "Rezept", "retsept"), ("untersuchen", "tekshirmoq"), ("helfen", "yordam bermoq"),
      ("bleiben", "qolmoq"), ("schlafen", "uxlamoq"), ("trinken", "ichmoq"), ("essen", "yemoq"), ("spazieren gehen", "sayr qilmoq"),
      ("Sport machen", "sport bilan shug'ullanmoq"), ("das", "Fitnessstudio", "sport zali"), ("stark", "kuchli"), ("schwach", "kuchsiz"),
      ("sich fühlen", "o'zini his qilmoq"), ("die", "Erkältung", "shamollash"), ("zu Hause bleiben", "uyda qolmoq"), ("gesund bleiben", "sog'lom qolmoq"),
      ("das", "Leben", "hayot"), ("lange leben", "uzoq yashamoq"), ("die frische Luft", "toza havo"), ("die", "Suppe", "sho'rva")]
WORDS = words(_W, "Gesundheit und Krankheit")


def items() -> list[dict]:
    return [
        base(L, "frage", 1, "Frage: Wie sind die Gesundheitsprobleme in Deutschland?", page=137,
             prompt="Welche Gesundheitsprobleme haben viele Menschen in Deutschland (Schmerzen, Erkältung, Schlafstörungen, Stress …)? "
                    "Was machen Sie für Ihre Gesundheit?",
             min_duration=10, max_duration=120),
        base(L, "grammatik", 1, "Grammatik: Futur I", page=138,
             rules=[{"title": "Futur I — Kelasi zamon", "html": _FUTUR}],
             exercises=[exercise("Topshiriqlar 1–10: werden einsetzen", WERDEN, _Q1),
                        exercise("Topshiriqlar 11–20: Sätze bilden (Futur I)", ORDNUNG, "Bilden Sie Sätze aus den Wörtern.")]),
        base(L, "lesen", 1, "Lesen: Gesund bleiben — krank sein", page=139,
             instruction="Lesen Sie die Texte und beantworten Sie die Fragen.",
             metadata={"book_page": 139, "note": "Savollar kitobdan; javob variantlari VIZU tomonidan."},
             passages=[{"title": "Ich möchte immer gesund werden.", "text": TEXT_1}, {"title": "Ich bin leider krank.", "text": TEXT_2}],
             questions=LESEN, max_score=len(LESEN)),
        base(L, "hoeren", 1, "Hören: Alisa oder Alex?", page=140, audio_file="A1-14.1.mp3 / A1-14.2.mp3", key_pending=True,
             instruction="Hören Sie den Text und wählen Sie: Alisa oder Alex?", questions=HOEREN),
        base(L, "schreiben", 1, "Schreiben: Ich werde wieder gesund", page=141,
             prompt="Sie sind krank, aber Sie werden wieder gesund. Schreiben Sie einen Text wie im Beispiel (Buch S. 141):\n"
                    "Welche Symptome haben Sie? Was machen Sie jetzt (zu Hause bleiben, schlafen, Tee trinken, Tabletten nehmen …)?\n"
                    "Was werden Sie machen, wenn Sie wieder gesund sind? Benutzen Sie das Futur I (Ich werde …).",
             task_type="description", min_words=50, max_words=150, time_limit=20,
             support_phrases=["Ich habe Fieber und Husten.", "Deshalb bleibe ich zu Hause.", "Ich werde bald wieder gesund sein.", "Danach werde ich …",
                              "Gesundheit ist sehr wichtig für mich."]),
        base(L, "sprechen", 1, "Beim Arzt — Dialog", page=142, topic="Beim Arzt",
             prompt="Sie sind der Patient / die Patientin. Antworten Sie dem Arzt.",
             questions=["Guten Tag. Wie heißen Sie?", "Was fehlt Ihnen?", "Seit wann sind Sie krank?", "Haben Sie auch Kopfschmerzen?",
                        "Haben Sie Halsschmerzen?", "Bitte öffnen Sie den Mund. Atmen Sie tief ein und aus.",
                        "Sie haben eine Erkältung. Hier ist ein Rezept. Nehmen Sie diese Tabletten zweimal am Tag.",
                        "Bleiben Sie zu Hause und schlafen Sie viel. Trinken Sie viel Tee oder Wasser.", "Gute Besserung!"],
             response_type="dialog", min_duration=30, max_duration=150,
             speech_goal="Beim Arzt Beschwerden beschreiben, Fragen stellen (Muss ich …? Soll ich …? Wann kann ich …?) und sich bedanken.",
             keywords=["Ich habe Fieber", "Seit … Tagen", "Muss ich …", "Danke, Herr Doktor"]),
        base(L, "wortschatz", 1, "Wortschatz Modul 14: Gesundheit", page=143, words=WORDS),
        base(L, "yakuniy", 1, "Yakuniy Test: Modul 14", source="vizu",
             instruction="Futur I va sog'liq so'zlari bo'yicha yakuniy test.",
             questions=[
                 choice_gap("Ich ___ morgen zum Arzt gehen.", ["werde", "wird", "wirst"], "werde"),
                 choice_gap("Er ___ bald wieder gesund.", ["wird", "werdet", "werde"], "wird"),
                 choice_gap("Ihr ___ viel Wasser trinken.", ["werdet", "werden", "wird"], "werdet"),
                 mc("Welcher Satz ist richtig?", ["Wir werden morgen Tennis spielen.", "Wir werden spielen morgen Tennis.", "Wir morgen werden Tennis spielen."], "A"),
                 mc("Wo steht das Infinitiv im Futur I?", ["Auf Position 2", "Am Ende", "Am Anfang"], "B"),
                 mc("„die Apotheke“ — o'zbekchasi qaysi?", ["dorixona", "shifoxona", "klinika"], "A"),
                 mc("„der Husten“ — o'zbekchasi qaysi?", ["yo'tal", "isitma", "bosh og'rig'i"], "A"),
                 mc("„Gute Besserung!“ sagt man …", ["einer kranken Person", "zum Geburtstag", "am Morgen"], "A"),
                 tf("„schwach“ bedeutet „kuchsiz“.", True),
                 match("Was passt zusammen?", ["das Rezept", "untersuchen", "das Fieber", "die Erkältung"], ["retsept", "tekshirmoq", "isitma", "shamollash", "dori"],
                       {"1": "A", "2": "B", "3": "C", "4": "D"}),
             ]),
    ]
