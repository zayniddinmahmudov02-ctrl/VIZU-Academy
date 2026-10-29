"""Global Chat: API contract, word filter and calendar maths without a
database; history, sending, mute / ban, pins, moderation, unread counts and
the separation from group chats against PostgreSQL (set VIZU_WB_TEST_DB_URL to
a migrated test database — the global_chat_* tables are emptied per test)."""

import os
import time
import unittest
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from pydantic import ValidationError

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")


def _now():
    return datetime.now(timezone.utc)


def _dependency_calls(dependant) -> list:
    calls = []
    for d in dependant.dependencies:
        calls.append(d.call)
        calls.extend(_dependency_calls(d))
    return calls


class TestApiContract(unittest.TestCase):
    def test_every_route_requires_a_logged_in_user(self):
        from app.api.dependencies.auth import get_current_user
        from app.api.global_chat.router import admin_router, router

        for r in (*router.routes, *admin_router.routes):
            with self.subTest(route=r.path):
                self.assertIn(get_current_user, _dependency_calls(r.dependant))

    def test_every_admin_route_requires_a_moderator(self):
        from app.api.global_chat.router import admin_router, moderator

        for r in admin_router.routes:
            with self.subTest(route=r.path):
                self.assertIn(moderator, [d.call for d in r.dependant.dependencies])

    def test_routes_are_mounted_under_api_v1(self):
        from app.main import app

        paths = set(app.openapi()["paths"])
        for p in ("/api/v1/global-chat/messages", "/api/v1/global-chat/updates", "/api/v1/global-chat/unread-count",
                  "/api/v1/admin/global-chat/restrictions", "/api/v1/admin/global-chat/messages/{message_id}",
                  "/api/v1/admin/global-chat/messages/{message_id}/edits"):
            self.assertIn(p, paths)
        own = app.openapi()["paths"]["/api/v1/global-chat/messages/{message_id}"]
        self.assertEqual(set(own), {"patch", "delete"})

    def test_bodies_cannot_smuggle_user_or_role(self):
        from app.api.global_chat.router import MessageIn, ModerateIn, RestrictionIn

        with self.assertRaises(ValidationError):
            MessageIn(body="hi", user_id=str(uuid.uuid4()))
        with self.assertRaises(ValidationError):
            MessageIn(body="hi", sender_id=str(uuid.uuid4()))
        with self.assertRaises(ValidationError):
            ModerateIn(action="pin", role="SUPER_ADMIN")
        with self.assertRaises(ValidationError):
            RestrictionIn(user_id=uuid.uuid4(), kind="ban", duration="1y", reason="spam", created_by=uuid.uuid4())

    def test_reply_body_carries_only_an_id(self):
        from app.api.global_chat.router import MessageIn, SendIn

        target = uuid.uuid4()
        self.assertEqual(SendIn(body="hi", reply_to_id=str(target)).reply_to_id, target)
        self.assertIsNone(SendIn(body="hi").reply_to_id)  # old clients: no reply
        with self.assertRaises(ValidationError):
            SendIn(body="hi", reply_to_id="not-a-uuid")
        # the quote is never taken from the client
        for extra in ({"reply_to_body": "fake"}, {"reply_to_sender": "Admin"}, {"sender_id": str(uuid.uuid4())}):
            with self.subTest(extra=extra), self.assertRaises(ValidationError):
                SendIn(body="hi", reply_to_id=str(target), **extra)
        # editing cannot move a reply to another message
        with self.assertRaises(ValidationError):
            MessageIn(body="neu", reply_to_id=str(target))

    def test_reply_preview_is_built_from_the_target(self):
        from types import SimpleNamespace

        from app.services.global_chat.messages import REPLY_EXCERPT, reply_preview

        viewer = SimpleNamespace(id=uuid.uuid4(), role="STUDENT")
        author = SimpleNamespace(id=uuid.uuid4(), first_name="Aziz", last_name="", username="aziz", role="STUDENT")

        def msg(**kw):
            base = {"reply_to_id": None, "reply_to": None, "status": "visible", "sender_id": author.id, "sender": author, "body": "x"}
            return SimpleNamespace(**{**base, **kw})

        self.assertIsNone(reply_preview(msg(), viewer))
        long_text = "Hallo  👋\n" + "ä" * 400
        target = msg(id=uuid.uuid4(), body=long_text)
        p = reply_preview(msg(reply_to_id=target.id, reply_to=target), viewer)
        self.assertTrue(p["available"])
        self.assertEqual(p["sender"]["name"], "Aziz")
        self.assertLessEqual(len(p["excerpt"]), REPLY_EXCERPT)
        self.assertTrue(p["excerpt"].startswith("Hallo 👋 ä"))  # whitespace collapsed, emoji kept
        self.assertTrue(p["excerpt"].endswith("…"))
        for status in ("deleted", "hidden"):
            with self.subTest(status=status):
                gone = msg(id=uuid.uuid4(), status=status, body="geheim")
                p = reply_preview(msg(reply_to_id=gone.id, reply_to=gone), viewer)
                self.assertEqual(p, {"id": gone.id, "available": False, "sender": None, "excerpt": None})
        # someone else's held message stays unknown; one's own held message is quoted to oneself
        held = msg(id=uuid.uuid4(), status="pending", body="wartet")
        self.assertFalse(reply_preview(msg(reply_to_id=held.id, reply_to=held), viewer)["available"])
        own_held = msg(id=uuid.uuid4(), status="pending", sender_id=viewer.id, body="meins")
        self.assertTrue(reply_preview(msg(reply_to_id=own_held.id, reply_to=own_held), viewer)["available"])

    def test_message_length_and_content(self):
        from app.api.global_chat.router import MessageIn
        from app.services.global_chat.messages import MAX_LENGTH, clean_text

        self.assertEqual(MAX_LENGTH, 2000)
        MessageIn(body="x" * 2000)
        with self.assertRaises(ValidationError):
            MessageIn(body="x" * 2001)
        with self.assertRaises(ValidationError):
            MessageIn(body="")
        for blank in ("   ", "\n\t ", "\x00\x07"):
            with self.assertRaises(HTTPException) as ctx:
                clean_text(blank)
            self.assertEqual(ctx.exception.detail, "empty")
        self.assertEqual(clean_text(" a\x00b\r\nc "), "ab\nc")
        # HTML is kept as plain text — escaping is the renderer's job, nothing is interpreted here
        self.assertEqual(clean_text("<script>alert(1)</script>"), "<script>alert(1)</script>")

    def test_calendar_years(self):
        from app.services.global_chat.restrictions import add_years

        utc = timezone.utc
        self.assertEqual(add_years(datetime(2026, 10, 29, 14, 5, tzinfo=utc), 1), datetime(2027, 10, 29, 14, 5, tzinfo=utc))
        self.assertEqual(add_years(datetime(2027, 3, 1, tzinfo=utc), 1), datetime(2028, 3, 1, tzinfo=utc))  # 366 days, still 1 year
        self.assertEqual(add_years(datetime(2028, 2, 29, tzinfo=utc), 1), datetime(2029, 2, 28, tzinfo=utc))
        self.assertEqual(add_years(datetime(2028, 2, 29, tzinfo=utc), 4), datetime(2032, 2, 29, tzinfo=utc))
        self.assertEqual(add_years(datetime(2026, 1, 15, tzinfo=utc), 5), datetime(2031, 1, 15, tzinfo=utc))


