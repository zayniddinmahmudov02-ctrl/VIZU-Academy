"""Multilevel Modelltest 1–6: the owner's Hören answer keys, the key tool (table / import / edit / validation) and the exam times.

Pure (no database): the text parser, the letter → option rules, and the six key lists of the owner checked against the real Modelltest data files
(35 answers for Modelltest 1, 30 for 2–6; every letter valid for its question type).
Against PostgreSQL (VIZU_WB_TEST_DB_URL): the real ten Modelltests are built, the script plan / apply sets exactly the six Hören key sets (tokens keep their
case, other tests and Lesen untouched, idempotent, conflict refused), the editing / import rules, per-test server scoring (35 and 30 questions), the exam
times 60 / 60 / 60 / 15 = 195, a timer that survives a refresh, the automatic close at the deadline, and 401 / 403 on the new routes."""

import json
import os
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from fastapi import HTTPException

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
DATA = Path(__file__).resolve().parents[1] / "app" / "data" / "multilevel"
EXPECTED_COUNTS = {1: 35, 2: 30, 3: 30, 4: 30, 5: 30, 6: 30}


def _fake(question_type: str, options: list[str], correct: int | None = None, token: str | None = None):
    return NS(question_type=question_type, options=[NS(option_text=t, is_correct=i == correct) for i, t in enumerate(options)], answer_key=token,
              question_text="A1. Text")


class TestParserAndRules(unittest.TestCase):
    def setUp(self):
        from app.services.mock_exam import multilevel_keys

        self.k = multilevel_keys

    def test_parse_formats_and_case(self):
        e, errors = self.k.parse_text("1-b, 2-B; 3:r\n4) F 5 = a  6 – c")
        self.assertEqual((e, errors), ({1: "b", 2: "B", 3: "r", 4: "F", 5: "a", 6: "c"}, []))  # the token keeps its case
        e, errors = self.k.parse_text("1-b, 1-c, 2-bb, x, 3-")
        self.assertEqual(e, {1: "b"})
        codes = sorted(x["code"] for x in errors)
        self.assertEqual(codes, ["DUPLICATE", "UNREADABLE", "UNREADABLE", "UNREADABLE"])
        self.assertEqual(self.k.parse_text("")[0], {})

    def test_letter_to_option(self):
        sc = _fake("SINGLE_CHOICE", ["x", "y", "z"])
        self.assertEqual([self.k._option_index(sc, t) for t in "aBc"], [0, 1, 2])
        for bad in ("d", "1", "", "ab", "r"):
            with self.assertRaises(KeyError):
                self.k._option_index(sc, bad)
        tf = _fake("TRUE_FALSE", ["Richtig", "Falsch"])
        self.assertEqual([self.k._option_index(tf, t) for t in ("r", "R", "f", "F", "a", "b")], [0, 0, 1, 1, 0, 1])
        with self.assertRaises(KeyError):
            self.k._option_index(tf, "c")
        mt = _fake("MATCHING", list("ABCDEFGH"))
        self.assertEqual((self.k._option_index(mt, "h"), self.k._option_index(mt, "A")), (7, 0))
        with self.assertRaises(KeyError):
            self.k._option_index(_fake("MULTIPLE_CHOICE", ["a", "b"]), "a")  # one correct option only

    def test_canonical_and_effective_key(self):
        tf = _fake("TRUE_FALSE", ["Richtig", "Falsch"], correct=1, token="f")
        self.assertEqual((self.k.canonical_key(tf), self.k.effective_key(tf)), ("F", ("f", "entered")))  # the typed token wins while it still fits
        tf.answer_key = "r"  # another editor moved the flag: the stale token is ignored
        self.assertEqual(self.k.effective_key(tf), ("F", "derived"))
        self.assertEqual(self.k.effective_key(_fake("SINGLE_CHOICE", ["a", "b", "c"])), (None, None))
        two = _fake("SINGLE_CHOICE", ["a", "b"], correct=0)
        two.options[1].is_correct = True
        self.assertIsNone(self.k.canonical_key(two))


