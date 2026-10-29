// node --test tests/unit  (Node >= 22.18 runs the .ts module directly, no build step, no extra dependency)
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  AXIS_LOCK_PX, LONG_PRESS_MS, SWIPE_MAX_PX, SWIPE_TRIGGER_PX,
  endSwipe, moveSwipe, startSwipe, swipeOffset, swipeProgress,
} from "../../src/features/global-chat/reply-swipe.ts";

/** drag along points [[dx, dy, ms], ...] from (200, 300) at t=0 */
function drag(points, { selection = false } = {}) {
  let s = startSwipe(200, 300, 0);
  for (const [dx, dy, at] of points) s = moveSwipe(s, 200 + dx, 300 + dy, at, selection);
  return s;
}

test("a clear leftward swipe past the trigger replies", () => {
  const s = drag([[-12, 1, 30], [-40, 3, 60], [-SWIPE_TRIGGER_PX - 5, 4, 90]]);
  assert.equal(s.axis, "x");
  assert.equal(endSwipe(s), true);
  assert.equal(swipeProgress(s), 1);
});

test("releasing before the trigger, or pulling back, does not reply", () => {
  assert.equal(endSwipe(drag([[-15, 0, 20], [-SWIPE_TRIGGER_PX + 10, 0, 60]])), false);
  assert.equal(endSwipe(drag([[-15, 0, 20], [-SWIPE_TRIGGER_PX - 10, 0, 60], [-20, 0, 120]])), false);
});

test("vertical scrolling wins: the swipe is dropped for the whole touch", () => {
  const s = drag([[-3, 14, 20], [-90, 40, 80]]); // starts vertical, later moves far left
  assert.equal(s.cancelled, true);
  assert.equal(s.axis, "y");
  assert.equal(endSwipe(s), false);
  assert.equal(swipeOffset(s), 0);
});

test("a diagonal drag is treated as scrolling", () => {
  assert.equal(drag([[-20, 16, 30]]).cancelled, true); // |dx| not > 1.5 * |dy|
});

test("rightward drags are never a reply (system back gesture)", () => {
  const s = drag([[20, 0, 20], [120, 0, 60]]);
  assert.equal(s.cancelled, true);
  assert.equal(endSwipe(s), false);
});

test("tiny jitter below the axis lock decides nothing", () => {
  const s = drag([[-(AXIS_LOCK_PX - 1), 2, 20]]);
  assert.equal(s.axis, "none");
  assert.equal(s.cancelled, false);
  assert.equal(swipeOffset(s), 0);
});

test("text selection and long press leave the message alone", () => {
  assert.equal(drag([[-80, 0, 40]], { selection: true }).cancelled, true);
  assert.equal(drag([[-2, 0, 100], [-80, 0, LONG_PRESS_MS + 50]]).cancelled, true);
});

test("the bubble follows 1:1 to the trigger, then with resistance, capped", () => {
  assert.equal(swipeOffset(drag([[-30, 0, 30]])), -30);
  const far = drag([[-15, 0, 10], [-400, 0, 60]]);
  assert.equal(swipeOffset(far), -SWIPE_MAX_PX);
  const just = drag([[-15, 0, 10], [-(SWIPE_TRIGGER_PX + 20), 0, 60]]);
  assert.ok(swipeOffset(just) > -(SWIPE_TRIGGER_PX + 20) && swipeOffset(just) < -SWIPE_TRIGGER_PX);
});

test("a cancelled swipe stays cancelled", () => {
  let s = drag([[0, 30, 20]]);
  s = moveSwipe(s, 0, 300, 40, false);
  assert.equal(s.cancelled, true);
  assert.equal(endSwipe(s), false);
});
