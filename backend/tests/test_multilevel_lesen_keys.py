"""Multilevel Modelltest 1-6: the Lesen answer keys of the owner's PDF (app/data/multilevel/lesen-keys.json, script multilevel_lesen_keys).

Pure (no database): six variants x 35 answers numbered 1-35, Teil 1 an order of a-e, Teil 3 seven different headings, every letter valid for its
question in the real Modelltest data files (ORDERING a-e, matching a-j, Lesen true / false a-c), spot checks against the PDF, the variants differ from
each other and from Hören, the letter rules (ORDERING, three-option true / false; Hören true / false still a / b / r / f only).
Against PostgreSQL (VIZU_WB_TEST_DB_URL): the real ten Modelltests are built, plan / apply sets exactly the 6 x 35 Lesen keys (Hören, other tests, option
texts untouched; idempotent; a conflict is refused), and the server scores each variant: 35 / 35 = full score, all wrong = 0, a mixed sheet exactly,
and one variant's letters on another variant score only where the two keys agree (no key mixing). Regrade (script multilevel_lesen_regrade): Lesen
sections closed before the keys existed get scored exactly like a new attempt (10 right = 10 / 35, nothing answered = 0 / 35), the attempt total now
includes Lesen, other sections / open sections / answers' choices untouched, a row copy is written first, a second run finds nothing."""

import json
import os
import re
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
DATA = Path(__file__).resolve().parents[1] / "app" / "data" / "multilevel"


def _keys_file() -> dict:
    return json.loads((DATA / "lesen-keys.json").read_text(encoding="utf-8"))


def _letters(lines: list[str]) -> str:
    return "".join(l.lower() for _n, l in re.findall(r"(\d+)-([A-Za-z])", " ".join(lines)))


def _fake(question_type: str, options: list[str], correct: int | None = None):
    return NS(question_type=question_type, options=[NS(option_text=t, is_correct=i == correct) for i, t in enumerate(options)], answer_key=None,
              question_text="A1. Text")


class TestKeyFile(unittest.TestCase):
    def test_six_variants_35_answers_and_their_own_rules(self):
        from app.scripts import multilevel_lesen_keys as script

        data = _keys_file()
        self.assertEqual(data["section"], "LESEN")
        self.assertEqual(sorted(int(n) for n in data["tests"]), [1, 2, 3, 4, 5, 6])
        for number, lines in data["tests"].items():
            entries, errors = script.entries_of(lines)
            self.assertEqual((sorted(entries), errors), (list(range(1, 36)), []), number)

    def test_letters_fit_the_real_questions(self):
        from app.services.mock_exam import multilevel_keys as k

        for number, lines in _keys_file()["tests"].items():
            doc = json.loads((DATA / f"modelltest-{int(number):02d}.json").read_text(encoding="utf-8"))
            lesen = next(x for x in doc["kompetenzen"] if x["type"] == "LESEN")
            rows = [(_fake(q["type"], [o["text"] for o in q["options"]]), None) for t in lesen["teile"] for q in t["questions"]]
            entries, _ = k.parse_text("\n".join(lines))
            check = k.validate(rows, entries, require_complete=True)
            self.assertEqual((len(rows), check["errors"]), (35, []), number)

    def test_values_are_the_pdf_tables(self):
        t = {int(n): _letters(lines) for n, lines in _keys_file()["tests"].items()}
        pdf = {  # Nr. 1-35 as printed in Antworten.pdf (pages 1-5: tables, page 6: infographic)
            1: "ceadbbacabifcdgjhb" + "aaababbbbbcbcbacc",
            2: "bcadebbcabadcbfjhb" + "abababaccbcabcbcb",
            3: "bcadebbbbciacbfjea" + "bababaaccbccbbbbc",
            4: "bacedbbcbcbacdefia" + "bbbababab" + "bbcbcbbc",
            5: "abcedcbbbchijafdeb" + "baababacbbbcbcbcc",
            6: "abcde" + "bbbcc" + "facedij" + "baabababba" + "bbbcbbcb",
        }
        self.assertEqual(t, pdf)
        self.assertTrue(all(len(v) == 35 for v in pdf.values()))
        # where the owner's typed message differed from the PDF, the PDF wins
        self.assertEqual(t[1][27:33], "bcbcba")  # Nr. 28-33 (typed: c b c b a c)
        self.assertEqual((t[6][15], t[6][16]), ("i", "j"))  # Nr. 16, 17 (typed: j, i)
        self.assertEqual(len(set(t.values())), 6)  # no two variants share a key list

    def test_lesen_keys_are_not_the_hoeren_keys(self):
        hoeren = json.loads((DATA / "hoeren-keys.json").read_text(encoding="utf-8"))["tests"]
        for number, lines in _keys_file()["tests"].items():
            self.assertNotEqual(_letters(lines), _letters(hoeren[number]).lower(), number)


