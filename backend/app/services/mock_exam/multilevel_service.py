"""Multilevel Modelltests (provider NATIONAL, level "Multilevel B1–C1"): import, readiness, answer keys, source PDF.

Data: app/data/multilevel/modelltest-NN.json, built by app/scripts/multilevel_build.py. 1–6 are copied verbatim from
the owner's PDFs (no answer keys: the PDFs have none), 7–10 are written by VIZU (keys included, Hören empty).

Rules:
- import is idempotent and additive: a level or Modelltest that already exists (same provider / title) is never
  changed or deleted; only missing ones are created, always as DRAFT. A missing source PDF / check-list file of an
  existing test is (re)attached.
- source PDFs and the check-list live in private storage (ProtectedMockExamSourceStorage), only for super admins.
- a Modelltest can only be PUBLISHED when every option-based question has a key and every Hören Teil has audio
  (`readiness`, enforced in hierarchy_service.update_model_test). A Kompetenz without Teile (Hören of 7–10) is shown
  as "Noch nicht verfügbar".
"""

import hashlib
import json
import shutil
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.storage.local import LocalStorage
from app.core.storage.protected_local import ProtectedMockExamSourceStorage
from app.models.certification_provider import CertificationProvider
from app.models.kompetenz import Kompetenz
from app.models.listening_content import ListeningContent
from app.models.mock_exam_level import MockExamLevel
from app.models.mock_question import OPTION_BASED_TYPES, TYPE_MULTIPLE_CHOICE, MockQuestion
from app.models.mock_question_option import MockQuestionOption
from app.models.model_test import STATUS_DRAFT, ModelTest
from app.models.reading_content import CONTENT_TEXT, ReadingContent
from app.models.speaking_task import SpeakingTask
from app.models.teil import Teil
from app.models.writing_task import WritingTask

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "multilevel"
PROVIDER_CODE = "NATIONAL"
LEVEL_CODE = "B1–C1"
LEVEL_TITLE = "Multilevel B1–C1"
LEVEL_DESCRIPTION = "Multilevel Modelltests 1–10: 1–6 aus den PDF-Vorlagen, 7–10 von VIZU erstellt (Übungstests)."
IMAGE_DIR = "images/mock-exams/multilevel"
NOT_AVAILABLE = "Noch nicht verfügbar"
QUESTION_TYPES = {"ORDERING": "ORDERING", "MATCHING": "MATCHING", "TRUE_FALSE": "TRUE_FALSE", "TF": "TRUE_FALSE"}
SOURCES = ProtectedMockExamSourceStorage()


def _src(name: str) -> Path:
    return SOURCES._inside_root(name)


# ============================================================
# Data files
# ============================================================


def load_docs(data_dir: Path = DATA_DIR) -> list[dict]:
    docs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(data_dir.glob("modelltest-*.json"))]
    numbers = [d["number"] for d in docs]
    if len(set(numbers)) != len(numbers):
        raise RuntimeError(f"duplicate Modelltest numbers in {data_dir}: {numbers}")
    return docs


def _question_text(q: dict) -> str:
    text = (q.get("text") or "").strip()
    return q["no"] if not text or text == q["no"] else f"{q['no']}. {text}"


def _doc_counts(doc: dict) -> dict:
    out = {}
    for k in doc["kompetenzen"]:
        out[k["type"]] = {"teile": len(k["teile"]), "questions": sum(len(t["questions"]) for t in k["teile"]),
                          "keys": sum(1 for t in k["teile"] for q in t["questions"] if any(o.get("correct") for o in q["options"]))}
    return out


# ============================================================
# Plan / apply
# ============================================================


def _level(db: Session, provider: CertificationProvider) -> MockExamLevel | None:
    return db.scalar(select(MockExamLevel).where(MockExamLevel.provider_id == provider.id, MockExamLevel.title == LEVEL_TITLE))


def _existing_tests(db: Session, level: MockExamLevel | None) -> dict[str, ModelTest]:
    if level is None:
        return {}
    return {t.title: t for t in db.scalars(select(ModelTest).where(ModelTest.level_id == level.id))}


