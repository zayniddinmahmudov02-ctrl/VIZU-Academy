import assert from "node:assert/strict";
import { test } from "node:test";

import { A2_MAX_BYTES, classify, precheck, summarize } from "../../src/features/admin/components/media-management/a2-audio-import.ts";

test("precheck lets real A2 names through", () => {
  for (const name of ["A2 1.Unterricht Hören.m4a", "A2 4.Unterricht Text 1.mp3", "A2 11.Unterricht Teil_1.M4A", "Aufnahme.mp3"]) {
    assert.equal(precheck(name, 900_000), null, name);
  }
});

test("precheck refuses what the server would refuse anyway", () => {
  assert.match(precheck("A2 1.Unterricht Hören.wav", 10), /MP3 oder M4A/);
  assert.match(precheck("ohne-endung", 10), /MP3 oder M4A/);
  assert.match(precheck("A2 1.Unterricht.mp3", 0), /leer/);
  assert.match(precheck("A2 1.Unterricht.mp3", A2_MAX_BYTES + 1), /100 MB/);
  assert.match(precheck("A1 3.Unterricht Hören.mp3", 10), /anderes Niveau/);
  assert.match(precheck("b1 Lektion.mp3", 10), /anderes Niveau/);
});

test("classify: created, duplicate, server error, network error", () => {
  assert.deepEqual(classify("a.mp3", { asset: { id: "1", linked: null } }),
                   { name: "a.mp3", outcome: "success", assetId: "1", message: null, unlinked: true });
  assert.equal(classify("a.mp3", { asset: { id: "1", linked: { listening_id: "x" } } }).unlinked, false);
  const dup = classify("b.mp3", { error: { response: { status: 409, data: { message: { code: "DUPLICATE", existing_id: "7", existing_filename: "A2 2.Unterricht Hören.mp3" } } } } });
  assert.equal(dup.outcome, "duplicate");
  assert.equal(dup.assetId, "7");
  assert.match(dup.message, /A2 2\.Unterricht Hören\.mp3/);
  const bad = classify("c.mp3", { error: { response: { status: 400, data: { message: "EXTENSION_MISMATCH: the content is M4A, the name says .mp3" } } } });
  assert.equal(bad.outcome, "error");
  assert.match(bad.message, /EXTENSION_MISMATCH/);
  assert.equal(classify("d.mp3", { error: new Error("Network Error") }).message, "Keine Verbindung zum Server.");
  assert.match(classify("e.mp3", { error: { response: { status: 500, data: {} } } }).message, /HTTP 500/);
});

test("summarize counts every outcome and the unlinked uploads", () => {
  const s = summarize([
    classify("a", { asset: { id: "1", linked: null } }),
    classify("b", { asset: { id: "2", linked: {} } }),
    classify("c", { error: { response: { status: 409, data: { message: { code: "DUPLICATE" } } } } }),
    classify("d", { error: { response: { status: 400, data: { message: "NOT_AUDIO" } } } }),
  ]);
  assert.deepEqual(s, { total: 4, success: 2, duplicate: 1, error: 1, unlinked: 1 });
});
