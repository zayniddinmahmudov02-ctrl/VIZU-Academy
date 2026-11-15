/* Pure helpers of the film player's subtitles (no React, no project imports: unit-tested with node --test). */

/** [start_ms, end_ms, plain text] — the form the backend sends (`GET /medien/subtitles/{id}/cues`). */
export type Cue = [number, number, string];

export type SubtitleSize = "small" | "medium" | "large";
export type SubtitlePosition = "bottom" | "higher";
export type SubtitleFont = "sans" | "serif" | "mono";

export interface SubtitlePrefs {
  enabled: boolean;
  size: SubtitleSize;
  color: string;
  bg_opacity: number;
  position: SubtitlePosition;
  font: SubtitleFont;
  dual: boolean;
  secondary: string;
}

export interface PlayerState {
  subtitle?: string;
  dual?: boolean;
  secondary?: string;
  speed?: number;
  quality?: string;
  audio?: string;
}

export const LANGUAGE_NAMES: Record<string, string> = { de: "Deutsch", uz: "O'zbekcha", en: "English", ru: "Русский" };
/** The order the subtitle languages are offered in: Deutsch, Uzbek, English (then anything else). */
const LANGUAGE_ORDER = ["de", "uz", "en", "ru"];
export function sortByLanguage<T extends { language: string }>(items: readonly T[]): T[] {
  const rank = (l: string) => { const i = LANGUAGE_ORDER.indexOf(l); return i < 0 ? LANGUAGE_ORDER.length : i; };
  return [...items].sort((a, b) => rank(a.language) - rank(b.language) || a.language.localeCompare(b.language));
}
export const SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 2];
export const COLORS = ["#ffffff", "#ffe066", "#7dd3fc", "#86efac", "#f9a8d4"];
export const SIZES: SubtitleSize[] = ["small", "medium", "large"];
export const FONTS: SubtitleFont[] = ["sans", "serif", "mono"];

export const DEFAULT_PREFS: SubtitlePrefs = { enabled: true, size: "medium", color: "#ffffff", bg_opacity: 75, position: "bottom", font: "sans", dual: false, secondary: "uz" };

/** The student's settings with every missing / invalid value replaced by the default. */
export function normalizePrefs(raw: Partial<SubtitlePrefs> | null | undefined): SubtitlePrefs {
  const r = raw ?? {};
  return {
    enabled: typeof r.enabled === "boolean" ? r.enabled : DEFAULT_PREFS.enabled,
    size: SIZES.includes(r.size as SubtitleSize) ? (r.size as SubtitleSize) : DEFAULT_PREFS.size,
    color: COLORS.includes(r.color as string) ? (r.color as string) : DEFAULT_PREFS.color,
    bg_opacity: typeof r.bg_opacity === "number" && r.bg_opacity >= 0 && r.bg_opacity <= 100 ? Math.round(r.bg_opacity) : DEFAULT_PREFS.bg_opacity,
    position: r.position === "higher" ? "higher" : "bottom",
    font: FONTS.includes(r.font as SubtitleFont) ? (r.font as SubtitleFont) : DEFAULT_PREFS.font,
    dual: typeof r.dual === "boolean" ? r.dual : DEFAULT_PREFS.dual,
    secondary: typeof r.secondary === "string" && r.secondary in LANGUAGE_NAMES ? r.secondary : DEFAULT_PREFS.secondary,
  };
}

/** The cues shown at `ms` (usually one; overlapping cues all stay visible). `cues` must be sorted by start (the server sorts them). */
export function activeCues(cues: readonly Cue[], ms: number): Cue[] {
  let lo = 0;
  let hi = cues.length - 1;
  let idx = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (cues[mid][0] <= ms) { idx = mid; lo = mid + 1; } else hi = mid - 1;
  }
  const out: Cue[] = [];
  for (let i = idx; i >= 0 && i > idx - 8; i -= 1) if (cues[i][1] > ms) out.unshift(cues[i]);
  return out;
}

/** Identity of the shown cue set — the overlay only re-renders when it changes. */
export const cueKey = (active: readonly Cue[]): string => active.map((c) => c[0]).join(",");

