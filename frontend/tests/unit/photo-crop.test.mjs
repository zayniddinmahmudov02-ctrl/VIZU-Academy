import assert from "node:assert/strict";
import { test } from "node:test";

import { centred, clampOffset, toCrop, zoomAround } from "../../src/features/profile/utils/photo-crop.ts";

test("centred landscape photo at zoom 1 = the server's centre square", () => {
  const { ox, oy } = centred(800, 600, 240);
  assert.deepEqual({ ox, oy }, { ox: -40, oy: 0 });
  assert.deepEqual(toCrop(800, 600, 240, 1, ox, oy), { x: 0.125, y: 0, size: 1 });
});

test("dragging is clamped so the frame stays covered", () => {
  assert.deepEqual(clampOffset(800, 600, 240, 1, 50, 50), { ox: 0, oy: 0 });
  assert.deepEqual(clampOffset(800, 600, 240, 1, -500, -500), { ox: -80, oy: 0 });
});

test("zoom keeps the centre and halves the crop side at zoom 2", () => {
  const start = centred(600, 600, 240);
  const z = zoomAround(600, 600, 240, 1, 2, start.ox, start.oy);
  assert.equal(z.zoom, 2);
  assert.deepEqual(toCrop(600, 600, 240, z.zoom, z.ox, z.oy), { x: 0.25, y: 0.25, size: 0.5 });
  assert.equal(zoomAround(600, 600, 240, 1, 9, 0, 0).zoom, 4);
});

test("top-left corner crop", () => {
  const z = zoomAround(1000, 500, 200, 1, 2, 0, 0);
  const c = toCrop(1000, 500, 200, z.zoom, 0, 0);
  assert.deepEqual(c, { x: 0, y: 0, size: 0.5 });
});
