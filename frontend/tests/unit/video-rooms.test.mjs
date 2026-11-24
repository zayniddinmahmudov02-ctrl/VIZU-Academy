// node --test tests/unit  (Node >= 22.18 runs the .ts modules directly)
import assert from "node:assert/strict";
import { test } from "node:test";

import { part12 } from "../../src/lib/i18n/extra/part12.ts";
import { videoRoomTranslations } from "../../src/lib/i18n/video-room-translations.ts";
import {
  cleanChat,
  clockOffset,
  FIVE_MINUTES_MS,
  remainingMs,
  errorCodeOf,
  errorKey,
  formatDuration,
  gridColumns,
  handsInOrder,
  initials,
  KNOWN_ERRORS,
  localInputToIso,
  mediaErrorKey,
  parseRoomMeta,
  roleOf,
  SOURCE,
  toLocalInput,
} from "../../src/features/video-rooms/video-room-utils.ts";

const placeholders = (s) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort().join(",");

test("every video lesson text exists in uz, de, en and ru with the same placeholders", () => {
  const extra = part12.videoRoom;
  assert.deepEqual(Object.keys(extra).sort(), Object.keys(videoRoomTranslations).sort());
  for (const [key, { de, uz }] of Object.entries(videoRoomTranslations)) {
    const [en, ru] = extra[key];
    for (const s of [de, uz, en, ru]) assert.ok(s.trim(), `${key} empty`);
    assert.equal(placeholders(uz), placeholders(de), key);
    assert.equal(placeholders(en), placeholders(de), key);
    assert.equal(placeholders(ru), placeholders(de), key);
  }
  for (const code of KNOWN_ERRORS) assert.ok(videoRoomTranslations[`err_${code}`], `no text for ${code}`);
});

test("room metadata from the backend, with safe defaults", () => {
  const defaults = { title: "", chat: true, screenShare: false, mic: true, camera: true, endsAt: null };
  assert.deepEqual(parseRoomMeta(undefined), defaults);
  assert.deepEqual(parseRoomMeta("not json"), defaults);
  assert.deepEqual(parseRoomMeta(JSON.stringify({ title: "Dars", chat: false, screen_share: true, mic: false, camera: false, ends_at: "2026-11-24T10:30:00+00:00" })),
    { title: "Dars", chat: false, screenShare: true, mic: false, camera: false, endsAt: "2026-11-24T10:30:00+00:00" });
  assert.equal(parseRoomMeta(JSON.stringify({ chat: "no" })).chat, true); // wrong types are ignored
  assert.equal(parseRoomMeta(JSON.stringify({ ends_at: "soon" })).endsAt, null);
});

test("special lesson countdown uses the server clock", () => {
  const end = "2026-11-24T10:30:00.000Z";
  const now = Date.parse("2026-11-24T10:20:00.000Z");
  assert.equal(remainingMs(end, now), 10 * 60 * 1000);
  // the local clock is 2 minutes behind the server: 2 minutes less remain
  assert.equal(remainingMs(end, now, clockOffset("2026-11-24T10:22:00.000Z", now)), 8 * 60 * 1000);
  assert.equal(remainingMs(end, now + 3_600_000), 0); // never negative
  assert.equal(remainingMs(null, now), null);
  assert.equal(clockOffset(undefined, now), 0);
  assert.ok(FIVE_MINUTES_MS === 300_000);
});

test("role comes from backend attributes or token metadata only", () => {
  assert.equal(roleOf(JSON.stringify({ role: "host" })), "host");
  assert.equal(roleOf(undefined, { "vizu.role": "host" }), "host");
  assert.equal(roleOf("{bad"), "student");
  assert.equal(roleOf(JSON.stringify({ role: "admin" })), "student");
});

test("durations, grid columns, initials", () => {
  assert.equal(formatDuration(0), "00:00");
  assert.equal(formatDuration(-5), "00:00");
  assert.equal(formatDuration(65_000), "01:05");
  assert.equal(formatDuration(3_723_000), "1:02:03");
  assert.equal(gridColumns(1, 1200), 1);
  assert.equal(gridColumns(2, 1200), 2);
  assert.equal(gridColumns(5, 1200), 3);
  assert.equal(gridColumns(16, 1200), 4);
  assert.equal(gridColumns(30, 1200), 4);
  assert.equal(gridColumns(9, 390), 2); // phone: never more than 2
  assert.equal(gridColumns(9, 800), 3);
  assert.equal(initials("Ali Valiyev"), "AV");
  assert.equal(initials("  madina "), "M");
  assert.equal(initials(""), "?");
});

test("raised hands keep the order they went up; lowered hands drop out", () => {
  const out = handsInOrder([
    { identity: "b", hand: "2026-11-21T10:00:05.000Z" },
    { identity: "a", hand: "" },
    { identity: "c", hand: "2026-11-21T10:00:01.000Z" },
  ]);
  assert.deepEqual(out.map((h) => h.identity), ["c", "b"]);
});

test("schedule input converts local time to an ISO time with zone", () => {
  assert.equal(localInputToIso(""), "");
  assert.equal(localInputToIso("nonsense"), "");
  const d = new Date(2026, 10, 21, 18, 30);
  assert.equal(toLocalInput(d), "2026-11-21T18:30");
  assert.equal(localInputToIso(toLocalInput(d)), d.toISOString());
});

test("backend error codes map to texts; unknown ones to the generic text", () => {
  const err = (message) => ({ response: { data: { message } } });
  assert.equal(errorCodeOf(err("VIDEO_ROOM_FULL")), "VIDEO_ROOM_FULL");
  assert.equal(errorCodeOf(err("VIDEO_ROOM_FULL: human text")), "VIDEO_ROOM_FULL");
  assert.equal(errorKey(err("VIDEO_ROOM_REMOVED")), "videoRoom.err_VIDEO_ROOM_REMOVED");
  assert.equal(errorKey(err("<script>")), "videoRoom.err_generic");
  assert.equal(errorKey(new Error("x")), "videoRoom.err_generic");
});

test("camera / microphone errors become clear messages", () => {
  assert.equal(mediaErrorKey({ name: "NotAllowedError" }), "videoRoom.perm_denied");
  assert.equal(mediaErrorKey({ name: "NotFoundError" }), "videoRoom.perm_notfound");
  assert.equal(mediaErrorKey({ name: "NotReadableError" }), "videoRoom.perm_busy");
  assert.equal(mediaErrorKey({ name: "Weird" }), "videoRoom.perm_other");
  assert.equal(mediaErrorKey({ name: "NotAllowedError" }, false), "videoRoom.perm_insecure");
});

test("chat text is trimmed, stripped of control characters and capped", () => {
  assert.equal(cleanChat("  salom\u0000 \u0007 "), "salom");
  assert.equal(cleanChat("a\nb"), "a\nb");
  assert.equal(cleanChat("x".repeat(900)).length, 500);
});

test("LiveKit TrackSource numbers used for permissions", () => {
  assert.deepEqual(SOURCE, { camera: 1, microphone: 2, screenShare: 3, screenShareAudio: 4 });
});
