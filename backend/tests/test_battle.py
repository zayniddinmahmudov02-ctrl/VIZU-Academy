"""VIZU DEUTSCH BATTLE: ranks / scoring / points, distractor engine, signed picture URLs, image
validation and the API contract without a database; matchmaking, the server clock, answers, AFK,
points ledger, IDOR, admin rules and themes against PostgreSQL (VIZU_WB_TEST_DB_URL = a migrated test
database; the battle_* tables are emptied per test)."""

import io
import os
import random
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")


def _dependency_calls(dependant) -> list:
    calls = []
    for d in dependant.dependencies:
        calls.append(d.call)
        calls.extend(_dependency_calls(d))
    return calls


def _webp(size=(400, 400), color=(200, 30, 30)) -> bytes:
    from PIL import Image

    out = io.BytesIO()
    Image.new("RGB", size, color).save(out, "PNG")
    return out.getvalue()


class TestConfig(unittest.TestCase):
    def test_ranks_follow_points(self):
        from app.services.battle import config

        self.assertEqual(config.rank_info(0)["title"], "A1-Einsteiger")
        self.assertEqual(config.rank_info(300)["title"], "A1-Meister")
        self.assertEqual(config.rank_info(450)["stage"], "A2")
        top = config.rank_info(10_000)
        self.assertEqual((top["stage"], top["title"], top["next_at"]), ("C1+", "C1+-Legende", None))
        info = config.rank_info(200)
        self.assertEqual((info["remaining"], info["next_title"]), (100, "A1-Meister"))

    def test_word_levels_never_above_c1(self):
        from app.services.battle import config

        self.assertEqual(config.word_levels_up_to("A2"), ["A1", "A2"])
        self.assertEqual(config.word_levels_up_to("C1+"), ["A1", "A2", "B1", "B2", "C1"])

    def test_match_window_widens(self):
        from app.services.battle import config

        self.assertEqual([config.match_window(s) for s in (0, 9.9, 10, 19, 25)], [10, 10, 25, 25, None])

    def test_scoring(self):
        from app.services.battle import config

        self.assertEqual(config.round_score(False, 100), 0)
        self.assertEqual(config.round_score(True, 0), 150)
        self.assertEqual(config.round_score(True, config.ROUND_S * 1000), 100)

    def test_points(self):
        from app.services.battle import config

        self.assertEqual(config.points_delta("win", 100, 100, 1), 25)
        self.assertEqual(config.points_delta("win", 100, 300, 3), 25 + 10 + 4)
        self.assertEqual(config.points_delta("draw", 0, 0, 0), 5)
        self.assertEqual(config.points_delta("loss", 300, 100, 0), -25)
        self.assertEqual(config.points_delta("loss", 100, 400, 0), -5)


def _w(lemma, category, article="der", translation=None, word_type="Nomen"):
    return SimpleNamespace(id=uuid.uuid4(), lemma=lemma, article=article, display=f"{article} {lemma}", category=category,
                           translation=translation or lemma.lower(), image_id=uuid.uuid4(), level="A1")


class TestDistractors(unittest.TestCase):
    def test_same_category_first_and_conflicts_excluded(self):
        from app.services.battle import questions

        words = [_w("Zug", "verkehr"), _w("Straßenbahn", "verkehr", "die"), _w("Auto", "verkehr", "das"), _w("Fahrrad", "verkehr", "das"),
                 _w("Flugzeug", "verkehr", "das"), _w("Bahnhof", "orte"), _w("Hund", "tiere"), _w("Katze", "tiere", "die")]
        for seed in range(30):
            out = questions._distractors(words[0], words, random.Random(seed), 3)
            lemmas = {w.lemma for w in out}
            self.assertEqual(len(out), 3)
            self.assertNotIn("Straßenbahn", lemmas)
            self.assertNotIn("Bahnhof", lemmas)
            self.assertTrue(all(w.category == "verkehr" for w in out))

    def test_no_duplicate_translation_or_display(self):
        from app.services.battle import questions

        target = _w("Uhr", "alltag", "die", translation="soat")
        words = [target, _w("Wecker", "alltag", translation="soat"), _w("Schuh", "alltag"), _w("Koffer", "alltag"), _w("Schlüssel", "alltag")]
        out = questions._distractors(target, words, random.Random(1), 3)
        self.assertNotIn("Wecker", [w.lemma for w in out])

    def test_positions_balanced(self):
        from app.services.battle import questions

        pos = questions.balanced_positions(10, random.Random(3))
        self.assertEqual(sorted(pos.count(i) for i in range(4)), [2, 2, 3, 3])

    def test_word_data_is_consistent(self):
        from app.services.battle import questions

        data = questions.word_data()
        lemmas = [w["lemma"] for w in data["words"]]
        self.assertEqual(len(lemmas), len(set(lemmas)))
        self.assertTrue(all(w["category"] in data["categories"] for w in data["words"]))
        self.assertTrue(all(a in lemmas and b in lemmas for a, b in data["conflicts"]))


