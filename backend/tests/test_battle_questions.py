"""VIZU Battle text questions (2026-11-19): the shipped question bank (≥ 500 valid, unique questions per level A1–C1, vocabulary and
grammar, level-appropriate topics), the validator, the choice of questions for a match (no repeats, mixed with picture rounds where the
level has its own picture words), the text round view (no answer before the reveal), the seed (plan / apply / idempotent), the admin
API (401 / 403, create / edit / delete / import with duplicates and invalid rows, statistics) — against PostgreSQL where needed
(VIZU_WB_TEST_DB_URL)."""

import importlib.util
import json
import os
import random
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from fastapi import HTTPException

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
DATA = Path(__file__).resolve().parents[1] / "app" / "data" / "battle" / "questions"
LEVELS = ("A1", "A2", "B1", "B2", "C1")

# grammar topics a level may use — keeps C1 grammar out of A1 (vocabulary topics follow the Wörterbuch level)
GRAMMAR_BY_LEVEL = {
    "A1": {"sein_haben", "praesens", "pronomen", "w_fragen", "negation", "possessiv", "modalverben", "praep_zeit", "akkusativ", "imperativ", "artikel"},
    "A2": {"akk_dat", "perfekt", "modalverben", "trennbare_verben", "wechselpraep", "possessiv", "pronomen", "komparativ", "praeteritum", "nebensaetze",
           "adjektiv_verb", "artikel"},
    "B1": {"konnektoren", "relativsaetze", "passiv", "infinitiv_zu", "konjunktiv2", "plusquamperfekt", "praepositionen", "verben_praep",
           "adjektivdeklination", "wortbildung", "artikel"},
    "B2": {"passiv_ersatz", "konjunktiv", "nominalisierung", "partizipien", "nebensaetze_komplex", "praep_genitiv", "artikel"},
    "C1": {"konnektoren_c1", "satzstrukturen", "nominalstil", "stilistik", "praep_komplex", "grammatik_c1", "artikel"},
}


def _load(level):
    return json.loads((DATA / f"{level}.json").read_text(encoding="utf-8"))


class TestShippedQuestions(unittest.TestCase):
    """The data files are the source of the seed: every rule is checked here, without a database."""

    @classmethod
    def setUpClass(cls):
        cls.docs = {lv: _load(lv) for lv in LEVELS}

    def test_at_least_500_valid_questions_per_level(self):
        from app.services.battle import question_bank as bank

        for lv, doc in self.docs.items():
            with self.subTest(level=lv):
                self.assertEqual(doc["level"], lv)
                qs = doc["questions"]
                self.assertGreaterEqual(len(qs), 500)
                bad = [(q["id"], bank.validate({**q, "level": lv})) for q in qs if bank.validate({**q, "level": lv})]
                self.assertEqual(bad, [])

    def test_no_duplicates_inside_a_level_or_across_levels(self):
        from app.services.battle import question_bank as bank

        ids, keys = set(), {}
        for lv, doc in self.docs.items():
            for q in doc["questions"]:
                self.assertNotIn(q["id"], ids, q["id"])
                ids.add(q["id"])
                key = bank.norm_key(q["format"], q["prompt"])
                self.assertNotIn(key, keys, f"{lv} {q['prompt']!r} also in {keys.get(key)}")
                keys[key] = lv
            refs = [q["ref"].lower() for q in doc["questions"] if q.get("ref")]
            self.assertEqual(len(refs), len(set(refs)), f"{lv}: a word is asked twice")

    def test_vocabulary_and_grammar_per_level_and_topics_fit_the_level(self):
        from app.services.battle import question_bank as bank

        for lv, doc in self.docs.items():
            with self.subTest(level=lv):
                kinds = {q["kind"] for q in doc["questions"]}
                self.assertEqual(kinds, {"vocab", "grammar"})
                grammar_topics = {q["topic"] for q in doc["questions"] if q["kind"] == "grammar"}
                self.assertLessEqual(grammar_topics, GRAMMAR_BY_LEVEL[lv], grammar_topics - GRAMMAR_BY_LEVEL[lv])
                self.assertGreaterEqual(len({q["topic"] for q in doc["questions"]}), 10)
                self.assertGreaterEqual(len({q["format"] for q in doc["questions"]}), 5)
                for q in doc["questions"]:
                    self.assertEqual(bank.TOPICS[q["topic"]][0], q["kind"], q["id"])
        a1_themes = {q["topic"] for q in self.docs["A1"]["questions"] if q["kind"] == "vocab"}
        for theme in ("familie", "wohnen", "essen", "farben_zahlen", "berufe", "tiere", "zeit", "verkehr", "orte", "verben", "adjektive"):
            self.assertIn(theme, a1_themes)
        # A1 is mostly vocabulary, the grammar share grows with the level
        share = {lv: sum(q["kind"] == "grammar" for q in d["questions"]) / len(d["questions"]) for lv, d in self.docs.items()}
        self.assertLess(share["A1"], 0.3)

    def test_picture_words_untouched(self):
        words = json.loads((DATA.parent / "words.json").read_text(encoding="utf-8"))
        self.assertEqual(len(words["words"]), 89)