class TestWordFilter(unittest.TestCase):
    def setUp(self):
        from app.services.global_chat.word_filter import DEFAULT_WORDS, find

        self.find = lambda text: find(text, DEFAULT_WORDS)

    def test_catches_common_insults(self):
        for text in ("you are a FUCKING idiot", "fuuuuck", "Du Hurensohn!", "du arschloch", "ты сука", "иди нахуй", "хуйня какая-то",
                     "sen qanjiq", "Jalab", "DALBAYOB", "blyat", "f*ck you motherfucker", "далбаёб", "Sikaman", "b1tch"):
            with self.subTest(text=text):
                self.assertTrue(self.find(text))

    def test_leaves_innocent_words_alone(self):
        for text in ("Scunthorpe", "assessment", "Basketball", "Der Dickdarm ist dick", "Hui, das war schnell!", "Die Fichte",
                     "Schlampenmeister", "Ich habe Hunger", "Kursk", "Huyen und Huy", "Men o‘zbek tilini o'rganyapman",
                     "Hörverstehen 1, Lesen 3, 5000 Wörter", "suchen, Suche", "Ich bin bei der Bank", "Spaß", "Hurra",
                     "Wie spät ist es?", "сукно", "Retten"):
            with self.subTest(text=text):
                self.assertEqual(self.find(text), [])

    def test_custom_list_with_prefix_and_infix(self):
        from app.services.global_chat.word_filter import clean_list, find

        words = ["idiot", "doof*", "еб*ть"]
        self.assertEqual(find("Du Idiot", words), ["idiot"])
        self.assertEqual(find("doofkopf", words), ["dofkopf"])
        self.assertEqual(find("ебать", words), ["ебать"])
        self.assertEqual(find("idiotisch", words), [])
        self.assertEqual(clean_list([" Idiot ", "idiot", "", "x" * 41]), ["idiot"])


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestGlobalChat(unittest.TestCase):
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
            u = User(email=f"gc-{name}-{tag}@test.local", username=f"gc_{name}_{tag}", password_hash="x", is_active=True, is_verified=True,
                     is_superuser=False, role=role, is_banned=False, preferred_language="uz", first_name=name,
                     created_at=_now() - timedelta(days=30))
            db.add(u)
            return u

        cls.u = {n: user(r, n) for n, r in (("student", "STUDENT"), ("student2", "STUDENT"), ("teacher", "TEACHER"),
                                             ("admin", "ADMIN"), ("super", "SUPER_ADMIN"), ("support", "SUPPORT"))}
        db.commit()
        cls.ids = {k: v.id for k, v in cls.u.items()}
        db.close()

    def setUp(self):
        from sqlalchemy import text

        from app.models.user import User

        self.db = self.Session()
        self.db.execute(text("TRUNCATE global_chat_moderation_actions, global_chat_restrictions, global_chat_reads, "
                             "global_chat_message_edits, global_chat_messages"))
        self.db.execute(text("DELETE FROM app_settings WHERE key = 'global_chat_word_filter'"))
        self.db.commit()
        self.user = {k: self.db.get(User, v) for k, v in self.ids.items()}

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    # helpers

    def _status(self, fn, *args, **kwargs):
        with self.assertRaises(HTTPException) as ctx:
            fn(*args, **kwargs)
        return ctx.exception.status_code, ctx.exception.detail

    def _post(self, who, body=None):
        from app.services.global_chat import messages

        return messages.post(self.db, self.user[who], body or f"Hallo {uuid.uuid4().hex[:8]}")

    def _insert(self, who, body, created_at, status="visible"):
        """A message written directly (fixed time stamp, bypasses rate limit)."""
        from app.models.global_chat import GlobalChatMessage

        m = GlobalChatMessage(sender_id=self.ids[who], body=body, status=status, created_at=created_at, updated_at=created_at)
        self.db.add(m)
        self.db.commit()
        return m

    def _restrict(self, kind, duration, who="student", by="admin", **extra):
        from app.services.global_chat import restrictions

        return restrictions.create(self.db, self.user[by], {"user_id": self.ids[who], "kind": kind, "duration": duration,
                                                             "reason": "Beleidigung im Chat", **extra})

    def _age(self, restriction_id, starts_at, ends_at):
        """Moves a restriction into the past (as if time had passed)."""
        from app.models.global_chat import GlobalChatRestriction

        r = self.db.get(GlobalChatRestriction, restriction_id)
        r.starts_at, r.ends_at = starts_at, ends_at
        self.db.commit()

    # 1-4: reading and writing

    def test_logged_in_users_read_and_write(self):
        from app.services.global_chat import messages

        a = self._post("student", "Hallo zusammen!")
        b = self._post("teacher", "Willkommen!")
        c = self._post("super", "Bitte freundlich bleiben.")
        page = messages.page(self.db, self.user["student2"])
        self.assertEqual([m["id"] for m in page["items"]], [a["id"], b["id"], c["id"]])
        self.assertEqual(page["items"][0]["sender"]["name"], "student")
        self.assertIsNone(page["items"][0]["sender"]["badge"])
        self.assertEqual(page["items"][1]["sender"]["badge"], "teacher")
        self.assertEqual(page["items"][2]["sender"]["badge"], "admin")
        self.assertFalse(any(m["mine"] for m in page["items"]))
        self.assertTrue(messages.page(self.db, self.user["student"])["items"][0]["mine"])
        self.assertNotIn("email", page["items"][0]["sender"])  # no e-mail addresses for users
        self.assertTrue(page["me"]["can_post"])
        self.assertIn("sync", page)

    def test_server_sets_time_and_keeps_html_as_text(self):
        before = _now()
        m = self._post("student", "<img src=x onerror=alert(1)> <b>fett</b>")
        self.assertEqual(m["body"], "<img src=x onerror=alert(1)> <b>fett</b>")
        self.assertGreaterEqual(m["created_at"], before - timedelta(seconds=5))
        self.assertEqual(m["status"], "visible")

    # 5-6: pins

    def test_only_moderators_pin(self):
        from app.services.global_chat import messages

        m = self._post("student")
        for who in ("student", "teacher", "support"):
            with self.subTest(who=who):
                self.assertEqual(self._status(messages.moderate, self.db, self.user[who], m["id"], "pin")[0], 403)

        pinned = messages.moderate(self.db, self.user["admin"], m["id"], "pin")
        self.assertTrue(pinned["is_pinned"])
        for who in ("student", "teacher"):
            self.assertEqual([p["id"] for p in messages.pinned(self.db, self.user[who])], [m["id"]])
        self.assertEqual([p["id"] for p in messages.page(self.db, self.user["student2"])["pinned"]], [m["id"]])

        messages.moderate(self.db, self.user["super"], m["id"], "unpin")
        self.assertEqual(messages.pinned(self.db, self.user["student"]), [])
        actions = [a["action"] for a in self._actions()]
        self.assertEqual(actions[:2], ["message.unpin", "message.pin"])

    def test_hiding_unpins_and_removes_for_users(self):
        from app.services.global_chat import messages

        m = self._post("student", "Werbung: kauft bei mir")
        messages.moderate(self.db, self.user["admin"], m["id"], "pin")
        sync = messages.page(self.db, self.user["student2"])["sync"]
        hidden = messages.moderate(self.db, self.user["admin"], m["id"], "hide", "Spam")
        self.assertEqual(hidden["status"], "hidden")
        self.assertFalse(hidden["is_pinned"])
        self.assertEqual(messages.pinned(self.db, self.user["student2"]), [])
        self.assertEqual(messages.page(self.db, self.user["student2"])["items"], [])
        upd = messages.updates(self.db, self.user["student2"], sync)
        self.assertIn(m["id"], upd["removed_ids"])
        # moderators still see it, with body and reason; the row is never deleted
        mod_view = messages.page(self.db, self.user["admin"])["items"][0]
        self.assertEqual((mod_view["body"], mod_view["hidden_reason"]), ("Werbung: kauft bei mir", "Spam"))
        self.assertEqual(self._status(messages.moderate, self.db, self.user["admin"], m["id"], "pin"), (409, "message_not_visible"))

    def test_pin_limit(self):
        from app.services.global_chat import messages

        base = _now() - timedelta(minutes=10)
        ids = [self._insert("student", f"m{i}", base + timedelta(seconds=i)).id for i in range(messages.MAX_PINS + 1)]
        for mid in ids[:-1]:
            messages.moderate(self.db, self.user["admin"], mid, "pin")
        self.assertEqual(self._status(messages.moderate, self.db, self.user["admin"], ids[-1], "pin"), (409, "too_many_pins"))

    # 7-12: mute and ban

    def test_muted_user_reads_but_cannot_write(self):
        from app.services.global_chat import messages, restrictions

        self._post("teacher", "Neue Aufgabe ist online")
        r = self._restrict("mute", "1h", public_note="Bitte keine Beleidigungen")
        self.assertEqual(r["state"], "active")
        self.assertAlmostEqual((r["ends_at"] - r["starts_at"]).total_seconds(), 3600, delta=1)
        self.assertEqual(len(messages.page(self.db, self.user["student"])["items"]), 1)
        self.assertEqual(self._status(self._post, "student"), (403, "chat_muted"))
        me = restrictions.viewer_status(self.db, self.user["student"])
        self.assertFalse(me["can_post"])
        self.assertEqual((me["restriction"]["kind"], me["restriction"]["note"]), ("mute", "Bitte keine Beleidigungen"))
        self.assertNotIn("reason", me["restriction"])  # the internal reason stays with the moderators
        self._post("student2")  # nobody else is affected

    def test_banned_user_reads_but_cannot_write(self):
        from app.services.global_chat import messages

        self._post("teacher")
        self._restrict("ban", "1y")
        self.assertEqual(len(messages.page(self.db, self.user["student"])["items"]), 1)
        self.assertEqual(self._status(self._post, "student"), (403, "chat_banned"))

    def test_ban_outranks_mute(self):
        from app.services.global_chat import restrictions

        self._restrict("mute", "10m")
        self._restrict("ban", "2y")
        me = restrictions.viewer_status(self.db, self.user["student"])
        self.assertEqual(me["restriction"]["kind"], "ban")
        self.assertEqual(self._status(self._post, "student"), (403, "chat_banned"))

    def test_expired_mute_and_ban_restore_writing(self):
        from app.services.global_chat import messages

        past = _now() - timedelta(days=400)
        mute = self._restrict("mute", "10m")
        self._age(mute["id"], past, past + timedelta(minutes=10))
        self._post("student", "wieder da")
        time.sleep(messages.MIN_INTERVAL.total_seconds() + 0.1)  # not the rate limit we test here
        ban = self._restrict("ban", "1y")
        self._age(ban["id"], past, past + timedelta(days=366))
        self._post("student", "wieder da nach dem Bann")

    def test_one_year_ban_ends_on_the_calendar_date(self):
        from app.services.global_chat.restrictions import add_years

        for duration, years in (("1y", 1), ("2y", 2), ("3y", 3), ("5y", 5)):
            with self.subTest(duration=duration):
                r = self._restrict("ban", duration)
                self.assertEqual(r["ends_at"], add_years(r["starts_at"], years))
                self.assertEqual((r["ends_at"].month, r["ends_at"].day), (r["starts_at"].month, r["starts_at"].day))
                self.assertEqual(r["ends_at"].year, r["starts_at"].year + years)

    def test_new_restriction_supersedes_the_old_one(self):
        from app.services.global_chat import restrictions

        first = self._restrict("mute", "10m")
        second = self._restrict("mute", "7d")
        listed = restrictions.list_restrictions(self.db, self.user["admin"], "all", "mute", self.ids["student"])["items"]
        states = {r["id"]: (r["state"], r["revoke_reason"]) for r in listed}
        self.assertEqual(states[first["id"]], ("revoked", "superseded"))
        self.assertEqual(states[second["id"]], ("active", None))

    def test_admin_extends_shortens_and_revokes(self):
        from app.services.global_chat import restrictions
        from app.services.global_chat.restrictions import add_years

        ban = self._restrict("ban", "1y")
        longer = restrictions.update(self.db, self.user["admin"], ban["id"], {"ban_years": 3, "reason": "wiederholt"})
        self.assertEqual(longer["ends_at"], add_years(ban["starts_at"], 3))
        soon = _now() + timedelta(days=2)
        shorter = restrictions.update(self.db, self.user["admin"], ban["id"], {"ends_at": soon})
        self.assertEqual(shorter["ends_at"], soon)
        self.assertEqual(self._status(restrictions.update, self.db, self.user["admin"], ban["id"], {"ends_at": _now() - timedelta(hours=1)}),
                         (422, "ends_at_in_past"))
        revoked = restrictions.revoke(self.db, self.user["admin"], ban["id"], "Entschuldigung angenommen")
        self.assertEqual(revoked["state"], "revoked")
        self._post("student", "danke")
        self.assertEqual(self._status(restrictions.revoke, self.db, self.user["admin"], ban["id"], None), (409, "restriction_revoked"))
        log = [a["action"] for a in self._actions()]
        self.assertEqual(log[:4], ["ban.revoke", "ban.update", "ban.update", "ban.create"])

    def test_mute_limits(self):
        from app.services.global_chat import restrictions

        r = self._restrict("mute", "custom", ends_at=_now() + timedelta(days=45))
        self.assertEqual(r["state"], "active")
        self.assertEqual(self._status(self._restrict, "mute", "custom", ends_at=_now() + timedelta(days=400)), (422, "mute_too_long"))
        self.assertEqual(self._status(self._restrict, "mute", "custom"), (422, "ends_at_required"))
        self.assertEqual(self._status(self._restrict, "mute", "1y"), (422, "invalid_duration"))
        self.assertEqual(self._status(self._restrict, "ban", "10m"), (422, "invalid_duration"))
        self.assertEqual(self._status(restrictions.update, self.db, self.user["admin"], r["id"], {"permanent": True}),
                         (422, "mute_cannot_be_permanent"))

    def test_permanent_ban_is_super_admin_only(self):
        from app.services.global_chat import restrictions

        self.assertEqual(self._status(self._restrict, "ban", "permanent", by="admin"), (403, "permanent_ban_super_admin_only"))
        r = self._restrict("ban", "permanent", by="super")
        self.assertTrue(r["permanent"])
        self.assertIsNone(r["ends_at"])
        self.assertEqual(self._status(restrictions.revoke, self.db, self.user["admin"], r["id"], None), (403, "permanent_ban_super_admin_only"))
        restrictions.revoke(self.db, self.user["super"], r["id"], None)

    def test_who_may_restrict_whom(self):
        from app.services.global_chat import restrictions

        for who in ("student2", "teacher", "support"):
            with self.subTest(by=who):
                self.assertEqual(self._status(self._restrict, "ban", "1y", by=who)[0], 403)
        self.assertEqual(self._status(self._restrict, "mute", "1h", who="admin", by="admin"), (422, "cannot_restrict_self"))
        self.assertEqual(self._status(self._restrict, "mute", "1h", who="super", by="admin"), (403, "cannot_restrict_moderator"))
        self.assertEqual(self._status(self._restrict, "mute", "1h", who="admin", by="super"), (403, "cannot_restrict_moderator"))
        self.assertEqual(self._status(restrictions.create, self.db, self.user["admin"],
                                      {"user_id": uuid.uuid4(), "kind": "mute", "duration": "1h", "reason": "x y z"})[0], 404)
        self.assertEqual(self._status(self._restrict, "mute", "1h", reason="   "), (422, "reason_required"))
        self._restrict("mute", "1h", who="teacher")  # a teacher is a normal chat participant

    def test_ban_does_not_touch_the_account_or_lms(self):
        from app.models.user import User
        from app.services.global_chat import restrictions

        def account():
            self.db.expire_all()
            u = self.db.get(User, self.ids["student"])
            return u.is_active, u.is_banned, u.ban_reason, u.suspended_until, u.premium_until, u.role, u.tokens_valid_after

        before = account()
        r = self._restrict("ban", "5y")
        self.assertEqual(account(), before)
        restrictions.revoke(self.db, self.user["admin"], r["id"], None)
        self.assertEqual(account(), before)

    # 14: rate limit

    def test_rate_limit_and_duplicates(self):
        from app.services.global_chat import messages

        base = _now() - timedelta(seconds=50)
        for i in range(messages.MAX_PER_MINUTE):
            self._insert("student", f"Nachricht {i}", base + timedelta(seconds=i))
        status, detail = self._status(self._post, "student")
        self.assertEqual((status, detail), (429, "too_many_messages"))

        self._post("student2", "Erste")
        self.assertEqual(self._status(self._post, "student2", "Zweite"), (429, "too_fast"))

        self._insert("teacher", "Gleicher Text", _now() - timedelta(seconds=10))
        self.assertEqual(self._status(self._post, "teacher", "Gleicher Text"), (429, "duplicate_message"))
        self._post("teacher", "Anderer Text")

    # 16: pagination

    def test_history_pages(self):
        from app.services.global_chat import messages

        base = _now() - timedelta(hours=2)
        ids = [self._insert("student" if i % 2 else "teacher", f"#{i}", base + timedelta(seconds=i)).id for i in range(45)]
        first = messages.page(self.db, self.user["student2"], limit=20)
        self.assertTrue(first["has_more"])
        self.assertEqual([m["id"] for m in first["items"]], ids[25:])
        second = messages.page(self.db, self.user["student2"], before=first["items"][0]["id"], limit=20)
        self.assertEqual([m["id"] for m in second["items"]], ids[5:25])
        third = messages.page(self.db, self.user["student2"], before=second["items"][0]["id"], limit=20)
        self.assertEqual([m["id"] for m in third["items"]], ids[:5])
        self.assertFalse(third["has_more"])
        # same time stamp: the id breaks the tie, nothing is skipped or repeated
        same = base + timedelta(minutes=5)
        twins = {self._insert("student", f"twin{i}", same).id for i in range(3)}
        seen = []
        before = None
        while True:
            p = messages.page(self.db, self.user["student2"], before=before, limit=2)
            seen.extend(m["id"] for m in p["items"])
            if not p["has_more"]:
                break
            before = p["items"][0]["id"]
        self.assertEqual(len(seen), len(set(seen)))
        self.assertTrue(twins <= set(seen))
        self.assertEqual(len(seen), 48)

    def test_updates_return_new_and_changed_messages(self):
        from app.services.global_chat import messages

        sync = messages.page(self.db, self.user["student2"])["sync"]
        m = self._post("student", "neu")
        upd = messages.updates(self.db, self.user["student2"], sync)
        self.assertFalse(upd["reset"])
        self.assertIn(m["id"], [x["id"] for x in upd["items"]])
        self.assertTrue(messages.updates(self.db, self.user["student2"], _now() - timedelta(hours=1))["reset"])

    # 17: unread

    def test_unread_count(self):
        from app.services.global_chat import messages

        self.assertEqual(messages.unread_count(self.db, self.user["student2"]), 0)
        self._post("student2", "meine zählt nicht")  # writing also marks everything before as read
        self._post("student", "eins")
        last = self._post("teacher", "zwei")
        self.assertEqual(messages.unread_count(self.db, self.user["student2"]), 2)
        messages.mark_read(self.db, self.user["student2"], last["id"])
        self.assertEqual(messages.unread_count(self.db, self.user["student2"]), 0)
        later = self._insert("teacher", "drei", _now())
        self.assertEqual(messages.unread_count(self.db, self.user["student2"]), 1)
        # the marker never moves back
        first_id = messages.page(self.db, self.user["student2"])["items"][0]["id"]
        messages.mark_read(self.db, self.user["student2"], first_id)
        self.assertEqual(messages.unread_count(self.db, self.user["student2"]), 1)
        messages.mark_read(self.db, self.user["student2"], later.id)
        self.assertEqual(messages.unread_count(self.db, self.user["student2"]), 0)

    def test_unread_count_is_capped(self):
        from app.models.global_chat import GlobalChatMessage
        from app.services.global_chat import messages

        base = _now() - timedelta(minutes=30)
        self.db.add_all([GlobalChatMessage(sender_id=self.ids["teacher"], body=f"n{i}", created_at=base + timedelta(milliseconds=i))
                         for i in range(messages.UNREAD_CAP + 20)])
        self.db.commit()
        self.assertEqual(messages.unread_count(self.db, self.user["student"]), messages.UNREAD_CAP)

    # word filter in the flow

    def test_word_filter_holds_for_review(self):
        from app.services.global_chat import messages

        m = self._post("student", "Du bist ein Hurensohn")
        self.assertEqual(m["status"], "pending")
        self.assertEqual([x["id"] for x in messages.page(self.db, self.user["student"])["items"]], [m["id"]])  # the sender sees it
        self.assertEqual(messages.page(self.db, self.user["student2"])["items"], [])  # others don't
        self.assertEqual(messages.unread_count(self.db, self.user["student2"]), 0)
        queue = messages.admin_list(self.db, self.user["admin"], "pending")
        self.assertEqual([x["id"] for x in queue["items"]], [m["id"]])
        self.assertEqual(queue["items"][0]["flagged_words"], ["hurensohn"])
        self.assertEqual(self._actions()[0]["action"], "message.flag")
        self.assertIsNone(self._actions()[0]["actor"])  # the filter, not a person
        # no automatic restriction
        from app.services.global_chat import restrictions

        self.assertTrue(restrictions.viewer_status(self.db, self.user["student"])["can_post"])

        sync = messages.page(self.db, self.user["student2"])["sync"]
        messages.moderate(self.db, self.user["admin"], m["id"], "approve")
        self.assertIn(m["id"], [x["id"] for x in messages.updates(self.db, self.user["student2"], sync)["items"]])

    def test_moderators_are_not_filtered_and_filter_is_configurable(self):
        from app.services.global_chat import messages, word_filter

        self.assertEqual(self._post("admin", "Das Wort 'Hurensohn' ist hier verboten.")["status"], "visible")
        self.assertEqual(self._post("student", "Das ist doof")["status"], "visible")
        from app.models.app_setting import AppSetting

        self.db.add(AppSetting(key=word_filter.SETTING_KEY, value={"enabled": True, "words": ["doof"]}))
        self.db.commit()
        self.assertEqual(self._post("student2", "Das ist doof")["status"], "pending")
        row = word_filter.settings_row(self.db)
        row.value = {"enabled": False, "words": ["doof"]}
        self.db.commit()
        self.assertEqual(self._post("teacher", "Das ist doof!")["status"], "visible")
        self.assertEqual(messages.admin_list(self.db, self.user["admin"], "flagged")["total"], 1)

    # 10: admin panel data

    def test_admin_history_and_stats(self):
        from app.services.global_chat import messages

        m = self._post("student", "Hallo")
        messages.moderate(self.db, self.user["admin"], m["id"], "hide", "off-topic")
        self._restrict("mute", "24h", message_id=m["id"])
        history = messages.user_history(self.db, self.user["admin"], self.ids["student"])
        self.assertEqual(history["messages"]["hidden"], 1)
        self.assertEqual([r["kind"] for r in history["restrictions"]], ["mute"])
        self.assertEqual({a["action"] for a in history["actions"]}, {"message.hide", "mute.create"})
        self.assertEqual(next(a for a in history["actions"] if a["action"] == "mute.create")["actor"], "admin")
        stats = messages.stats(self.db, self.user["admin"])
        self.assertEqual((stats["active_mutes"], stats["hidden_7d"]), (1, 1))
        self.assertEqual(self._status(messages.stats, self.db, self.user["teacher"])[0], 403)
        self.assertEqual(self._status(messages.user_history, self.db, self.user["student2"], self.ids["student"])[0], 403)
        found = messages.search_users(self.db, self.user["admin"], self.user["student2"].email)
        self.assertEqual([u["id"] for u in found], [self.ids["student2"]])

    # 19: group chats are separate

    def test_group_chat_and_global_chat_do_not_mix(self):
        from app.services.global_chat import messages
        from app.services.study_groups import chat, groups

        group, code = groups.create(self.db, self.user["teacher"], {"name": f"GC {uuid.uuid4().hex[:4]}", "level": "A1", "course_ids": []})
        groups.join(self.db, self.user["student"], code, "10.0.0.9")
        from app.services.study_groups.access import require_view

        g, member = require_view(self.db, self.user["student"], group["id"])
        chat.post_message(self.db, self.user["student"], g, member, "nur in der Gruppe")
        self._post("student2", "nur global")
        self.assertEqual([m["body"] for m in messages.page(self.db, self.user["student"])["items"]], ["nur global"])
        group_texts = [m["body"] for m in chat.list_messages(self.db, self.user["student"], g, member)["items"] if m["kind"] == "text"]
        self.assertEqual(group_texts, ["nur in der Gruppe"])
        # a Global Chat ban does not stop group chat
        self._restrict("ban", "1y")
        g, member = require_view(self.db, self.user["student"], group["id"])
        chat.post_message(self.db, self.user["student"], g, member, "trotzdem in der Gruppe")
        self.assertEqual(self._status(self._post, "student"), (403, "chat_banned"))

    # authors edit and delete their own messages

    def test_author_edits_own_message(self):
        from app.models.global_chat import GlobalChatMessageEdit
        from app.services.global_chat import messages

        m = self._post("student", "Halo zusamen")
        sync = messages.page(self.db, self.user["student2"])["sync"]
        before = _now()
        edited = messages.edit_own(self.db, self.user["student"], m["id"], "Hallo zusammen <b>alle</b>")
        self.assertEqual(edited["body"], "Hallo zusammen <b>alle</b>")  # stored as text, never interpreted
        self.assertGreaterEqual(edited["edited_at"], before - timedelta(seconds=5))
        self.assertEqual(edited["created_at"], m["created_at"])  # position in the chat unchanged
        self.assertEqual(edited["status"], "visible")
        other = messages.page(self.db, self.user["student2"])["items"][0]
        self.assertEqual((other["body"], other["edited_at"]), (edited["body"], edited["edited_at"]))
        upd = messages.updates(self.db, self.user["student2"], sync)
        self.assertIn(m["id"], [x["id"] for x in upd["items"]])
        # the earlier text: moderators only
        history = messages.edit_history(self.db, self.user["admin"], m["id"])
        self.assertEqual([h["previous_body"] for h in history], ["Halo zusamen"])
        self.assertEqual(self._status(messages.edit_history, self.db, self.user["student"], m["id"])[0], 403)
        self.assertEqual(self.db.query(GlobalChatMessageEdit).filter_by(message_id=m["id"]).count(), 1)
        # unchanged text: no new version
        messages.edit_own(self.db, self.user["student"], m["id"], "Hallo zusammen <b>alle</b>")
        self.assertEqual(len(messages.edit_history(self.db, self.user["admin"], m["id"])), 1)

    def test_edit_validation(self):
        from app.api.global_chat.router import MessageIn
        from app.services.global_chat import messages

        m = self._post("student", "Text")
        for body in ("", "   ", "\x00"):
            with self.subTest(body=body):
                self.assertEqual(self._status(messages.edit_own, self.db, self.user["student"], m["id"], body), (422, "empty"))
        self.assertEqual(self._status(messages.edit_own, self.db, self.user["student"], m["id"], "x" * 2001), (422, "too_long"))
        with self.assertRaises(ValidationError):
            MessageIn(body="x" * 2001)
        with self.assertRaises(ValidationError):
            MessageIn(body="neu", sender_id=str(self.ids["student2"]))
        self.assertEqual(messages.page(self.db, self.user["student"])["items"][0]["body"], "Text")

    def test_only_the_author_edits_or_deletes(self):
        from app.services.global_chat import messages

        m = self._post("teacher", "Aufgabe 3 bis Freitag")
        for who in ("student", "admin", "super"):
            with self.subTest(who=who):
                self.assertEqual(self._status(messages.edit_own, self.db, self.user[who], m["id"], "gehackt"), (403, "not_author"))
                self.assertEqual(self._status(messages.delete_own, self.db, self.user[who], m["id"]), (403, "not_author"))
        self.assertEqual(self._status(messages.edit_own, self.db, self.user["student"], uuid.uuid4(), "x")[0], 404)
        self.assertEqual(self._status(messages.delete_own, self.db, self.user["student"], uuid.uuid4())[0], 404)
        # someone else's held / hidden message: 404, its existence is not confirmed
        held = self._post("student2", "du Hurensohn")
        self.assertEqual(self._status(messages.delete_own, self.db, self.user["student"], held["id"])[0], 404)
        self.assertEqual(messages.page(self.db, self.user["student"])["items"][0]["body"], "Aufgabe 3 bis Freitag")

    def test_author_deletes_own_message(self):
        from app.services.global_chat import messages

        keep = self._post("teacher", "bleibt")
        time.sleep(messages.MIN_INTERVAL.total_seconds() + 0.1)
        m = self._post("student", "Tippfehler-Nachricht")
        sync = messages.page(self.db, self.user["student2"])["sync"]
        self.assertEqual(messages.unread_count(self.db, self.user["student2"]), 2)
        messages.delete_own(self.db, self.user["student"], m["id"])
        # gone for everybody else, also from the unread count
        self.assertEqual([x["id"] for x in messages.page(self.db, self.user["student2"])["items"]], [keep["id"]])
        self.assertEqual([x["id"] for x in messages.page(self.db, self.user["student"])["items"]], [keep["id"]])
        self.assertIn(m["id"], messages.updates(self.db, self.user["student2"], sync)["removed_ids"])
        self.assertEqual(messages.unread_count(self.db, self.user["student2"]), 1)
        # moderators keep the text and the log entry
        mod = next(x for x in messages.page(self.db, self.user["admin"])["items"] if x["id"] == m["id"])
        self.assertEqual((mod["status"], mod["body"]), ("deleted", "Tippfehler-Nachricht"))
        self.assertIsNotNone(mod["deleted_at"])
        entry = self._actions()[0]
        self.assertEqual((entry["action"], entry["actor"], entry["message_id"]), ("message.delete", "student", m["id"]))
        self.assertEqual(messages.admin_list(self.db, self.user["admin"], "deleted")["total"], 1)
        # twice, or edit after delete: it no longer exists for the author
        self.assertEqual(self._status(messages.delete_own, self.db, self.user["student"], m["id"])[0], 404)
        self.assertEqual(self._status(messages.edit_own, self.db, self.user["student"], m["id"], "x")[0], 404)
        # and moderators cannot pin / approve / unhide it back into the chat
        for action in ("pin", "approve", "unhide", "hide"):
            self.assertEqual(self._status(messages.moderate, self.db, self.user["admin"], m["id"], action), (409, "message_deleted"))

    def test_pinned_message_edit_and_delete(self):
        from app.services.global_chat import messages

        m = self._post("student", "Wichtiger Link")
        messages.moderate(self.db, self.user["admin"], m["id"], "pin")
        self.assertEqual(self._status(messages.edit_own, self.db, self.user["student"], m["id"], "Spam-Link"), (409, "message_pinned"))
        messages.delete_own(self.db, self.user["student"], m["id"])
        self.assertEqual(messages.pinned(self.db, self.user["student2"]), [])
        self.assertEqual(messages.page(self.db, self.user["admin"])["pinned"], [])
        self.assertEqual(messages.admin_list(self.db, self.user["admin"], "pinned")["total"], 0)
        self.assertTrue(self._actions()[0]["meta"]["was_pinned"])
        # a new pin is not blocked by the deleted one
        for i in range(messages.MAX_PINS):
            mid = self._insert("teacher", f"p{i}", _now() - timedelta(minutes=5, seconds=i)).id
            messages.moderate(self.db, self.user["admin"], mid, "pin")

    def test_hidden_message_stays_hidden(self):
        from app.services.global_chat import messages

        m = self._post("student", "Beleidigung")
        messages.moderate(self.db, self.user["admin"], m["id"], "hide", "Beleidigung")
        # the author no longer sees it, so to them it does not exist
        self.assertEqual(self._status(messages.edit_own, self.db, self.user["student"], m["id"], "nett")[0], 404)
        self.assertEqual(self._status(messages.delete_own, self.db, self.user["student"], m["id"])[0], 404)
        # a moderator's own hidden message is not editable either
        own = self._post("admin", "Admin-Text")
        messages.moderate(self.db, self.user["super"], own["id"], "hide")
        self.assertEqual(self._status(messages.edit_own, self.db, self.user["admin"], own["id"], "x"), (409, "message_hidden"))
        self.assertEqual(self._status(messages.delete_own, self.db, self.user["admin"], own["id"]), (409, "message_hidden"))
        log = [a["action"] for a in self._actions()]
        self.assertEqual(log.count("message.hide"), 2)

    def test_edit_runs_the_word_filter_again(self):
        from app.services.global_chat import messages

        m = self._post("student", "Guten Morgen")
        sync = messages.page(self.db, self.user["student2"])["sync"]
        held = messages.edit_own(self.db, self.user["student"], m["id"], "Guten Morgen, Hurensohn")
        self.assertEqual(held["status"], "pending")
        self.assertEqual(messages.page(self.db, self.user["student2"])["items"], [])
        self.assertIn(m["id"], messages.updates(self.db, self.user["student2"], sync)["removed_ids"])
        self.assertEqual(messages.admin_list(self.db, self.user["admin"], "pending")["items"][0]["flagged_words"], ["hurensohn"])
        self.assertEqual(self._actions()[0]["reason"], "word_filter_edit")
        # editing it clean again does not release it — a moderator decides (the insult stays in the history)
        again = messages.edit_own(self.db, self.user["student"], m["id"], "Guten Morgen")
        self.assertEqual(again["status"], "pending")
        self.assertEqual([h["previous_body"] for h in messages.edit_history(self.db, self.user["admin"], m["id"])],
                         ["Guten Morgen", "Guten Morgen, Hurensohn"])
        # the author may also withdraw it; that empties the review queue
        messages.delete_own(self.db, self.user["student"], m["id"])
        self.assertEqual(messages.admin_list(self.db, self.user["admin"], "pending")["total"], 0)

    def test_mute_and_ban_block_editing_but_not_deleting(self):
        from app.services.global_chat import messages

        a = self._post("student", "eins")
        time.sleep(messages.MIN_INTERVAL.total_seconds() + 0.1)
        b = self._post("student", "zwei")
        self._restrict("mute", "1h")
        self.assertEqual(self._status(messages.edit_own, self.db, self.user["student"], a["id"], "neu"), (403, "chat_muted"))
        messages.delete_own(self.db, self.user["student"], a["id"])
        self._restrict("ban", "1y")
        self.assertEqual(self._status(messages.edit_own, self.db, self.user["student"], b["id"], "neu"), (403, "chat_banned"))
        messages.delete_own(self.db, self.user["student"], b["id"])
        self.assertEqual(self._status(self._post, "student"), (403, "chat_banned"))  # the ban itself is untouched

    def test_edit_rate_limit(self):
        from app.services.global_chat import messages

        m = self._post("student", "v0")
        for i in range(messages.MAX_EDITS_PER_MINUTE):
            messages.edit_own(self.db, self.user["student"], m["id"], f"v{i + 1}")
        self.assertEqual(self._status(messages.edit_own, self.db, self.user["student"], m["id"], "zu viel"), (429, "too_many_edits"))

    # replies

    def _reply(self, who, target_id, body=None):
        from app.services.global_chat import messages

        return messages.post(self.db, self.user[who], body or f"Antwort {uuid.uuid4().hex[:8]}", target_id)

    def test_reply_links_to_the_original(self):
        from app.models.global_chat import GlobalChatMessage
        from app.services.global_chat import messages

        original = self._post("teacher", "Wer hat Aufgabe 3 gelöst?")
        reply = self._reply("student", original["id"], "Ich! 🙋 Lösung: B")
        self.assertEqual(self.db.get(GlobalChatMessage, reply["id"]).reply_to_id, original["id"])
        self.assertEqual(reply["reply_to"], {"id": original["id"], "available": True, "excerpt": "Wer hat Aufgabe 3 gelöst?",
                                             "sender": {"id": self.ids["teacher"], "name": "teacher"}})
        for viewer in ("student2", "admin"):
            with self.subTest(viewer=viewer):
                item = next(m for m in messages.page(self.db, self.user[viewer])["items"] if m["id"] == reply["id"])
                self.assertEqual(item["reply_to"]["id"], original["id"])
                self.assertTrue(item["reply_to"]["available"])
        # the original itself is no reply; a reply to a reply works too
        self.assertIsNone(next(m for m in messages.page(self.db, self.user["student2"])["items"] if m["id"] == original["id"])["reply_to"])
        time.sleep(messages.MIN_INTERVAL.total_seconds() + 0.1)
        nested = self._reply("teacher", reply["id"], "Richtig!")
        self.assertEqual(nested["reply_to"]["sender"]["name"], "student")
        # polling delivers the reply with its quote
        sync = messages.page(self.db, self.user["student2"])["sync"]
        time.sleep(messages.MIN_INTERVAL.total_seconds() + 0.1)
        late = self._reply("student", original["id"], "Ich auch")
        upd = next(m for m in messages.updates(self.db, self.user["student2"], sync)["items"] if m["id"] == late["id"])
        self.assertEqual(upd["reply_to"]["id"], original["id"])

    def test_reply_to_unknown_or_foreign_message_is_refused(self):
        from app.models.global_chat import GlobalChatMessage
        from app.models.study_group import StudyGroupMessage
        from app.services.global_chat import messages
        from app.services.study_groups import chat, groups
        from app.services.study_groups.access import require_view

        self.assertEqual(self._status(self._reply, "student", uuid.uuid4()), (422, "reply_not_found"))
        # a group-chat message id is not a Global Chat message
        group, code = groups.create(self.db, self.user["teacher"], {"name": f"GR {uuid.uuid4().hex[:4]}", "level": "A1", "course_ids": []})
        groups.join(self.db, self.user["student"], code, "10.0.0.9")
        g, member = require_view(self.db, self.user["student"], group["id"])
        chat.post_message(self.db, self.user["student"], g, member, "nur in der Gruppe")
        group_msg = self.db.query(StudyGroupMessage).filter_by(group_id=group["id"]).order_by(StudyGroupMessage.created_at.desc()).first()
        self.assertEqual(self._status(self._reply, "student", group_msg.id), (422, "reply_not_found"))
        # someone else's held message and a hidden one: not visible -> same answer, existence not confirmed
        held = self._post("student2", "du Hurensohn")
        self.assertEqual(held["status"], "pending")
        self.assertEqual(self._status(self._reply, "student", held["id"]), (422, "reply_not_found"))
        hidden = self._post("teacher", "off-topic")
        messages.moderate(self.db, self.user["admin"], hidden["id"], "hide", "x")
        self.assertEqual(self._status(self._reply, "student", hidden["id"]), (422, "reply_not_found"))
        # nothing was stored by the refused attempts
        self.assertEqual(self.db.query(GlobalChatMessage).filter(GlobalChatMessage.reply_to_id.is_not(None)).count(), 0)

    def test_reply_to_deleted_message(self):
        from app.services.global_chat import messages

        original = self._post("student2", "Tippfehler")
        time.sleep(messages.MIN_INTERVAL.total_seconds() + 0.1)
        reply = self._reply("student", original["id"], "Was meinst du?")
        messages.delete_own(self.db, self.user["student2"], original["id"])
        # the reply stays and shows the fallback, no text of the deleted message
        for viewer in ("student", "teacher", "admin"):
            with self.subTest(viewer=viewer):
                item = next(m for m in messages.page(self.db, self.user[viewer])["items"] if m["id"] == reply["id"])
                self.assertEqual(item["reply_to"], {"id": original["id"], "available": False, "sender": None, "excerpt": None})
        # and nobody can reply to it any more
        self.assertEqual(self._status(self._reply, "teacher", original["id"]), (422, "reply_not_found"))

    def test_reply_respects_mute_ban_and_rate_limit(self):
        from app.services.global_chat import messages

        original = self._post("teacher", "Frage an alle")
        r = self._restrict("mute", "1h")
        self.assertEqual(self._status(self._reply, "student", original["id"]), (403, "chat_muted"))
        # the restriction answers first: an invalid target does not tell a muted user anything else
        self.assertEqual(self._status(self._reply, "student", uuid.uuid4()), (403, "chat_muted"))
        from app.services.global_chat import restrictions

        restrictions.revoke(self.db, self.user["admin"], r["id"], None)
        self._restrict("ban", "1y")
        self.assertEqual(self._status(self._reply, "student", original["id"]), (403, "chat_banned"))
        # rate limit: replies count like messages
        self._reply("student2", original["id"], "eins")
        self.assertEqual(self._status(self._reply, "student2", original["id"], "zwei"), (429, "too_fast"))
        base = _now() - timedelta(seconds=50)
        for i in range(messages.MAX_PER_MINUTE):
            self._insert("teacher", f"spam {i}", base + timedelta(seconds=i))
        self.assertEqual(self._status(self._reply, "teacher", original["id"]), (429, "too_many_messages"))
        # the word filter holds a reply like any message
        time.sleep(messages.MIN_INTERVAL.total_seconds() + 0.1)
        held = self._reply("student2", original["id"], "du Hurensohn")
        self.assertEqual(held["status"], "pending")
        self.assertNotIn(held["id"], [m["id"] for m in messages.page(self.db, self.user["teacher"])["items"]])

    def test_old_messages_without_reply_still_work(self):
        from app.services.global_chat import messages

        old = self._insert("teacher", "vor dem Update", _now() - timedelta(days=2))
        page = messages.page(self.db, self.user["student"])
        self.assertIsNone(page["items"][0]["reply_to"])
        self.assertEqual(self._reply("student", old.id, "alte Nachricht")["reply_to"]["excerpt"], "vor dem Update")
        # an old message's id still works as a cursor, unread counting is unchanged
        self.assertEqual(messages.page(self.db, self.user["student"], before=page["items"][0]["id"])["items"], [])

    def test_reply_with_edit_and_delete(self):
        from app.services.global_chat import messages

        original = self._post("teacher", "Termin: Montag")
        time.sleep(messages.MIN_INTERVAL.total_seconds() + 0.1)
        reply = self._reply("student", original["id"], "Danke")
        # the original is edited: the quote follows the current text
        messages.edit_own(self.db, self.user["teacher"], original["id"], "Termin: Dienstag")
        self.db.expire_all()
        item = next(m for m in messages.page(self.db, self.user["student2"])["items"] if m["id"] == reply["id"])
        self.assertEqual(item["reply_to"]["excerpt"], "Termin: Dienstag")
        # the reply is edited: its link stays
        edited = messages.edit_own(self.db, self.user["student"], reply["id"], "Danke, notiert")
        self.assertEqual((edited["body"], edited["reply_to"]["id"]), ("Danke, notiert", original["id"]))
        # the reply is deleted: the original is untouched, still quotable
        messages.delete_own(self.db, self.user["student"], reply["id"])
        self.assertEqual([m["id"] for m in messages.page(self.db, self.user["student2"])["items"]], [original["id"]])
        time.sleep(messages.MIN_INTERVAL.total_seconds() + 0.1)
        self.assertTrue(self._reply("student2", original["id"])["reply_to"]["available"])
        # a hidden original: users get the fallback, moderators still see the quote
        messages.moderate(self.db, self.user["admin"], original["id"], "hide", "x")
        self.db.expire_all()
        user_view = messages.page(self.db, self.user["student"])["items"]
        self.assertFalse(next(m for m in user_view if m["reply_to"])["reply_to"]["available"])
        mod_view = [m for m in messages.page(self.db, self.user["admin"])["items"] if m["reply_to"]]
        self.assertTrue(all(m["reply_to"]["available"] for m in mod_view if m["status"] != "deleted"))

    def _actions(self):
        from app.services.global_chat import restrictions

        return restrictions.list_actions(self.db, self.user["super"])["items"]


if __name__ == "__main__":
    unittest.main()
