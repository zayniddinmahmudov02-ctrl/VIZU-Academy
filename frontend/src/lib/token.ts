const TOKEN_KEY = "vizu_access_token";
const IMPERSONATOR_TOKEN_KEY = "vizu_impersonator_token";
const IMPERSONATING_LABEL_KEY = "vizu_impersonating_label";

export function saveToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return localStorage.getItem(TOKEN_KEY);
}

export function removeToken() {
  localStorage.removeItem(TOKEN_KEY);
}

/** Swaps the active session token for an impersonated user's token, stashing
 * the admin's original token so it can be restored via stopImpersonation(). */
export function startImpersonation(impersonationToken: string, targetLabel: string) {
  const currentToken = getToken();
  if (currentToken) {
    localStorage.setItem(IMPERSONATOR_TOKEN_KEY, currentToken);
  }
  localStorage.setItem(IMPERSONATING_LABEL_KEY, targetLabel);
  saveToken(impersonationToken);
}

export function stopImpersonation() {
  const originalToken = localStorage.getItem(IMPERSONATOR_TOKEN_KEY);
  if (originalToken) {
    saveToken(originalToken);
  } else {
    removeToken();
  }
  localStorage.removeItem(IMPERSONATOR_TOKEN_KEY);
  localStorage.removeItem(IMPERSONATING_LABEL_KEY);
}

export function isImpersonating(): boolean {
  if (typeof window === "undefined") return false;
  return Boolean(localStorage.getItem(IMPERSONATOR_TOKEN_KEY));
}

export function getImpersonatingLabel(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(IMPERSONATING_LABEL_KEY);
}