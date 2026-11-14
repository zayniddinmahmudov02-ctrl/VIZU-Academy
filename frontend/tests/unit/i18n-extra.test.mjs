import assert from "node:assert/strict";
import { test } from "node:test";

import { part1 } from "../../src/lib/i18n/extra/part1.ts";
import { part2 } from "../../src/lib/i18n/extra/part2.ts";
import { part3 } from "../../src/lib/i18n/extra/part3.ts";
import { part4 } from "../../src/lib/i18n/extra/part4.ts";
import { part5 } from "../../src/lib/i18n/extra/part5.ts";
import { part6 } from "../../src/lib/i18n/extra/part6.ts";
import { part7 } from "../../src/lib/i18n/extra/part7.ts";
import { part8 } from "../../src/lib/i18n/extra/part8.ts";
import { part9 } from "../../src/lib/i18n/extra/part9.ts";

const parts = [part1, part2, part3, part4, part5, part6, part7, part8, part9];
const placeholders = (s) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort().join(",");

test("every English / Russian text is filled and both use the same {placeholders}", () => {
  let n = 0;
  for (const part of parts) {
    for (const [ns, entries] of Object.entries(part)) {
      for (const [key, [en, ru]] of Object.entries(entries)) {
        n++;
        assert.ok(en.trim() && ru.trim(), `${ns}.${key} empty`);
        assert.equal(placeholders(en), placeholders(ru), `${ns}.${key} placeholders differ`);
      }
    }
  }
  assert.ok(n > 1700, `only ${n} translated keys`);
});

test("no namespace is split across two files", () => {
  const seen = new Map();
  for (const [i, part] of parts.entries()) {
    for (const ns of Object.keys(part)) {
      assert.ok(!seen.has(ns), `${ns} in part${seen.get(ns) + 1} and part${i + 1}`);
      seen.set(ns, i);
    }
  }
});

test("sidebar purchase label per language", () => {
  assert.deepEqual(part1.sidebar.angebote, ["Purchase", "Покупка"]);
});
