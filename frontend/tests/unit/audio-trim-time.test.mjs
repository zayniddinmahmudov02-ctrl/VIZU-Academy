import assert from "node:assert/strict";
import { test } from "node:test";

import { clampRange, formatMs, MIN_TRIM_MS, parseTime, peaks } from "../../src/features/admin/components/audio/audio-trim-time.ts";

test("formatMs writes mm:ss.s", () => {
  assert.equal(formatMs(0), "00:00.0");
  assert.equal(formatMs(35_000), "00:35.0");
  assert.equal(formatMs(80_500), "01:20.5");
  assert.equal(formatMs(225_000), "03:45.0");
  assert.equal(formatMs(-5), "00:00.0");
});

test("parseTime reads m:ss, seconds and decimal commas", () => {
  assert.equal(parseTime("1:20"), 80_000);
  assert.equal(parseTime("00:35"), 35_000);
  assert.equal(parseTime("01:20.5"), 80_500);
  assert.equal(parseTime("80"), 80_000);
  assert.equal(parseTime("80,5"), 80_500);
  assert.equal(parseTime("1:02:03"), 3_723_000);
  for (const bad of ["", "abc", "1:xx", "-5", "1:2:3:4"]) assert.equal(parseTime(bad), null, bad);
});

test("the example from the brief: 00:35 to 01:20 of a 03:45 file is 45 seconds", () => {
  const [start, end] = clampRange(parseTime("00:35"), parseTime("01:20"), 225_000, "end");
  assert.equal(end - start, 45_000);
});

test("clampRange stays inside the audio and keeps a minimum length", () => {
  assert.deepEqual(clampRange(-100, 5_000, 10_000, "start"), [0, 5_000]);
  assert.deepEqual(clampRange(1_000, 99_000, 10_000, "end"), [1_000, 10_000]);
  assert.deepEqual(clampRange(5_000, 5_100, 10_000, "end"), [5_000, 5_000 + MIN_TRIM_MS]);
  assert.deepEqual(clampRange(4_900, 5_000, 10_000, "start"), [5_000 - MIN_TRIM_MS, 5_000]);
});

test("peaks are normalised to 0..1 per bucket", () => {
  const samples = new Float32Array([0, 0.5, -1, 0.25, 0, 0, 0.1, -0.1]);
  const out = peaks(samples, 4);
  assert.equal(out.length, 4);
  assert.equal(Math.max(...out), 1);
  assert.ok(out.every((v) => v >= 0 && v <= 1));
});
