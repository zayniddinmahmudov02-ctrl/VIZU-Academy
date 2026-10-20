"""Answer keys / verification notes of the A2 course with their source (see a2_keys.py).

Timestamps [m:ss] refer to the audio file of the task (the same file as on
the server, SHA-256 compared). "TR" = machine transcript of that file by two
models. "Blatt" = "Vizu-Antworten A2" (keys for some lessons only)."""

TR = "Audio-Transkript (Whisper large-v3 + medium)"
AUDIT = "VIZU-Audit 2026-10-21"


def one(answer: str) -> dict:
    """Key of a one-gap Lückentext / picture choice (dropdown option text)."""
    return {"1": [answer]}


# ============================================================ Hören
HOEREN: dict[str, dict] = {}

HOEREN["vizu-a2-l01-hoeren-01"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 1.Unterricht Hören.m4a“: Johann [0:08-0:32] „Mein Beruf ist Architekt, weil mein Vater auch "
                "Architekt war … als Kind … Häuser gezeichnet … Jetzt plane ich moderne Gebäude“; Julia [0:41-1:06] „Ärztin, weil ich schon als "
                "Kind Menschen helfen wollte … Puppen behandelt … Biologie sehr gemocht … arbeite ich im Krankenhaus“; Mikey [1:15-1:35] "
                "„Cristiano Ronaldo immer bewundert. Letztes Jahr … in einer Mannschaft trainiert. Jetzt trainiere ich hart und werde in "
                "Zukunft professionell Fußball spielen“. Bestehende Lösung (Blatt) bestätigt.",
    "keys": ["Weil sein Vater Architekt war", "Cristiano Ronaldo", "In einem Krankenhaus", "Er hat Häuser gezeichnet", "Menschen helfen",
             "Er wird professionell Fußball spielen", "Biologie", "Er plant moderne Gebäude", "Er hat in einer Mannschaft trainiert",
             "Weil sie schon als Kind helfen wollte", "Architekt", "Er trainiert hart"],
}

HOEREN["vizu-a2-l10-hoeren-01"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 10.Unterricht Teil 1.m4a“: 1 [1:01] „Ich lasse mir mittellange Haare schneiden“; 2 [2:09] „Nur mein "
                "Vater versteht mich“; 3 [3:13] „am besten passt mir der Frühling“; 4 [4:53] „Bayern München gewinnt gegen Atletico Madrid 2 zu 1“; "
                "5 [5:45] „Jeanshosen, beste Qualität, nur 17 Euro“. Beide Modelle gleich.",
    "keys": ["Eine mittellange Frisur.", "Mit ihrem Vater.", "Den Frühling.", "Bayern München hat 2:1 gewonnen.", "17 Euro."],
}

HOEREN["vizu-a2-l10-hoeren-02"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 10.Unterricht Teil 2.m4a“ [1:36-2:13]: „Anne hat … eine karierte Tischdecke … mitgebracht“; "
                "„Olaf hat eine große Kiste Äpfel mitgebracht“; „Harry hat seine ganzen Legos mitgebracht“; „Niki ihre alten Puppen“; Martin: "
                "„Mein Rad. Ich habe ja zum Geburtstag ein Moped geschenkt bekommen“ (das Mofa wurde nicht verkauft). Beispiel Anton → a Poster.",
    "keys": [one("c) Tischdecke"), one("i) Kiste mit Äpfeln"), one("d) Bausteine (Lego)"), one("f) Puppen"), one("g) Fahrrad")],
}

