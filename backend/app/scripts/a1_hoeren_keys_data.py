"""Answer keys of the A1 Hören tasks with their source (see a1_hoeren_keys.py).

Timestamps [m:ss] refer to the audio file of the task. "Blatt" = the old
answer sheet "Vizu-Javoblar A1.pdf" (older course version)."""

TR = "Audio-Transkript (Whisper large-v3 + medium)"


def gaps(*answers, start: int = 1) -> dict:
    return {str(i): [a] if isinstance(a, str) else a for i, a in enumerate(answers, start=start)}


TASKS: dict[str, dict] = {}

# ---------------------------------------------------------------- L1
TASKS["vizu-a1-l01-hoeren-01"] = {
    "page": 9,
    "evidence": f"Geprüft: {TR}, A1-1.mp3 [0:00-0:19]: „Es ist Samstag … in den Park … sonnig und warm … Tom spielt Fußball und Anna liest ein Buch "
                "… Ein Hund kommt und läuft zu ihnen … spielen mit dem Hund … Nach zwei Stunden … müde, aber glücklich.“ Bestehende Lösung bestätigt.",
    "keys": ["Samstag", "In den Park", "Falsch", "Er spielt Fußball.", "Sie liest ein Buch.", "Richtig", "Richtig", "Nach zwei Stunden",
             {"1": ["sonnig"], "2": ["warm"]}, {"1": ["müde"], "2": ["glücklich"]}],
}

# ---------------------------------------------------------------- L2
TASKS["vizu-a1-l02-hoeren-01"] = {
    "page": 22,
    "evidence": f"Geprüft: {TR}, A1-2.mp3 — der Lückentext stimmt Wort für Wort mit dem Audio überein. Blatt (ältere Version) weicht ab: "
                "Lücke 1 „Peter“ (Audio: „Ich heiße Anna“), Lücke 5 „arbeitet“ (Audio: „arbeitet als Lehrer“).",
    "keys": [
        gaps("Anna", "wohne"),
        gaps("Familie", "Vater", "Lehrer", "freundlich", "Bücher", "Fußball", start=3),
        gaps("Mutter", "Lehrerin", "liest", "Musik", "backt", start=9),
        gaps("Bruder", "Fußball", "Musik", "Garten", start=14),
        gaps("Schwester", "malt", "Bücher", "Katze", start=18),
        gaps("Haus", "Familie", "Ausflüge", "Geburtstage", start=22),
    ],
    # the word list shown to students named the old version's words (Peter, arbeitet …)
    "instruction": "Hören Sie den Text und ergänzen Sie die Lücken. Passende Wörter — mos keladigan so'zlar: Anna (Anna), Ausflüge (sayrlar), "
                   "backt (pishiradi), Bruder (aka), Bücher (kitoblar), Familie (oila), freundlich (do'stona), Fußball (futbol), Garten (bog'), "
                   "Geburtstage (tug'ilgan kunlar), Haus (uy), Katze (mushuk), Lehrer (o'qituvchi), Lehrerin (o'qituvchi ayol), liest (o'qiydi), "
                   "malt (rasm chizadi), Musik (musiqa), Mutter (ona), Schwester (singil), Vater (ota), wohne (yashayman). "
                   "Einige Wörter kommen zweimal vor.",
}

# ---------------------------------------------------------------- L3
TASKS["vizu-a1-l03-hoeren-01"] = {
    "page": 34,
    "evidence": f"Geprüft: {TR}, A1-3.mp3: „einen Tisch für zwei Personen [0:03] … ein Glas Wasser … einen Apfelsaft [0:16-0:20] … das Schnitzel "
                "mit Pommes … die Margherita [0:28-0:35] … keine Allergien … sehr lecker … alles war frisch [0:35-0:50] … wir sind satt [0:58]“. "
                "Bestehende Lösung bestätigt.",
    "keys": ["Für zwei Personen", "Ein Glas Wasser", "Einen Apfelsaft", "Das Schnitzel mit Pommes", "Die Pizza Margherita", "Falsch", "Richtig",
             "Nein, sie sind satt"],
}

# ---------------------------------------------------------------- L4
TASKS["vizu-a1-l04-hoeren-01"] = {
    "page": 43,
    "evidence": f"Geprüft: {TR}, A1-4.mp3: „Ich heiße Alex und bin 20 Jahre alt [0:04] … Mein Zimmer ist schön, sauber und hell … Auf dem Tisch steht "
                "ein Computer … einen großen Schrank für meine Kleidung … ein großes Fenster … An der Wand hängen viele Bilder … Ich lerne oft in "
                "meinem Zimmer … Manchmal lese ich Bücher oder höre Musik … mein Lieblingsplatz zu Hause [0:10-0:34]“.",
    "keys": ["Alex", "20 Jahre alt", "Schön, sauber und hell", "Ein Computer", "Einen Schrank", "Ein großes Fenster", "Bilder", "Er lernt.",
             "Bücher lesen oder Musik hören", "Es ist sein Lieblingsplatz zu Hause."],
}

