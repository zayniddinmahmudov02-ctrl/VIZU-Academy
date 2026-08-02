/** Decodes a JWT payload without verifying its signature — safe only for
 * UI-routing decisions (e.g. "which screen to show next"), never for
 * security checks. The backend re-verifies every token on every request;
 * nothing here is a substitute for that. */
export function decodeJwtPayload<T = Record<string, unknown>>(
  token: string,
): T | null {
  try {
    const base64Url = token.split(".")[1];
    if (!base64Url) return null;

    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const json = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + c.charCodeAt(0).toString(16).padStart(2, "0"))
        .join(""),
    );

    return JSON.parse(json) as T;
  } catch {
    return null;
  }
}
