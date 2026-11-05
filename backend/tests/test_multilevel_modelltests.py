"""Multilevel Modelltests 1–10 (app/data/multilevel, app/services/mock_exam/multilevel_service.py): the data files
(1–6 from the PDFs without keys, 7–10 by VIZU with one key per question, same structure and word counts as their
reference variant, Hören empty), super-admin-only endpoints (401/403), and against PostgreSQL (VIZU_WB_TEST_DB_URL)
the idempotent import, the publish guard and the key rules."""

import os
import re
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
WORD = re.compile(r"[0-9A-Za-zÄÖÜäöüß]+(?:[’'\-][0-9A-Za-zÄÖÜäöüß]+)*")
REFERENCE = {7: 1, 8: 2, 9: 3, 10: 4}


def _wc(s):
    return len(WORD.findall(s or ""))


def _docs():
    from app.services.mock_exam.multilevel_service import load_docs

    return {d["number"]: d for d in load_docs()}


class TestMultilevelData(unittest.TestCase):
    def test_ten_tests_numbered(self):
        docs = _docs()
        self.assertEqual(sorted(docs), list(range(1, 11)))
        for n, d in docs.items():
            self.assertEqual(d["title"], f"Modelltest {n}")
            self.assertEqual(d["origin"], "pdf" if n <= 6 else "vizu")

    def test_pdf_tests_have_no_invented_keys(self):
        for n in range(1, 7):
            d = _docs()[n]
            self.assertTrue(d["source_pdf"])
            for k in d["kompetenzen"]:
                for t in k["teile"]:
                    for q in t["questions"]:
                        self.assertFalse(any(o.get("correct") for o in q["options"]), f"MT{n} {q['no']}")

    def test_vizu_tests_marked_keys_and_no_hoeren(self):
        for n in range(7, 11):
            d = _docs()[n]
            self.assertIn("kein offizielles Prüfungsmaterial", d["description"])
            hoeren = [k for k in d["kompetenzen"] if k["type"] == "HOEREN"]
            self.assertEqual(len(hoeren), 1)
            self.assertEqual(hoeren[0]["teile"], [])
            lesen = next(k for k in d["kompetenzen"] if k["type"] == "LESEN")
            numbers = [q["no"] for t in lesen["teile"] for q in t["questions"]]
            self.assertEqual(numbers, [f"A{i}" for i in range(1, 36)])
            for t in lesen["teile"]:
                for q in t["questions"]:
                    self.assertEqual(sum(1 for o in q["options"] if o.get("correct")), 1, f"MT{n} {q['no']}")

    def test_vizu_tests_mirror_reference_structure_and_word_counts(self):
        docs = _docs()
        for n, ref_n in REFERENCE.items():
            new, ref = docs[n], docs[ref_n]
            for kn, kr in zip(new["kompetenzen"], ref["kompetenzen"]):
                self.assertEqual(kn["type"], kr["type"])
                if kn["type"] == "HOEREN":
                    continue
                self.assertEqual([t["title"] for t in kn["teile"]], [t["title"] for t in kr["teile"]])
                for tn, tr in zip(kn["teile"], kr["teile"]):
                    with self.subTest(mt=n, teil=f"{kn['type']} {tn['title']}"):
                        self.assertEqual(len(tn["questions"]), len(tr["questions"]))
                        self.assertEqual([len(q["options"]) for q in tn["questions"]], [len(q["options"]) for q in tr["questions"]])
                        a, b = _wc(tr["text"]), _wc(tn["text"])
                        self.assertLessEqual(abs(a - b), max(2, round(a * 0.01)), f"words {a} → {b}")

    def test_vizu_texts_are_new(self):
        docs = _docs()
        old = {re.sub(r"\s+", " ", t["text"]).strip() for n in range(1, 7) for k in docs[n]["kompetenzen"] for t in k["teile"]
               if _wc(t["text"]) > 40}
        for n in range(7, 11):
            for k in docs[n]["kompetenzen"]:
                for t in k["teile"]:
                    if k["type"] == "LESEN":
                        self.assertNotIn(re.sub(r"\s+", " ", t["text"]).strip(), old)


