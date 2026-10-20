"""A1 Lektion 14 Hören: two separate audio slots „Text von Alisa“ (the task's
main audio) and „Text von Alex“ (an extra track) instead of one combined audio.

Idempotent; dry run unless --apply. Never touches files, questions, keys or
the publish state — it only names the main slot and makes sure the Alex slot
exists (renames the old „Audio von Alex“ track or creates an empty slot).
The files are uploaded in Admin -> Medienverwaltung (or a1_hoeren_keys
--apply --audio-dir ...); the task publishes itself once both slots have a
file and every key is verified.

    python -m app.scripts.a1_l14_audio_slots [--apply]
"""

import argparse
import json
import sys

from sqlalchemy import select

from app.core.audit import write_audit
from app.db.session import SessionLocal
from app.models.listening import Listening
from app.models.listening_audio_track import ListeningAudioTrack

CONTENT_ID = "vizu-a1-l14-hoeren-01"
ALISA = "Text von Alisa"
ALEX = "Text von Alex"
OLD_ALEX = ("Audio von Alex",)


def plan(lst: Listening) -> list[tuple[str, str]]:
    """[(action, detail)] — empty when the slots are already right."""
    out = []
    if lst.audio_label != ALISA:
        out.append(("label_main", f"{lst.audio_label!r} -> {ALISA!r}"))
    if not any(t.label == ALEX for t in lst.audio_tracks):
        old = next((t for t in lst.audio_tracks if t.label in OLD_ALEX), None)
        out.append(("rename_track", f"{old.label!r} -> {ALEX!r}") if old else ("create_track", f"empty slot {ALEX!r}"))
    return out


def apply(db, lst: Listening, steps: list[tuple[str, str]]) -> None:
    for action, _ in steps:
        if action == "label_main":
            lst.audio_label = ALISA
        elif action == "rename_track":
            next(t for t in lst.audio_tracks if t.label in OLD_ALEX).label = ALEX
        elif action == "create_track":
            db.add(ListeningAudioTrack(listening_id=lst.id, label=ALEX,
                                       order_index=max([t.order_index for t in lst.audio_tracks] or [0]) + 1))
    db.commit()
    db.refresh(lst)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="write (default: dry run)")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        lst = db.scalar(select(Listening).where(Listening.content_id == CONTENT_ID))
        if lst is None:
            print(f"{CONTENT_ID}: Aufgabe fehlt — nichts geändert")
            return 1
        others = [t.label for t in lst.audio_tracks if t.label not in (ALEX, *OLD_ALEX)]
        if others:
            print(f"Hinweis: weitere Spuren bleiben unverändert: {others}")
        steps = plan(lst)
        print(f"{lst.title} [{CONTENT_ID}] veröffentlicht={lst.is_published}")
        for action, detail in steps or [("ok", "Slots bereits korrekt")]:
            print(f"  {action}: {detail}")
        if args.apply and steps:
            apply(db, lst, steps)
            write_audit(db, None, "a1_l14_audio_slots", details=json.dumps({"task": str(lst.id), "steps": steps}, ensure_ascii=False))
        from app.services.lesson_skills.admin import audio_tracks_admin

        print("  Slots:", [(s["label"], s["file_name"], s["file_status"]) for s in audio_tracks_admin(lst)])
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
