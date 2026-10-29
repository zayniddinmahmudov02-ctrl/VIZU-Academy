import assert from "node:assert/strict";
import { test } from "node:test";

import { EXCERPT_CHARS, excerpt, resolveReply } from "../../src/features/global-chat/reply-preview.ts";

const ref = (over = {}) => ({ id: "m1", available: true, sender: { id: "u1", name: "Aziz" }, excerpt: "Server-Text", ...over });
const msg = (over = {}) => ({ id: "m1", body: "Lokaler Text", status: "visible", sender: { id: "u1", name: "Aziz" }, ...over });
const none = new Map();
const noRemoved = new Set();

test("no reply -> nothing to show", () => {
  assert.equal(resolveReply(null, none, noRemoved), null);
  assert.equal(resolveReply(undefined, none, noRemoved), null);
});

test("original not loaded: the server's quote is used", () => {
  assert.deepEqual(resolveReply(ref(), none, noRemoved), { id: "m1", available: true, senderName: "Aziz", excerpt: "Server-Text" });
});

test("original loaded: its current (edited) text wins", () => {
  const loaded = new Map([["m1", msg({ body: "nach dem Bearbeiten" })]]);
  assert.equal(resolveReply(ref(), loaded, noRemoved).excerpt, "nach dem Bearbeiten");
});

test("deleted, removed by polling or unavailable on the server -> fallback, no text", () => {
  const gone = { id: "m1", available: false, senderName: null, excerpt: null };
  assert.deepEqual(resolveReply(ref(), none, new Set(["m1"])), gone);
  assert.deepEqual(resolveReply(ref({ available: false, sender: null, excerpt: null }), none, noRemoved), gone);
  assert.deepEqual(resolveReply(ref(), new Map([["m1", msg({ status: "deleted" })]]), noRemoved), gone);
  assert.deepEqual(resolveReply(ref(), new Map([["m1", msg({ body: null, status: "hidden" })]]), noRemoved), gone);
});

test("deleted account: name left to the caller", () => {
  assert.equal(resolveReply(ref({ sender: null }), none, noRemoved).senderName, null);
});

test("excerpt collapses whitespace and never cuts an emoji in half", () => {
  assert.equal(excerpt("  Hallo \n\n  Welt  "), "Hallo Welt");
  const long = "😀".repeat(EXCERPT_CHARS + 20);
  const out = excerpt(long);
  assert.equal(Array.from(out).length, EXCERPT_CHARS);
  assert.ok(out.endsWith("…"));
  assert.ok(!out.includes("�"));
  assert.equal(excerpt(""), "");
});