class TestMedia(unittest.TestCase):
    def test_round_token(self):
        from app.services.battle import media

        mid = uuid.uuid4()
        token = media.round_token(mid, 3, now=1000.0)
        self.assertEqual(media.read_token(token, now=1050.0), (mid, 3))
        with self.assertRaises(HTTPException):
            media.read_token(token, now=1000.0 + media.TOKEN_TTL_S + 1)
        forged = token.replace(".3.", ".4.")
        with self.assertRaises(HTTPException):
            media.read_token(forged, now=1050.0)
        self.assertNotIn(str(uuid.uuid4()), token)

    def test_normalise_reencodes_and_rejects(self):
        from app.services.battle import media

        out, w, h = media.normalise(_webp((1200, 800)), "x.png", "image/png", 960)
        self.assertEqual((out[:4], out[8:12], w, h), (b"RIFF", b"WEBP", 960, 640))
        for data, name, mime, code in ((b"<svg/>", "x.png", "image/png", "IMAGE_INVALID"), (_webp(), "x.gif", "image/gif", "IMAGE_EXTENSION"),
                                       (_webp((100, 100)), "x.png", "image/png", "IMAGE_TOO_SMALL"), (_webp(), "x.png", "image/jpeg", "IMAGE_TYPE")):
            with self.subTest(code=code), self.assertRaises(HTTPException) as ctx:
                media.normalise(data, name, mime, 960)
            self.assertEqual(ctx.exception.detail, code)

    def test_safe_path(self):
        from app.services.battle import media

        for name in ("../x.webp", "a/b.webp", "x.png", ""):
            with self.subTest(name=name), self.assertRaises(HTTPException):
                media.safe_path(media.IMAGE_ROOT, name)


