/** Pure helpers for the Battle UI (unit-tested in tests/unit/battle-utils.test.mjs). */

export const BATTLE_COLORS = {
  navy: "#101D35",
  darkBlue: "#172A46",
  blue: "#3984E8",
  gold: "#F2C45B",
  red: "#D83B43",
  light: "#F4F6FA",
} as const;

/**
 * Theme image reference → URL. "static:/battle/themes/x.webp" is shipped with the frontend,
 * "asset:<name>.webp" is an admin upload served by the API. Anything else is ignored (null).
 */
export function resolveThemeImage(ref: string | null | undefined, apiUrl: string): string | null {
  if (!ref) return null;
  if (/^static:\/battle\/themes\/[a-z0-9][a-z0-9_-]*\.(webp|jpg|avif)$/.test(ref)) return ref.slice("static:".length);
  const m = /^asset:([0-9a-f]{32}\.webp)$/.exec(ref);
  if (m) return `${apiUrl.replace(/\/$/, "")}/api/v1/battle/themes/assets/${m[1]}`;
  return null;
}

/** Absolute URL for an API-relative path such as the round picture ("/api/v1/battle/media/…"). */
export function apiAsset(path: string, apiUrl: string): string {
  return path.startsWith("/") ? `${apiUrl.replace(/\/$/, "")}${path}` : path;
}

/** Offset (ms) to add to Date.now() to get the server's clock. */
export function clockOffset(serverIso: string, receivedAt: number, roundTripMs = 0): number {
  const server = Date.parse(serverIso);
  return Number.isFinite(server) ? server + roundTripMs / 2 - receivedAt : 0;
}

/** Milliseconds left until `iso`, measured on the server's clock; never negative. */
export function msUntil(iso: string | null | undefined, offsetMs: number, now = Date.now()): number {
  if (!iso) return 0;
  const t = Date.parse(iso);
  return Number.isFinite(t) ? Math.max(0, t - (now + offsetMs)) : 0;
}

export type OptionState = "idle" | "selected" | "correct" | "wrong" | "missed" | "dimmed";

/** Visual state of one answer option. */
export function optionState(index: number, phase: "question" | "reveal", myChoice: number | null | undefined, correct: number | null | undefined): OptionState {
  const chosen = myChoice !== null && myChoice !== undefined;
  if (phase === "question") {
    if (!chosen) return "idle";
    return index === myChoice ? "selected" : "dimmed";
  }
  if (index === correct) return chosen && myChoice === correct ? "correct" : "missed";
  if (chosen && index === myChoice) return "wrong";
  return "dimmed";
}

export function winRate(rate: number): string {
  return `${Math.round(rate * 100)}%`;
}

/** Polling interval for a match: fast while a round runs, slower in the lobby or when finished. */
export function pollInterval(status: string | undefined, hidden: boolean): number | false {
  if (status === "finished" || status === "cancelled") return false;
  if (hidden) return 4000;
  return status === "active" ? 700 : 1500;
}
