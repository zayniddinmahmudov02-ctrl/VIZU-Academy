import assert from "node:assert/strict";
import { test } from "node:test";

import { apiAsset, clockOffset, msUntil, optionState, pollInterval, resolveThemeImage, winRate } from "../../src/features/battle/lib/battle-utils.ts";

const API = "https://vizu-deutsch.com/";

test("theme image references resolve only to shipped files or API assets", () => {
  assert.equal(resolveThemeImage("static:/battle/themes/berlin-desktop.webp", API), "/battle/themes/berlin-desktop.webp");
  assert.equal(resolveThemeImage(`asset:${"a".repeat(32)}.webp`, API), `https://vizu-deutsch.com/api/v1/battle/themes/assets/${"a".repeat(32)}.webp`);
  for (const bad of ["https://evil.example/x.webp", "static:/../etc/passwd", "asset:../x.webp", "static:/battle/themes/x.svg", "", null, undefined]) {
    assert.equal(resolveThemeImage(bad, API), null, String(bad));
  }
});

test("api assets get the API origin", () => {
  assert.equal(apiAsset("/api/v1/battle/media/t", API), "https://vizu-deutsch.com/api/v1/battle/media/t");
});

test("server clock offset and countdowns", () => {
  const offset = clockOffset("2026-11-05T12:00:10.000Z", Date.parse("2026-11-05T12:00:00.000Z"), 200);
  assert.equal(offset, 10_100);
  const now = Date.parse("2026-11-05T12:00:00.000Z");
  assert.equal(msUntil("2026-11-05T12:00:15.000Z", offset, now), 4_900);
  assert.equal(msUntil("2026-11-05T12:00:01.000Z", offset, now), 0);
  assert.equal(msUntil(null, 0, now), 0);
  assert.equal(clockOffset("garbage", 1), 0);
});

test("option states", () => {
  assert.equal(optionState(0, "question", null, null), "idle");
  assert.equal(optionState(2, "question", 2, null), "selected");
  assert.equal(optionState(1, "question", 2, null), "dimmed");
  assert.equal(optionState(2, "reveal", 2, 2), "correct");
  assert.equal(optionState(1, "reveal", 1, 2), "wrong");
  assert.equal(optionState(2, "reveal", 1, 2), "missed");
  assert.equal(optionState(2, "reveal", null, 2), "missed");
  assert.equal(optionState(3, "reveal", 1, 2), "dimmed");
});

test("misc", () => {
  assert.equal(winRate(0.667), "67%");
  assert.equal(pollInterval("active", false), 700);
  assert.equal(pollInterval("waiting", false), 1500);
  assert.equal(pollInterval("active", true), 4000);
  assert.equal(pollInterval("finished", false), false);
});