# ---------------------------------------------------------------- L5
TASKS["vizu-a1-l05-hoeren-01"] = {
    "page": 55,
    "evidence": f"Geprüft: {TR}, A1-5.mp3: „Am Samstag stehe ich um 8 Uhr auf [0:06] … frühstücke um 8.30 Uhr [0:08] … Um 11 Uhr treffe ich [0:13] … "
                "Um 13 Uhr esse ich Mittag [0:17] … Um 18 Uhr gehe ich einkaufen [0:24] … Um 23 Uhr gehe ich ins Bett [0:31] … Am Sonntag … um 9 Uhr "
                "[0:36] … Um 12 Uhr gehe ich … ins Café [0:41] … Um 22.30 Uhr gehe ich schlafen [0:55]“. Blatt (ältere Version): 08:00, 08:30, 11:00, "
                "13:00, 18:00, 23:00, 09:00, 12:00, 22:00 — Lücke 9 laut Audio 22.30.",
    "keys": [{"1": {"time": "8"}, "2": {"time": "8:30"}, "3": {"time": "11"}, "4": {"time": "13"}, "5": {"time": "18"}, "6": {"time": "23"},
              "7": {"time": "9"}, "8": {"time": "12"}, "9": {"time": "22:30"}}],
}

# ---------------------------------------------------------------- L6
TASKS["vizu-a1-l06-hoeren-01"] = {
    "page": 66,
    "evidence": f"Geprüft: {TR}, A1-6.mp3 (20 nummerierte Sätze „Erster … Zwanzigster“): Brot, Butter, Marmelade, Käse, Wurst, Reis, Nudeln, Kartoffeln, "
                "Huhn, Rind, Gemüse, Salat, Tomaten, Gurken, Karotten, Paprika, Äpfel, Bananen, Milch, Saft — stimmt mit dem Blatt überein. Das Audio "
                "gehört zur älteren Version: die Bilder / „Wörter zum Thema“ der Buchseite (Suppe, Fisch, Obst, Kuchen …) passen nicht dazu.",
    "keys": [{**gaps("Brot", "Butter", "Marmelade", "Käse", "Wurst", "Reis", "Nudeln", "Kartoffeln", "Huhn", "Rind", "Gemüse", "Salat", "Tomaten",
                     "Gurken", "Karotten", "Paprika", ["Äpfel", "Aepfel"], "Bananen", "Milch", "Saft")}],
    # two sentences of the task said something else than the speaker
    "text_fixes": {1: [("Zum Frühstück esse ich [[2]].", "Zum Frühstück nehme ich [[2]]."),
                       ("Zum Mittagessen esse ich [[6]].", "Zum Mittagessen koche ich [[6]].")]},
    "instruction": "Höre die Sätze und ergänze die fehlenden Wörter. Wörter zum Thema: Äpfel, Bananen, Brot, Butter, Gemüse, Gurken, Huhn, "
                   "Karotten, Kartoffeln, Käse, Marmelade, Milch, Nudeln, Paprika, Reis, Rind, Saft, Salat, Tomaten, Wurst.",
}

# ---------------------------------------------------------------- L7
TASKS["vizu-a1-l07-hoeren-01"] = {
    "page": 76,
    "evidence": f"Geprüft: {TR}, A1-7.mp3 [0:02-0:41]: war, kam, war, frühstückte, aß, trank, ging, sah, besuchte, machte, ging, ruhte, kaufte, aß, "
                "probierte, ging, war, war — Wort für Wort wie die bestehende Lösung (und das Blatt).",
    "keys": [gaps("war", "kam", "war", "frühstückte", "aß", "trank", "ging", "sah", "besuchte", "machte", "ging", "ruhte", "kaufte", "aß", "probierte",
                  "ging", "war", "war")],
}

# ---------------------------------------------------------------- L8
TASKS["vizu-a1-l08-hoeren-01"] = {
    "page": 85,
    "evidence": f"Geprüft: {TR}, A1-8.mp3 [0:03-1:06]: bin geflogen, bin gefahren, habe übernachtet, hat gefallen, (bin) gegangen, habe bewundert, "
                "habe gemacht ×2, habe genossen, habe probiert, habe getroffen, haben gelacht, habe gekauft, hat gefallen, habe entspannt, habe "
                "gesammelt, ist, möchte hinfahren. Lücke 9: der Sprecher sagt „Ich habe … spazieren gegangen“ (Fehler im Audio) — die Aufgabe gibt "
                "(sein) vor, richtig ist „bin“. Lücke 33: Audio „ist“, Blatt „war“ — beide akzeptiert.",
    "keys": [gaps("bin", "geflogen", "bin", "gefahren"),
             gaps("habe", "übernachtet", "hat", "gefallen", "bin", "gegangen", "habe", "bewundert", start=5),
             gaps("habe", "gemacht", "habe", "gemacht", "habe", "genossen", "habe", "probiert", start=13),
             gaps("habe", "getroffen", "haben", "gelacht", "habe", "gekauft", start=21),
             gaps("hat", "gefallen", "habe", "entspannt", "habe", "gesammelt", ["ist", "war"], "möchte", "hinfahren", start=27)],
}

