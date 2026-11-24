// node --test tests/unit  (Node >= 22.18 runs the .ts modules directly)
import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

import { marketTranslations } from "../../src/lib/i18n/market-translations.ts";

const placeholders = (s) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort().join(",");

test("every My Teacher text exists in de and uz with the same placeholders", () => {
  for (const [key, value] of Object.entries(marketTranslations)) {
    assert.ok(value.de?.trim(), `${key}: de empty`);
    assert.ok(value.uz?.trim(), `${key}: uz empty`);
    assert.equal(placeholders(value.uz), placeholders(value.de), key);
  }
});

test("every error code of the marketplace backend has a text for students and teachers", (t) => {
  const backend = join(import.meta.dirname, "..", "..", "..", "backend", "app");
  const sources = [join(backend, "services", "teacher_market"), join(backend, "api", "teacher_market")];
  if (!sources.every(existsSync)) {
    t.skip("backend sources not in this checkout");
    return;
  }
  const codes = new Set();
  for (const dir of sources) {
    for (const name of readdirSync(dir).filter((n) => n.endsWith(".py"))) {
      const text = readFileSync(join(dir, name), "utf8");
      for (const m of text.matchAll(/\b(?:err|error)\(\s*\d{3}\s*,\s*"([A-Z0-9_]+)/g)) codes.add(m[1]);
    }
  }
  assert.ok(codes.size > 30, "the scan found the error codes");
  // codes built at run time by common.one_line ({FIELD}_REQUIRED / _TOO_SHORT) and common.choices ({FIELD}_INVALID)
  for (const field of ["TITLE", "TOPIC", "FIRST_NAME", "ISSUER", "REASON"]) codes.add(`${field}_REQUIRED`).add(`${field}_TOO_SHORT`);
  for (const field of ["LANGUAGES", "LEVELS", "EXAM_PREP", "WEEKDAYS"]) codes.add(`${field}_INVALID`);
  const missing = [...codes].filter((code) => !marketTranslations[`err_${code}`]);
  assert.deepEqual(missing, []);
});
