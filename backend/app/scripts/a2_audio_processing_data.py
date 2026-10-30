"""What the A2 audio processing (2026-10-30) found per current Hören task of
lessons 1-13 — keyed by the task's content id (book edition, "vizu-a2buch-…")
or task_key (4. Unterricht Text 1-3).

Every key was re-checked against the transcript of the exact file on the
server (same SHA-256 as the transcribed file, app/data/a2_audio_transcripts
.json): the line that proves the answer is quoted in `evidence`. The keys and
the corrections of the audit of 2026-10-21 (a2_keys_data.py, first edition)
were taken over where the re-check confirmed them — the book edition has the
same questions. Nothing is guessed:

  `audio`     the file names the task was checked with, in playing order —
              the task's stored files must have exactly this content
  `match`     MATCHED / NEEDS_REVIEW / MISMATCH (+ note) — MISMATCH: the
              audio is not the task's audio, nothing is applied
  `keys` …    as in a1_hoeren_keys.plan_task (text_fixes, option_fixes,
              gap_option_renames, review = NEEDS_REVIEW instead of VERIFIED)
  `remove_questions`  questions neither on the book page nor in the audio
  `add_tracks`        book files missing on the server, added as labelled tracks
  `audio_only`        a task without questions (the Text slots)"""

import copy

from app.scripts.a2_keys_data import HOEREN as AUDIT

RECHECK = "Neu geprüft 2026-10-30 mit dem Transkript dieser Datei (gleiche SHA-256). "


def _audit(old_id: str, audio: list[str], note: str = "", **extra) -> dict:
    spec = copy.deepcopy(AUDIT[old_id])
    spec["evidence"] = RECHECK + (note + " " if note else "") + spec["evidence"]
    spec.update(audio=audio, match={"status": "MATCHED", "note": "Transkript passt zu Aufgabe und Fragen."}, **extra)
    return spec


def _mismatch(audio: str, same_as: str, title: str) -> dict:
    # `audio` names the CONTENT the stored file has — the 12. Unterricht file
    return {"audio": [same_as], "match": {"status": "MISMATCH", "note": (
        f"Falsche Audiodatei: „{audio}“ ist byte-identisch mit „{same_as}“ (gleiche SHA-256) — das Transkript gehört zu 12. Unterricht "
        f"„{title}“, nicht zu den Fragen dieser Aufgabe. Die richtige 13. Unterricht-Datei fehlt (auch im Quellordner). Keine Lösung gesetzt, "
        "bleibt Entwurf.")}}