# ---------------------------------------------------------------- L9
TASKS["vizu-a1-l09-hoeren-01"] = {
    "page": 94,
    "evidence": f"Geprüft: {TR}, A1-9.mp3 [0:12-1:52]: nach Italien, in Rom, im Zentrum, im Café, auf den Markt, auf der Straße, in die Türkei, in "
                "Istanbul, am Meer, auf die Party, in die Schweiz, in Zürich, zur Messe, auf die Straße, ins Kino, in den Park — wie die bestehende "
                "Lösung; deren grammatisch richtige Varianten (zum Markt, zur Party, auf die Messe) bleiben akzeptiert.",
    "keys": [gaps("nach", "in", "im", "im", ["auf den", "zum"], "auf der", "in die", "in", "am", ["auf die", "zur"], "in die", "in", ["zur", "auf die"],
                  "auf die", "ins", "in den")],
}

# ---------------------------------------------------------------- L10 — the two audio files were attached the wrong way round
TASKS["vizu-a1-l10-hoeren-01"] = {
    "page": "103-104",
    "evidence": f"Geprüft: {TR}, A1-10.2.mp3 = „Wir sind im Supermarkt“: „mit unserem Deutschlehrer in den Supermarkt [0:02] … 20 neue Wörter "
                "[0:10] … auf Deutsch und auf Usbekisch [0:14] … ein kleines Geschenk gekauft [0:25] … Wir haben uns sehr gefreut [0:30]“. "
                "Die Aufgabe hatte A1-10.1.mp3 (= Text „Wir sind im Markt“) — Audio getauscht; die Lösung war richtig.",
    "keys": ["In den Supermarkt", "Mit ihrem Deutschlehrer", "20 neue Wörter schreiben", "Deutsche und usbekische Wörter", "Er hat Geschenke gekauft.",
             "Sie freuen sich."],
    "audio_parts": ["A1-10.2.mp3"],
}
TASKS["vizu-a1-l10-hoeren-02"] = {
    "page": "103-104",
    "evidence": f"Geprüft: {TR}, A1-10.1.mp3 = „Wir sind im Markt“: „ich bin zwölf Jahre alt [0:02] … Kleidung für die Schule kaufen [0:09] … schöne "
                "Kleidung für uns Kinder [0:12] … ein Kopftuch [0:16] … für sich selbst nichts gekauft [0:21] … Ich war traurig und habe geweint "
                "[0:37]“. Die Aufgabe hatte A1-10.2.mp3 (= Text „Wir sind im Supermarkt“) — Audio getauscht; die Lösung war richtig.",
    "keys": ["12 Jahre alt", "Um Kleidung für die Schule zu kaufen", "Nur für die Kinder", "Ein Kopftuch", "Nichts", "Er weint."],
    "audio_parts": ["A1-10.1.mp3"],
}

# ---------------------------------------------------------------- L11
TASKS["vizu-a1-l11-hoeren-01"] = {
    "page": 113,
    "evidence": f"Geprüft: {TR}, A1-11.mp3: „Wir sind vier Studierende [0:05] … Ich heiße Max und erzähle unsere Geschichte … ich studiere Informatik "
                "[0:18] … Tom … putzt er oft die Küche und das Bad [0:36] … Anna … kocht sie gern und backt Kuchen [0:50] … Lisa ist kreativ [0:58] … "
                "wir essen oft zusammen in der Küche … unsere Wohngemeinschaft ist ruhig und freundlich [1:10-1:18]“ — stimmt mit dem Blatt "
                "(1-B, 2-A, 3-B, 4-A, 5-A, 6-B, 7-A, 8-B) überein.",
    "keys": ["Vier", "Max", "Informatik", "Tom", "Anna", "Lisa", "Küche", "Ruhig"],
}


def _num(n: int, word: str) -> list[str]:
    return [str(n), word]