HOEREN["vizu-a2-l10-hoeren-03"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 10.Unterricht Teil 3.m4a“: 11 [0:56] „Diesmal habe ich mich mit meiner Mutter gestritten“ (Bild a: "
                "Frau); 12 [1:38] „da brauche ich … geeignete Tennisschuhe“ (Schläger hat er schon); 13 [2:49] „Dann doch lieber das Top“; 14 [3:43] "
                "„dass ein Computerspiel genau das Richtige für ihn ist“; 15 [4:44] „wenn ich mich als Krankenschwester verkleide“ — Bild b zeigt "
                "die Figur im weißen Kittel; die bisherige Beschriftung „als Arzt“ widersprach dem Audio und wurde angepasst.",
    "option_fixes": {5: [("b) als Arzt", "b) als Krankenschwester (weißer Kittel, Bild b)")]},
    "keys": ["a) mit der Frau (Bild a)", "a) Tennisschuhe", "c) ein Top", "b) ein Computerspiel", "b) als Krankenschwester (weißer Kittel, Bild b)"],
}

HOEREN["vizu-a2-l10-hoeren-04"] = {
    "evidence": f"Geprüft ({AUDIT}): {TR}, „A2 10.Unterricht Teil 4.m4a“: 16 [1:38] „Feriencamps für Jugendliche ab 14“; 17 [2:02] „Ich war im "
                "Feriencamp in Italien“; 18 [2:05] „jeden Vormittag von 10 bis 12 einen Sprachkurs“; 19 [2:33] „Im Juli und August“; 20 [2:46-2:55] "
                "„Man bezahlt nur sein Ticket … Natürlich braucht man auch etwas Taschengeld“ (man bekommt keines).",
    "keys": ["Ja", "Nein", "Ja", "Nein", "Nein"],
}

# ============================================================ Lesen
# every question re-read against its text; the key was confirmed by the text
# passage quoted in the question's explanation (or found in the text)
_LESEN_EVIDENCE = (f"Geprüft ({AUDIT}): Lösung mit dem Lesetext abgeglichen — die Antwort steht im Text (Textstelle in der Erklärung der "
                   "Frage). Lösung unverändert.")

_LESEN_COUNTS = {
    "vizu-a2-l01-lesen-01#1": 11, "vizu-a2-l01-lesen-01#2": 12, "vizu-a2-l01-lesen-01#3": 12,
    "vizu-a2-l02-lesen-01#1": 8, "vizu-a2-l02-lesen-01#2": 8, "vizu-a2-l02-lesen-01#3": 8,
    "vizu-a2-l03-lesen-01#1": 6, "vizu-a2-l03-lesen-01#2": 6,
    "vizu-a2-l04-lesen-01#1": 6, "vizu-a2-l04-lesen-01#2": 6, "vizu-a2-l04-lesen-01#3": 6,
    "vizu-a2-l05-lesen-01#1": 16,
    "vizu-a2-l06-lesen-01#1": 12, "vizu-a2-l06-lesen-01#2": 11,
    "vizu-a2-l07-lesen-01#1": 12,
    "vizu-a2-l08-lesen-01#1": 10,
    "vizu-a2-l09-lesen-01#1": 8,
    "vizu-a2-l10-lesen-01#1": 5, "vizu-a2-l10-lesen-02#1": 5, "vizu-a2-l10-lesen-03#1": 5, "vizu-a2-l10-lesen-04#1": 1,
    "vizu-a2-l11-lesen-01#1": 4, "vizu-a2-l11-lesen-02#1": 5, "vizu-a2-l11-lesen-03#1": 5, "vizu-a2-l11-lesen-04#1": 1,
    "vizu-a2-l12-lesen-01#1": 3, "vizu-a2-l12-lesen-02#1": 5, "vizu-a2-l12-lesen-03#1": 5, "vizu-a2-l12-lesen-04#1": 1,
    "vizu-a2-l13-lesen-01#1": 5, "vizu-a2-l13-lesen-02#1": 5, "vizu-a2-l13-lesen-03#1": 5, "vizu-a2-l13-lesen-04#1": 1,
}

LESEN: dict[str, dict] = {cid: {"questions": n, "evidence": _LESEN_EVIDENCE} for cid, n in _LESEN_COUNTS.items()}
# Notes for the admin where the check found something worth knowing (key still correct):
LESEN["vizu-a2-l09-lesen-01#1"]["evidence"] += (" Frage 6 („Weniger als 30 % … problematisch“ → Richtig) beruht auf „fast 30 %“ im Text — "
                                                "sachlich richtig, aber knifflig formuliert.")
LESEN["vizu-a2-l11-lesen-01#1"]["evidence"] += " Buchaufgabe 5 fehlt bewusst: der Bungee-Preis steht auch im Buchtext nicht (PDF S. 5–6 geprüft)."