def plan(db: Session, pdf_dir: Path | None = None, data_dir: Path = DATA_DIR) -> dict:
    provider = db.scalar(select(CertificationProvider).where(CertificationProvider.code == PROVIDER_CODE))
    if provider is None:
        raise RuntimeError(f"provider {PROVIDER_CODE} not found — nothing was changed")
    level = _level(db, provider)
    existing = _existing_tests(db, level)
    items = []
    for doc in load_docs(data_dir):
        test = existing.get(doc["title"])
        pdf = (pdf_dir / doc["source_pdf"]) if (pdf_dir and doc.get("source_pdf")) else None
        pdf_ok = bool(pdf and pdf.is_file())
        item = {"number": doc["number"], "title": doc["title"], "origin": doc["origin"], "counts": _doc_counts(doc),
                "review": len(doc.get("review", [])), "source_pdf": doc.get("source_pdf"),
                "pdf_found": pdf_ok, "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest() if pdf_ok else None,
                "doc_sha256": hashlib.sha256(json.dumps(doc, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}
        if test is None:
            item["action"] = "create"
        else:
            item["model_test_id"] = str(test.id)
            missing_pdf = bool(doc.get("source_pdf")) and not _src(f"{test.id}.pdf").is_file()
            missing_meta = not _src(f"{test.id}.json").is_file()
            item["action"] = "attach" if ((missing_pdf and pdf_ok) or missing_meta) else "skip"
        if doc.get("source_pdf") and not pdf_ok and item["action"] != "skip":
            item["warning"] = "source PDF not found — the test is imported without it"
        items.append(item)
    state = {"provider": str(provider.id), "level": str(level.id) if level else None,
             "items": [{k: i.get(k) for k in ("number", "action", "doc_sha256", "pdf_sha256", "model_test_id")} for i in items]}
    plan_id = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()[:12]
    return {"plan_id": plan_id, "provider": provider.name, "level": LEVEL_TITLE, "create_level": level is None, "items": items}


def _store_sources(test: ModelTest, doc: dict, pdf_dir: Path | None) -> bool:
    pdf_stored = False
    if doc.get("source_pdf") and pdf_dir and (pdf_dir / doc["source_pdf"]).is_file():
        target = _src(f"{test.id}.pdf")
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file():
            shutil.copyfile(pdf_dir / doc["source_pdf"], target)
        pdf_stored = True
    meta = {"content_id": doc["content_id"], "number": doc["number"], "origin": doc["origin"],
            "source_pdf": doc.get("source_pdf"), "review": doc.get("review", [])}
    meta_path = _src(f"{test.id}.json")
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    if not meta_path.is_file():
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return pdf_stored


def _copy_image(name: str | None, data_dir: Path) -> str | None:
    if not name:
        return None
    src = data_dir / "images" / name
    if not src.is_file():
        raise RuntimeError(f"image {name} missing in {data_dir / 'images'} — nothing was changed")
    target = LocalStorage.ROOT / IMAGE_DIR / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file():
        shutil.copyfile(src, target)
    return f"/uploads/{IMAGE_DIR}/{name}"


def _add_questions(db: Session, teil_doc: dict, *, reading_id=None, listening_id=None) -> None:
    for i, q in enumerate(teil_doc["questions"], start=1):
        question = MockQuestion(reading_content_id=reading_id, listening_content_id=listening_id,
                                question_type=QUESTION_TYPES.get(q["type"], "SINGLE_CHOICE"), question_text=_question_text(q),
                                points=1, sort_order=i)
        db.add(question)
        db.flush()
        for j, o in enumerate(q["options"], start=1):
            if len(o["text"]) > 1000:
                raise RuntimeError(f"option text too long in {q['no']} — nothing was changed")
            db.add(MockQuestionOption(question_id=question.id, option_text=o["text"], is_correct=o.get("correct") is True, sort_order=j))


def _create_test(db: Session, level: MockExamLevel, doc: dict, data_dir: Path) -> ModelTest:
    test = ModelTest(level_id=level.id, title=doc["title"], description=doc["description"], status=STATUS_DRAFT, sort_order=doc["number"])
    db.add(test)
    db.flush()
    for ks, k in enumerate(doc["kompetenzen"], start=1):
        empty = not k["teile"]
        komp = Kompetenz(model_test_id=test.id, type=k["type"], title=k["title"], description=NOT_AVAILABLE if empty else None,
                         total_points=k["total_points"], duration_minutes=0 if empty else k["duration_minutes"], sort_order=ks)
        db.add(komp)
        db.flush()
        for ts, t in enumerate(k["teile"], start=1):
            description = "Gleiche Situation wie in Teil 1.1." if t.get("same_situation") else None
            if k["type"] == "HOEREN" and t.get("text"):
                description = t["text"]
            teil = Teil(kompetenz_id=komp.id, title=t["title"], instructions=t.get("instructions") or None, description=description,
                        points=len(t["questions"]), sort_order=ts)
            db.add(teil)
            db.flush()
            if k["type"] == "LESEN":
                rc = ReadingContent(teil_id=teil.id, content_type=CONTENT_TEXT, text=t.get("text") or "")
                db.add(rc)
                db.flush()
                _add_questions(db, t, reading_id=rc.id)
            elif k["type"] == "HOEREN":
                lc = ListeningContent(teil_id=teil.id, audio_url="", transcript=None)
                db.add(lc)
                db.flush()
                _add_questions(db, t, listening_id=lc.id)
            elif k["type"] == "SCHREIBEN":
                db.add(WritingTask(teil_id=teil.id, task_text=t.get("text") or "", word_limit=t.get("words"), points=0))
            elif k["type"] == "SPRECHEN":
                db.add(SpeakingTask(teil_id=teil.id, task_text=t.get("text") or "", image_url=_copy_image(t.get("image"), data_dir)))
    return test


def apply(db: Session, confirm: str, pdf_dir: Path | None = None, data_dir: Path = DATA_DIR) -> dict:
    current = plan(db, pdf_dir, data_dir)
    if confirm != current["plan_id"]:
        raise RuntimeError(f"plan changed or wrong id: current plan id is {current['plan_id']} — nothing was changed")
    provider = db.scalar(select(CertificationProvider).where(CertificationProvider.code == PROVIDER_CODE))
    level = _level(db, provider)
    if level is None:
        top = db.scalar(select(func.max(MockExamLevel.sort_order)).where(MockExamLevel.provider_id == provider.id)) or 0
        level = MockExamLevel(provider_id=provider.id, level=LEVEL_CODE, title=LEVEL_TITLE, description=LEVEL_DESCRIPTION,
                              sort_order=top + 1, is_active=True)
        db.add(level)
        db.flush()
    docs = {d["number"]: d for d in load_docs(data_dir)}
    existing = _existing_tests(db, level)
    result = []
    try:
        for item in current["items"]:
            doc = docs[item["number"]]
            if item["action"] == "create":
                test = _create_test(db, level, doc, data_dir)
            elif item["action"] == "attach":
                test = existing[doc["title"]]
            else:
                result.append({"number": item["number"], "action": "skip", "model_test_id": item["model_test_id"]})
                continue
            db.flush()
            pdf = _store_sources(test, doc, pdf_dir)
            result.append({"number": item["number"], "action": item["action"], "model_test_id": str(test.id), "pdf_stored": pdf})
        db.commit()
    except Exception:
        db.rollback()
        raise
    write_audit(db, actor_id=None, action="mock_exam_multilevel_import",
                details=f"plan={current['plan_id']}; level={LEVEL_TITLE}; " + ", ".join(f"MT{r['number']}={r['action']}" for r in result))
    return {"plan_id": current["plan_id"], "level_id": str(level.id), "results": result}


# ============================================================
# Admin: readiness, keys, source PDF / check-list
# ============================================================


def _test_questions(db: Session, model_test_id: UUID):
    reading = (select(MockQuestion, Teil, Kompetenz).join(ReadingContent, MockQuestion.reading_content_id == ReadingContent.id)
               .join(Teil, ReadingContent.teil_id == Teil.id).join(Kompetenz, Teil.kompetenz_id == Kompetenz.id)
               .where(Kompetenz.model_test_id == model_test_id))
    listening = (select(MockQuestion, Teil, Kompetenz).join(ListeningContent, MockQuestion.listening_content_id == ListeningContent.id)
                 .join(Teil, ListeningContent.teil_id == Teil.id).join(Kompetenz, Teil.kompetenz_id == Kompetenz.id)
                 .where(Kompetenz.model_test_id == model_test_id))
    return list(db.execute(reading).all()) + list(db.execute(listening).all())


def readiness(db: Session, model_test_id: UUID) -> dict:
    """What still blocks publishing: option-based questions without a marked key, Hören Teile without audio."""
    missing_keys = []
    total = 0
    for question, teil, komp in _test_questions(db, model_test_id):
        if question.question_type not in OPTION_BASED_TYPES:
            continue
        total += 1
        if not any(o.is_correct for o in question.options):
            missing_keys.append(f"{komp.title} {teil.title}: {question.question_text.split('.', 1)[0][:20]}")
    missing_audio = [f"{komp.title} {teil.title}" for lc, teil, komp in db.execute(
        select(ListeningContent, Teil, Kompetenz).join(Teil, ListeningContent.teil_id == Teil.id)
        .join(Kompetenz, Teil.kompetenz_id == Kompetenz.id).where(Kompetenz.model_test_id == model_test_id)
        .order_by(Kompetenz.sort_order, Teil.sort_order)).all() if not (lc.audio_url or "").strip()]
    return {"questions": total, "keys_set": total - len(missing_keys), "missing_keys": missing_keys,
            "missing_audio": missing_audio, "ready": not missing_keys and not missing_audio}


def assert_publishable(db: Session, model_test_id: UUID) -> None:
    r = readiness(db, model_test_id)
    if not r["ready"]:
        parts = []
        if r["missing_keys"]:
            parts.append(f"{len(r['missing_keys'])} Fragen ohne Lösung")
        if r["missing_audio"]:
            parts.append(f"{len(r['missing_audio'])} Hören-Teile ohne Audio")
        raise HTTPException(status_code=409, detail="MODEL_TEST_NOT_READY: " + ", ".join(parts))


def set_question_key(db: Session, question_id: UUID, option_ids: list[UUID]) -> MockQuestion:
    question = db.get(MockQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="QUESTION_NOT_FOUND")
    if question.question_type not in OPTION_BASED_TYPES:
        raise HTTPException(status_code=422, detail="QUESTION_HAS_NO_OPTIONS")
    wanted = set(option_ids)
    own = {o.id for o in question.options}
    if not wanted <= own:
        raise HTTPException(status_code=422, detail="OPTION_NOT_IN_QUESTION")
    if len(wanted) > 1 and question.question_type != TYPE_MULTIPLE_CHOICE:
        raise HTTPException(status_code=422, detail="ONLY_ONE_CORRECT_OPTION")
    for o in question.options:
        o.is_correct = o.id in wanted
    db.commit()
    db.refresh(question)
    return question


def source_info(db: Session, model_test_id: UUID) -> dict:
    if db.get(ModelTest, model_test_id) is None:
        raise HTTPException(status_code=404, detail="MODEL_TEST_NOT_FOUND")
    meta_path = _src(f"{model_test_id}.json")
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
    return {"has_source_pdf": _src(f"{model_test_id}.pdf").is_file(), "source_pdf_name": meta.get("source_pdf"),
            "origin": meta.get("origin"), "review": meta.get("review", []), "readiness": readiness(db, model_test_id)}


def source_pdf_path(db: Session, model_test_id: UUID) -> Path:
    if db.get(ModelTest, model_test_id) is None:
        raise HTTPException(status_code=404, detail="MODEL_TEST_NOT_FOUND")
    path = _src(f"{model_test_id}.pdf")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="SOURCE_PDF_NOT_FOUND")
    return path
