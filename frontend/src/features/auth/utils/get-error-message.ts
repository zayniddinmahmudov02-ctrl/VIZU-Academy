export function getErrorMessage(error: unknown, fallback: string): string {
  const response = (error as { response?: { data?: { message?: string; detail?: string } } })
    ?.response;
  return response?.data?.message ?? response?.data?.detail ?? fallback;
}

// The backend's fixed auth messages -> translation keys, so server errors
// follow the selected language (backend untouched).
const AUTH_ERROR_KEYS: Record<string, string> = {
  "Invalid email or password": "auth.errInvalidCredentials",
  "Email already exists.": "auth.errEmailExists",
  "Username already exists.": "auth.errUsernameExists",
  "This account has been banned.": "auth.errBanned",
  "This account is suspended.": "auth.errSuspended",
  "Incorrect administrator password.": "auth.errAdminPassword",
};

/** A translation key for a known auth error (or the fallback key); an
 * unknown server message is returned as-is. Render the result with t() —
 * t() returns plain text unchanged — so the message re-translates when the
 * language is switched. */
export function getAuthErrorKey(error: unknown, fallbackKey: string): string {
  const message = getErrorMessage(error, "");
  if (!message) return fallbackKey;
  return AUTH_ERROR_KEYS[message.trim()] ?? message;
}
