const TOKEN_KEY = "vizu_access_token";
const REFRESH_TOKEN_KEY = "vizu_refresh_token";

function primaryStorage(remember: boolean): Storage {
  return remember ? localStorage : sessionStorage;
}

function secondaryStorage(remember: boolean): Storage {
  return remember ? sessionStorage : localStorage;
}

export function saveToken(token: string, remember: boolean = true) {
  if (typeof window === "undefined") return;
  primaryStorage(remember).setItem(TOKEN_KEY, token);
  secondaryStorage(remember).removeItem(TOKEN_KEY);
}

export function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return localStorage.getItem(TOKEN_KEY) ?? sessionStorage.getItem(TOKEN_KEY);
}

export function removeToken() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
}

export function saveRefreshToken(token: string, remember: boolean = true) {
  if (typeof window === "undefined") return;
  primaryStorage(remember).setItem(REFRESH_TOKEN_KEY, token);
  secondaryStorage(remember).removeItem(REFRESH_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return (
    localStorage.getItem(REFRESH_TOKEN_KEY) ??
    sessionStorage.getItem(REFRESH_TOKEN_KEY)
  );
}

export function removeRefreshToken() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}

/** Whether the current session was stored under "remember me" (localStorage,
 * survives browser restarts) rather than sessionStorage. Used so a silent
 * token refresh writes the new pair back to the same storage it came from. */
export function isRemembered(): boolean {
  if (typeof window === "undefined") return true;
  return localStorage.getItem(TOKEN_KEY) !== null;
}
