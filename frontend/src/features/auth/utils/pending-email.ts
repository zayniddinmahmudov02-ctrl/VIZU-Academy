/** The address waiting for confirmation, kept for this browser tab only
 * (sessionStorage) so it never appears in a URL. Codes are never stored. */
const KEY = "vizu-pending-verification-email";
const NOTICE_KEY = "vizu-auth-notice";

export type AuthNotice = "verified" | "password-reset";

function store(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.sessionStorage;
  } catch {
    return null;
  }
}

const SEND_FAILED_KEY = "vizu-pending-verification-send-failed";

export function setPendingEmail(email: string, sendFailed = false): void {
  store()?.setItem(KEY, email);
  if (sendFailed) store()?.setItem(SEND_FAILED_KEY, "1");
  else store()?.removeItem(SEND_FAILED_KEY);
}

/** True if the registration e-mail could not be sent (cleared by a resend
 * or a successful verification). */
export function getPendingSendFailed(): boolean {
  return store()?.getItem(SEND_FAILED_KEY) === "1";
}

export function getPendingEmail(): string | null {
  return store()?.getItem(KEY) ?? null;
}

export function clearPendingEmail(): void {
  store()?.removeItem(KEY);
  store()?.removeItem(SEND_FAILED_KEY);
}

/** One-shot success message for the login page. */
export function setAuthNotice(notice: AuthNotice): void {
  store()?.setItem(NOTICE_KEY, notice);
}

/** Read without removing: the login page may mount more than once during a
 * client navigation; the notice is cleared on the next login attempt. */
export function peekAuthNotice(): AuthNotice | null {
  const value = store()?.getItem(NOTICE_KEY) ?? null;
  return value === "verified" || value === "password-reset" ? value : null;
}

export function clearAuthNotice(): void {
  store()?.removeItem(NOTICE_KEY);
}

/** "a***@example.com" — enough to recognise, not to read off a screen. */
export function maskEmail(email: string): string {
  const [local, domain] = email.split("@");
  if (!domain) return email;
  const visible = local.slice(0, Math.min(2, Math.max(1, local.length - 1)));
  return `${visible}${"*".repeat(Math.max(3, local.length - visible.length))}@${domain}`;
}
