// node --test tests/unit  (Node >= 22.18 runs the .ts module directly)
import assert from "node:assert/strict";
import { test } from "node:test";

import { formatGaps, formatSchreibenTable, lesenTableProblems, parseSchreibenTable } from "../../src/features/vorbereitung/lib/multilevel-scoring.ts";

test("Schreiben table round-trips in the official notation", () => {
  const rows = [[22.1, 22.5, 54], [35.1, 36, 75], [5.6, 6, 21]];
  const text = formatSchreibenTable(rows);
  assert.equal(text, "35.1–36.0 = 75\n22.1–22.5 = 54\n5.6–6.0 = 21");
  assert.deepEqual(parseSchreibenTable(text), { rows: [[35.1, 36, 75], [22.1, 22.5, 54], [5.6, 6, 21]], errors: [] });
});

test("Schreiben table parser accepts hyphens and decimal commas, reports unreadable lines", () => {
  const { rows, errors } = parseSchreibenTable("19,6-20,0 = 47\n\n18.6 – 19.0: 46\nkaputt\n20-19 = 3\n30-37 = 70\n1-2 = 80");
  assert.deepEqual(rows, [[19.6, 20, 47], [18.6, 19, 46]]);
  assert.deepEqual(errors, [4, 5, 6, 7]);
});

test("gaps are shown as ranges", () => {
  assert.equal(formatGaps([[0, 5.5], [17, 22]]), "0.0–5.5, 17.0–22.0");
  assert.equal(formatGaps([]), "");
  assert.equal(formatGaps(undefined), "");
});

test("Lesen table rules match the server", () => {
  const ok = Array.from({ length: 36 }, (_, i) => Math.round((i * 75) / 35));
  assert.equal(lesenTableProblems(ok), null);
  assert.match(lesenTableProblems(ok.slice(1)), /36/);
  assert.match(lesenTableProblems([...ok.slice(0, 35), 74]), /75/);
  assert.match(lesenTableProblems([10, ...ok.slice(1)]), /sinken/);
  assert.match(lesenTableProblems([...ok.slice(0, 35), 75.5]), /ganze/);
});
