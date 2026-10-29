/** Swipe-left-to-reply, as plain functions (no React, no DOM) so the rules
 *  can be unit-tested (frontend/tests/unit/reply-swipe.test.mjs).
 *
 *  Rules — the gesture must never take over what the finger meant:
 *  * only a clearly horizontal, leftward drag is a reply swipe; the axis is
 *    decided once, after AXIS_LOCK_PX of movement. Vertical (or diagonal)
 *    → the list scrolls, the swipe is dropped for this touch;
 *  * a rightward drag is never ours (system "back" gesture, nothing to do);
 *  * holding still longer than LONG_PRESS_MS first, or an active text
 *    selection, means the user is selecting text → dropped;
 *  * the reply fires on release beyond SWIPE_TRIGGER_PX, not while moving,
 *    so pulling back cancels it. */

export const AXIS_LOCK_PX = 10;
export const SWIPE_TRIGGER_PX = 64;
export const SWIPE_MAX_PX = 96;
export const LONG_PRESS_MS = 450;
/** horizontal must dominate: |dx| > |dy| * AXIS_RATIO */
export const AXIS_RATIO = 1.5;

export type SwipeAxis = "none" | "x" | "y";

export interface SwipeState {
  startX: number;
  startY: number;
  startAt: number;
  axis: SwipeAxis;
  dx: number;
  cancelled: boolean;
}

export function startSwipe(x: number, y: number, at: number): SwipeState {
  return { startX: x, startY: y, startAt: at, axis: "none", dx: 0, cancelled: false };
}

export function moveSwipe(s: SwipeState, x: number, y: number, at: number, hasSelection: boolean): SwipeState {
  if (s.cancelled) return s;
  if (hasSelection) return { ...s, cancelled: true, dx: 0 };
  const dx = x - s.startX;
  const dy = y - s.startY;
  if (s.axis === "none") {
    if (Math.abs(dx) < AXIS_LOCK_PX && Math.abs(dy) < AXIS_LOCK_PX) return s;
    if (at - s.startAt > LONG_PRESS_MS) return { ...s, cancelled: true }; // long press first: text selection
    const horizontal = Math.abs(dx) > Math.abs(dy) * AXIS_RATIO;
    if (!horizontal || dx > 0) return { ...s, axis: horizontal ? "x" : "y", cancelled: true, dx: 0 };
    return { ...s, axis: "x", dx: Math.min(0, dx) };
  }
  return { ...s, dx: Math.min(0, dx) };
}

/** true → reply to the message */
export function endSwipe(s: SwipeState): boolean {
  return !s.cancelled && s.axis === "x" && s.dx <= -SWIPE_TRIGGER_PX;
}

/** How far the bubble follows the finger (px, ≤ 0): 1:1 up to the trigger, then with resistance, capped. */
export function swipeOffset(s: SwipeState): number {
  if (s.cancelled || s.axis !== "x") return 0;
  const pull = -s.dx;
  const eased = pull <= SWIPE_TRIGGER_PX ? pull : SWIPE_TRIGGER_PX + (pull - SWIPE_TRIGGER_PX) * 0.35;
  return -Math.min(SWIPE_MAX_PX, eased);
}

/** 0..1 — how close the swipe is to replying (for the reply icon). */
export function swipeProgress(s: SwipeState): number {
  return Math.min(1, -swipeOffset(s) / SWIPE_TRIGGER_PX);
}
