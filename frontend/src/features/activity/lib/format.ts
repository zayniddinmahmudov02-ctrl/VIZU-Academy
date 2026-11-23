/** Formatting of tracked times (pure, unit-tested). Times arrive in seconds from the server. */

const UNITS: Record<string, { h: string; m: string; s: string; none: string }> = {
  uz: { h: "soat", m: "daq", s: "son", none: "0 daq" },
  de: { h: "Std.", m: "Min.", s: "Sek.", none: "0 Min." },
  en: { h: "h", m: "min", s: "s", none: "0 min" },
  ru: { h: "ч", m: "мин", s: "с", none: "0 мин" },
};

/** 3725 -> "1 soat 2 daq" / "1 Std. 2 Min."; under a minute -> seconds; 0 -> "0 daq". */
export function formatDuration(seconds: number | null | undefined, language = "uz"): string {
  const u = UNITS[language] ?? UNITS.de;
  const total = Math.max(0, Math.floor(seconds ?? 0));
  if (total === 0) return u.none;
  if (total < 60) return `${total} ${u.s}`;
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  if (h === 0) return `${m} ${u.m}`;
  return m ? `${h} ${u.h} ${m} ${u.m}` : `${h} ${u.h}`;
}

/** "12:05" for seconds of a film / song position. */
export function formatClock(seconds: number | null | undefined): string {
  const total = Math.max(0, Math.floor(seconds ?? 0));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const mm = h ? String(m).padStart(2, "0") : String(m);
  return `${h ? `${h}:` : ""}${mm}:${String(s).padStart(2, "0")}`;
}

/** Percent 0..100 of a part (null when the total is unknown). */
export function percent(part: number | null | undefined, total: number | null | undefined): number | null {
  if (!total || total <= 0 || part == null) return null;
  return Math.max(0, Math.min(100, Math.round((part * 100) / total)));
}

export function formatDateTime(iso: string | null | undefined, language = "uz"): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString(language === "uz" ? "uz-UZ" : language === "ru" ? "ru-RU" : language === "en" ? "en-GB" : "de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Tashkent",
  });
}

export function formatDate(iso: string | null | undefined, language = "uz"): string {
  if (!iso) return "—";
  const d = new Date(iso.length === 10 ? `${iso}T12:00:00Z` : iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString(language === "uz" ? "uz-UZ" : language === "ru" ? "ru-RU" : language === "en" ? "en-GB" : "de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: "Asia/Tashkent",
  });
}

/** Height (0..100 %) of each day's stacked bar against the busiest day. */
export function barScale(days: { total: number }[]): number[] {
  const max = Math.max(0, ...days.map((d) => d.total));
  return days.map((d) => (max > 0 ? Math.round((d.total * 100) / max) : 0));
}