class TestMultilevelEndpointsAuth(unittest.TestCase):
    def test_http_401_and_403(self):
        try:
            from fastapi.testclient import TestClient
        except Exception:  # httpx missing (server)
            self.skipTest("httpx not installed")
        from types import SimpleNamespace

        from app.api.dependencies.auth import get_current_user
        from app.main import app

        client = TestClient(app)
        some = uuid.uuid4()
        calls = [("get", f"/api/v1/mock-exam/model-tests/{some}/review", None),
                 ("get", f"/api/v1/mock-exam/model-tests/{some}/source-pdf", None),
                 ("put", f"/api/v1/mock-exam/questions/{some}/key", {"option_ids": []}),
                 ("put", f"/api/v1/mock-exam/questions/{some}/text", {"question_text": "x"}),
                 ("put", f"/api/v1/mock-exam/question-options/{some}/text", {"option_text": "x"})]
        for method, url, body in calls:
            self.assertEqual(getattr(client, method)(url, **({"json": body} if body else {})).status_code, 401, url)
        for role in ("ADMIN", "CONTENT_MANAGER", "TEACHER", "STUDENT"):
            app.dependency_overrides[get_current_user] = lambda role=role: SimpleNamespace(id=uuid.uuid4(), role=role)
            try:
                for method, url, body in calls:
                    with self.subTest(role=role, url=url):
                        self.assertEqual(getattr(client, method)(url, **({"json": body} if body else {})).status_code, 403)
            finally:
                app.dependency_overrides.pop(get_current_user, None)


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestMultilevelImport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401
        from app.models.certification_provider import CertificationProvider
        from app.models.mock_exam_level import MockExamLevel
        from app.services.mock_exam import multilevel_service as svc

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        db = cls.Session()
        provider = db.scalar(select(CertificationProvider).where(CertificationProvider.code == svc.PROVIDER_CODE))
        cls.created_provider = provider is None
        if provider is None:
            provider = CertificationProvider(name=f"National test {uuid.uuid4().hex[:6]}", code=svc.PROVIDER_CODE, is_active=True)
            db.add(provider)
            db.commit()
        if db.scalar(select(MockExamLevel).where(MockExamLevel.provider_id == provider.id, MockExamLevel.title == svc.LEVEL_TITLE)):
            db.close()
            raise unittest.SkipTest("the test database already holds the Multilevel level")
        cls.provider_id = provider.id
        db.close()
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.patches = [patch.object(type(svc.SOURCES), "ROOT", root / "sources"),
                       patch.object(svc.LocalStorage, "ROOT", root / "uploads")]
        for p in cls.patches:
            p.start()
        cls.pdf_dir = root / "pdfs"
        cls.pdf_dir.mkdir()
        for n in range(1, 7):
            (cls.pdf_dir / f"Multilevel Mock Variant {n}.pdf").write_bytes(b"%PDF-1.4\n% test " + str(n).encode())

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete

        from app.models.certification_provider import CertificationProvider
        from app.models.mock_exam_level import MockExamLevel
        from app.services.mock_exam import multilevel_service as svc

        with cls.Session() as db:
            for level in db.query(MockExamLevel).filter(MockExamLevel.provider_id == cls.provider_id, MockExamLevel.title == svc.LEVEL_TITLE):
                db.delete(level)
            if cls.created_provider:
                db.execute(delete(CertificationProvider).where(CertificationProvider.id == cls.provider_id))
            db.commit()
        for p in cls.patches:
            p.stop()
        cls.tmp.cleanup()
        cls.engine.dispose()

    def test_import_idempotent_guard_and_keys(self):
        from fastapi import HTTPException
        from sqlalchemy import select

        from app.models.mock_question import MockQuestion
        from app.models.model_test import ModelTest
        from app.models.reading_content import ReadingContent
        from app.models.teil import Teil
        from app.models.kompetenz import Kompetenz
        from app.schemas.mock_exam import ModelTestUpdate
        from app.services.mock_exam import hierarchy_service
        from app.services.mock_exam import multilevel_service as svc

        with self.Session() as db:
            first = svc.plan(db, self.pdf_dir)
            self.assertTrue(first["create_level"])
            self.assertEqual([i["action"] for i in first["items"]], ["create"] * 10)
            with self.assertRaises(RuntimeError):
                svc.apply(db, "wrong", self.pdf_dir)
            result = svc.apply(db, first["plan_id"], self.pdf_dir)
            self.assertEqual(sum(1 for r in result["results"] if r["pdf_stored"]), 6)

        with self.Session() as db:
            again = svc.plan(db, self.pdf_dir)
            self.assertEqual([i["action"] for i in again["items"]], ["skip"] * 10)
            svc.apply(db, again["plan_id"], self.pdf_dir)
            tests = {t.title: t for t in db.scalars(select(ModelTest).where(ModelTest.level_id == result["level_id"]))}
            self.assertEqual(len(tests), 10)
            self.assertTrue(all(t.status == "DRAFT" for t in tests.values()))

            mt1, mt7 = tests["Modelltest 1"], tests["Modelltest 7"]
            info = svc.source_info(db, mt1.id)
            self.assertTrue(info["has_source_pdf"])
            self.assertTrue(info["review"])
            self.assertEqual(info["readiness"]["keys_set"], 0)
            self.assertTrue(svc.source_pdf_path(db, mt1.id).read_bytes().startswith(b"%PDF"))
            with self.assertRaises(HTTPException) as ctx:
                svc.source_pdf_path(db, mt7.id)
            self.assertEqual(ctx.exception.status_code, 404)

            with self.assertRaises(HTTPException) as ctx:
                hierarchy_service.update_model_test(db, mt1.id, ModelTestUpdate(status="PUBLISHED"))
            self.assertEqual(ctx.exception.status_code, 409)
            self.assertTrue(ctx.exception.detail.startswith("MODEL_TEST_NOT_READY"))
            self.assertEqual(hierarchy_service.update_model_test(db, mt7.id, ModelTestUpdate(status="PUBLISHED")).status, "PUBLISHED")

            q = db.scalar(select(MockQuestion).join(ReadingContent, MockQuestion.reading_content_id == ReadingContent.id)
                          .join(Teil, ReadingContent.teil_id == Teil.id).join(Kompetenz, Teil.kompetenz_id == Kompetenz.id)
                          .where(Kompetenz.model_test_id == mt1.id).order_by(Teil.sort_order, MockQuestion.sort_order))
            options = [o.id for o in q.options]
            with self.assertRaises(HTTPException):
                svc.set_question_key(db, q.id, options[:2])
            with self.assertRaises(HTTPException):
                svc.set_question_key(db, q.id, [uuid.uuid4()])
            svc.set_question_key(db, q.id, [options[1]])
            self.assertEqual([o.is_correct for o in db.get(MockQuestion, q.id).options].count(True), 1)
            self.assertEqual(svc.readiness(db, mt1.id)["keys_set"], 1)
            svc.set_question_key(db, q.id, [])
            self.assertEqual(svc.readiness(db, mt1.id)["keys_set"], 0)

            from app.schemas.mock_exam import PublicQuestion

            dumped = PublicQuestion.model_validate(q, from_attributes=True).model_dump()
            self.assertNotIn("is_correct", str(dumped))
            self.assertNotIn("explanation", dumped)
            self.assertTrue(all(set(o) == {"id", "option_text", "sort_order"} for o in dumped["options"]))


if __name__ == "__main__":
    unittest.main()