class TestOwnerKeyLists(unittest.TestCase):
    """The six lists against the real data files — no database."""

    def rows(self, number: int):
        doc = json.loads((DATA / f"modelltest-{number:02d}.json").read_text(encoding="utf-8"))
        hoeren = next(k for k in doc["kompetenzen"] if k["type"] == "HOEREN")
        return [(_fake({"TF": "TRUE_FALSE"}.get(q["type"], q["type"]), [o["text"] for o in q["options"]]), None) for t in hoeren["teile"] for q in t["questions"]]

    def test_counts_and_letters_fit_the_tests(self):
        from app.services.mock_exam import multilevel_keys as k

        data = json.loads((DATA / "hoeren-keys.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(int(n) for n in data["tests"]), [1, 2, 3, 4, 5, 6])
        for number, lines in data["tests"].items():
            entries, parse_errors = k.parse_text("\n".join(lines))
            rows = self.rows(int(number))
            check = k.validate(rows, entries, require_complete=True)
            self.assertEqual((len(rows), len(entries), parse_errors, check["errors"]), (EXPECTED_COUNTS[int(number)], EXPECTED_COUNTS[int(number)], [], []), number)
        # spot checks of the owner's exact tokens
        t = {n: k.parse_text("\n".join(lines))[0] for n, lines in data["tests"].items()}
        self.assertEqual((t["1"][16], t["1"][15], t["1"][35]), ("h", "f", "b"))
        self.assertEqual((t["2"][1], t["3"][1], t["3"][3], t["6"][1], t["6"][2]), ("r", "F", "R", "R", "B"))
        self.assertEqual(sum(len(v) for v in t.values()), 185)

    def test_every_other_count_is_refused(self):
        from app.services.mock_exam import multilevel_keys as k

        rows = self.rows(1)
        too_few = {n: "a" for n in range(1, 35)}  # 34 of 35
        self.assertIn("COUNT_MISMATCH", [e["code"] for e in k.validate(rows, too_few, True)["errors"]])
        too_many = {n: "a" for n in range(1, 37)}
        self.assertIn("NO_SUCH_QUESTION", [e["code"] for e in k.validate(rows, too_many, True)["errors"]])
        self.assertEqual(k.validate(rows, {5: "a"}, require_complete=False)["errors"], [])  # a single edit is fine
        self.assertEqual(k.validate(rows, {5: "c"}, False)["errors"], [])  # Nr. 5 is a three-answer question
        self.assertEqual([e["code"] for e in k.validate(rows, {6: "c"}, False)["errors"]], ["INVALID_ANSWER"])  # Nr. 6 is true / false: r f a b only


class TestRoutesAuth(unittest.TestCase):
    def test_401_403(self):
        try:
            from fastapi.testclient import TestClient
        except Exception:  # httpx missing (server)
            self.skipTest("httpx not installed")
        from app.api.dependencies.auth import get_current_user
        from app.main import app

        client = TestClient(app)
        a = uuid.uuid4()
        base = f"/api/v1/admin/multilevel-exam/model-tests/{a}/answer-keys"
        calls = [("get", base, None), ("put", base, {"section": "HOEREN", "answers": {"1": "b"}}), ("post", base + "/import", {"section": "HOEREN", "text": "1-b"})]
        for method, url, body in calls:
            self.assertEqual(getattr(client, method)(url, **({"json": body} if body else {})).status_code, 401, url)
        for role in ("STUDENT", "TEACHER"):
            app.dependency_overrides[get_current_user] = lambda role=role: NS(id=uuid.uuid4(), role=role)
            try:
                for method, url, body in calls[1:]:  # writing needs a content editor
                    self.assertEqual(getattr(client, method)(url, **({"json": body} if body else {})).status_code, 403, (role, url))
            finally:
                app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides[get_current_user] = lambda: NS(id=uuid.uuid4(), role="STUDENT")
        try:
            self.assertEqual(client.get(base).status_code, 403)
            self.assertEqual(client.get(base + "?section=SCHREIBEN").status_code, 403)  # the section pattern is checked too (403 comes first for a student)
        finally:
            app.dependency_overrides.pop(get_current_user, None)


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestKeysAgainstDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401
        from app.core.storage.local import LocalStorage
        from app.models.audit_log import AuditLog
        from app.models.certification_provider import CertificationProvider
        from app.models.mock_exam_level import MockExamLevel
        from app.models.user import User
        from app.services.mock_exam import multilevel_service

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        db = cls.Session()
        if db.scalar(select(MockExamLevel).where(MockExamLevel.title == multilevel_service.LEVEL_TITLE)):
            db.close()
            raise unittest.SkipTest("the test database already holds a Multilevel level")
        cls.audit_before = set(db.scalars(select(AuditLog.id).where(AuditLog.action.in_(("multilevel_answer_keys", "multilevel_exam_minutes")))))
        cls.tmp = tempfile.TemporaryDirectory()
        cls.storage = patch.object(LocalStorage, "ROOT", Path(cls.tmp.name))
        cls.storage.start()
        tag = uuid.uuid4().hex[:6]
        users = []
        for name, role in (("s", "STUDENT"), ("e", "CONTENT_MANAGER")):
            u = User(email=f"mlk-{name}-{tag}@test.local", username=f"mlk_{name}_{tag}", password_hash="x", is_active=True, is_verified=True,
                     is_superuser=False, role=role, is_banned=False, preferred_language="uz", premium_until=datetime.now(timezone.utc) + timedelta(days=30))
            db.add(u)
            users.append(u)
        provider = CertificationProvider(name=f"MLK {tag}", code=f"MLK{tag}", is_active=True)
        db.add(provider)
        db.flush()
        level = MockExamLevel(provider_id=provider.id, level="B1–C1", title=multilevel_service.LEVEL_TITLE, is_active=True)
        db.add(level)
        db.flush()
        cls.test_ids = {}
        for doc in multilevel_service.load_docs():
            test = multilevel_service._create_test(db, level, doc, multilevel_service.DATA_DIR)
            cls.test_ids[doc["number"]] = test.id
        db.commit()
        cls.user_ids = [u.id for u in users]
        cls.provider_id = provider.id
        db.close()

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete

        from app.models.audit_log import AuditLog
        from app.models.certification_provider import CertificationProvider
        from app.models.user import User

        with cls.Session() as db:
            db.execute(delete(CertificationProvider).where(CertificationProvider.id == cls.provider_id))
            db.execute(delete(AuditLog).where(AuditLog.action.in_(("multilevel_answer_keys", "multilevel_exam_minutes")), AuditLog.id.not_in(cls.audit_before)))
            db.execute(delete(AuditLog).where(AuditLog.actor_id.in_(cls.user_ids)))
            db.execute(delete(User).where(User.id.in_(cls.user_ids)))
            db.commit()
        cls.storage.stop()
        cls.tmp.cleanup()
        cls.engine.dispose()

    # ---------------- helpers ----------------
    def users(self, db):
        from app.models.user import User

        return [db.get(User, i) for i in self.user_ids]

    def tid(self, n):
        return self.test_ids[n]

    def run_script(self, db, overwrite=False):
        from app.scripts import multilevel_hoeren_keys as script

        plan = script.build_plan(db)
        return plan, script.apply_plan(db, plan["plan_id"], overwrite=overwrite)

    def answers(self, db, number, section="HOEREN"):
        from app.services.mock_exam import multilevel_keys as k

        return {i["number"]: i for i in k.key_table(db, self.tid(number), section)["items"]}

    # ---------------- tests (order matters: later ones build on the applied keys) ----------------
    def test_1_before_the_script_nothing_is_set_and_the_counts_are_35_and_30(self):
        from app.scripts import multilevel_hoeren_keys as script
        from app.services.mock_exam import multilevel_keys as k

        with self.Session() as db:
            for number, expected in EXPECTED_COUNTS.items():
                table = k.key_table(db, self.tid(number), "HOEREN")
                self.assertEqual((table["question_count"], table["keys_set"], table["complete"]), (expected, 0, False), number)
            plan = script.build_plan(db)
            self.assertEqual([(i["number"], i["action"], i["expected"], i["given"]) for i in plan["items"]], [(n, "set", c, c) for n, c in EXPECTED_COUNTS.items()])

    def test_2_the_script_sets_exactly_the_owners_keys_and_nothing_else(self):
        from sqlalchemy import select

        from app.models.kompetenz import Kompetenz
        from app.services.mock_exam import multilevel_keys as k

        with self.Session() as db:
            # exam times of an older import: Hören 40 in test 1–6, one odd Lesen and one odd Sprechen time — the script sets all to 60 / 60 / 60 / 15
            for number in range(1, 7):
                db.scalar(select(Kompetenz).where(Kompetenz.model_test_id == self.tid(number), Kompetenz.type == "HOEREN")).duration_minutes = 40
            db.scalar(select(Kompetenz).where(Kompetenz.model_test_id == self.tid(3), Kompetenz.type == "LESEN")).duration_minutes = 45
            db.scalar(select(Kompetenz).where(Kompetenz.model_test_id == self.tid(8), Kompetenz.type == "SPRECHEN")).duration_minutes = 10
            db.commit()
            # a Lesen key that exists before must stay as it is
            lesen = self.answers(db, 1, "LESEN")
            first = next(i for i in lesen.values() if i["type"] == "SINGLE_CHOICE")
            k.apply_keys(db, None, self.tid(1), "LESEN", {first["number"]: "c"}, source="test")
            lesen_before = {n: (i["answer"], i["source"]) for n, i in self.answers(db, 1, "LESEN").items()}
            hoeren_ids = {n: [q.id for q, _ in k._questions(db, self.tid(n), "HOEREN")] for n in EXPECTED_COUNTS}
            plan, done = self.run_script(db)
            self.assertEqual({d["number"]: d["action"] for d in done["keys"]}, {n: "set" for n in EXPECTED_COUNTS})
            self.assertEqual(sum(d["answers"] for d in done["keys"]), 185)
            self.assertEqual(done["minutes_changed"], 8)  # six Hören + one Lesen + one Sprechen
            data = json.loads((DATA / "hoeren-keys.json").read_text(encoding="utf-8"))
            for number, lines in data["tests"].items():
                entries, _ = k.parse_text("\n".join(lines))
                table = k.key_table(db, self.tid(int(number)), "HOEREN")
                self.assertEqual((table["keys_set"], table["question_count"], table["complete"]), (EXPECTED_COUNTS[int(number)],) * 2 + (True,), number)
                for item in table["items"]:
                    self.assertEqual((item["answer"], item["source"]), (entries[item["number"]], "entered"), (number, item["number"]))  # the token exactly as typed
                self.assertEqual([q.id for q, _ in k._questions(db, self.tid(int(number)), "HOEREN")], hoeren_ids[int(number)])
            # the marked option is the one the letter names — spot checks on the real options
            t1 = {i["number"]: i for i in self.answers(db, 1).values()}
            self.assertEqual((t1[16]["answer"], t1[16]["option_text"]), ("h", "H"))  # matching A–H: the 8th option
            self.assertEqual((t1[6]["answer"], t1[6]["option_text"]), ("a", "Richtig"))  # a = the first true / false option
            t3 = self.answers(db, 3)
            self.assertEqual((t3[1]["answer"], t3[1]["option_text"], t3[3]["answer"], t3[3]["option_text"]), ("F", "Falsch", "R", "Richtig"))
            self.assertEqual(self.answers(db, 2)[1]["option_text"], "Richtig")  # lower-case r is the same answer as R
            # exactly one correct option per question, Lesen untouched, other options of the database untouched
            for number in EXPECTED_COUNTS:
                for q, _ in k._questions(db, self.tid(number), "HOEREN"):
                    self.assertEqual(sum(1 for o in q.options if o.is_correct), 1)
            self.assertEqual({n: (i["answer"], i["source"]) for n, i in self.answers(db, 1, "LESEN").items()}, lesen_before)
            self.assertEqual(self.answers(db, 2, "LESEN")[first["number"]]["answer"], None)  # another test's Lesen: still no key
            # isolation: a different key in test 4 does not appear in test 3
            self.assertNotEqual(self.answers(db, 3)[2]["answer"], self.answers(db, 4)[2]["answer"])

    def test_3_exam_times_60_60_60_15_for_every_modelltest(self):
        from sqlalchemy import select

        from app.models.kompetenz import Kompetenz
        from app.services.mock_exam import multilevel_exam_service as exam

        with self.Session() as db:
            for number, test_id in self.test_ids.items():
                komps = {kz.type: kz for kz in db.scalars(select(Kompetenz).where(Kompetenz.model_test_id == test_id))}
                self.assertEqual({t: komps[t].duration_minutes for t in ("LESEN", "SCHREIBEN", "SPRECHEN")}, {"LESEN": 60, "SCHREIBEN": 60, "SPRECHEN": 15}, number)
                if number <= 6:
                    self.assertEqual(komps["HOEREN"].duration_minutes, 60, number)
                else:
                    self.assertEqual(komps["HOEREN"].duration_minutes, 0)  # Hören of 7–10 is "Noch nicht verfügbar": no length until it exists
                    self.assertEqual(exam._duration(komps["HOEREN"]), 60)  # and its fallback is 60 too
            self.assertEqual((exam.DEFAULT_MINUTES, exam.TOTAL_MINUTES), ({"LESEN": 60, "HOEREN": 60, "SCHREIBEN": 60, "SPRECHEN": 15}, 195))

    def test_4_the_script_is_idempotent_and_refuses_a_conflicting_key(self):
        from app.scripts import multilevel_hoeren_keys as script
        from app.services.mock_exam import multilevel_keys as k

        with self.Session() as db:
            plan = script.build_plan(db)
            self.assertEqual({i["action"] for i in plan["items"]}, {"skip"})
            self.assertEqual(plan["minutes"], [])
            self.assertEqual(script.apply_plan(db, plan["plan_id"])["minutes_changed"], 0)
            with self.assertRaises(RuntimeError):
                script.apply_plan(db, "wrongplanid0")
            # somebody changes one Hören key of test 3 by hand: the script reports a conflict and keeps the hand-made change unless told otherwise
            k.apply_keys(db, None, self.tid(3), "HOEREN", {2: "b"}, source="test")
            plan = script.build_plan(db)
            self.assertEqual({i["number"]: i["action"] for i in plan["items"]}[3], "conflict")
            with self.assertRaises(RuntimeError):
                script.apply_plan(db, plan["plan_id"])
            self.assertEqual(self.answers(db, 3)[2]["answer"], "b")
            script.apply_plan(db, plan["plan_id"], overwrite=True)
            self.assertEqual(self.answers(db, 3)[2]["answer"], "a")  # the owner's token again

    def test_5_editing_import_and_validation(self):
        from sqlalchemy import select

        from app.models.audit_log import AuditLog
        from app.services.mock_exam import multilevel_keys as k

        with self.Session() as db:
            _, editor = self.users(db)
            before = self.answers(db, 2)
            # one edit changes one question (R / F tokens keep their case)
            table = k.apply_keys(db, editor, self.tid(2), "HOEREN", {3: "R"}, source="admin")
            self.assertEqual((table["items"][2]["answer"], table["items"][2]["option_text"]), ("R", "Richtig"))
            self.assertEqual({n: i["answer"] for n, i in self.answers(db, 2).items() if n != 3}, {n: i["answer"] for n, i in before.items() if n != 3})
            # invalid input changes nothing at all
            for entries, complete in (({1: "z"}, False), ({31: "a"}, False), ({2: "r"}, False), ({n: "a" for n in range(1, 30)}, True)):
                with self.assertRaises(HTTPException) as ctx:
                    k.apply_keys(db, editor, self.tid(2), "HOEREN", entries, require_complete=complete)
                self.assertEqual(ctx.exception.status_code, 422)
                self.assertTrue(str(ctx.exception.detail).startswith("INVALID_KEYS"))
            self.assertEqual(self.answers(db, 2)[3]["answer"], "R")
            self.assertEqual(self.answers(db, 2)[1]["answer"], before[1]["answer"])
            # import: a dry run reports, a list with a wrong count is not saved, the full list is
            data = json.loads((DATA / "hoeren-keys.json").read_text(encoding="utf-8"))
            full = "\n".join(data["tests"]["2"])
            short = k.import_text(db, editor, self.tid(2), "HOEREN", full.replace("30-a", ""), dry_run=False)
            self.assertEqual((short["ok"], short["applied"], short["given"], short["expected"]), (False, False, 29, 30))
            self.assertIn("COUNT_MISMATCH", [e["code"] for e in short["errors"]])
            self.assertEqual(self.answers(db, 2)[3]["answer"], "R")
            dry = k.import_text(db, editor, self.tid(2), "HOEREN", full, dry_run=True)
            self.assertEqual((dry["ok"], dry["applied"], len(dry["preview"])), (True, False, 30))
            self.assertEqual(self.answers(db, 2)[3]["answer"], "R")  # the dry run saved nothing
            applied = k.import_text(db, editor, self.tid(2), "HOEREN", full, dry_run=False)
            self.assertEqual((applied["ok"], applied["applied"]), (True, True))
            self.assertEqual(self.answers(db, 2)[3]["answer"], "f")  # the owner's list again
            # Lesen: the same tool, its own questions; Schreiben / Sprechen are not key sections; a non-Multilevel id is not found
            self.assertEqual(k.key_table(db, self.tid(1), "LESEN")["question_count"], 35)
            with self.assertRaises(HTTPException) as ctx:
                k.key_table(db, self.tid(1), "SCHREIBEN")
            self.assertEqual(ctx.exception.status_code, 422)
            with self.assertRaises(HTTPException) as ctx:
                k.key_table(db, uuid.uuid4(), "HOEREN")
            self.assertEqual(ctx.exception.status_code, 404)
            rows = db.scalars(select(AuditLog).where(AuditLog.action == "multilevel_answer_keys", AuditLog.id.not_in(self.audit_before))).all()
            self.assertGreaterEqual(len(rows), 7)
            self.assertTrue(all("answers" in r.details and "@" not in r.details for r in rows))

    def test_6_publish_readiness_names_what_is_still_missing(self):
        from app.services.mock_exam import multilevel_keys as k

        with self.Session() as db:
            r = k.key_table(db, self.tid(1), "HOEREN")["readiness"]
            self.assertFalse(r["ready"])  # Lesen keys and Hören audio of this test are not there
            self.assertEqual(len(r["missing_audio"]), 6)  # Modelltest 1 has six Hören Teile
            self.assertEqual(len(k.key_table(db, self.tid(2), "HOEREN")["readiness"]["missing_audio"]), 4)
            self.assertTrue(r["missing_keys"])  # the Lesen questions

    def test_7_scoring_per_test_35_and_30_questions(self):
        from sqlalchemy import func, select

        from app.models.mock_attempt_section import MockAttemptSection
        from app.models.mock_question_answer import MockQuestionAnswer
        from app.models.model_test import ModelTest
        from app.services.mock_exam import multilevel_exam_service as exam
        from app.services.mock_exam import multilevel_keys as k

        with self.Session() as db:
            student, _ = self.users(db)
            for number in (1, 2):
                test = db.get(ModelTest, self.tid(number))
                test.status = "PUBLISHED"
            db.commit()
            self.assertEqual([e["number"] for e in exam.list_exams(db, student)], [1, 2])  # only what is published is listed
            results = {}
            for number, expected_total, wrong in ((1, 35, 1), (2, 30, 1)):
                attempt = exam.start_attempt(db, student, self.tid(number))
                exam.start_section(db, student, attempt.id, "HOEREN")
                rows = k._questions(db, self.tid(number), "HOEREN")
                self.assertEqual(len(rows), expected_total)
                for index, (q, _) in enumerate(rows):
                    good = next(o for o in q.options if o.is_correct)
                    chosen = good if index >= wrong else next(o for o in q.options if not o.is_correct)  # the first `wrong` questions are answered wrongly
                    exam.save_answer(db, student, attempt.id, "HOEREN", q.id, [chosen.id])
                exam.submit_section(db, student, attempt.id, "HOEREN")
                s = db.scalar(select(MockAttemptSection).where(MockAttemptSection.attempt_id == attempt.id, MockAttemptSection.section_type == "HOEREN"))
                results[number] = (s.raw_points, s.raw_max, s.score, s.status)
                # every answer is stored with its own correctness
                stored = db.execute(select(MockQuestionAnswer.is_correct, func.count()).where(MockQuestionAnswer.attempt_id == attempt.id).group_by(MockQuestionAnswer.is_correct)).all()
                self.assertEqual(dict(stored), {True: expected_total - wrong, False: wrong})
            self.assertEqual(results[1], (34, 35, 73, "SUBMITTED"))  # 34 / 35 × 75 = 72.86
            self.assertEqual(results[2], (29, 30, 73, "SUBMITTED"))  # 29 / 30 × 75 = 72.5, half up
            exam.finish_attempt(db, student, exam.start_attempt(db, student, self.tid(1)).id)  # closes the first attempt: the timer test starts a fresh one

    def test_8_timer_server_side_survives_refresh_and_closes_at_the_deadline(self):
        from sqlalchemy import select

        from app.models.mock_attempt_section import MockAttemptSection
        from app.services.mock_exam import multilevel_exam_service as exam
        from app.services.mock_exam import multilevel_keys as k

        with self.Session() as db:
            student, _ = self.users(db)
            listed = next(e for e in exam.list_exams(db, student) if e["number"] == 1)
            self.assertEqual([(s["type"], s["duration_minutes"]) for s in listed["sections"]], [("LESEN", 60), ("HOEREN", 60), ("SCHREIBEN", 60), ("SPRECHEN", 15)])
            self.assertEqual(listed["total_minutes"], 195)
            attempt = exam.start_attempt(db, student, self.tid(1))
            view = exam.attempt_view(db, student, attempt.id)
            self.assertEqual((view["total_minutes"], view["number"]), (195, 1))
            granted = {}
            for section, minutes in (("LESEN", 60), ("SCHREIBEN", 60), ("SPRECHEN", 15)):
                exam.start_section(db, student, attempt.id, section)
                paper = exam.section_paper(db, student, attempt.id, section)
                self.assertTrue(minutes * 60 - 5 <= paper["remaining_seconds"] <= minutes * 60, section)
                s = db.scalar(select(MockAttemptSection).where(MockAttemptSection.attempt_id == attempt.id, MockAttemptSection.section_type == section))
                granted[section] = s.duration_seconds
                self.assertEqual((s.duration_seconds, round((s.deadline_at - s.started_at).total_seconds())), (minutes * 60, minutes * 60))
                if section == "LESEN":  # refresh: the time is not reset — move the start back ten minutes, ask again
                    s.started_at -= timedelta(minutes=10)
                    s.deadline_at -= timedelta(minutes=10)
                    db.commit()
                    again = exam.section_paper(db, student, attempt.id, section)
                    self.assertTrue(50 * 60 - 5 <= again["remaining_seconds"] <= 50 * 60)
                    self.assertTrue(50 * 60 - 5 <= exam.attempt_view(db, student, attempt.id)["sections"][0]["remaining_seconds"] <= 50 * 60)
                    # the deadline passes (plus the 30 s grace): the server closes and grades the section itself, answers are refused
                    q = k._questions(db, self.tid(1), "LESEN")[0][0]
                    exam.save_answer(db, student, attempt.id, "LESEN", q.id, [q.options[0].id])
                    s.deadline_at = datetime.now(timezone.utc) - timedelta(seconds=60)
                    db.commit()
                    with self.assertRaises(HTTPException) as ctx:
                        exam.save_answer(db, student, attempt.id, "LESEN", q.id, [q.options[1].id])
                    self.assertEqual((ctx.exception.status_code, ctx.exception.detail), (409, "SECTION_CLOSED"))
                    db.refresh(s)
                    self.assertEqual(s.status, "EXPIRED")
                    self.assertIsNotNone(s.submitted_at)
                    self.assertLessEqual(s.submitted_at, s.deadline_at)
                    self.assertEqual((s.raw_max, s.score is not None), (35, True))  # graded and stored (no Lesen key yet: nothing counts)
                    self.assertEqual(exam.attempt_view(db, student, attempt.id)["sections"][0]["ended_at"], s.submitted_at)
                else:
                    exam.submit_section(db, student, attempt.id, section)
            self.assertEqual(granted, {"LESEN": 3600, "SCHREIBEN": 3600, "SPRECHEN": 900})
            exam.start_section(db, student, attempt.id, "HOEREN")
            self.assertTrue(3595 <= exam.section_paper(db, student, attempt.id, "HOEREN")["remaining_seconds"] <= 3600)
            exam.finish_attempt(db, student, attempt.id)
            final = exam.attempt_view(db, student, attempt.id)
            self.assertTrue(final["finished"])
            self.assertEqual({s["status"] for s in final["sections"]} <= {"SUBMITTED", "EXPIRED"}, True)
            self.assertEqual(sum(s["duration_minutes"] for s in final["sections"]), 195)


if __name__ == "__main__":
    unittest.main()
