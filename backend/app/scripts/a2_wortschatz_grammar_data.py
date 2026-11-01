"""Grammar of the A2 lesson words that have no Wörterbuch entry (owner decision 2026-11-01:
"Grammatikani to'ldir"). Standard German grammar (Duden forms), written by VIZU — recorded as
source "vizu-grammatik" in vocabularies.data_sources; no example sentences.

PLURAL: "–" = no plural in this meaning (Obst, Gesundheit …); the listed form itself = a plural
form (die Kopfschmerzen). VERBS: (Präteritum er/sie/es, Partizip II, Hilfsverb)."""

NO_PLURAL = "–"

PLURAL = {
    # 1. Unterricht
    "Ärztin": "Ärztinnen", "Lehrerin": "Lehrerinnen", "Koch": "Köche", "Köchin": "Köchinnen",
    "Fußballspieler": "Fußballspieler", "Polizist": "Polizisten", "Polizistin": "Polizistinnen", "Journalist": "Journalisten",
    "Journalistin": "Journalistinnen", "Fahrer": "Fahrer", "Verkäufer": "Verkäufer", "Manager": "Manager",
    "Studentin": "Studentinnen", "Zahnarzt": "Zahnärzte", "Schauspielerin": "Schauspielerinnen", "Programmierer": "Programmierer",
    "Friseur": "Friseure", "Fotograf": "Fotografen", "Elektriker": "Elektriker",
    # 2. Unterricht
    "soziale Netzwerk": "sozialen Netzwerke", "Internet": NO_PLURAL, "Benutzer": "Benutzer", "Account": "Accounts",
    "Profil": "Profile", "Video": "Videos", "Kommentar": "Kommentare", "Freund / die Freundin": "Freunde / Freundinnen",
    "Chat": "Chats", "Sicherheit": NO_PLURAL, "Zeit": "Zeiten", "Gruppe": "Gruppen", "Link": "Links",
    # 3. Unterricht
    "Gesundheit": NO_PLURAL, "Körper": "Körper", "Ernährung": NO_PLURAL, "Lebensmittel": "Lebensmittel", "Obst": NO_PLURAL,
    "Fast Food": NO_PLURAL, "Radfahren": NO_PLURAL, "Gymnastik": NO_PLURAL, "Ruhe": NO_PLURAL, "Husten": NO_PLURAL,
    "Fieber": NO_PLURAL, "Kopfschmerzen": "Kopfschmerzen", "Halsschmerzen": "Halsschmerzen", "Rückenschmerzen": "Rückenschmerzen",
    "Tablette": "Tabletten", "Apotheke": "Apotheken", "Flüssigkeit": "Flüssigkeiten", "Ingwer": NO_PLURAL, "Honig": NO_PLURAL,
    "Zitrone": "Zitronen", "Tee": "Tees",
    # 4. Unterricht
    "Vormittag": "Vormittage", "Nachmittag": "Nachmittage", "Unterricht": NO_PLURAL, "Hausaufgaben": "Hausaufgaben",
    "Aufgabe": "Aufgaben", "Schüler": "Schüler", "Liste": "Listen", "Alltag": NO_PLURAL,
    # 9. Unterricht
    "Nachrichten": "Nachrichten", "Quellen": "Quellen",
}

VERBS = {
    "bewundern": ("bewunderte", "bewundert", "haben"),
    "zeichnen": ("zeichnete", "gezeichnet", "haben"),
    "studieren": ("studierte", "studiert", "haben"),
    "teilen": ("teilte", "geteilt", "haben"),
    "liken": ("likte", "gelikt", "haben"),
    "folgen": ("folgte", "gefolgt", "sein"),
    "sprechen": ("sprach", "gesprochen", "haben"),
    "organisieren": ("organisierte", "organisiert", "haben"),
    "sich ausruhen": ("ruhte sich aus", "ausgeruht", "haben"),
    "achten auf": ("achtete auf", "geachtet", "haben"),
}

WORD_TYPE = {
    **{w: "Verb" for w in VERBS},
    "motiviert": "Adjektiv", "produktiv": "Adjektiv", "offline": "Adjektiv",
    "früher": "Adverb", "heutzutage": "Adverb", "genug": "Adverb",
    **{w: "Wendung" for w in ("gesund bleiben", "fit bleiben", "zur Schule gehen", "Sport machen", "spazieren gehen",
                              "Freunde treffen", "Musik hören")},
}
