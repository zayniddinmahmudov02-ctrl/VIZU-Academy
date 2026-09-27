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