class TestApiContract(unittest.TestCase):
    PUBLIC = {"/battle/media/{token}", "/battle/themes/assets/{name}"}

    def test_student_routes_need_a_user(self):
        from app.api.battle.router import router
        from app.api.dependencies.auth import get_current_user

        for r in router.routes:
            with self.subTest(route=r.path):
                calls = _dependency_calls(r.dependant)
                if r.path in self.PUBLIC:
                    self.assertNotIn(get_current_user, calls)
                else:
                    self.assertIn(get_current_user, calls)

    def test_admin_routes_need_staff_and_writes_need_an_editor(self):
        from app.api.battle.router import admin_router
        from app.api.dependencies.auth import require_admin_panel_access, require_content_editor

        for r in admin_router.routes:
            with self.subTest(route=r.path, methods=r.methods):
                calls = [d.call for d in r.dependant.dependencies]
                if r.methods & {"POST", "PUT", "PATCH", "DELETE"} or r.path.endswith("/commons/search"):
                    self.assertIn(require_content_editor, calls)
                else:
                    self.assertIn(require_admin_panel_access, calls)

    def test_open_to_every_logged_in_user(self):
        """Battle is a free gamification module: no course, lesson, premium or staff dependency on student routes."""
        from app.api.battle.router import router
        from app.api.dependencies.auth import get_current_user
        from app.db.session import get_db

        for r in router.routes:
            with self.subTest(route=r.path):
                self.assertLessEqual({d.call for d in r.dependant.dependencies}, {get_db, get_current_user})
        self.assertIn("/battle/summary", {r.path for r in router.routes})

    def test_bodies_cannot_carry_scores_or_users(self):
        from app.api.battle.router import AnswerIn, ThemeDraftIn

        with self.assertRaises(ValidationError):
            AnswerIn(round=1, choice=0, correct=True)
        with self.assertRaises(ValidationError):
            AnswerIn(round=1, choice=4)
        with self.assertRaises(ValidationError):
            AnswerIn(round=1, choice=0, time_ms=1)
        with self.assertRaises(ValidationError):
            ThemeDraftIn(level="A1")

    def test_mounted_under_api_v1(self):
        from app.main import app

        paths = set(app.openapi()["paths"])
        for p in ("/api/v1/battle/home", "/api/v1/battle/queue", "/api/v1/battle/matches/{match_id}/answer", "/api/v1/admin/battle/words"):
            self.assertIn(p, paths)


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestBattleDb(unittest.TestCase):
    CATEGORIES = ("essen", "tiere", "wohnen", "verkehr")

    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.models.user import User

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        db = cls.Session()
        tag = uuid.uuid4().hex[:6]

        def user(role, name):
            u = User(email=f"bt-{name}-{tag}@test.local", username=f"bt_{name}_{tag}", password_hash="x", is_active=True, is_verified=True,
                     is_superuser=False, role=role, is_banned=False, preferred_language="uz", first_name=name.capitalize())
            db.add(u)
            return u

        cls.u = {n: user(r, n) for n, r in (("anna", "STUDENT"), ("bek", "STUDENT"), ("carl", "STUDENT"), ("editor", "CONTENT_MANAGER"))}
        db.commit()
        cls.ids = {k: v.id for k, v in cls.u.items()}
        db.close()

    @classmethod
    def _wipe(cls, db):
        from sqlalchemy import text

        db.execute(text("TRUNCATE battle_answers, battle_points_ledger, battle_matches, battle_profiles, battle_words, battle_images, battle_themes"))
        db.execute(text("DELETE FROM dictionary_entries WHERE source_id >= 900000"))
        db.commit()

    @classmethod
    def tearDownClass(cls):
        db = cls.Session()
        cls._wipe(db)
        db.close()
        cls.engine.dispose()

    def setUp(self):
        from app.models.user import User

        self.db = self.Session()
        self._wipe(self.db)
        self.user = {k: self.db.get(User, v) for k, v in self.ids.items()}
        self.files = []
        self.clock = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
        self.words = self._seed_words(16)

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        for f in self.files:
            f.unlink(missing_ok=True)

    # helpers

    def _seed_words(self, n, status="published"):
        from app.models.battle import BattleImage, BattleWord
        from app.models.dictionary import DictionaryEntry
        from app.services.battle import media

        media.IMAGE_ROOT.mkdir(parents=True, exist_ok=True)
        out = []
        for i in range(n):
            lemma = f"Testwort{i:02d}"
            e = DictionaryEntry(level="A1", source_id=900000 + i, lemma=lemma, word_type="Nomen", article="das", translation=f"so‘z {i}", status="verified",
                                group_key=f"t{i}", search_de=lemma.lower(), search_uz=f"soz {i}", content_hash="x" * 64)
            self.db.add(e)
            self.db.flush()
            name = f"{uuid.uuid4().hex}.webp"
            (media.IMAGE_ROOT / name).write_bytes(b"RIFF0000WEBP")
            self.files.append(media.IMAGE_ROOT / name)
            img = BattleImage(storage_name=name, mime="image/webp", width=400, height=400, size_bytes=12, sha256=uuid.uuid4().hex * 2, source="upload",
                              author="Test", license="CC0", status=status)
            self.db.add(img)
            self.db.flush()
            w = BattleWord(entry_id=e.id, level="A1", article="das", lemma=lemma, translation=e.translation, category=self.CATEGORIES[i % 4],
                           status=status, image_id=img.id)
            self.db.add(w)
            out.append(w)
        self.db.commit()
        return out

    def _at(self, seconds):
        return patch("app.services.battle.engine._now", return_value=self.clock + timedelta(seconds=seconds))

    def _status(self, fn, *args, **kwargs):
        with self.assertRaises(HTTPException) as ctx:
            fn(*args, **kwargs)
        return ctx.exception.status_code, str(ctx.exception.detail).split(":")[0]

    def _pair(self):
        from app.services.battle import engine

        with self._at(0):
            a = engine.queue(self.db, self.user["anna"])
            self.assertEqual(a["status"], "waiting")
            b = engine.queue(self.db, self.user["bek"])
        self.assertEqual(b["id"], a["id"])
        self.assertEqual(b["status"], "active")
        return a["id"]

    def _correct(self, match_id, round_no):
        from app.models.battle import BattleMatch

        self.db.expire_all()
        return self.db.get(BattleMatch, uuid.UUID(match_id)).questions[round_no - 1]["c"]

    # tests

    def test_matchmaking_and_full_match(self):
        from app.models.battle import BattlePointsLedger, BattleProfile
        from app.services.battle import config, engine

        mid = self._pair()
        with self._at(1):
            s = engine.state(self.db, mid, self.user["anna"])
        self.assertIsNone(s["round"])
        self.assertEqual(s["opponent"]["name"], "Bek")
        t = config.COUNTDOWN_S
        for r in range(1, config.ROUNDS + 1):
            with self._at(t + 1):
                s = engine.state(self.db, mid, self.user["anna"])
                self.assertEqual((s["round"]["no"], s["round"]["phase"]), (r, "question"))
                self.assertIsNone(s["round"]["correct"])
                self.assertNotIn("c", s["round"])
                self.assertEqual(len(s["round"]["options"]), 4)
                c = self._correct(mid, r)
                engine.answer(self.db, self.user["anna"], uuid.UUID(mid), r, c)
                self.assertEqual(self._status(engine.answer, self.db, self.user["anna"], uuid.UUID(mid), r, c), (409, "ALREADY_ANSWERED"))
                s = engine.answer(self.db, self.user["bek"], uuid.UUID(mid), r, (c + 1) % 4)
                self.assertEqual(s["round"]["phase"], "reveal")
                self.assertEqual(s["round"]["correct"], c)
            t += 1 + config.REVEAL_S
        with self._at(t + 1):
            s = engine.state(self.db, mid, self.user["anna"])
            sb = engine.state(self.db, mid, self.user["bek"])
        self.assertEqual(s["status"], "finished")
        self.assertEqual((s["result"]["outcome"], sb["result"]["outcome"]), ("win", "loss"))
        self.assertEqual(s["me"]["score"], config.ROUNDS * config.round_score(True, 1000))
        self.assertEqual((s["result"]["points_delta"], sb["result"]["points_delta"]), (25, 0))
        self.db.expire_all()
        ledger = self.db.query(BattlePointsLedger).all()
        self.assertEqual(sorted(l.delta for l in ledger), [0, 25])
        anna = self.db.query(BattleProfile).filter_by(user_id=self.ids["anna"]).one()
        self.assertEqual((anna.points, anna.wins, anna.streak), (25, 1, 1))

    def test_double_answer_and_late_answer(self):
        from app.services.battle import config, engine

        mid = uuid.UUID(self._pair())
        t = config.COUNTDOWN_S
        with self._at(t + 2):
            engine.answer(self.db, self.user["anna"], mid, 1, 0)
            self.assertEqual(self._status(engine.answer, self.db, self.user["anna"], mid, 1, 1), (409, "ALREADY_ANSWERED"))
            self.assertEqual(self._status(engine.answer, self.db, self.user["anna"], mid, 2, 1), (409, "ROUND_CLOSED"))
        with self._at(t + config.ROUND_S + 1):
            self.assertEqual(self._status(engine.answer, self.db, self.user["bek"], mid, 1, 1), (409, "ROUND_CLOSED"))
            s = engine.state(self.db, mid, self.user["bek"])
        self.assertEqual(s["round"]["phase"], "reveal")
        self.assertIsNone(s["round"]["my_answer"]["choice"])

    def test_third_user_cannot_see_or_answer(self):
        from app.services.battle import engine

        mid = uuid.UUID(self._pair())
        with self._at(5):
            self.assertEqual(self._status(engine.state, self.db, mid, self.user["carl"]), (404, "MATCH_NOT_FOUND"))
            self.assertEqual(self._status(engine.answer, self.db, self.user["carl"], mid, 1, 0), (404, "MATCH_NOT_FOUND"))
            self.assertEqual(self._status(engine.leave, self.db, self.user["carl"], mid), (404, "MATCH_NOT_FOUND"))

    def test_afk_player_loses(self):
        from app.services.battle import config, engine

        mid = self._pair()
        for t in range(2, config.AFK_S + 3, 5):
            with self._at(t):
                engine.state(self.db, mid, self.user["anna"])
        with self._at(config.AFK_S + 3):
            s = engine.state(self.db, mid, self.user["anna"])
        self.assertEqual((s["status"], s["result"]["outcome"], s["result"]["reason"]), ("finished", "win", "afk"))

    def test_leave_is_a_forfeit_and_waiting_leave_cancels(self):
        from app.services.battle import engine

        with self._at(0):
            w = engine.queue(self.db, self.user["carl"])
            self.assertEqual(engine.leave(self.db, self.user["carl"], uuid.UUID(w["id"]))["status"], "cancelled")
        mid = uuid.UUID(self._pair())
        with self._at(6):
            s = engine.leave(self.db, self.user["bek"], mid)
        self.assertEqual((s["result"]["outcome"], s["result"]["reason"]), ("loss", "forfeit"))

    def test_points_window_and_waiting_players_meet(self):
        from app.services.battle import engine, profiles

        p = profiles.get_profile(self.db, self.ids["bek"])
        p.points = 140
        self.db.commit()
        with self._at(0):
            a = engine.queue(self.db, self.user["anna"])
            b = engine.queue(self.db, self.user["bek"])
        self.assertNotEqual(a["id"], b["id"])
        self.assertEqual(b["status"], "waiting")
        with self._at(9):
            engine.state(self.db, a["id"], self.user["anna"])
            self.assertEqual(engine.state(self.db, b["id"], self.user["bek"])["status"], "waiting")
        with self._at(21):
            sa = engine.state(self.db, a["id"], self.user["anna"])
            sb = engine.state(self.db, b["id"], self.user["bek"])
        self.assertEqual((sa["status"], sb["status"]), ("active", "active"))
        self.assertEqual(sa["id"], sb["id"])

    def test_bot_and_private_rooms_give_no_points(self):
        from app.models.battle import BattlePointsLedger
        from app.services.battle import config, engine

        with self._at(0):
            s = engine.practice(self.db, self.user["anna"])
        self.assertEqual((s["mode"], s["opponent"]["is_bot"]), ("bot", True))
        with self._at(config.COUNTDOWN_S + 10):
            s = engine.state(self.db, s["id"], self.user["anna"])
        self.assertTrue(s["round"]["opponent_answered"])
        with self._at(200):
            engine.leave(self.db, self.user["anna"], uuid.UUID(s["id"]))
            room = engine.create_room(self.db, self.user["anna"])
            self.assertEqual(len(room["room_code"]), 6)
            self.assertEqual(self._status(engine.join_room, self.db, self.user["anna"], room["room_code"]), (409, "MATCH_ALREADY_OPEN"))
            joined = engine.join_room(self.db, self.user["bek"], room["room_code"].lower())
            self.assertEqual(joined["status"], "active")
            engine.leave(self.db, self.user["bek"], uuid.UUID(joined["id"]))
        self.assertEqual(self.db.query(BattlePointsLedger).count(), 0)

    def test_not_enough_words(self):
        from sqlalchemy import update

        from app.models.battle import BattleWord
        from app.services.battle import engine

        self.db.execute(update(BattleWord).values(status="draft"))
        self.db.commit()
        with self._at(0):
            self.assertEqual(self._status(engine.queue, self.db, self.user["anna"]), (409, "BATTLE_NOT_ENOUGH_WORDS"))

    def test_picture_url_only_for_the_running_round(self):
        from app.services.battle import config, engine, media

        mid = self._pair()
        with self._at(config.COUNTDOWN_S + 1):
            s = engine.state(self.db, mid, self.user["anna"])
        token = s["round"]["image_url"].rsplit("/", 1)[1]
        with patch("app.services.battle.media.time.time", return_value=(self.clock + timedelta(seconds=config.COUNTDOWN_S + 3)).timestamp()):
            resp = engine.media_for(self.db, token)
            self.assertEqual(resp.media_type, "image/webp")
            bad = media.round_token(uuid.UUID(mid), 99)
            self.assertEqual(self._status(engine.media_for, self.db, bad), (404, "NOT_FOUND"))
        self.assertNotIn("Testwort", s["round"]["image_url"])
        with patch("app.services.battle.media.time.time", return_value=(self.clock + timedelta(minutes=10)).timestamp()):
            self.assertEqual(self._status(engine.media_for, self.db, token), (404, "NOT_FOUND"))

    def test_admin_publish_rules(self):
        from app.models.battle import BattleImage
        from app.services.battle import admin

        editor = self.user["editor"]
        w = self.words[0]
        img = self.db.get(BattleImage, w.image_id)
        img.status = "draft"
        self.db.commit()
        self.assertEqual(self._status(admin.set_image_status, self.db, editor, img.id, "published", None), (409, "IMAGE_NOT_VERIFIED"))
        admin.set_image_status(self.db, editor, img.id, "verified", "ok")
        admin.set_image_status(self.db, editor, img.id, "published", None)
        admin.update_word(self.db, editor, w.id, {"status": "published"})
        admin.set_image_status(self.db, editor, img.id, "rejected", "falsches Motiv")
        self.db.refresh(w)
        self.assertEqual(w.status, "draft")
        self.assertEqual(self._status(admin.update_word, self.db, editor, w.id, {"status": "published"}), (409, "WORD_NEEDS_PUBLISHED_IMAGE"))
        self.assertEqual(self._status(admin.add_word, self.db, editor, "A1-900001", "essen"), (409, "WORD_EXISTS"))
        self.assertEqual(self._status(admin.add_word, self.db, editor, "A1-900001", "nope"), (422, "CATEGORY_UNKNOWN"))

    def test_theme_draft_preview_publish(self):
        from app.models.battle import BattleTheme
        from app.services.battle import themes

        editor = self.user["editor"]
        d = themes.defaults()[0]
        self.db.add(BattleTheme(level=d["stage"], **{f: d[f] for f in themes.FIELDS}, published_at=self.clock))
        self.db.commit()
        live_city = d["city"]
        themes.save_draft(self.db, editor, "A1", {"city": "Potsdam", "overlay": 70, "attribution": {"author": "", "license": ""}})
        self.assertEqual(themes.for_stage(self.db, "A1")["city"], live_city)
        self.assertEqual(self._status(themes.publish, self.db, editor, "A1"), (422, "THEME_ATTRIBUTION_REQUIRED"))
        themes.save_draft(self.db, editor, "A1", {"attribution": {"author": "X", "license": "CC BY-SA 4.0"}})
        themes.publish(self.db, editor, "A1")
        self.assertEqual((themes.for_stage(self.db, "A1")["city"], themes.for_stage(self.db, "A1")["overlay"]), ("Potsdam", 70))
        for bad in ({"desktop_image": "https://evil.example/x.jpg"}, {"accent": "red"}, {"overlay": 95}, {"title": ""}):
            with self.subTest(bad=bad):
                self.assertEqual(self._status(themes.save_draft, self.db, editor, "A1", bad)[0], 422)

    def test_rank_up_notifies_and_photo_reaches_every_card(self):
        from app.models.notification import Notification
        from app.services.battle import engine, home, profiles

        anna = self.user["anna"]
        anna.profile_image = "/uploads/avatars/" + "a" * 32 + ".webp"
        for who in ("anna", "bek"):
            profiles.get_profile(self.db, self.ids[who]).points = 440
        self.db.commit()
        mid = self._pair()
        with self._at(6):
            self.assertEqual(engine.state(self.db, mid, self.user["bek"])["opponent"]["photo"], anna.profile_image)
            engine.leave(self.db, self.user["bek"], uuid.UUID(mid))
            s = engine.state(self.db, mid, anna)
        self.assertTrue(s["result"]["stage_up"])
        self.assertEqual(s["me"]["photo"], anna.profile_image)
        notes = self.db.query(Notification).filter_by(user_id=self.ids["anna"], type="battle").all()
        self.assertEqual(len(notes), 1)
        self.assertIn("A2-Einsteiger", notes[0].title)
        self.assertEqual(notes[0].link_path, "/battle")
        self.assertEqual(self.db.query(Notification).filter_by(user_id=self.ids["bek"], type="battle").count(), 0)
        board = profiles.leaderboard(self.db, self.user["bek"])
        self.assertEqual(board["items"][0]["photo"], anna.profile_image)
        self.assertEqual(profiles.recent_matches(self.db, self.user["bek"])[0]["opponent_photo"], anna.profile_image)
        sm = home.summary(self.db, anna)
        self.assertEqual((sm["played"], sm["wins"], sm["rank"]["stage"]), (True, 1, "A2"))
        self.db.query(Notification).filter(Notification.user_id.in_(list(self.ids.values()))).delete(synchronize_session=False)
        anna.profile_image = None
        self.db.commit()

    def test_leaderboard_and_avatars(self):
        from app.services.battle import profiles

        p = profiles.get_profile(self.db, self.ids["bek"])
        p.points, p.wins = 500, 3
        self.db.commit()
        board = profiles.leaderboard(self.db, self.user["anna"])
        self.assertEqual(board["items"][0]["name"], "Bek")
        self.assertNotIn("email", board["items"][0])
        self.assertEqual(board["me"]["position"], 2)
        self.assertEqual(self._status(profiles.set_avatar, self.db, self.user["anna"], "legend"), (403, "AVATAR_LOCKED"))
        self.assertEqual(profiles.set_avatar(self.db, self.user["bek"], "scholar")["avatar"], "scholar")
