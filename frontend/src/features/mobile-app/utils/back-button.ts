/** What the Android back button does inside the app (pure, unit-tested). Order: an open dialog / drawer closes first,
 * then the page goes back in its history, a page opened without history goes to its panel's start page, and on a start
 * page a first press only shows a hint — the app closes on a second press within EXIT_WINDOW_MS. */

export type BackDecision = "close-dialog" | "history-back" | "home" | "exit-hint" | "exit";

export const EXIT_WINDOW_MS = 2000;
const START_PAGES = new Set(["/", "/dashboard", "/teacher", "/admin", "/login"]);

export function isStartPage(path: string): boolean {
  const clean = path.split(/[?#]/)[0].replace(/\/+$/, "") || "/";
  return START_PAGES.has(clean);
}

/** The start page of the panel a path belongs to. */
export function homeOf(path: string): string {
  if (path.startsWith("/teacher")) return "/teacher";
  if (path.startsWith("/admin")) return "/admin";
  return "/dashboard";
}

export function decideBack(input: { dialogOpen: boolean; path: string; canGoBack: boolean; now: number; lastHintAt: number | null }): BackDecision {
  if (input.dialogOpen) return "close-dialog";
  if (isStartPage(input.path)) {
    return input.lastHintAt !== null && input.now - input.lastHintAt <= EXIT_WINDOW_MS ? "exit" : "exit-hint";
  }
  return input.canGoBack ? "history-back" : "home";
}
