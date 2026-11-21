"""Group video lessons (LiveKit): API contract, join tokens, webhook signatures (no DB) and, against PostgreSQL
(VIZU_WB_TEST_DB_URL at head), who may create / join / moderate, cross-group access, moderation state in tokens,
remove / block, raised hands, capacity, rate limits, webhook sync and ending. LiveKit itself is replaced by a fake gateway;
the real server is exercised by the E2E spec (e2e/tests/video-rooms.spec.ts)."""

import base64
import hashlib
import json
import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
LK = {"LIVEKIT_URL": "ws://127.0.0.1:7880", "LIVEKIT_API_URL": "", "LIVEKIT_API_KEY": "vizutestkey",
      "LIVEKIT_API_SECRET": "vizu-test-secret-not-real-0123456789abcdef"}


def _now():
    return datetime.now(timezone.utc)


def _claims(token: str) -> dict:
    import jwt

    return jwt.decode(token, LK["LIVEKIT_API_SECRET"], algorithms=["HS256"], options={"verify_aud": False})


def _signed(event) -> tuple[str, str]:
    from google.protobuf.json_format import MessageToJson
    from livekit import api

    body = MessageToJson(event)
    digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
    return body, api.AccessToken(LK["LIVEKIT_API_KEY"], LK["LIVEKIT_API_SECRET"]).with_sha256(digest).to_jwt()


class FakeGateway:
    """Records what would have been sent to LiveKit."""

    def __init__(self):
        self.calls, self.present, self.fail = [], {}, False

    def _rec(self, *call):
        from app.services.video_rooms import livekit_service as lk

        if self.fail:
            raise lk.LiveKitUnavailable(call[0])
        self.calls.append(call)

    def of(self, kind):
        return [c for c in self.calls if c[0] == kind]

    def ensure_room(self, name, max_participants, metadata):
        self._rec("ensure", name, max_participants, metadata)

    def set_room_metadata(self, name, metadata):
        self._rec("meta", name, metadata)
        return True

    def delete_room(self, name):
        self._rec("delete", name)
        return True

    def participants(self, name):
        from livekit import api

        self._rec("list", name)
        return [api.ParticipantInfo(identity=i, tracks=[api.TrackInfo(sid=f"TR_{i[:6]}", source=api.TrackSource.MICROPHONE, muted=False)])
                for i in self.present.get(name, ())]

    def rooms(self):
        return {name: len(ids) for name, ids in self.present.items()}

    def update_permission(self, name, identity, sources, can_data):
        self._rec("perm", name, identity, tuple(sources), can_data)
        return True

    def set_attributes(self, name, identity, attributes):
        self._rec("attrs", name, identity, attributes)
        return True

    def mute(self, name, identities, sources=("microphone",)):
        self._rec("mute", name, tuple(sorted(identities)), tuple(sources))
        return len(identities)

    def remove(self, name, identity):
        self._rec("remove", name, identity)
        return True

    def status(self):
        return "unavailable" if self.fail else "available"


