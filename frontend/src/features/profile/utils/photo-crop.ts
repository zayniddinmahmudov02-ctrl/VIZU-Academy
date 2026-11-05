/**
 * Square crop of a profile photo (tests: tests/unit/photo-crop.test.mjs).
 * The image is shown in a square frame of `frame` px: at zoom 1 its short side fills the frame; (ox, oy) is
 * the image's top-left corner relative to the frame (≤ 0). The result is what the server expects
 * (app.services.profile_photo.crop_box): x / y = left / top as a fraction of width / height,
 * size = side as a fraction of the short side.
 */

export interface Crop {
  x: number;
  y: number;
  size: number;
}

export const MIN_ZOOM = 1;
export const MAX_ZOOM = 4;

const scale = (w: number, h: number, frame: number, zoom: number) => (frame / Math.min(w, h)) * zoom;

export function clampOffset(w: number, h: number, frame: number, zoom: number, ox: number, oy: number) {
  const s = scale(w, h, frame, zoom);
  return {
    ox: Math.min(0, Math.max(frame - w * s, ox)),
    oy: Math.min(0, Math.max(frame - h * s, oy)),
  };
}

export function centred(w: number, h: number, frame: number, zoom = 1) {
  const s = scale(w, h, frame, zoom);
  return { ox: (frame - w * s) / 2, oy: (frame - h * s) / 2 };
}

/** New offset after a zoom change that keeps the frame's centre on the same image point. */
export function zoomAround(w: number, h: number, frame: number, from: number, to: number, ox: number, oy: number) {
  const z = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, to));
  const s0 = scale(w, h, frame, from);
  const s1 = scale(w, h, frame, z);
  const cx = (frame / 2 - ox) / s0;
  const cy = (frame / 2 - oy) / s0;
  return { zoom: z, ...clampOffset(w, h, frame, z, frame / 2 - cx * s1, frame / 2 - cy * s1) };
}

export function toCrop(w: number, h: number, frame: number, zoom: number, ox: number, oy: number): Crop {
  const s = scale(w, h, frame, zoom);
  const round = (v: number) => Math.round(Math.min(1, Math.max(0, v)) * 10000) / 10000;
  return { x: round(-ox / s / w), y: round(-oy / s / h), size: round(1 / zoom) };
}
