import assert from "node:assert/strict";
import { test } from "node:test";

import { isExamPath, isMusicPath, playerView, progressFraction, ringOffset, songSeconds } from "../../src/features/medien/lib/player-view.ts";

test("Medien → Musik is recognised, other pages are not", () => {
  for (const p of ["/medien/musik", "/medien/musik/", "/medien/musik/x"]) assert.equal(isMusicPath(p), true, p);
  for (const p of ["/medien", "/medien/musikalisch", "/medien/bibliothek", "/dashboard", "", null, undefined]) assert.equal(isMusicPath(p), false, String(p));
});

test("the Multilevel exam page moves the disc above the Hören dock", () => {
  assert.equal(isExamPath("/vorbereitung/multilevel/pruefung/abc"), true);
  assert.equal(isExamPath("/vorbereitung/multilevel"), false);
  assert.equal(isExamPath(null), false);
});

test("which player view is shown", () => {
  const v = (hasSong, isMusicPageActive, isLargePlayerOpen) => playerView({ hasSong, isMusicPageActive, isLargePlayerOpen });
  // nothing loaded (or X pressed): nothing at all
  assert.deepEqual(v(false, true, true), { large: false, floating: false, bar: false });
  assert.deepEqual(v(false, false, false), { large: false, floating: false, bar: false });
  // the large player hides the others, wherever it is opened
  assert.deepEqual(v(true, true, true), { large: true, floating: false, bar: false });
  assert.deepEqual(v(true, false, true), { large: true, floating: false, bar: false });
  // back on Musik: the page + bar, no floating disc
  assert.deepEqual(v(true, true, false), { large: false, floating: false, bar: true });
  // any other page: only the floating disc
  assert.deepEqual(v(true, false, false), { large: false, floating: true, bar: false });
});

test("progress ring and song length", () => {
  assert.equal(progressFraction(30, 120), 0.25);
  assert.equal(progressFraction(200, 120), 1);
  assert.equal(progressFraction(-5, 120), 0);
  assert.equal(progressFraction(10, 0), 0);
  assert.equal(progressFraction(10, Number.NaN), 0);
  assert.equal(ringOffset(0, 100, 300), 300);
  assert.equal(ringOffset(50, 100, 300), 150);
  assert.equal(ringOffset(100, 100, 300), 0);
  assert.equal(songSeconds(Number.NaN, 90_000), 90);
  assert.equal(songSeconds(42.5, 90_000), 42.5);
  assert.equal(songSeconds(0, null), 0);
});
