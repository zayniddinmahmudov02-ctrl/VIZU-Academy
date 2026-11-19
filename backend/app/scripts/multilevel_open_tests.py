"""Multilevel Modelltest 1–6 for every student (owner, 2026-11-18): publish them and link a Hören audio that was uploaded for one of them.
Default is the read-only plan.

    python -m app.scripts.multilevel_open_tests plan
    python -m app.scripts.multilevel_open_tests apply --confirm <plan id>

plan (nothing is written): for each of Modelltest 1–6 the status, the answer keys per section (a question without a key is only counted — it is
not scored, see multilevel_exam_service._grade_auto), the Hören audio, structural gaps, and the action: PUBLISH (DRAFT, all four sections with
content), KEEP (already published) or BLOCKED (a section without Teile / questions — never published). Missing keys / audio are warnings only
(multilevel_service.OPEN_TEST_NUMBERS); they are never filled in — no answer is guessed.
Audio: an uploaded ORIGINAL audio file that nothing uses and whose file name names a variant and Hören ("Variant 1 Hören….m4a") belongs to the
Modelltest made from that variant's PDF ("Multilevel Mock Variant 1.pdf", the test's source PDF name). Only an unambiguous case is linked:
a Modelltest in shared-audio mode (Modelltest 1: one audio for the whole Hören section) without audio → LINK_SHARED. For a test with one audio
per Teil a whole-section file cannot be cut without the right cut points → MANUAL (reported, not linked). Two files for one test → AMBIGUOUS.
apply: exactly what the current plan says (refused when the plan changed), the link first, then the status; audit entries. Take a DB backup
before apply. Modelltest 7–10, questions, keys, Teile, PDFs and attempts are never touched."""

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.db.session import SessionLocal
from app.models.audio_file import KIND_ORIGINAL, AudioFile
from app.models.kompetenz import Kompetenz
from app.models.listening_content import ListeningContent
from app.models.model_test import STATUS_DRAFT, STATUS_PUBLISHED, ModelTest
from app.services.mock_exam import multilevel_exam_service as exam
from app.services.mock_exam import multilevel_keys as keys
from app.services.mock_exam import multilevel_service as ml

VARIANT = re.compile(r"variant\D{0,3}(\d{1,2})", re.IGNORECASE)
HOEREN = re.compile(r"h(?:ö|o|oe)ren", re.IGNORECASE)


def _tests(db: Session) -> dict[int, ModelTest]:
    ids = exam._multilevel_level_ids(db)
    rows = db.scalars(select(ModelTest).where(ModelTest.level_id.in_(ids)).order_by(ModelTest.sort_order)) if ids else []
    return {t.sort_order: t for t in rows if t.sort_order in ml.OPEN_TEST_NUMBERS}


def _variant_of_test(db: Session, test: ModelTest) -> int | None:
    name = ml.source_info(db, test.id).get("source_pdf_name") or ""
    m = VARIANT.search(name)
    return int(m.group(1)) if m else None


def _unused_hoeren_audio(db: Session) -> list[tuple[AudioFile, int]]:
    """ORIGINAL files nobody plays, named "… Variant N … Hören …" → (file, N)."""
    used = set(db.scalars(select(ListeningContent.audio_file_id).where(ListeningContent.audio_file_id.is_not(None))))
    used |= set(db.scalars(select(Kompetenz.audio_file_id).where(Kompetenz.audio_file_id.is_not(None))))
    out = []
    for a in db.scalars(select(AudioFile).where(AudioFile.kind == KIND_ORIGINAL, AudioFile.deleted_at.is_(None)).order_by(AudioFile.created_at)):
        name = unicodedata.normalize("NFC", a.original_name or "")  # uploads may carry "ö" decomposed (o + U+0308)
        m = VARIANT.search(name)
        if a.id in used or not m or not HOEREN.search(name):
            continue
        # a trimmed copy of it that is in use counts as "in use" as well
        if set(db.scalars(select(AudioFile.id).where(AudioFile.source_id == a.id))) & used:
            continue
        out.append((a, int(m.group(1))))
    return out


