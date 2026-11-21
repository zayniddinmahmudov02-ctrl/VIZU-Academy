// node --test tests/unit  (Node >= 22.18 runs the .ts module directly)
import assert from "node:assert/strict";
import { test } from "node:test";

import { formatCount, percentOf } from "../../src/features/admin/components/dashboard/student-stats-format.ts";

const NBSP = " ";

test("student counts are grouped by thousands with a non-breaking space", () => {
  assert.equal(formatCount(0), "0");
  assert.equal(formatCount(283), "283");
  assert.equal(formatCount(1250), `1${NBSP}250`);
  assert.equal(formatCount(12450), `12${NBSP}450`);
  assert.equal(formatCount(125000), `125${NBSP}000`);
  assert.equal(formatCount(1234567), `1${NBSP}234${NBSP}567`);
  assert.equal(formatCount(-1250), `-1${NBSP}250`);
});

test("no invented number when the API gave none", () => {
  assert.equal(formatCount(undefined), "—");
  assert.equal(formatCount(null), "—");
  assert.equal(formatCount(Number.NaN), "—");
});

test("share of active students", () => {
  assert.equal(percentOf(184, 281), "65 %");
  assert.equal(percentOf(0, 0), "—");
});