class TestLetterRules(unittest.TestCase):
    def test_ordering_and_three_option_true_false(self):
        from app.services.mock_exam import multilevel_keys as k

        order = _fake("ORDERING", list("ABCDE"))
        self.assertEqual([k._option_index(order, t) for t in "abcdeE"], [0, 1, 2, 3, 4, 4])
        with self.assertRaises(KeyError):
            k._option_index(order, "f")
        tf3 = _fake("TRUE_FALSE", ["Richtig", "Falsch", "Der Text sagt nichts dazu"])
        self.assertEqual([k._option_index(tf3, t) for t in ("a", "b", "c", "r", "F")], [0, 1, 2, 0, 1])
        with self.assertRaises(KeyError):
            k._option_index(tf3, "d")
        tf3.options[2].is_correct = True
        self.assertEqual(k.canonical_key(tf3), "C")
        # Hören true / false has two options: unchanged, c stays invalid
        tf2 = _fake("TRUE_FALSE", ["Richtig", "Falsch"])
        self.assertEqual([k._option_index(tf2, t) for t in ("a", "b", "r", "f")], [0, 1, 0, 1])
        with self.assertRaises(KeyError):
            k._option_index(tf2, "c")
        with self.assertRaises(KeyError):
            k._option_index(_fake("MULTIPLE_CHOICE", ["a", "b"]), "a")


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestLesenKeysAgainstDatabase(unittest.TestCase):
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
        from app.models.user_entitlement import PRODUCT_MULTILEVEL_PREMIUM, UserEntitlement
        from app.services.mock_exam import multilevel_service

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        db = cls.Session()
        if db.scalar(select(MockExamLevel).where(MockExamLevel.title == multilevel_service.LEVEL_TITLE)):
            db.close()
            raise unittest.SkipTest("the test database already holds a Multilevel level")
        cls.audit_before = set(db.scalars(select(AuditLog.id).where(AuditLog.action.in_(("multilevel_answer_keys", "multilevel_lesen_keys")))))
        cls.tmp = tempfile.TemporaryDirectory()
        cls.storage = patch.object(LocalStorage, "ROOT", Path(cls.tmp.name))
        cls.storage.start()
        tag = uuid.uuid4().hex[:6]
        student = User(email=f"mll-{tag}@test.local", username=f"mll_{tag}", password_hash="x", is_active=True, is_verified=True, is_superuser=False,
                       role="STUDENT", is_banned=False, preferred_language="uz", premium_until=datetime.now(timezone.utc) + timedelta(days=30))
        db.add(student)
        db.flush()
        db.add(UserEntitlement(user_id=student.id, product=PRODUCT_MULTILEVEL_PREMIUM, source="PAYMENT", granted_at=datetime.now(timezone.utc)))
        provider = CertificationProvider(name=f"MLL {tag}", code=f"MLL{tag}", is_active=True)
        db.add(provider)
        db.flush()
        level = MockExamLevel(provider_id=provider.id, level="B1–C1", title=multilevel_service.LEVEL_TITLE, is_active=True)
        db.add(level)
        db.flush()
        cls.test_ids = {}
        for doc in multilevel_service.load_docs():
            test = multilevel_service._create_test(db, level, doc, multilevel_service.DATA_DIR)
            cls.test_ids[doc["number"]] = test.id
            test.status = "PUBLISHED" if doc["number"] <= 6 else test.status
        db.commit()
        cls.student_id, cls.provider_id = student.id, provider.id
        db.close()

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete

        from app.models.audit_log import AuditLog
        from app.models.certification_provider import CertificationProvider
        from app.models.user import User

        with cls.Session() as db:
            db.execute(delete(CertificationProvider).where(CertificationProvider.id == cls.provider_id))
            db.execute(delete(AuditLog).where(AuditLog.action.in_(("multilevel_answer_keys", "multilevel_lesen_keys")), AuditLog.id.not_in(cls.audit_before)))
            db.execute(delete(User).where(User.id == cls.student_id))
            db.commit()
        cls.storage.stop()
        cls.tmp.cleanup()
        cls.engine.dispose()

    def table(self, db, number, section="LESEN"):
        from app.services.mock_exam import multilevel_keys as k

        return k.key_table(db, self.test_ids[number], section)

    def test_0_attempts_closed_before_the_keys_exist(self):
        """Two Lesen sections handed in while the test had no Lesen keys (they stay "not scored" until the regrade, test_4)."""
        from sqlalchemy import select

        from app.models.mock_attempt_section import MockAttemptSection
        from app.models.user import User
        from app.services.mock_exam import multilevel_exam_service as exam
        from app.services.mock_exam import multilevel_keys as k

        data = {int(n): _letters(lines) for n, lines in _keys_file()["tests"].items()}
        with self.Session() as db:
            student = db.get(User, self.student_id)
            a = exam.start_attempt(db, student, self.test_ids[1])  # MT1: 10 right (by the PDF), 5 wrong, 20 not answered
            exam.start_section(db, student, a.id, "LESEN")
            for i, (q, _) in enumerate(k._questions(db, self.test_ids[1], "LESEN")[:15]):
                index = k._option_index(q, data[1][i])
                exam.save_answer(db, student, a.id, "LESEN", q.id, [q.options[index if i < 10 else (index + 1) % len(q.options)].id])
            exam.submit_section(db, student, a.id, "LESEN")
            exam.finish_attempt(db, student, a.id)
            b = exam.start_attempt(db, student, self.test_ids[2])  # MT2: finished without touching Lesen
            exam.finish_attempt(db, student, b.id)
            type(self).before_keys = {}
            for number, attempt in ((1, a), (2, b)):
                s = db.scalar(select(MockAttemptSection).where(MockAttemptSection.attempt_id == attempt.id, MockAttemptSection.section_type == "LESEN"))
                db.refresh(attempt)
                self.assertTrue(exam._unscorable(s), number)  # no key at that time: not scored, left out of the total
                type(self).before_keys[number] = (attempt.id, attempt.max_score)

    def test_1_plan_apply_sets_exactly_the_pdf_keys(self):
        from app.scripts import multilevel_lesen_keys as script
        from app.services.mock_exam import multilevel_keys as k

        with self.Session() as db:
            option_texts = {n: [[o.option_text for o in q.options] for q, _ in k._questions(db, self.test_ids[n], "LESEN")] for n in range(1, 11)}
            others_before = {n: [(i["answer"], i["source"]) for i in self.table(db, n)["items"]] for n in range(7, 11)}  # 7-10 bring their own keys
            for n in range(1, 7):
                self.assertEqual((self.table(db, n)["question_count"], self.table(db, n)["keys_set"]), (35, 0), n)
            plan = script.build_plan(db)
            self.assertEqual([(i["number"], i["action"], i["given"], i["expected"]) for i in plan["items"]], [(n, "set", 35, 35) for n in range(1, 7)])
            done = script.apply_plan(db, plan["plan_id"])
            self.assertEqual(sum(d["answers"] for d in done["keys"]), 210)
            data = {int(n): _letters(lines) for n, lines in _keys_file()["tests"].items()}
            for n in range(1, 7):
                table = self.table(db, n)
                self.assertEqual((table["keys_set"], table["complete"]), (35, True), n)
                self.assertEqual("".join(i["answer"] for i in table["items"]), data[n], n)  # Nr. 1-35 in order, the tokens as written
                self.assertTrue(all(sum(o.is_correct for o in q.options) == 1 for q, _ in k._questions(db, self.test_ids[n], "LESEN")))
                self.assertEqual(self.table(db, n, "HOEREN")["keys_set"], 0, n)  # Hören untouched
            for n in range(7, 11):
                self.assertEqual([(i["answer"], i["source"]) for i in self.table(db, n)["items"]], others_before[n], n)  # other Modelltests untouched
            after = {n: [[o.option_text for o in q.options] for q, _ in k._questions(db, self.test_ids[n], "LESEN")] for n in range(1, 11)}
            self.assertEqual(after, option_texts)  # no question or option text changed
            # the letter names the right option: spot checks on the real texts
            t1, t2, t6 = (({i["number"]: i for i in self.table(db, n)["items"]}) for n in (1, 2, 6))
            self.assertEqual((t1[1]["answer"], t1[1]["option_text"], t1[1]["type"]), ("c", "C", "ORDERING"))
            self.assertEqual((t2[26]["answer"], t2[26]["option_text"][:13].lower()), ("c", "der text sagt"))  # Teil 4: c = nicht im Text
            self.assertEqual((t6[16]["answer"], t6[16]["option_text"]), ("i", "Die Rolle von Freunden"))
            self.assertEqual((t6[17]["answer"], t6[17]["option_text"]), ("j", "Lernen in Gruppen oder allein"))

    def test_2_idempotent_and_conflicts_refused(self):
        from app.scripts import multilevel_lesen_keys as script
        from app.services.mock_exam import multilevel_keys as k

        with self.Session() as db:
            plan = script.build_plan(db)
            self.assertEqual({i["action"] for i in plan["items"]}, {"skip"})
            with self.assertRaises(RuntimeError):
                script.apply_plan(db, "wrongplanid0")
            k.apply_keys(db, None, self.test_ids[4], "LESEN", {7: "a"}, source="test")  # a hand edit in variant 4
            plan = script.build_plan(db)
            self.assertEqual({i["number"]: i["action"] for i in plan["items"]}[4], "conflict")
            with self.assertRaises(RuntimeError):
                script.apply_plan(db, plan["plan_id"])
            self.assertEqual(self.table(db, 4)["items"][6]["answer"], "a")
            script.apply_plan(db, plan["plan_id"], overwrite=True)
            self.assertEqual(self.table(db, 4)["items"][6]["answer"], "b")  # the PDF value again

    def _sheet(self, db, number, letters):
        """Starts an attempt on Modelltest `number`, answers Lesen with the given letters (None = a wrong option), submits, returns (raw, max, score)."""
        from sqlalchemy import select

        from app.models.mock_attempt_section import MockAttemptSection
        from app.models.user import User
        from app.services.mock_exam import multilevel_exam_service as exam
        from app.services.mock_exam import multilevel_keys as k

        student = db.get(User, self.student_id)
        attempt = exam.start_attempt(db, student, self.test_ids[number])
        exam.start_section(db, student, attempt.id, "LESEN")
        for (q, _), letter in zip(k._questions(db, self.test_ids[number], "LESEN"), letters):
            option = q.options[k._option_index(q, letter)] if letter else next(o for o in q.options if not o.is_correct)
            exam.save_answer(db, student, attempt.id, "LESEN", q.id, [option.id])
        exam.submit_section(db, student, attempt.id, "LESEN")
        s = db.scalar(select(MockAttemptSection).where(MockAttemptSection.attempt_id == attempt.id, MockAttemptSection.section_type == "LESEN"))
        result = (s.raw_points, s.raw_max, s.score)
        exam.finish_attempt(db, student, attempt.id)
        return result

    def test_3_scoring_per_variant(self):
        data = {int(n): _letters(lines) for n, lines in _keys_file()["tests"].items()}
        with self.Session() as db:
            for n in range(1, 7):
                self.assertEqual(self._sheet(db, n, data[n]), (35, 35, 75), n)  # all right: full score
            self.assertEqual(self._sheet(db, 3, [None] * 35), (0, 35, 0))  # all wrong
            mixed = list(data[5][:20]) + [None] * 15
            self.assertEqual(self._sheet(db, 5, mixed)[:2], (20, 35))  # 20 right, 15 wrong
            # variant 1's letters on variant 2: right only where both keys have the same letter
            same = sum(a == b for a, b in zip(data[1], data[2]))
            self.assertLess(same, 35)
            self.assertEqual(self._sheet(db, 2, data[1])[:2], (same, 35))

    def test_4_old_lesen_sections_are_scored_by_the_regrade(self):
        from sqlalchemy import func, select

        from app.models.mock_attempt_section import MockAttemptSection
        from app.models.mock_question_answer import MockQuestionAnswer
        from app.models.mock_test_attempt import MockTestAttempt
        from app.models.user import User
        from app.scripts import multilevel_lesen_regrade as regrade
        from app.services.mock_exam import multilevel_exam_service as exam

        def lesen(db, attempt_id):
            return db.scalar(select(MockAttemptSection).where(MockAttemptSection.attempt_id == attempt_id, MockAttemptSection.section_type == "LESEN"))

        with self.Session() as db:
            student = db.get(User, self.student_id)
            open_attempt = exam.start_attempt(db, student, self.test_ids[4])  # an OPEN Lesen section must not be touched
            exam.start_section(db, student, open_attempt.id, "LESEN")
            others = {s.id: (s.status, s.raw_points, s.raw_max, s.score) for s in db.scalars(select(MockAttemptSection).where(
                MockAttemptSection.attempt_id.in_([self.before_keys[1][0], self.before_keys[2][0]]), MockAttemptSection.section_type != "LESEN"))}
            plan = regrade.build_plan(db)
            self.assertEqual(sorted((i["number"], i["answered_anything"]) for i in plan["items"]), [(1, True), (2, False)])
            db.expire_all()
            self.assertEqual((lesen(db, self.before_keys[1][0]).raw_max, lesen(db, self.before_keys[1][0]).score), (0, None))  # the plan changed nothing
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(RuntimeError):
                    regrade.apply_plan(db, "wrongplanid0", Path(tmp))
                done = regrade.apply_plan(db, plan["plan_id"], Path(tmp))
                self.assertEqual(done["regraded"], 2)
                snap = json.loads(Path(done["backup"]).read_text(encoding="utf-8"))
                self.assertEqual(len(snap["attempts"]), 2)  # a row copy of everything it changed
            db.expire_all()
            s1, s2 = lesen(db, self.before_keys[1][0]), lesen(db, self.before_keys[2][0])
            self.assertEqual((s1.raw_points, s1.raw_max, s1.score), (10, 35, exam.scale(10, 35)))  # 10 right of 35 with the PDF key
            self.assertEqual((s2.raw_points, s2.raw_max, s2.score), (0, 35, 0))  # nothing answered: 0, like a new attempt
            for number in (1, 2):  # Lesen now counts in the attempt: its maximum grows by one section
                attempt = db.get(MockTestAttempt, self.before_keys[number][0])
                self.assertEqual(attempt.max_score, self.before_keys[number][1] + exam.SECTION_MAX, number)
            marked = dict(db.execute(select(MockQuestionAnswer.is_correct, func.count()).where(MockQuestionAnswer.attempt_id == self.before_keys[1][0])
                                     .group_by(MockQuestionAnswer.is_correct)).all())
            self.assertEqual(marked, {True: 10, False: 5})
            after_others = {s.id: (s.status, s.raw_points, s.raw_max, s.score) for s in db.scalars(select(MockAttemptSection).where(
                MockAttemptSection.id.in_(list(others))))}
            self.assertEqual(after_others, others)  # Hören / Schreiben / Sprechen untouched
            self.assertEqual((lesen(db, open_attempt.id).status, lesen(db, open_attempt.id).raw_max), ("OPEN", None))
            self.assertEqual(regrade.build_plan(db)["items"], [])  # idempotent
            exam.finish_attempt(db, student, open_attempt.id)


if __name__ == "__main__":
    unittest.main()
