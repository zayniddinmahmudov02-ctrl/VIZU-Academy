// Where the Global Chat button is shown (owner, 2026-11-19): ONLY on the dashboard home page of each area — the student dashboard,
// the teacher panel's start page and the admin panel's start page (staff moderate the chat from there). Every other page (courses,
// Medienwelt, Vorbereitung, lessons, admin / teacher sub-pages …) has no chat button; leaving the dashboard closes an open chat.
// Pure: unit-tested in tests/unit/chat-visibility.test.mjs.

export const CHAT_PAGES: readonly string[] = ["/dashboard", "/teacher", "/admin"];

/** True when the Global Chat button belongs on this page (a trailing slash does not matter, sub-pages do). */
export function chatVisibleOn(pathname: string | null | undefined): boolean {
  if (!pathname) return false;
  const path = pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
  return CHAT_PAGES.includes(path);
}