TASKS: dict[str, dict] = {
    "vizu-a2buch-l01-hoeren-01": _audit("vizu-a2-l01-hoeren-01", ["A2 1.Unterricht Hören.m4a"]),
    "vizu-a2buch-l02-hoeren-01": _audit("vizu-a2-l02-hoeren-01", ["A2 2.Unterricht Hören.mp3"]),
    "vizu-a2buch-l03-hoeren-01": _audit("vizu-a2-l03-hoeren-01", ["A2.  3.Unterricht Hören.mp3"]),
    "a2-u04-hoeren-text-1": {"audio": ["A2 4.Unterricht Text 1.mp3"], "audio_only": True,
                             "match": {"status": "MATCHED", "note": "Text 1: Johann Mannsberg (45) über sein Wochenende — Datei „Text 1“, Inhalt passt."}},
    "a2-u04-hoeren-text-2": {"audio": ["A2 4.Unterricht Text 2.mp3"], "audio_only": True,
                             "match": {"status": "MATCHED", "note": "Text 2: Anna Mannsberg (40) über ihr Wochenende — Datei „Text 2“, Inhalt passt."}},
    "a2-u04-hoeren-text-3": {"audio": ["A2 4.Unterricht Text 3.mp3"], "audio_only": True,
                             "match": {"status": "MATCHED", "note": "Text 3: Julio Mannsberg (18) über sein Wochenende — Datei „Text 3“, Inhalt passt."}},
    "vizu-a2buch-l05-hoeren-01": _audit("vizu-a2-l05-hoeren-01", ["A2 5.Unterricht Hören.mp3"],
                                        "Frage 4: die importierte Lösung „800–1000 Euro“ widerspricht dem Audio [22.5] „zwischen 1.500 und 2.100 Euro“ — korrigiert."),
    "vizu-a2buch-l06-hoeren-01": _audit("vizu-a2-l06-hoeren-01", ["A2 6.Unterricht.mp3"]),
    "vizu-a2buch-l07-hoeren-01": _audit(
        "vizu-a2-l07-hoeren-01", ["A2 7.Unterricht Text 1.mp3", "A2 7.Unterricht Text 2.mp3"],
        "Auf dem Server fehlte „Text 2“ (Sara) — die Fragen 2, 4, 6, 9, 10, 12, 15 sind nur damit beantwortbar; die Buchdatei wurde als Spur „Text 2“ ergänzt.",
        audio_label="Text 1", add_tracks=[{"label": "Text 2", "file": "A2 7.Unterricht Text 2.mp3"}]),
    "vizu-a2buch-l08-hoeren-01": _audit(
        "vizu-a2-l08-hoeren-01", ["A2 8.Unterricht.mp3"],
        "Frage 6 („manchmal am Wochenende“): das Audio sagt [60.6-68.4] „manchmal … Süßigkeiten … 1–2 Tafeln Schokolade pro Woche“ — "
        "„Wochenende“ kommt nicht vor, von den Optionen passt nur Schokolade."),
    "vizu-a2buch-l09-hoeren-01": _audit("vizu-a2-l09-hoeren-01", ["A2 9.Unterricht Hören.mp3"]),
    "vizu-a2buch-l10-hoeren-01": _audit("vizu-a2-l10-hoeren-01", ["A2 10.Unterricht Teil 1.m4a"]),
    "vizu-a2buch-l10-hoeren-02": _audit("vizu-a2-l10-hoeren-02", ["A2 10.Unterricht Teil 2.m4a"]),
    "vizu-a2buch-l10-hoeren-03": _audit("vizu-a2-l10-hoeren-03", ["A2 10.Unterricht Teil 3.m4a"]),
    "vizu-a2buch-l10-hoeren-04": _audit("vizu-a2-l10-hoeren-04", ["A2 10.Unterricht Teil 4.m4a"]),
    "vizu-a2buch-l11-hoeren-01": _audit("vizu-a2-l11-hoeren-01", ["A2 11.Unterricht Teil_1.m4a"]),
    "vizu-a2buch-l11-hoeren-02": _audit("vizu-a2-l11-hoeren-02", ["A2 11.Unterricht Teil_2.m4a"]),
    "vizu-a2buch-l11-hoeren-03": _audit("vizu-a2-l11-hoeren-03", ["A2 11.Unterricht Teil_3.m4a"]),
    "vizu-a2buch-l11-hoeren-04": _audit("vizu-a2-l11-hoeren-04", ["A2 11.Unterricht Teil_4.m4a"]),
    "vizu-a2buch-l12-hoeren-01": _audit("vizu-a2-l12-hoeren-01", ["A2 12.Unterricht Teil_1.m4a"]),
    "vizu-a2buch-l12-hoeren-02": _audit("vizu-a2-l12-hoeren-02", ["A2 12.Unterricht Teil_2.m4a"]),
    "vizu-a2buch-l12-hoeren-03": _audit("vizu-a2-l12-hoeren-03", ["A2 12.Unterricht Teil_3.m4a"]),
    "vizu-a2buch-l12-hoeren-04": _audit("vizu-a2-l12-hoeren-04", ["A2 12.Unterricht Teil_4.m4a"]),
    "vizu-a2buch-l13-hoeren-01": _mismatch("A2 13.Unterricht Teil 1.m4a", "A2 12.Unterricht Teil_1.m4a", "Teil 1: Fünf kurze Texte"),
    "vizu-a2buch-l13-hoeren-02": _mismatch("A2 13.Unterricht Teil 2.m4a", "A2 12.Unterricht Teil_2.m4a", "Teil 2: Was kommt in den Koffer?"),
    "vizu-a2buch-l13-hoeren-03": _mismatch("A2 13.Unterricht Teil 3.m4a", "A2 12.Unterricht Teil_3.m4a", "Teil 3: Fünf kurze Gespräche"),
    "vizu-a2buch-l13-hoeren-04": _mismatch("A2 13.Unterricht Teil 4.m4a", "A2 12.Unterricht Teil_4.m4a", "Teil 4: Interview mit Sandra"),
}

# 6. Unterricht: the answers are clear in the audio, but all 12 are open questions graded word by word
# (audit 2026-10-21) — every key stays "Prüfung nötig" until an admin has checked the accepted wordings.
TASKS["vizu-a2buch-l06-hoeren-01"]["match"] = {"status": "MATCHED", "note": "Transkript passt; 12 offene Fragen — Lösungsvarianten prüfen (Prüfung nötig)."}