# ---------------------------------------------------------------- L12 — two reports, two audio files (not the same answers)
TASKS["vizu-a1-l12-hoeren-01"] = {
    "page": 122,
    "evidence": f"Geprüft: {TR}, A1-12.1.mp3: „In Berlin sind es am Morgen 8 Grad. In Hamburg sind es nur 7 Grad und es ist windig [0:12-0:17] … In Köln "
                "sind es 12 Grad und es gibt wenig Regen [0:27-0:30]“ — stimmt mit dem Blatt überein. Zwei Sätze des Audios fehlten im Text "
                "(Mittag: Berlin 11, Hamburg 10 Grad; Abend: 9 Grad) — ergänzt, damit der Text dem Audio folgt.",
    "keys": [{"1": ["Berlin"], "2": _num(8, "acht"), "3": ["Hamburg"], "4": _num(7, "sieben"), "5": ["Köln", "Koeln"], "6": _num(12, "zwölf")}],
    "text_fixes": {1: [("Am Mittag steigen die Temperaturen ein bisschen.",
                        "Am Mittag steigen die Temperaturen ein bisschen. In Berlin sind es 11 Grad, in Hamburg 10 Grad."),
                       ("Am Abend wird es wieder kälter.", "Am Abend wird es wieder kälter. Die Temperaturen sinken auf 9 Grad.")]},
}
TASKS["vizu-a1-l12-hoeren-02"] = {
    "page": 122,
    "evidence": f"Geprüft: {TR}, A1-12.2.mp3: „In München sind es 16 Grad. In Stuttgart sind es 17 Grad [0:13-0:19] … In Frankfurt steigen die "
                "Temperaturen auf 24 Grad [0:34-0:38]“ — stimmt mit dem Blatt überein. Zwei Sätze des Audios fehlten im Text (Mittag: München 22, "
                "Stuttgart 23 Grad; Abend: zwischen 18 und 19 Grad) — ergänzt.",
    "keys": [{"7": ["München", "Muenchen"], "8": _num(16, "sechzehn"), "9": ["Stuttgart"], "10": _num(17, "siebzehn"), "11": ["Frankfurt"],
              "12": _num(24, "vierundzwanzig")}],
    "text_fixes": {1: [("Am Mittag wird es warm.", "Am Mittag wird es warm. In München sind es 22 Grad, in Stuttgart 23 Grad."),
                       ("Am Abend bleibt es mild.", "Am Abend bleibt es mild. Die Temperaturen sind zwischen 18 und 19 Grad.")]},
}

# ---------------------------------------------------------------- L13
TASKS["vizu-a1-l13-hoeren-01"] = {
    "page": 132,
    "evidence": f"Geprüft: {TR}, A1-13.m4a: Markus Klein „Ich konnte heute leider nicht zu unserem Termin kommen“ [0:01] · Leon Schmidt „komme 30 "
                "Minuten später“ [0:12] · Laura Neumann „Ich bin krank geworden und musste zu Hause bleiben“ [0:24] · Tim Wagner „ich konnte keinen "
                "Parkplatz finden“ [0:35] · Jana Hoffmann „Der Zug hatte Verspätung“ [0:51] · Daniel Fischer „Könnten wir das Treffen auf morgen "
                "verschieben?“ [1:07] — stimmt mit dem Blatt (B, A, B, B, C, A) überein.",
    "keys": ["Er konnte nicht zum Termin kommen.", "30 Minuten später.", "Sie war krank.", "Er konnte keinen Parkplatz finden.",
             "Der Zug hatte Verspätung.", "Das Treffen verschieben."],
}

# ---------------------------------------------------------------- L14 — Alex speaks only in the second audio file
TASKS["vizu-a1-l14-hoeren-01"] = {
    "page": 140,
    "evidence": f"Geprüft: {TR}. A1-14.1.mp3 (Alisa): Gymnastik und frische Luft [0:00-0:20], zu Fuß zur Arbeit, Freundin im Park, am Abend Salat "
                "oder Suppe, vor dem Schlafen ein Buch [0:20-0:48]. A1-14.2.mp3 (Alex): dreimal pro Woche ins Fitnessstudio, eine Stunde, am "
                "Wochenende Basketball [0:00-0:14], viel Gemüse … Fisch [0:14-0:28], stark und aktiv bleiben [0:28-0:36]. Die Aufgabe hatte nur "
                "A1-14.1.mp3 — die Alex-Fragen waren nicht hörbar; jetzt zwei getrennte Audiodateien („Audio von Alisa“, „Audio von Alex“). "
                "Das Blatt (ältere Fragenfolge) weicht bei 5–10 ab; das Audio ist eindeutig.",
    "keys": ["Alisa", "Alex", "Alisa", "Alex", "Alisa", "Alex", "Alisa", "Alex", "Alisa", "Alex"],
    # two separate audio slots (2026-10-20): the main audio is Alisa's, Alex is an extra track
    # (slot names as in Admin -> Medienverwaltung, see a1_l14_audio_slots.py)
    "audio_parts": ["A1-14.1.mp3"],
    "audio_label": "Text von Alisa",
    "audio_tracks": [("Text von Alex", "A1-14.2.mp3")],
}
