/** Minimal, reusable Telegram Mini App integration — every accessor here
 * is safe to call from any browser (Telegram or not) and never throws.
 * `initDataUnsafe` (and everything derived from it, like getTelegramUser)
 * is UI-only: convenience-parsed by the SDK itself, NOT signature-
 * verified. Real authentication must send `getTelegramInitData()`'s raw
 * string to the backend, which validates it with
 * backend/app/core/security/telegram.py's HMAC check — never trust this
 * module's parsed fields for who a user is. */

export function isTelegramWebApp(): boolean {
  return typeof window !== "undefined" && !!window.Telegram?.WebApp;
}

export function getTelegramWebApp(): TelegramWebApp | null {
  if (!isTelegramWebApp()) return null;
  return window.Telegram!.WebApp;
}

/** The raw, signed initData string — the only thing safe to send to a
 * backend for verification. Empty string outside Telegram. */
export function getTelegramInitData(): string {
  return getTelegramWebApp()?.initData ?? "";
}

/** UI-only convenience (e.g. pre-filling a display name before the
 * backend confirms it) — never treat this as authenticated identity. */
export function getTelegramUser(): TelegramWebAppUser | null {
  return getTelegramWebApp()?.initDataUnsafe?.user ?? null;
}

export function getTelegramThemeParams(): TelegramWebAppThemeParams | null {
  return getTelegramWebApp()?.themeParams ?? null;
}

export function getTelegramColorScheme(): "light" | "dark" | null {
  return getTelegramWebApp()?.colorScheme ?? null;
}

/** Idempotent — safe to call more than once (e.g. StrictMode's double
 * render-effect in development). ready()/expand() are no-ops if called
 * again, and this never touches anything outside window.Telegram.WebApp
 * when the SDK isn't present. */
export function initTelegramWebApp(): void {
  const webApp = getTelegramWebApp();
  if (!webApp) return;

  webApp.ready();
  webApp.expand();
}

// ============================================================
// Script-load synchronization
// ============================================================
//
// The SDK is loaded via next/script's strategy="afterInteractive" (see
// components/telegram/telegram-webapp-script.tsx) — it's injected once
// the page is interactive, but *executing* it (and so populating
// window.Telegram.WebApp) still finishes asynchronously, on its own
// schedule, racing against every component's mount effects. A single
// synchronous isTelegramWebApp() check made once on mount can lose that
// race (the exact production bug this fixes: auto-login's one-shot
// check ran before the script had finished loading, found nothing, and
// never checked again) — every real consumer must go through
// waitForTelegramWebApp() below instead of checking isTelegramWebApp()
// directly and giving up.

const SCRIPT_LOADED_EVENT = "telegram-webapp-script-loaded";

/** Called from the Script tag's onLoad (see
 * telegram-webapp-script.tsx) — the one authoritative "the SDK has
 * finished loading" signal. Not exported for consumers to wait on
 * directly; go through waitForTelegramWebApp(), which also covers the
 * "already loaded before you started waiting" case correctly. */
export function notifyTelegramScriptLoaded(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(SCRIPT_LOADED_EVENT));
}

/** Resolves with the WebApp object as soon as it's genuinely available:
 * immediately, if the script already finished loading before this was
 * called (e.g. a second mount, or a client-side navigation back to a
 * page that checks again) — otherwise once the script's load event
 * fires. Resolves with `null` after `timeoutMs` (default 4s) if it never
 * shows up at all — an ordinary browser tab, or a genuinely failed/
 * blocked script load — which callers should treat as "this is not a
 * Telegram launch", not as an error.
 *
 * Never rejects. Pass an AbortSignal (tied to the caller's effect
 * cleanup) to stop waiting early without leaking the listener/timer or
 * resolving into a stale/unmounted caller — this is what keeps a caller
 * safe under React Strict Mode's dev-only mount -> cleanup -> mount
 * replay (the first, aborted attempt's resolution is simply never
 * acted on). */
export function waitForTelegramWebApp(options?: {
  timeoutMs?: number;
  signal?: AbortSignal;
}): Promise<TelegramWebApp | null> {
  const existing = getTelegramWebApp();
  if (existing) return Promise.resolve(existing);

  if (typeof window === "undefined") return Promise.resolve(null);

  const timeoutMs = options?.timeoutMs ?? 4000;
  const signal = options?.signal;

  if (signal?.aborted) return Promise.resolve(null);

  return new Promise((resolve) => {
    let settled = false;

    function finish(result: TelegramWebApp | null) {
      if (settled) return;
      settled = true;
      window.removeEventListener(SCRIPT_LOADED_EVENT, onScriptLoaded);
      clearTimeout(timer);
      signal?.removeEventListener("abort", onAbort);
      resolve(result);
    }

    function onScriptLoaded() {
      // Re-check via getTelegramWebApp() rather than trusting the event
      // alone — belt-and-braces against a load event firing before the
      // global is actually assigned.
      finish(getTelegramWebApp());
    }

    function onAbort() {
      finish(null);
    }

    const timer = setTimeout(() => finish(null), timeoutMs);
    window.addEventListener(SCRIPT_LOADED_EVENT, onScriptLoaded);
    signal?.addEventListener("abort", onAbort);
  });
}
