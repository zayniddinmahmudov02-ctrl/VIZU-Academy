/** Pure helpers of the student statistics card (unit tested in tests/unit/student-stats.test.mjs). */

/** 1250 -> "1 250", 125000 -> "125 000" (non-breaking spaces, so a number never wraps). Not a number -> "—". */
export function formatCount(value: number | null | undefined): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "—";
  const sign = value < 0 ? "-" : "";
  return sign + String(Math.trunc(Math.abs(value))).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

/** Share in whole percent, "—" without a base. */
export function percentOf(part: number, whole: number): string {
  if (!whole || whole <= 0) return "—";
  return `${Math.round((part / whole) * 100)} %`;
}