def build_plan(db: Session) -> dict:
    tests = _tests(db)
    by_variant = {}
    for number, test in tests.items():
        by_variant[_variant_of_test(db, test) or number] = test
    audio_items = []
    candidates = _unused_hoeren_audio(db)
    for audio, variant in candidates:
        test = by_variant.get(variant)
        item = {"audio_id": str(audio.id), "file": audio.original_name, "seconds": (audio.duration_ms or 0) // 1000, "variant": variant,
                "model_test_id": str(test.id) if test else None, "number": test.sort_order if test else None}
        same = [v for _, v in candidates if v == variant]
        if test is None:
            audio_items.append({**item, "action": "NO_TEST"})
        elif len(same) > 1:
            audio_items.append({**item, "action": "AMBIGUOUS"})
        elif ml.shared_audio_test(test):
            komp = db.scalar(select(Kompetenz).where(Kompetenz.model_test_id == test.id, Kompetenz.type == "HOEREN"))
            has = komp is not None and komp.audio_file is not None and komp.audio_file.deleted_at is None
            audio_items.append({**item, "kompetenz_id": str(komp.id) if komp else None, "action": "SKIP_HAS_AUDIO" if has else "LINK_SHARED" if komp else "NO_TEST"})
        else:
            audio_items.append({**item, "action": "MANUAL"})
    linking = {a["number"] for a in audio_items if a["action"] == "LINK_SHARED"}
    items = []
    for number, test in sorted(tests.items()):
        r = ml.readiness(db, test.id)
        sections = {s: keys.key_table(db, test.id, s) for s in ("LESEN", "HOEREN")}
        audio_missing = len(r["missing_audio"]) if number not in linking else 0
        action = "KEEP" if test.status == STATUS_PUBLISHED else "BLOCKED" if r["missing_sections"] else "PUBLISH" if test.status == STATUS_DRAFT else "SKIP_STATUS"
        items.append({"number": number, "model_test_id": str(test.id), "status": test.status, "action": action,
                      "keys": {s: [t["keys_set"], t["question_count"]] for s, t in sections.items()},
                      "audio_missing": audio_missing, "gaps": r["missing_sections"]})
    state = {"items": [{k: i[k] for k in ("number", "model_test_id", "status", "action")} for i in items],
             "audio": [{k: a.get(k) for k in ("audio_id", "model_test_id", "action")} for a in audio_items]}
    return {"plan_id": hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()[:12], "items": items, "audio": audio_items}


def apply_plan(db: Session, confirm: str) -> dict:
    plan = build_plan(db)
    if confirm != plan["plan_id"]:
        raise RuntimeError(f"plan changed or wrong id: current plan id is {plan['plan_id']} — nothing was changed")
    linked, published = [], []
    for a in plan["audio"]:
        if a["action"] != "LINK_SHARED":
            continue
        komp = db.get(Kompetenz, UUID(a["kompetenz_id"]))
        komp.audio_file_id = UUID(a["audio_id"])
        linked.append(a)
    db.flush()
    for i in plan["items"]:
        if i["action"] != "PUBLISH":
            continue
        test = db.get(ModelTest, UUID(i["model_test_id"]))
        if not ml.readiness(db, test.id)["publishable"]:
            db.rollback()
            raise RuntimeError(f"MT{i['number']} is not publishable any more — nothing was changed")
        test.status = STATUS_PUBLISHED
        published.append(i)
    db.commit()
    for a in linked:
        write_audit(db, actor_id=None, action="multilevel_audio_shared_set",
                    details=f"test={a['model_test_id']} audio={a['audio_id']} (script multilevel_open_tests, file \"{a['file']}\" = Variant {a['variant']})")
    for i in published:
        write_audit(db, actor_id=None, action="multilevel_open_publish",
                    details=f"plan={plan['plan_id']}; Modelltest {i['number']} PUBLISHED (free for every student); Lesen keys {i['keys']['LESEN'][0]}/{i['keys']['LESEN'][1]}, "
                            f"Hören keys {i['keys']['HOEREN'][0]}/{i['keys']['HOEREN'][1]}, Hören Teile without audio {i['audio_missing']}")
    return {"plan_id": plan["plan_id"], "linked": [f"MT{a['number']} ← {a['file']}" for a in linked],
            "published": [f"MT{i['number']}" for i in published], "kept": [f"MT{i['number']}" for i in plan["items"] if i["action"] == "KEEP"],
            "blocked": [f"MT{i['number']}: {'; '.join(i['gaps'])}" for i in plan["items"] if i["action"] == "BLOCKED"]}


def _print_plan(plan: dict) -> None:
    print(f"Multilevel Modelltest 1–6 open for every student — plan id {plan['plan_id']}")
    for i in plan["items"]:
        warn = []
        for s, (have, total) in i["keys"].items():
            if have < total:
                warn.append(f"{total - have} {s} questions without a key (not scored)")
        if i["audio_missing"]:
            warn.append(f"{i['audio_missing']} Hören Teile without audio")
        print(f"  {i['action']:8} MT{i['number']} ({i['status']}): keys Lesen {i['keys']['LESEN'][0]}/{i['keys']['LESEN'][1]}, Hören {i['keys']['HOEREN'][0]}/{i['keys']['HOEREN'][1]}"
              + (f" — warnings: {'; '.join(warn)}" if warn else "") + (f" — BLOCKED: {'; '.join(i['gaps'])}" if i["gaps"] else ""))
    print("  audio:" + ("" if plan["audio"] else " no unused Hören upload named after a variant"))
    for a in plan["audio"]:
        print(f"    {a['action']:14} \"{a['file']}\" ({a['seconds'] // 60}:{a['seconds'] % 60:02d}) Variant {a['variant']} → MT{a['number']}")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="stage")
    sub.add_parser("plan")
    a = sub.add_parser("apply")
    a.add_argument("--confirm", required=True)
    args = parser.parse_args()
    try:
        with SessionLocal() as db:
            if (args.stage or "plan") == "plan":
                _print_plan(build_plan(db))
                print("READ-ONLY: nothing was changed.")
            else:
                print(json.dumps(apply_plan(db, args.confirm), ensure_ascii=False, indent=1))
    except RuntimeError as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