class TestValidator(unittest.TestCase):
    BASE = {"level": "B1", "kind": "grammar", "format": "grammar", "topic": "passiv", "prompt": "Das Haus ___ 1990 gebaut.", "answer": "wurde",
            "wrong": ["wird", "hatte", "würde"]}

    def test_rules(self):
        from app.services.battle import question_bank as bank

        self.assertEqual(bank.validate(self.BASE), [])
        self.assertIn("OPTIONS_NOT_UNIQUE", bank.validate({**self.BASE, "wrong": ["Wurde", "hatte", "würde"]}))  # the answer among the wrong ones
        self.assertIn("OPTION_COUNT", bank.validate({**self.BASE, "wrong": ["wird", "hatte"]}))
        self.assertIn("TOPIC_KIND", bank.validate({**self.BASE, "kind": "vocab"}))
        self.assertIn("GAP_MISSING", bank.validate({**self.BASE, "format": "gap", "kind": "vocab", "topic": "nomen", "prompt": "Das Haus"}))
        art = {**self.BASE, "format": "article", "topic": "artikel", "prompt": "___ Haus", "answer": "das", "wrong": ["der", "die"]}
        self.assertEqual(bank.validate(art), [])
        self.assertIn("ARTICLE_OPTIONS", bank.validate({**art, "wrong": ["der", "den"]}))
        uz = {"level": "A1", "kind": "vocab", "format": "de_uz", "topic": "essen", "prompt": "der Apfel", "answer": "olma", "wrong": ["non", "suv", "go'sht"]}
        self.assertIn("UZ_APOSTROPHE", bank.validate(uz))
        self.assertIn("CYRILLIC", bank.validate({**uz, "wrong": ["non", "suv", "нон"]}))
        self.assertEqual(bank.fix_uz("go'sht, ma'no, o`qituvchi"), "go‘sht, ma’no, o‘qituvchi")
        self.assertEqual(bank.normalize("„Das  Haus“ …"), '"das haus" ___')

    def test_choice_for_a_match(self):
        from app.services.battle import question_bank as bank

        pool = [NS(id=uuid.uuid4(), topic=f"t{i % 6}", kind="grammar" if i % 3 == 0 else "vocab", ref=f"w{i}" if i % 2 else None,
                   format="grammar", answer=f"a{i}", wrong=[f"x{i}", f"y{i}", f"z{i}"], prompt=f"p{i}", hint=None, explanation=None) for i in range(40)]
        rng = random.Random(1)
        avoid = {str(q.id) for q in pool[:20]}
        chosen = bank.pick(pool, 10, rng, avoid_ids=avoid, avoid_refs={"w21"}, min_grammar=3)
        self.assertEqual(len({q.id for q in chosen}), 10)
        self.assertFalse({str(q.id) for q in chosen} & avoid)  # the recent questions only when nothing else is left
        self.assertNotIn("w21", {q.ref for q in chosen})
        self.assertGreaterEqual(sum(q.kind == "grammar" for q in chosen), 3)
        self.assertLessEqual(max(sum(q.topic == t for q in chosen) for t in {q.topic for q in chosen}), 2)
        small = bank.pick(pool[:10], 10, rng)  # a small pool relaxes the topic cap, never the uniqueness
        self.assertEqual(len({q.id for q in small}), 10)
        e = bank.round_entry(pool[0], 2, rng)
        self.assertEqual((e["opts"][2], e["c"], len(e["opts"])), ("a0", 2, 4))
        art = NS(**{**vars(pool[1]), "wrong": ["der", "die"], "answer": "das", "format": "article"})
        e = bank.round_entry(art, 3, rng)  # position 3 does not exist with 3 options
        self.assertLess(e["c"], 3)
        self.assertEqual(e["opts"][e["c"]], "das")