const EDGE = /^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu;

/** A clicked token without surrounding punctuation / quotes ("Welt!" -> "Welt", "„Hallo“" -> "Hallo"); keeps inner apostrophes and hyphens. */
export function cleanWord(raw: string): string {
  return raw.replace(/[‘’]/g, "'").replace(EDGE, "").trim();
}

export interface Token { text: string; word: string | null }

/** One subtitle line as tokens: words (clickable) and the spaces between them. */
export function tokenize(line: string): Token[] {
  return line.split(/(\s+)/).filter((p) => p !== "").map((p) => {
    if (/^\s+$/.test(p)) return { text: p, word: null };
    const word = cleanWord(p);
    return { text: p, word: /[\p{L}\p{N}]/u.test(word) ? word : null };
  });
}

/** The subtitle language that starts: the one used last on this film, else the student's default ("de" if the film has it). */
export function initialSubtitle(available: readonly string[], state: PlayerState | null | undefined, prefs: SubtitlePrefs): string {
  if (state?.subtitle === "off") return "off";
  if (state?.subtitle && available.includes(state.subtitle)) return state.subtitle;
  if (!prefs.enabled || !available.length) return "off";
  return available.includes("de") ? "de" : available[0];
}

/** The second language of the dual view: the wanted one when it exists and differs from the first, else a sensible other one. */
export function pickSecondary(available: readonly string[], primary: string, wanted: string | undefined): string | null {
  const others = available.filter((l) => l !== primary);
  if (wanted && others.includes(wanted)) return wanted;
  for (const l of ["uz", "en", "ru", "de"]) if (others.includes(l)) return l;
  return null;
}

/** The lines shown, top to bottom: German always on top when it is one of the two; a single line when dual is off or impossible. */
export function subtitleLines(available: readonly string[], primary: string, dual: boolean, secondary: string | undefined): string[] {
  if (primary === "off" || !available.includes(primary)) return [];
  if (!dual) return [primary];
  const second = pickSecondary(available, primary, secondary);
  if (!second) return [primary];
  const pair = [primary, second];
  return pair.includes("de") ? ["de", pair.find((l) => l !== "de")!] : pair;
}

const FONT_FAMILY: Record<SubtitleFont, string> = {
  sans: 'ui-sans-serif, system-ui, "Segoe UI", Roboto, sans-serif',
  serif: 'Georgia, "Times New Roman", serif',
  mono: 'ui-monospace, "Cascadia Mono", Menlo, Consolas, monospace',
};
const FONT_SIZE: Record<SubtitleSize, string> = { small: "clamp(12px, 1.7vw, 18px)", medium: "clamp(14px, 2.2vw, 24px)", large: "clamp(17px, 3vw, 34px)" };

/** Inline CSS of the subtitle block for the student's settings. `barHeight`: the measured height (px) of the control bar while it is shown
 * (0 when it is hidden) — the text always sits above it, also on a phone where the bar has two rows. */
export function subtitleStyle(prefs: SubtitlePrefs, barHeight: number) {
  const lift = prefs.position === "higher" ? 3.5 : 0;
  const bottom = barHeight > 0 ? `calc(${Math.round(barHeight)}px + ${0.75 + lift}rem)` : `${1.25 + lift}rem`;
  return {
    block: { bottom, fontFamily: FONT_FAMILY[prefs.font], fontSize: FONT_SIZE[prefs.size], color: prefs.color },
    line: { backgroundColor: `rgba(0, 0, 0, ${prefs.bg_opacity / 100})` },
  };
}

/** What "continue watching" stores for a film. */
export function stateOf(v: { subtitle: string; dual: boolean; secondary: string | null; speed: number; quality: string | null }): PlayerState {
  const out: PlayerState = { subtitle: v.subtitle, dual: v.dual, speed: v.speed };
  if (v.secondary) out.secondary = v.secondary;
  if (v.quality) out.quality = v.quality;
  return out;
}

export function clamp(n: number, low: number, high: number): number {
  return Math.min(Math.max(n, low), high);
}
