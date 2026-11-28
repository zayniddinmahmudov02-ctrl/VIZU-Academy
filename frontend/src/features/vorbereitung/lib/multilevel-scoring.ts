/** Pure helpers for the Multilevel scoring settings in Admin (the server validates again and computes every score). */

export type SchreibenRow = [number, number, number];

const num = (v: number) => (Number.isInteger(v) ? v.toFixed(1) : String(v));

/** "35.1–36.0 = 75" per line, highest raw first — the notation of the official table. */
export function formatSchreibenTable(rows: SchreibenRow[]): string {
  return [...rows].sort((a, b) => b[0] - a[0]).map(([lo, hi, score]) => `${num(lo)}–${num(hi)} = ${score}`).join("\n");
}

/** Lines "from–to = score" (also "-" and decimal commas). Returns the rows or the numbers of the lines that are not readable. */
export function parseSchreibenTable(text: string): { rows: SchreibenRow[]; errors: number[] } {
  const rows: SchreibenRow[] = [];
  const errors: number[] = [];
  text.split(/\r?\n/).forEach((line, i) => {
    const clean = line.trim();
    if (!clean) return;
    const m = clean.replace(/,/g, ".").match(/^(\d+(?:\.\d+)?)\s*[–—-]\s*(\d+(?:\.\d+)?)\s*[=:→>]+\s*(\d+)$/);
    if (!m) {
      errors.push(i + 1);
      return;
    }
    const [lo, hi, score] = [Number(m[1]), Number(m[2]), Number(m[3])];
    if (lo > hi || hi > 36 || score > 75) errors.push(i + 1);
    else rows.push([lo, hi, score]);
  });
  return { rows, errors };
}

/** "0–5.5, 17.0–22.0" — the raw Schreiben scores the table does not convert (the Super Admin decides those sections). */
export function formatGaps(gaps: [number, number][] | undefined): string {
  return (gaps ?? []).map(([a, b]) => `${num(a)}–${num(b)}`).join(", ");
}

/** The Lesen table: 36 whole numbers 0–75, never going down, 35 correct = 75 (same rules as the server). */
export function lesenTableProblems(table: number[]): string | null {
  if (table.length !== 36) return "36 Werte nötig (0–35 richtig).";
  if (table.some((v) => !Number.isInteger(v) || v < 0 || v > 75)) return "Nur ganze Zahlen 0–75.";
  if (table.some((v, i) => i > 0 && v < table[i - 1])) return "Die Werte dürfen nicht sinken.";
  if (table[35] !== 75) return "35 richtig muss 75 sein.";
  return null;
}
