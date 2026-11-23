const TOKEN_KEY = "vizu_access_token";
const REFRESH_TOKEN_KEY = "vizu_refresh_token";

/* ── Android app: the session lives in the app's Keystore-encrypted storage ─────────────────────────────────────────
 * The installed app (mobile/, SecureSessionPlugin) hands the session to the page before any script runs, as
 * window.__VIZU_SESSION__ (only for this site's own origin), and keeps it in sync through the VizuSession plugin.
 * Then the tokens are never written to localStorage / sessionStorage. A browser (or an old app WebView without
 * document-start scripts) keeps using the normal storages below. */

interface NativeSession {
  access: string | null;
  refresh: string | null;
  remember: boolean;
}

interface SessionPlugin {
  set: (session: NativeSession) => Promise<unknown>;
}

type NativeWindow = Window & {
  __VIZU_SESSION__?: { access?: string | null; refresh?: string | null; remember?: boolean };
  Capacitor?: { isNativePlatform?: () => boolean; Plugins?: { VizuSession?: SessionPlugin } };
};

let native: NativeSession | null | undefined; // undefined = not decided yet, null = browser storage

function sessionPlugin(): SessionPlugin | null {
  const cap = (window as NativeWindow).Capacitor;
  return cap?.isNativePlatform?.() ? cap.Plugins?.VizuSession ?? null : null;
}

function nativeSession(): NativeSession | null {
  if (native !== undefined) return native;
  const injected = (window as NativeWindow).__VIZU_SESSION__;
  if (!injected || !sessionPlugin()) {
    native = null;
    return native;
  }
  native = { access: injected.access ?? null, refresh: injected.refresh ?? null, remember: injected.remember !== false };
  // an older app version kept the tokens in the WebView storage: move them once, then remove every plain copy
  const oldAccess = localStorage.getItem(TOKEN_KEY) ?? sessionStorage.getItem(TOKEN_KEY);
  const oldRefresh = localStorage.getItem(REFRESH_TOKEN_KEY) ?? sessionStorage.getItem(REFRESH_TOKEN_KEY);
  if (!native.access && !native.refresh && (oldAccess || oldRefresh)) {
    native = { access: oldAccess, refresh: oldRefresh, remember: localStorage.getItem(REFRESH_TOKEN_KEY) !== null };
    pushNative();
  }
  for (const storage of [localStorage, sessionStorage]) {
    storage.removeItem(TOKEN_KEY);
    storage.removeItem(REFRESH_TOKEN_KEY);
  }
  return native;
}

function pushNative() {
  const plugin = sessionPlugin();
  if (plugin && native) void plugin.set({ ...native }).catch(() => undefined);
}

/** Whether the login session is kept by the Android app (encrypted) instead of the browser storage. */
export function usesNativeSession(): boolean {
  return typeof window !== "undefined" && nativeSession() !== null;
}

/* ── browser storage ──────────────────────────────────────────────────────────────────────────────────────────────── */

function primaryStorage(remember: boolean): Storage {
  return remember ? localStorage : sessionStorage;
}

function secondaryStorage(remember: boolean): Storage {
  return remember ? sessionStorage : localStorage;
}

export function saveToken(token: string, remember: boolean = true) {
  if (typeof window === "undefined") return;
  const n = nativeSession();
  if (n) {
    n.access = token;
    n.remember = remember;
    pushNative();
    return;
  }
  primaryStorage(remember).setItem(TOKEN_KEY, token);
  secondaryStorage(remember).removeItem(TOKEN_KEY);
}

export function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const n = nativeSession();
  if (n) return n.access;

  return localStorage.getItem(TOKEN_KEY) ?? sessionStorage.getItem(TOKEN_KEY);
}

export function removeToken() {
  if (typeof window === "undefined") return;
  const n = nativeSession();
  if (n) {
    n.access = null;
    pushNative();
  } else {
    localStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
  }
  clearRuntimeCache();
}

/** Tells the service worker (see public/sw.js) to drop its runtime
 * cache — the one holding network-first lesson/progress/user-data
 * responses — on every logout (explicit or forced by a 401), so the
 * next user on this device never sees a previous student's cached
 * data. The static-asset cache is untouched; nothing sensitive lives
 * there. No-ops silently if service workers aren't supported/active. */
function clearRuntimeCache() {
  if (!("serviceWorker" in navigator)) return;
  navigator.serviceWorker.ready
    .then((registration) => {
      registration.active?.postMessage({ type: "CLEAR_RUNTIME_CACHE" });
    })
    .catch(() => {});
}

export function saveRefreshToken(token: string, remember: boolean = true) {
  if (typeof window === "undefined") return;
  const n = nativeSession();
  if (n) {
    n.refresh = token;
    n.remember = remember;
    pushNative();
    return;
  }
  primaryStorage(remember).setItem(REFRESH_TOKEN_KEY, token);
  secondaryStorage(remember).removeItem(REFRESH_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const n = nativeSession();
  if (n) return n.refresh;

  return (
    localStorage.getItem(REFRESH_TOKEN_KEY) ??
    sessionStorage.getItem(REFRESH_TOKEN_KEY)
  );
}

export function removeRefreshToken() {
  if (typeof window === "undefined") return;
  const n = nativeSession();
  if (n) {
    n.refresh = null;
    pushNative();
    return;
  }
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}

/** Whether the current session was stored under "remember me" (localStorage,
 * survives browser restarts) rather than sessionStorage. Used so a silent
 * token refresh writes the new pair back to the same storage it came from.
 * In the Android app: whether the app keeps the session after a restart. */
export function isRemembered(): boolean {
  if (typeof window === "undefined") return true;
  const n = nativeSession();
  if (n) return n.remember;
  return localStorage.getItem(TOKEN_KEY) !== null;
}
