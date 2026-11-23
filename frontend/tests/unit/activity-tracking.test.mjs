// node --test tests/unit  (Node >= 22.18 runs the .ts module directly)
import assert from "node:assert/strict";
import { test } from "node:test";

import { heartbeatContexts, IDLE_MS, isActive, newTabId, pageContext } from "../../src/features/activity/lib/activity-context.ts";
import { barScale, formatClock, formatDuration, percent } from "../../src/features/activity/lib/format.ts";

const LESSON = "0f8a1d4e-7a7b-4f1c-9a52-1c2d3e4f5a6b";
const SONG = "11111111-2222-4333-8444-555555555555";
const BOOK = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee";

test("the page decides the learning area", () => {
  assert.deepEqual(pageContext(`/lektion/${LESSON}`), { area: "COURSE", ref_id: LESSON, position: null });
  assert.deepEqual(pageContext(`/lektion/${LESSON}/wortschatz`), { area: "WORTSCHATZ", ref_id: LESSON, position: null });
  assert.deepEqual(pageContext(`/lessons/${LESSON}/vocabulary`), { area: "WORTSCHATZ", ref_id: LESSON, position: null });
  assert.deepEqual(pageContext("/woerterbuch"), { area: "WORTSCHATZ", ref_id: null, position: null });
  assert.equal(pageContext("/vorbereitung/multilevel")?.area, "EXAM");
  assert.equal(pageContext("/vizu-multilevel/x/lesen")?.area, "EXAM");
  assert.equal(pageContext("/dashboard"), null);
  assert.equal(pageContext("/medien/bibliothek/abc"), null, "books come from the reader, not the path");
  assert.equal(pageContext("/lektion/not-a-uuid"), null);
});

test("active = visible and input within the idle time", () => {
  assert.equal(isActive(1000, 1000 + IDLE_MS, true), true);
  assert.equal(isActive(1000, 1001 + IDLE_MS, true), false);
  assert.equal(isActive(1000, 2000, false), false, "a hidden tab is never active");
});

test("a page or book counts only while active, media only while playing", () => {
  const page = pageContext(`/lektion/${LESSON}`);
  const song = { area: "MUSIC", refId: SONG, position: 42.7, playing: true };
  const book = { area: "BOOK", refId: BOOK, position: null, playing: false };
  assert.deepEqual(heartbeatContexts(page, [song, book], true), [
    { area: "COURSE", ref_id: LESSON, position: null },
    { area: "MUSIC", ref_id: SONG, position: 42 },
    { area: "BOOK", ref_id: BOOK, position: null },
  ]);
  assert.deepEqual(heartbeatContexts(page, [song, book], false), [{ area: "MUSIC", ref_id: SONG, position: 42 }], "idle: only the playing song");
  assert.equal(heartbeatContexts(page, [{ ...song, playing: false }, book], false), null, "idle and nothing plays: send nothing");
  assert.deepEqual(heartbeatContexts(null, [{ ...song, playing: false }], true), [], "active on a page without an area: session time only");
  assert.deepEqual(heartbeatContexts(null, [{ ...song, refId: "x" }], true), [], "an id that is not a uuid is never sent");
});

test("tab ids", () => {
  const id = newTabId();
  assert.match(id, /^[a-z0-9]{16}$/);
  assert.notEqual(newTabId(), id);
});

test("durations and clocks", () => {
  assert.equal(formatDuration(0, "uz"), "0 daq");
  assert.equal(formatDuration(45, "de"), "45 Sek.");
  assert.equal(formatDuration(600, "uz"), "10 daq");
  assert.equal(formatDuration(3725, "uz"), "1 soat 2 daq");
  assert.equal(formatDuration(7200, "de"), "2 Std.");
  assert.equal(formatDuration(null, "de"), "0 Min.");
  assert.equal(formatClock(65), "1:05");
  assert.equal(formatClock(3725), "1:02:05");
  assert.equal(percent(12, 14), 86);
  assert.equal(percent(5, 0), null);
  assert.equal(percent(20, 10), 100);
  assert.deepEqual(barScale([{ total: 0 }, { total: 50 }, { total: 100 }]), [0, 50, 100]);
  assert.deepEqual(barScale([{ total: 0 }]), [0]);
});
