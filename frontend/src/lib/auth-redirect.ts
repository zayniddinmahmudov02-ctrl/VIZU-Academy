/** "Return to the page you wanted after logging in" — /login?next=<path>.
 *
 * Only same-site relative paths are ever accepted as `next` (no scheme, no
 * protocol-relative "//host", no backslash tricks), so the parameter can't
 * be abused as an open redirect. Auth pages themselves are never a target. */

const AUTH_PAGES = ["/login", "/register", "/forgot-password", "/reset-password"];
const MAX_NEXT_LENGTH = 2000;

export function safeNextPath(raw: string | null | undefined): string | null {
  if (!raw || raw.length > MAX_NEXT_LENGTH) return null;
  let path: string;
  try {
    path = decodeURIComponent(raw);
  } catch {
    return null;
  }
  if (!path.startsWith("/") || path.startsWith("//") || path.includes("\\")) return null;
  if (/[\u0000-\u001f]/.test(path)) return null;
  // must stay on this origin once resolved
  try {
    const url = new URL(path, "http://same.origin");
    if (url.origin !== "http://same.origin") return null;
    if (AUTH_PAGES.some((p) => url.pathname === p || url.pathname.startsWith(p + "/"))) return null;
    return url.pathname + url.search + url.hash;
  } catch {
    return null;
  }
}

/** The page the visitor is on right now (path + query + hash). */
export function currentPath(): string {
  if (typeof window === "undefined") return "/";
  const { pathname, search, hash } = window.location;
  return pathname + search + hash;
}

/** /login, carrying the given (or current) page as `next` when it's useful. */
export function loginUrl(next: string = currentPath()): string {
  const safe = safeNextPath(next);
  return safe && safe !== "/" ? `/login?next=${encodeURIComponent(safe)}` : "/login";
}

/** The validated `next` of the current URL, or null. */
export function readNextParam(): string | null {
  if (typeof window === "undefined") return null;
  return safeNextPath(new URLSearchParams(window.location.search).get("next"));
}