class TestContract(unittest.TestCase):
    def test_every_route_needs_a_user_except_the_signed_webhook(self):
        from app.api.dependencies.auth import get_current_user, require_super_admin
        from app.api.video_rooms.router import router

        for route in router.routes:
            deps = [d.call for d in route.dependant.dependencies]
            with self.subTest(route=route.path):
                if route.path == "/video-rooms/webhooks/livekit":
                    self.assertNotIn(get_current_user, deps)
                elif route.path.startswith("/admin/"):
                    self.assertIn(require_super_admin, deps)
                else:
                    self.assertIn(get_current_user, deps)

    def test_webhook_route_comes_before_room_routes(self):
        from app.api.video_rooms.router import router

        paths = [r.path for r in router.routes]
        self.assertLess(paths.index("/video-rooms/webhooks/livekit"), paths.index("/video-rooms/{room_id}"))

    def test_bodies_cannot_smuggle_room_names_roles_or_ids(self):
        from app.api.video_rooms.router import ConnectionIn, HandIn, PermissionIn, RoomCreate

        with self.assertRaises(ValidationError):
            RoomCreate(title="Dars", start_now=True, room_name="another-room")
        with self.assertRaises(ValidationError):
            RoomCreate(title="Dars", group_id=str(uuid.uuid4()))
        with self.assertRaises(ValidationError):
            PermissionIn(allowed=True, role="host")
        with self.assertRaises(ValidationError):
            HandIn(raised=True, identity="x")
        with self.assertRaises(ValidationError):
            ConnectionIn(state="hacked")

    def test_join_token_is_room_bound_short_and_cannot_edit_itself(self):
        from app.core.config import settings
        from app.services.video_rooms import livekit_service as lk

        with patch.multiple(settings, **LK):
            token = lk.join_token(room_name="vizu-abc", identity="user-1", name="Ali", role="student", sources=["camera", "microphone"],
                                  can_data=False, attributes={"vizu.role": "student", "vizu.hand": ""}, ttl_seconds=300)
            empty = lk.join_token(room_name="vizu-abc", identity="user-1", name="Ali", role="student", sources=[], can_data=True,
                                  attributes={}, ttl_seconds=60)
        c = _claims(token)
        self.assertEqual(c["sub"], "user-1")
        self.assertEqual(c["video"]["room"], "vizu-abc")
        self.assertTrue(c["video"]["roomJoin"])
        self.assertEqual(c["video"]["canPublishSources"], ["camera", "microphone"])
        self.assertFalse(c["video"]["canPublishData"])
        self.assertFalse(c["video"]["canUpdateOwnMetadata"])
        self.assertNotIn("roomAdmin", c["video"])
        self.assertLessEqual(c["exp"] - c["nbf"], 300)
        self.assertNotIn(LK["LIVEKIT_API_SECRET"], token)
        # LiveKit reads an empty source list as "all sources": no source must mean no publishing at all
        self.assertFalse(_claims(empty)["video"]["canPublish"])

    def test_webhook_needs_our_signature_and_the_exact_body(self):
        from livekit import api

        from app.core.config import settings
        from app.services.video_rooms import livekit_service as lk

        body, auth = _signed(api.WebhookEvent(event="room_finished", room=api.Room(name="vizu-x")))
        with patch.multiple(settings, **LK):
            self.assertEqual(lk.verify_webhook(body, auth).room.name, "vizu-x")
            with self.assertRaises(Exception):
                lk.verify_webhook(body.replace("vizu-x", "vizu-y"), auth)
            with self.assertRaises(Exception):
                lk.verify_webhook(body, None)
            forged = api.AccessToken(LK["LIVEKIT_API_KEY"], "another-secret-0123456789abcdef0123").with_sha256(
                base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()).to_jwt()
            with self.assertRaises(Exception):
                lk.verify_webhook(body, forged)
        with patch.multiple(settings, LIVEKIT_URL="", LIVEKIT_API_KEY="", LIVEKIT_API_SECRET=""):
            with self.assertRaises(Exception):
                lk.verify_webhook(body, auth)

    def test_grants_follow_the_stored_permissions(self):
        from app.models.video_room import ROLE_HOST, ROLE_STUDENT, VideoRoom, VideoRoomParticipant
        from app.services.video_rooms.permissions import can_chat, sources

        room = VideoRoom(chat_enabled=True)
        host = VideoRoomParticipant(role=ROLE_HOST, can_speak=False, can_share_screen=False, can_chat=False)
        self.assertEqual(sources(host), ["camera", "microphone", "screen_share", "screen_share_audio"])
        self.assertTrue(can_chat(VideoRoom(chat_enabled=False), host))
        s = VideoRoomParticipant(role=ROLE_STUDENT, can_speak=True, can_share_screen=False, can_chat=True)
        self.assertEqual(sources(s), ["camera", "microphone"])
        s.can_speak, s.can_share_screen = False, True
        self.assertEqual(sources(s), ["camera", "screen_share", "screen_share_audio"])
        self.assertTrue(can_chat(room, s))
        self.assertFalse(can_chat(VideoRoom(chat_enabled=False), s))
        s.can_chat = False
        self.assertFalse(can_chat(room, s))

    def test_api_url_never_needs_the_public_websocket(self):
        from app.core.config import settings
        from app.services.video_rooms import livekit_service as lk

        with patch.multiple(settings, LIVEKIT_URL="wss://vizu.example/livekit", LIVEKIT_API_URL=""):
            self.assertEqual(lk.api_url(), "https://vizu.example/livekit")
        with patch.multiple(settings, LIVEKIT_URL="wss://vizu.example/livekit", LIVEKIT_API_URL="http://127.0.0.1:7880"):
            self.assertEqual(lk.api_url(), "http://127.0.0.1:7880")


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestVideoRooms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.models.user import User

        cls.Session = sessionmaker(bind=create_engine(DB_URL))
        db = cls.Session()
        cls.tag = uuid.uuid4().hex[:6]
        users = {}
        for name, role in (("teacher", "TEACHER"), ("teacher2", "TEACHER"), ("admin", "SUPER_ADMIN"), ("staff", "ADMIN"),
                           ("s1", "STUDENT"), ("s2", "STUDENT"), ("s3", "STUDENT"), ("other", "STUDENT"), ("outsider", "STUDENT")):
            users[name] = User(email=f"v-{name}-{cls.tag}@test.local", username=f"v_{name}_{cls.tag}", password_hash="x", is_active=True,
                               is_verified=True, is_superuser=False, role=role, is_banned=False, preferred_language="uz", first_name=name)
            db.add(users[name])
        db.commit()
        cls.ids = {k: v.id for k, v in users.items()}
        db.close()

    def setUp(self):
        from sqlalchemy import text

        from app.core.config import settings
        from app.models.user import User
        from app.services.video_rooms import livekit_service as lk

        self.db = self.Session()
        self.db.execute(text("DELETE FROM auth_rate_limit_events WHERE action LIKE 'video_%'"))
        self.db.commit()
        self.user = {k: self.db.get(User, v) for k, v in self.ids.items()}
        self.fake = FakeGateway()
        self._patches = [patch.object(lk, "gateway", self.fake), patch.multiple(settings, **LK)]
        for p in self._patches:
            p.start()
        self.group, code = self._group("teacher")
        for s in ("s1", "s2", "s3"):
            self._join_group(s, code)
        self.group2, code2 = self._group("teacher2")
        self._join_group("other", code2)

    def tearDown(self):
        for p in self._patches:
            p.stop()
        self.db.rollback()
        self.db.close()

    # helpers
    def _group(self, teacher):
        from app.services.study_groups import groups

        g, code = groups.create(self.db, self.user[teacher], {"name": f"Video {uuid.uuid4().hex[:4]}", "level": "A1"})
        return g["id"], code

    def _join_group(self, who, code):
        from app.services.study_groups import groups

        groups.join(self.db, self.user[who], code, "10.0.0.1")

    def _status(self, fn, *args):
        with self.assertRaises(HTTPException) as ctx:
            fn(*args)
        return ctx.exception.status_code, ctx.exception.detail

    def _live(self, group=None, teacher="teacher", **extra):
        from app.services.video_rooms import service

        return service.create(self.db, self.user[teacher], group or self.group, {"title": "Nemis tili darsi", "start_now": True, **extra})

    def _join(self, who, room):
        from app.services.video_rooms import service

        return service.join(self.db, self.user[who], room["id"], "10.0.0.7")

    def _webhook(self, kind, room_name, identity=None, **participant):
        from livekit import api

        from app.services.video_rooms import moderation

        ev = api.WebhookEvent(event=kind, room=api.Room(name=room_name))
        if identity is not None:
            ev.participant.CopyFrom(api.ParticipantInfo(identity=identity, **participant))
        body, auth = _signed(ev)
        return moderation.webhook(self.db, body, auth)

    def _room_name(self, room):
        from app.models.video_room import VideoRoom

        return self.db.get(VideoRoom, room["id"]).room_name

    # 1, 3, 4: who may create and start
    def test_only_the_groups_teacher_or_super_admin_creates_rooms(self):
        from app.services.video_rooms import service

        data = {"title": "Dars", "start_now": True}
        self.assertEqual(self._status(service.create, self.db, self.user["s1"], self.group, data), (403, "VIDEO_MODERATOR_REQUIRED"))
        self.assertEqual(self._status(service.create, self.db, self.user["outsider"], self.group, data)[0], 404)
        self.assertEqual(self._status(service.create, self.db, self.user["teacher2"], self.group, data)[0], 404)
        self.assertEqual(self._status(service.create, self.db, self.user["staff"], self.group, data)[0], 404)  # ADMIN: existing policy
        room = service.create(self.db, self.user["admin"], self.group, data)
        self.assertEqual(room["status"], "live")
        self.assertEqual(self.fake.of("ensure")[0][1], self._room_name(room))
        self.assertTrue(self._room_name(room).startswith("vizu-"))

    def test_schedule_rules_and_one_live_room_per_group(self):
        from app.services.video_rooms import service

        t = self.user["teacher"]
        self.assertEqual(self._status(service.create, self.db, t, self.group, {"title": "Dars"})[1], "SCHEDULE_REQUIRED")
        self.assertEqual(self._status(service.create, self.db, t, self.group, {"title": "Dars", "scheduled_at": _now() - timedelta(hours=1)})[1],
                         "SCHEDULE_IN_PAST")
        self.assertEqual(self._status(service.create, self.db, t, self.group, {"title": "Dars", "scheduled_at": datetime.now() + timedelta(hours=1)})[1],
                         "SCHEDULE_TIMEZONE_REQUIRED")
        planned = service.create(self.db, t, self.group, {"title": "Ertangi dars", "scheduled_at": _now() + timedelta(days=1)})
        self.assertEqual(planned["status"], "scheduled")
        self.assertEqual(self._status(self._join, "s1", planned), (409, "VIDEO_ROOM_NOT_STARTED"))
        self._live()
        self.assertEqual(self._status(service.start, self.db, t, planned["id"]), (409, "VIDEO_ROOM_ALREADY_LIVE"))
        listed = service.list_rooms(self.db, self.user["s1"], self.group)
        self.assertEqual(listed["live"]["title"], "Nemis tili darsi")
        self.assertEqual([r["id"] for r in listed["upcoming"]], [planned["id"]])
        self.assertFalse(listed["is_manager"])
        self.assertEqual(service.active(self.db, self.user["s2"], self.group)["room"]["status"], "live")
        self.assertEqual(self._status(service.active, self.db, self.user["other"], self.group)[0], 404)
        cancelled = service.cancel(self.db, t, planned["id"])
        self.assertEqual(cancelled["status"], "cancelled")

    def test_start_fails_cleanly_without_livekit(self):
        from app.core.config import settings
        from app.models.video_room import VideoRoom
        from app.services.video_rooms import service

        planned = service.create(self.db, self.user["teacher"], self.group, {"title": "Dars", "scheduled_at": _now() + timedelta(hours=2)})
        self.fake.fail = True
        self.assertEqual(self._status(service.start, self.db, self.user["teacher"], planned["id"]), (503, "VIDEO_SERVICE_UNAVAILABLE"))
        self.assertEqual(self.db.get(VideoRoom, planned["id"]).status, "scheduled")
        self.fake.fail = False
        with patch.object(settings, "LIVEKIT_API_SECRET", ""):
            self.assertEqual(self._status(service.start, self.db, self.user["teacher"], planned["id"]), (503, "VIDEO_SERVICE_NOT_CONFIGURED"))

    # 1, 2: only members of THIS group get a token
    def test_join_token_only_for_members_of_the_rooms_group(self):
        room = self._live()
        out = self._join("s1", room)
        c = _claims(out["token"])
        self.assertEqual(c["sub"], str(self.ids["s1"]))
        self.assertEqual(c["video"]["room"], self._room_name(room))
        self.assertEqual(c["video"]["canPublishSources"], ["camera", "microphone"])
        self.assertTrue(c["video"]["canPublishData"])
        self.assertEqual(c["attributes"]["vizu.role"], "student")
        self.assertEqual(out["permissions"]["moderate"], False)
        self.assertEqual(out["server_url"], LK["LIVEKIT_URL"])
        self.assertNotIn("secret", json.dumps(out, default=str).lower())
        host = _claims(self._join("teacher", room)["token"])
        self.assertIn("screen_share", host["video"]["canPublishSources"])
        # outsiders, the other group's student and the other teacher learn nothing about the room
        for who in ("outsider", "other", "teacher2", "staff"):
            with self.subTest(who=who):
                self.assertEqual(self._status(self._join, who, room), (404, "VIDEO_ROOM_NOT_FOUND"))
        # the other group's live room does not open with this group's membership
        other_room = self._live(group=self.group2, teacher="teacher2")
        self.assertEqual(self._status(self._join, "s1", other_room), (404, "VIDEO_ROOM_NOT_FOUND"))
        self.assertEqual(self._join("other", other_room)["identity"], str(self.ids["other"]))

    def test_left_group_member_loses_access(self):
        from app.services.study_groups import groups

        room = self._live()
        self._join("s3", room)
        groups.leave(self.db, self.user["s3"], self.group)
        self.assertEqual(self._status(self._join, "s3", room)[0], 404)
        # and if LiveKit still reports them, the webhook throws them out
        self._webhook("participant_joined", self._room_name(room), str(self.ids["s3"]))
        self.assertIn(("remove", self._room_name(room), str(self.ids["s3"])), self.fake.calls)

    # 3: students never reach moderator actions
    def test_moderation_is_for_hosts_of_this_group_only(self):
        from app.services.video_rooms import moderation

        room = self._live()
        self._join("s1", room)
        s2 = self.ids["s2"]
        actions = [
            (moderation.mute_participant, (s2,)), (moderation.mute_all, (True,)), (moderation.mic_permission, (False, s2)),
            (moderation.screen_share_permission, (True, None)), (moderation.chat_permission, (False, None)),
            (moderation.remove_participant, (s2, True)),
        ]
        for fn, args in actions:
            with self.subTest(fn=fn.__name__):
                self.assertEqual(self._status(fn, self.db, self.user["s1"], room["id"], *args), (403, "VIDEO_MODERATOR_REQUIRED"))
                self.assertEqual(self._status(fn, self.db, self.user["teacher2"], room["id"], *args)[0], 404)
                self.assertEqual(self._status(fn, self.db, self.user["outsider"], room["id"], *args)[0], 404)
        from app.services.video_rooms import service

        for fn in (service.end, service.cancel, service.start):
            self.assertEqual(self._status(fn, self.db, self.user["s1"], room["id"]), (403, "VIDEO_MODERATOR_REQUIRED"))
        self.assertEqual(self.fake.of("remove"), [])
        self.assertEqual(self.fake.of("mute"), [])

    def test_mic_screen_and_chat_permissions_reach_livekit_and_the_next_token(self):
        from app.services.video_rooms import moderation

        room = self._live()
        self._join("s1", room)
        self._join("s2", room)
        t, s1 = self.user["teacher"], str(self.ids["s1"])
        out = moderation.mic_permission(self.db, t, room["id"], False, self.ids["s1"])
        self.assertTrue(out["live_applied"])
        self.assertIn(("mute", self._room_name(room), (s1,), ("microphone",)), self.fake.calls)
        self.assertIn(("perm", self._room_name(room), s1, ("camera",), True), self.fake.calls)
        self.assertNotIn("microphone", _claims(self._join("s1", room)["token"])["video"]["canPublishSources"])
        moderation.screen_share_permission(self.db, t, room["id"], True, None)
        self.assertIn("screen_share", _claims(self._join("s2", room)["token"])["video"]["canPublishSources"])
        moderation.chat_permission(self.db, t, room["id"], False, None)
        self.assertFalse(_claims(self._join("s2", room)["token"])["video"]["canPublishData"])
        self.assertTrue(_claims(self._join("teacher", room)["token"])["video"]["canPublishData"])  # the host always may
        self.assertEqual(self.fake.of("meta")[-1][2]["chat"], False)
        # a host is never moderated
        self.assertEqual(self._status(moderation.mute_participant, self.db, t, room["id"], self.ids["teacher"]), (409, "CANNOT_MODERATE_HOST"))

    def test_mute_all_with_lock_also_applies_to_students_who_join_later(self):
        from app.services.video_rooms import moderation

        room = self._live()
        self._join("s1", room)
        out = moderation.mute_all(self.db, self.user["teacher"], room["id"], True)
        self.assertTrue(out["locked"])
        self.assertEqual(out["muted_tracks"], 1)
        self.assertNotIn("microphone", _claims(self._join("s2", room)["token"])["video"]["canPublishSources"])
        moderation.mic_permission(self.db, self.user["teacher"], room["id"], True, None)
        self.assertIn("microphone", _claims(self._join("s2", room)["token"])["video"]["canPublishSources"])

    def test_remove_and_block(self):
        from app.services.video_rooms import moderation

        room = self._live()
        self._join("s1", room)
        self._join("s2", room)
        moderation.remove_participant(self.db, self.user["teacher"], room["id"], self.ids["s1"], False)
        self.assertIn(("remove", self._room_name(room), str(self.ids["s1"])), self.fake.calls)
        self.assertIn("token", self._join("s1", room))  # removed, not blocked: may come back
        moderation.remove_participant(self.db, self.user["teacher"], room["id"], self.ids["s2"], True)
        self.assertEqual(self._status(self._join, "s2", room), (403, "VIDEO_ROOM_REMOVED"))
        # a still-valid old token of the blocked student is thrown out by the webhook
        self.fake.calls.clear()
        self._webhook("participant_joined", self._room_name(room), str(self.ids["s2"]))
        self.assertEqual(self.fake.of("remove"), [("remove", self._room_name(room), str(self.ids["s2"]))])

    def test_raised_hands(self):
        from app.services.video_rooms import moderation, service

        room = self._live()
        self.assertEqual(self._status(moderation.raise_hand, self.db, self.user["s1"], room["id"], True, None), (409, "NOT_IN_ROOM"))
        self._join("s1", room)
        self._join("s2", room)
        out = moderation.raise_hand(self.db, self.user["s1"], room["id"], True, None)
        self.assertIsNotNone(out["hand_raised_at"])
        self.assertEqual(self.fake.of("attrs")[-1][2], str(self.ids["s1"]))
        self.assertEqual(self._status(moderation.raise_hand, self.db, self.user["s2"], room["id"], False, self.ids["s1"]),
                         (403, "VIDEO_MODERATOR_REQUIRED"))
        self.assertEqual(self._status(moderation.raise_hand, self.db, self.user["teacher"], room["id"], True, self.ids["s2"]),
                         (400, "ONLY_LOWER_OTHERS_HAND"))
        self.fake.present[self._room_name(room)] = [str(self.ids["s1"]), str(self.ids["s2"])]
        hands = [i for i in service.participants(self.db, self.user["teacher"], room["id"])["items"] if i["hand_raised_at"]]
        self.assertEqual([i["user_id"] for i in hands], [self.ids["s1"]])
        moderation.raise_hand(self.db, self.user["teacher"], room["id"], False, self.ids["s1"])
        self.assertEqual(self.fake.of("attrs")[-1][3], {"vizu.hand": ""})
        # the hand comes back with a new token (attributes), so a reload keeps it
        moderation.raise_hand(self.db, self.user["s2"], room["id"], True, None)
        self.assertTrue(_claims(self._join("s2", room)["token"])["attributes"]["vizu.hand"])

    def test_participant_list_students_see_who_is_online_teachers_see_absent(self):
        from app.services.video_rooms import service

        room = self._live()
        self._join("teacher", room)
        self._join("s1", room)
        self.fake.present[self._room_name(room)] = [str(self.ids["teacher"]), str(self.ids["s1"])]
        mine = service.participants(self.db, self.user["s1"], room["id"])
        self.assertEqual({i["user_id"] for i in mine["items"]}, {self.ids["teacher"], self.ids["s1"]})
        self.assertNotIn("absent", mine)
        self.assertNotIn("blocked", mine["items"][0])
        theirs = service.participants(self.db, self.user["teacher"], room["id"])
        self.assertEqual({a["user_id"] for a in theirs["absent"]}, {self.ids["s2"], self.ids["s3"]})
        self.assertEqual(theirs["online_count"], 2)
        self.assertTrue(all("email" not in i for i in theirs["items"]))

    def test_capacity_hosts_always_get_in(self):
        from app.services.video_rooms import service

        room = self._live(max_participants=2)
        self._join("s1", room)
        self._join("s2", room)
        self.assertEqual(self._status(self._join, "s3", room), (409, "VIDEO_ROOM_FULL"))
        self.assertIn("token", self._join("teacher", room))
        service.leave(self.db, self.user["s1"], room["id"])
        self.assertIn("token", self._join("s3", room))

    def test_join_is_rate_limited(self):
        room = self._live()
        for _ in range(12):
            self._join("s1", room)
        self.assertEqual(self._status(self._join, "s1", room), (429, "VIDEO_TOO_MANY_REQUESTS"))
        self.assertIn("token", self._join("s2", room))  # per user

    def test_webhook_syncs_connections_and_ends_empty_rooms(self):
        from livekit import api

        from app.models.video_room import VideoRoom, VideoRoomParticipant
        from app.services.video_rooms import moderation

        room = self._live()
        self._join("s1", room)
        name = self._room_name(room)
        self._webhook("participant_joined", name, str(self.ids["s1"]))
        p = self.db.scalar(__import__("sqlalchemy").select(VideoRoomParticipant).where(
            VideoRoomParticipant.room_id == room["id"], VideoRoomParticipant.user_id == self.ids["s1"]))
        self.assertEqual((p.connection_status, p.join_count), ("connected", 1))
        # a second tab replaces the first connection: still connected
        self._webhook("participant_left", name, str(self.ids["s1"]), disconnect_reason=api.DUPLICATE_IDENTITY)
        self.db.refresh(p)
        self.assertEqual(p.connection_status, "connected")
        self._webhook("participant_left", name, str(self.ids["s1"]))
        self.db.refresh(p)
        self.assertEqual(p.connection_status, "disconnected")
        # someone LiveKit reports who never got a token from us
        self._webhook("participant_joined", name, "intruder")
        self.assertIn(("remove", name, "intruder"), self.fake.calls)
        self._webhook("room_finished", name)
        self.assertEqual((self.db.get(VideoRoom, room["id"]).status, self.db.get(VideoRoom, room["id"]).end_reason), ("ended", "empty"))
        with self.assertRaises(HTTPException) as ctx:
            moderation.webhook(self.db, '{"event": "room_finished", "room": {"name": "%s"}}' % name, "forged")
        self.assertEqual(ctx.exception.status_code, 401)

    def test_end_closes_livekit_and_blocks_new_joins(self):
        from app.models.study_group import StudyGroupAuditLog
        from app.services.video_rooms import service

        room = self._live()
        self._join("s1", room)
        out = service.end(self.db, self.user["teacher"], room["id"])
        self.assertTrue(out["livekit_closed"])
        self.assertEqual(out["room"]["status"], "ended")
        self.assertIn(("delete", self._room_name(room)), self.fake.calls)
        self.assertEqual(self._status(self._join, "s1", room), (409, "VIDEO_ROOM_NOT_LIVE"))
        self.assertEqual(self._status(service.end, self.db, self.user["teacher"], room["id"]), (409, "VIDEO_ROOM_NOT_LIVE"))
        actions = {a.action for a in self.db.scalars(__import__("sqlalchemy").select(StudyGroupAuditLog).where(
            StudyGroupAuditLog.group_id == self.group))}
        self.assertTrue({"video_room_created", "video_room_started", "video_room_ended"} <= actions)

    def test_admin_overview_and_force_end(self):
        from app.models.video_room import VideoRoomEvent
        from app.services.video_rooms import service

        room = self._live()
        self.fake.present[self._room_name(room)] = [str(self.ids["teacher"])]
        overview = service.admin_overview(self.db)
        mine = [r for r in overview["live"] if r["id"] == room["id"]]
        self.assertEqual(mine[0]["server_participants"], 1)
        self.assertEqual(overview["livekit_status"], "available")
        out = service.admin_end(self.db, self.user["admin"], room["id"])
        self.assertEqual(out["room"]["end_reason"], "admin")
        events = [e.event_type for e in self.db.scalars(__import__("sqlalchemy").select(VideoRoomEvent).where(VideoRoomEvent.room_id == room["id"]))]
        self.assertIn("ended", events)
        for e in self.db.scalars(__import__("sqlalchemy").select(VideoRoomEvent).where(VideoRoomEvent.room_id == room["id"])):
            self.assertNotIn("token", json.dumps(e.meta or {}))

    def test_stale_rooms_expire(self):
        from app.models.video_room import VideoRoom
        from app.services.video_rooms import service

        room = self._live()
        r = self.db.get(VideoRoom, room["id"])
        r.started_at = _now() - timedelta(hours=7)
        self.db.commit()
        self.assertIsNone(service.active(self.db, self.user["s1"], self.group)["room"])
        self.assertEqual(self.db.get(VideoRoom, room["id"]).end_reason, "expired")


if __name__ == "__main__":
    unittest.main()
