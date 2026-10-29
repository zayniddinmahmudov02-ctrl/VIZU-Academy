"""A2 sales readiness: what is true in the system today, and the checks a
person has to confirm (a payment test, access after purchase, mobile and
desktop, test run). Admin -> Media Management -> A2 Audio Manager.

Status, first that applies:
  NEEDS_CONFIGURATION  price / offer, course or lessons are not set up
  NEEDS_CONTENT        description, audio manifest, Hören audio, verification or links are missing
  NEEDS_TESTING        everything above is fine, a manual check is still open
  READY                all checks pass

Nothing here switches sales on: the "Verkauf" switch in Admin -> Angebote
stays a separate decision (and needs a price, see offers.validate_overrides).
A course without its real audio files is never "READY". Automatic checks
are recomputed on every request; manual checks are stored in app_settings
(key a2_sales_readiness) with who confirmed them and when."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.app_setting import AppSetting
from app.models.user import User
from app.services.a2_audio import assets as a2_assets
from app.services.lesson_skills import exercises as skill_exercises
from app.services.lms import structure as lms_structure
from app.services.vizu_pay import offers as offer_config

SETTINGS_KEY = "a2_sales_readiness"
LEVEL = "A2"

CONFIGURATION, CONTENT, TESTING = "configuration", "content", "testing"
MANUAL_CHECKS = {
    "payment_tested": "Zahlung im Test-/Sandbox-Ablauf geprüft (Bestellung, Freigabe, Ablehnung)",
    "access_tested": "Zugriff nach dem Kauf geprüft (gekauft: offen · nicht gekauft: gesperrt)",
    "responsive_tested": "Kursseite und Lektionen auf Handy und Desktop geprüft",
    "tests_passed": "Automatische Tests bestanden (docs/audit/test-results.md)",
}


def _check(key: str, group: str, ok: bool, label: str, detail: str | None = None, items: list | None = None) -> dict:
    return {"key": key, "group": group, "ok": ok, "label": label, "detail": detail, "items": items or []}


def _manual_state(db: Session) -> dict:
    row = db.scalar(select(AppSetting).where(AppSetting.key == SETTINGS_KEY))
    return dict(row.value or {}) if row else {}


def confirm(db: Session, actor: User, key: str, done: bool, note: str | None) -> dict:
    if key not in MANUAL_CHECKS:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail=f"UNKNOWN_CHECK: {', '.join(MANUAL_CHECKS)}")
    row = db.scalar(select(AppSetting).where(AppSetting.key == SETTINGS_KEY))
    if row is None:
        row = AppSetting(key=SETTINGS_KEY, value={})
        db.add(row)
    value = dict(row.value or {})
    value[key] = {"done": bool(done), "note": (note or "").strip()[:500] or None, "by": str(actor.id),
                  "by_name": " ".join(p for p in (actor.first_name, actor.last_name) if p) or actor.username,
                  "at": datetime.now(timezone.utc).isoformat()}
    row.value, row.updated_by = value, actor.id
    db.commit()
    return compute(db)


def compute(db: Session) -> dict:
    checks: list[dict] = []
    course = lms_structure.level_course(db, LEVEL)
    module = lms_structure.main_module(db, course) if course else None
    lessons = lms_structure.level_lessons(db, module)

    # --- configuration ---
    offer = offer_config.offer(offer_config.OFFER_A2) or {}
    priced = bool(offer.get("active") and offer.get("sale_price"))
    checks.append(_check("price", CONFIGURATION, priced, "Preis festgelegt (Angebote, eine Quelle für Frontend und Backend)",
                         f"{offer.get('sale_price')} UZS (statt {offer.get('original_price')}), aktiv: {offer.get('active')}" if offer else "kein Angebot"))
    published = [lesson for lesson in lessons if lesson.is_published]
    first_open = bool(lessons) and lessons[0].is_published
    checks.append(_check("lessons", CONFIGURATION, bool(course and course.is_active and published and first_open),
                         "Kurs und Lektionen eingerichtet (Kurs aktiv, Lektion 1 als kostenlose Vorschau veröffentlicht)",
                         f"{len(published)} von {len(lessons)} Lektionen veröffentlicht" if course else "A2-Kurs fehlt",
                         [f"{lesson.number}. {lesson.title}" for lesson in lessons if not lesson.is_published]))

    # --- content ---
    checks.append(_check("description", CONTENT, bool(course and (course.description or "").strip()), "Kursbeschreibung vorhanden",
                         None if course and (course.description or "").strip() else "Admin -> Kurse: Beschreibung des A2-Kurses ausfüllen"))
    manifest = a2_assets.manifest(db)
    counts = manifest["counts"]
    checks.append(_check("manifest", CONTENT, counts["files"] > 0, "Audio-Manifest erstellt (echte Dateien im A2 Audio Manager)",
                         f"{counts['files']} Datei(en) in der Bibliothek"))
    missing = manifest["missing_audio"]
    checks.append(_check("audio_complete", CONTENT, counts["tasks"] > 0 and not missing, "Keine fehlenden Pflicht-Audios (jede Hören-Aufgabe hat Audio)",
                         f"{counts['tasks_with_audio']} von {counts['tasks']} Hören-Aufgaben mit Audio",
                         [f"{r['lesson_number']}. Unterricht · {r['title']}" for r in missing]))
    assets = [a for lesson in manifest["lessons"] for a in lesson["assets"]] + manifest["unassigned"]
    unverified = [a for a in assets if a["linked"] and a["verification"] != "verified"]
    problems = [a for a in assets if a["verification"] == "problem" or a["file_status"] != "ok"]
    checks.append(_check("audio_verified", CONTENT, counts["linked"] > 0 and not unverified and not problems,
                         "Verknüpfte Audios angehört und geprüft", f"{counts['verified']} geprüft · {counts['pending']} offen · {counts['problem']} Problem",
                         [f"{a['original_filename']}: {'Problem — ' + (a['verification_note'] or '') if a['verification'] == 'problem' else ('Datei fehlt' if a['file_status'] != 'ok' else 'noch nicht geprüft')}"
                          for a in unverified + [p for p in problems if p not in unverified]]))
    bad_links = [a for a in assets if a["linked"] and (not a["linked"]["in_sync"] or a["link_mismatch"])]
    checks.append(_check("links", CONTENT, counts["linked"] > 0 and not bad_links, "Zuordnungen Audio ↔ Lektion stimmen",
                         f"{counts['linked']} verknüpft · {counts['unlinked']} nicht verknüpft",
                         [f"{a['original_filename']}: {'Aufgabe spielt eine andere Datei' if not a['linked']['in_sync'] else 'Unterricht passt nicht zur Lektion'}"
                          for a in bad_links]))

    # --- content gaps per lesson (what an admin still has to fill in) ---
    gaps = []
    for t, lesson in a2_assets.a2_tasks(db, lessons):
        without_key = sum(1 for q in t.questions if not skill_exercises.has_key(q))
        if without_key:
            gaps.append(f"{lesson.number}. Unterricht · {t.title}: {without_key} Antwortschlüssel fehlen (Aufgabe bleibt Entwurf)")

    # --- manual ---
    state = _manual_state(db)
    for key, label in MANUAL_CHECKS.items():
        entry = state.get(key) or {}
        detail = f"bestätigt von {entry.get('by_name')} am {entry.get('at', '')[:10]}" + (f" — {entry['note']}" if entry.get("note") else "") \
            if entry.get("done") else "offen"
        checks.append({**_check(key, TESTING, bool(entry.get("done")), label, detail), "manual": True})

    failed = {c["group"] for c in checks if not c["ok"]}
    status = ("NEEDS_CONFIGURATION" if CONFIGURATION in failed else "NEEDS_CONTENT" if CONTENT in failed
              else "NEEDS_TESTING" if TESTING in failed else "READY")
    return {"level": LEVEL, "status": status, "sales_enabled": offer_config.level_sales_enabled(LEVEL),
            "checks": checks, "content_gaps": gaps, "missing_audio": missing, "counts": counts}
