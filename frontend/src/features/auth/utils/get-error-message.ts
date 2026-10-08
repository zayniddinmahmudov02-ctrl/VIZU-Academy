/** The server's error text: `message` (our handler) or `detail` (FastAPI).
 * A request-validation error carries `detail` as a list — its messages are
 * joined, so callers always get a string. */
export function getErrorMessage(error: unknown, fallback: string): string {
  const response = (error as { response?: { data?: { message?: unknown; detail?: unknown } } })?.response;
  const value = response?.data?.message ?? response?.data?.detail;
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    const text = value
      .map((item) => (item && typeof item === "object" && "msg" in item ? String((item as { msg: unknown }).msg) : ""))
      .filter(Boolean)
      .join(" ");
    return text || fallback;
  }
  return fallback;
}

// The backend's fixed auth messages / codes -> translation keys, so server
// errors follow the selected language.
const AUTH_ERROR_KEYS: Record<string, string> = {
  "Invalid email or password": "auth.errInvalidCredentials",
  ACCOUNT_EXISTS: "auth.errAccountExists",
  "Email already exists.": "auth.errAccountExists",
  INVALID_IDENTIFIER: "auth.errIdentifierInvalid",
  PASSWORD_MISMATCH: "auth.errPasswordMismatch",
  "Username already exists.": "auth.errUsernameExists",
  "This account has been banned.": "auth.errBanned",
  "This account is suspended.": "auth.errSuspended",
  "Incorrect administrator password.": "auth.errAdminPassword",
  ADMIN_VERIFICATION_NOT_CONFIGURED: "auth.errAdminNotConfigured",
  RATE_LIMITED: "auth.errRateLimited",
};

/** A translation key for a known auth error (or the fallback key); an
 * unknown server message is returned as-is. Render the result with t() —
 * t() returns plain text unchanged — so the message re-translates when the
 * language is switched. */
export function getAuthErrorKey(error: unknown, fallbackKey: string): string {
  const message = getErrorMessage(error, "").trim();
  if (!message) return fallbackKey;
  if (AUTH_ERROR_KEYS[message]) return AUTH_ERROR_KEYS[message];
  // validation messages look like "Value error, PASSWORD_MISMATCH"
  const code = Object.keys(AUTH_ERROR_KEYS).find((k) => /^[A-Z_]+$/.test(k) && message.includes(k));
  return code ? AUTH_ERROR_KEYS[code] : message;
}
