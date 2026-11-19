/* Pure maths of the book reader's page view (no React, no project imports: unit-tested with node --test).
 * Coordinates: px relative to the CENTRE of the stage; the page box is centred and moved by (x, y), scaled around its centre by `scale`. */

export interface View { scale: number; x: number; y: number }
export interface Point { x: number; y: number }

export const MIN_SCALE = 1;
export const MAX_SCALE = 4;
export const ZOOM_STEPS = [1, 1.25, 1.5, 2, 3, 4];
/** a swipe turns the page when the finger travelled this share of the page width … */
export const SWIPE_SHARE = 0.18;
/** … or was fast (px per ms) */
export const SWIPE_SPEED = 0.45;
export const TAP_MOVE = 10;
export const TAP_MS = 350;
/** the page angle (deg) when it lies on the other side of the spine */
export const FLIP_DEG = 100;

export const clampScale = (s: number) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, s));

/** The biggest page box (CSS px) of this aspect ratio (width / height) that fits the stage minus `pad` on every side. */
export function fitPage(stageW: number, stageH: number, ratio: number, pad = 12): { w: number; h: number } {
  const w = Math.max(1, stageW - 2 * pad);
  const h = Math.max(1, stageH - 2 * pad);
  const r = ratio > 0 ? ratio : 0.707;
  return w / h > r ? { w: Math.round(h * r), h: Math.round(h) } : { w: Math.round(w), h: Math.round(w / r) };
}

/** Keeps a zoomed page covering the stage (no empty band beside it); a page smaller than the stage stays centred on that axis. */
export function clampView(v: View, pageW: number, pageH: number, stageW: number, stageH: number): View {
  const scale = clampScale(v.scale);
  const limX = Math.max(0, (pageW * scale - stageW) / 2);
  const limY = Math.max(0, (pageH * scale - stageH) / 2);
  return { scale, x: Math.min(limX, Math.max(-limX, v.x)) + 0, y: Math.min(limY, Math.max(-limY, v.y)) + 0 }; // + 0: no "-0"
}

export const distance = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y);
export const midpoint = (a: Point, b: Point): Point => ({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 });

/** Two-finger zoom: the point of the page that was under the fingers' midpoint at the start stays under the (moving) midpoint — so the
 * fingers zoom where they are and can move the page at the same time. */
export function pinchView(start: View, a0: Point, b0: Point, a: Point, b: Point): View {
  const d0 = Math.max(1, distance(a0, b0));
  const scale = clampScale(start.scale * (distance(a, b) / d0));
  const m0 = midpoint(a0, b0);
  const m = midpoint(a, b);
  const px = (m0.x - start.x) / start.scale; // that page point, unscaled, relative to the page centre
  const py = (m0.y - start.y) / start.scale;
  return { scale, x: m.x - px * scale, y: m.y - py * scale };
}

/** Zoom by a factor around a point (a button: the stage centre = 0,0; a double tap / ctrl+wheel: where it happened). */
export function zoomAt(v: View, scale: number, at: Point = { x: 0, y: 0 }): View {
  const s = clampScale(scale);
  const px = (at.x - v.x) / v.scale;
  const py = (at.y - v.y) / v.scale;
  return { scale: s, x: at.x - px * s, y: at.y - py * s };
}

export function nextZoomStep(scale: number, dir: 1 | -1): number {
  if (dir > 0) return ZOOM_STEPS.find((z) => z > scale + 1e-3) ?? MAX_SCALE;
  return [...ZOOM_STEPS].reverse().find((z) => z < scale - 1e-3) ?? MIN_SCALE;
}

/** What a finished one-finger drag on an un-zoomed page means: right-to-left = next page, left-to-right = previous, a mostly vertical
 * or short, slow one = nothing. */
export function swipeDecision(dx: number, dy: number, ms: number, width: number): "next" | "prev" | "cancel" {
  if (Math.abs(dx) < 24 || Math.abs(dy) > Math.abs(dx) * 0.9) return "cancel";
  const far = Math.abs(dx) >= width * SWIPE_SHARE;
  const fast = Math.abs(dx) / Math.max(1, ms) >= SWIPE_SPEED && Math.abs(dx) >= 40;
  if (!far && !fast) return "cancel";
  return dx < 0 ? "next" : "prev";
}

/** A tap / click on an un-zoomed page: the outer thirds turn the page (left = back, right = forward), the middle does nothing. */
export function tapZone(x: number, width: number): "prev" | "next" | "middle" {
  if (width <= 0) return "middle";
  const share = x / width;
  return share < 1 / 3 ? "prev" : share > 2 / 3 ? "next" : "middle";
}

/** The angle of the turning page while a finger drags it (0 = flat on the right, -FLIP_DEG = on the left side of the spine). */
export function dragAngle(dx: number, width: number, dir: "next" | "prev"): number {
  const share = Math.min(1, Math.abs(dx) / Math.max(1, width * 0.8));
  return dir === "next" ? -FLIP_DEG * share : -FLIP_DEG * (1 - share);
}