class TestApiContract(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("httpx"), "HTTP test: needs httpx (FastAPI TestClient)")
    def test_question_routes_mounted_and_guarded(self):
        from fastapi.testclient import TestClient

        from app.api.dependencies.auth import get_current_user
        from app.main import app

        paths = set(app.openapi()["paths"])
        for p in ("/api/v1/admin/battle/questions", "/api/v1/admin/battle/questions/stats", "/api/v1/admin/battle/questions/import",
                  "/api/v1/admin/battle/questions/{question_id}"):
            self.assertIn(p, paths)
        client = TestClient(app)
        qid = uuid.uuid4()
        calls = (("get", "/api/v1/admin/battle/questions/stats", None), ("get", "/api/v1/admin/battle/questions", None),
                 ("post", "/api/v1/admin/battle/questions", {"level": "A1"}), ("patch", f"/api/v1/admin/battle/questions/{qid}", {}),
                 ("delete", f"/api/v1/admin/battle/questions/{qid}", None), ("post", "/api/v1/admin/battle/questions/import", {"items": [{}]}))
        for method, url, body in calls:
            with self.subTest(method=method, url=url):
                self.assertEqual(getattr(client, method)(url, **({"json": body} if body is not None else {})).status_code, 401)
        student = NS(id=uuid.uuid4(), role="STUDENT", is_active=True, is_banned=False, is_superuser=False)
        support = NS(id=uuid.uuid4(), role="SUPPORT", is_active=True, is_banned=False, is_superuser=False)
        try:
            app.dependency_overrides[get_current_user] = lambda: student
            for method, url, body in calls:
                with self.subTest(method=method, url=url, who="student"):
                    self.assertEqual(getattr(client, method)(url, **({"json": body} if body is not None else {})).status_code, 403)
            app.dependency_overrides[get_current_user] = lambda: support  # staff may read, not write
            for method, url, body in calls[2:]:
                with self.subTest(method=method, url=url, who="support"):
                    self.assertEqual(getattr(client, method)(url, **({"json": body} if body is not None else {})).status_code, 403)
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_bodies_are_strict(self):
        from pydantic import ValidationError

        from app.api.battle.router import QuestionIn

        ok = {"level": "A1", "format": "de_uz", "topic": "essen", "prompt": "der Apfel", "answer": "olma", "wrong": ["non", "suv", "tuz"]}
        QuestionIn(**ok)
        for bad in ({**ok, "level": "C2"}, {**ok, "format": "essay"}, {**ok, "wrong": ["a", "b", "c", "d"]}, {**ok, "source": "seed"}):
            with self.assertRaises(ValidationError):
                QuestionIn(**bad)


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestQuestionsDb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.models.user import User

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        db = cls.Session()
        tag = uuid.uuid4().hex[:6]
        cls.ids = {}
        for name, role in (("anna", "STUDENT"), ("editor", "CONTENT_MANAGER")):
            u = User(email=f"bq-{name}-{tag}@test.local", username=f"bq_{name}_{tag}", password_hash="x", is_active=True, is_verified=True,
                     is_superuser=False, role=role, is_banned=False, preferred_language="uz", first_name=name.capitalize())
            db.add(u)
            db.flush()
            cls.ids[name] = u.id
        db.commit()
        db.close()

    @classmethod
    def _wipe(cls, db):
        from sqlalchemy import delete, text

        from app.models.audit_log import AuditLog

        db.execute(text("TRUNCATE battle_answers, battle_points_ledger, battle_matches, battle_profiles, battle_words, battle_images, battle_questions"))
        db.execute(delete(AuditLog).where(AuditLog.action.like("battle_question%")))
        db.commit()

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete

        from app.models.user import User

        db = cls.Session()
        cls._wipe(db)
        db.execute(delete(User).where(User.id.in_(list(cls.ids.values()))))
        db.commit()
        db.close()
        cls.engine.dispose()

    def setUp(self):
        from app.models.user import User

        self.db = self.Session()
        self._wipe(self.db)
        self.user = {k: self.db.get(User, v) for k, v in self.ids.items()}

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def _seed(self):
        from app.services.battle import question_seed as seed

        plan = seed.build_plan(self.db)
        return plan, seed.apply(self.db, plan["plan_id"])

    def test_seed_plan_apply_and_idempotent(self):
        from sqlalchemy import func, select

        from app.models.audit_log import AuditLog
        from app.models.battle import BattleQuestion
        from app.services.battle import question_seed as seed

        plan = seed.build_plan(self.db)
        self.assertEqual(plan["problems"], [])
        for lv in LEVELS:
            self.assertGreaterEqual(plan["counts"][lv]["add"], 500)
        with self.assertRaises(seed.SeedError):
            seed.apply(self.db, "000000000000")
        self.assertEqual(self.db.execute(select(func.count()).select_from(BattleQuestion)).scalar_one(), 0)  # nothing written
        out = seed.apply(self.db, plan["plan_id"])
        self.assertEqual(out["added"], plan["total_in_files"])
        again = seed.build_plan(self.db)
        self.assertEqual(sum(c["add"] for c in again["counts"].values()), 0)
        self.assertEqual(sum(c["keep"] for c in again["counts"].values()), plan["total_in_files"])
        published = dict(self.db.execute(select(BattleQuestion.level, func.count()).where(BattleQuestion.status == "published")
                                         .group_by(BattleQuestion.level)).all())
        self.assertTrue(all(published[lv] >= 500 for lv in LEVELS))
        self.assertEqual(self.db.execute(select(func.count()).select_from(AuditLog).where(AuditLog.action == "battle_questions_seeded")).scalar_one(), 1)

    def test_matches_mix_picture_and_text_rounds_and_never_repeat(self):
        from app.models.battle import BattleImage, BattleWord
        from app.services.battle import config, questions

        self._seed()
        for i in range(16):  # A1 picture words (no files needed to build a match)
            img = BattleImage(storage_name=f"{uuid.uuid4().hex}.webp", mime="image/webp", width=4, height=4, size_bytes=1, sha256=uuid.uuid4().hex * 2,
                              source="upload", author="T", license="CC0", status="published")
            self.db.add(img)
            self.db.flush()
            self.db.add(BattleWord(level="A1", article="das", lemma=f"Bildwort{i:02d}", translation=f"rasm {i}", category="essen", status="published", image_id=img.id))
        self.db.commit()
        rng = random.Random(3)
        for _ in range(20):
            a1 = questions.build(self.db, "A1", rng=rng, bot=True)
            self.assertEqual(sum(1 for q in a1 if q.get("t") != "q"), config.PICTURE_ROUNDS)
            text = [q for q in a1 if q.get("t") == "q"]
            self.assertEqual(len({q["q"] for q in text}), len(text))
            for q in a1:
                self.assertLess(q["c"], len(q["opts"]))
                self.assertLess(q["bot"]["choice"], len(q["opts"]))
            for stage in ("A2", "B1", "B2", "C1", "C1+"):
                m = questions.build(self.db, stage, rng=rng)
                self.assertTrue(all(q.get("t") == "q" for q in m))  # no own picture words → only level-appropriate text rounds
                self.assertEqual(len({q["q"] for q in m}), config.ROUNDS)
                self.assertGreaterEqual(sum(q["kind"] == "grammar" for q in m), config.MIN_GRAMMAR)
                refs = [q["ref"].lower() for q in m if q.get("ref")]
                self.assertEqual(len(refs), len(set(refs)))
        self.assertTrue(questions.readiness(self.db, "B1")["ready"])

    def test_text_round_view_hides_the_answer_until_the_reveal(self):
        from app.models.battle import BattleMatch
        from app.services.battle import engine

        self._seed()
        anna = self.user["anna"]
        clock = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)
        with patch("app.services.battle.engine._now", return_value=clock):
            m = engine.practice(self.db, anna)
        mid = m["id"]
        with patch("app.services.battle.engine._now", return_value=clock + timedelta(seconds=5)):
            st = engine.state(self.db, uuid.UUID(mid), anna)
        r = st["round"]
        self.assertEqual(r["kind"], "text")
        self.assertIsNone(r["image_url"])
        self.assertTrue(r["prompt"] and r["instruction"]["uz"] and r["category"]["de"])
        self.assertIsNone(r["correct"])
        self.assertIsNone(r["explanation"])
        raw = json.dumps(st, ensure_ascii=False)
        match = self.db.get(BattleMatch, uuid.UUID(mid))
        self.assertNotIn('"c"', raw)
        q = match.questions[0]
        # the picture endpoint has nothing for a text round
        from app.services.battle import media

        token = media.round_token(match.id, 1)  # a valid token (real clock): the round has no picture
        self.assertEqual(media.read_token(token)[1], 1)
        with self.assertRaises(HTTPException) as ctx:
            engine.media_for(self.db, token)
        self.assertEqual(ctx.exception.status_code, 404)
        with patch("app.services.battle.engine._now", return_value=clock + timedelta(seconds=6)):
            if len(q["opts"]) == 3:
                with self.assertRaises(HTTPException) as bad:
                    engine.answer(self.db, anna, uuid.UUID(mid), 1, 3)
                self.assertEqual(bad.exception.status_code, 422)
            st = engine.answer(self.db, anna, uuid.UUID(mid), 1, q["c"])
        self.assertTrue(st["round"]["my_answer"]["correct"])
        ended = max(2.0, q["bot"]["at"] / 1000)  # the round ends when both answered (mine after 2 s, the bot's at its planned time)
        with patch("app.services.battle.engine._now", return_value=clock + timedelta(seconds=4 + ended + 1.5)):
            st = engine.state(self.db, uuid.UUID(mid), anna)
        self.assertEqual(st["round"]["phase"], "reveal")
        self.assertEqual(st["round"]["correct"], q["c"])

    def test_admin_create_edit_delete_import_and_stats(self):
        from sqlalchemy import select

        from app.models.audit_log import AuditLog
        from app.models.battle import BattleQuestion
        from app.services.battle import question_bank as bank

        ed = self.user["editor"]
        base = {"level": "B1", "format": "grammar", "topic": "passiv", "prompt": "Der Kuchen ___ gerade gebacken.", "answer": "wird",
                "wrong": ["ist", "hat", "werden"], "explanation": "Passiv Präsens", "status": "published"}
        made = bank.create(self.db, ed, base)
        self.assertEqual((made["kind"], made["source"], made["problems"]), ("grammar", "admin", []))
        with self.assertRaises(HTTPException) as ctx:  # the same question again (case / spaces / quotes do not matter)
            bank.create(self.db, ed, {**base, "prompt": "der kuchen  ___ gerade gebacken"})
        self.assertEqual(ctx.exception.status_code, 409)
        with self.assertRaises(HTTPException) as ctx:  # two correct answers
            bank.create(self.db, ed, {**base, "prompt": "Das Brot ___ gebacken.", "wrong": ["wird", "hat", "ist"]})
        self.assertEqual(ctx.exception.status_code, 422)
        upd = bank.update(self.db, ed, uuid.UUID(made["id"]), {"wrong": ["ist", "hat", "wurde"], "hint": None})
        self.assertEqual(upd["wrong"], ["ist", "hat", "wurde"])
        uz = bank.create(self.db, ed, {"level": "A1", "format": "de_uz", "topic": "essen", "prompt": "das Salz (Test)", "answer": "tuz",
                                       "wrong": ["go'sht", "non", "suv"], "status": "draft"})
        self.assertIn("go‘sht", uz["wrong"])  # apostrophes unified
        report = bank.import_questions(self.db, ed, [base, {**base, "prompt": "Die Briefe ___ morgen verschickt.", "answer": "werden", "wrong": ["wird", "haben", "wurden"]},
                                                     {**base, "prompt": "Die Briefe ___ morgen verschickt.", "answer": "werden", "wrong": ["wird", "haben", "wurden"]},
                                                     {**base, "prompt": "Ohne Antwort ___", "answer": "", "wrong": ["a", "b", "c"]}, "kein Objekt"],
                                       apply=False, publish=True)
        self.assertEqual((report["valid"], report["duplicates"], report["invalid"], report["added"]), (1, 2, 2, 0))
        report = bank.import_questions(self.db, ed, [{**base, "prompt": "Die Briefe ___ morgen verschickt.", "answer": "werden", "wrong": ["wird", "haben", "wurden"]}],
                                       apply=True, publish=True)
        self.assertEqual(report["added"], 1)
        stats = bank.stats(self.db)
        self.assertEqual((stats["levels"]["B1"]["total"], stats["levels"]["B1"]["grammar"], stats["levels"]["B1"]["published"]), (2, 2, 2))
        self.assertEqual((stats["levels"]["A1"]["draft"], stats["levels"]["A1"]["vocab"]), (1, 1))
        self.db.execute(select(BattleQuestion).where(BattleQuestion.id == uuid.UUID(uz["id"]))).scalar_one().answer = "non"  # a broken row
        self.db.commit()
        self.assertEqual(bank.stats(self.db)["levels"]["A1"]["problems"], 1)
        listed = bank.list_questions(self.db, "A1", None, None, None, None, "", True, 1)
        self.assertEqual([i["id"] for i in listed["items"]], [uz["id"]])
        bank.delete(self.db, ed, uuid.UUID(uz["id"]))
        self.assertIsNone(self.db.get(BattleQuestion, uuid.UUID(uz["id"])))
        actions = set(self.db.execute(select(AuditLog.action).where(AuditLog.actor_id == str(ed.id))).scalars())
        self.assertTrue({"battle_question_created", "battle_question_updated", "battle_question_deleted", "battle_questions_imported"} <= actions)


if __name__ == "__main__":
    unittest.main()
