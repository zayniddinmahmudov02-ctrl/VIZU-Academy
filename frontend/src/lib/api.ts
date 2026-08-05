import { API_URL } from "@/constants/api";
import {
  getRefreshToken,
  getToken,
  isRemembered,
  removeRefreshToken,
  removeToken,
  saveRefreshToken,
  saveToken,
} from "@/src/lib/token";

function redirectToLogin() {
  removeToken();
  removeRefreshToken();
  if (typeof window !== "undefined" && window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}

// Shared across concurrent 401s so only one refresh call is ever in flight
// at a time — mirrors the same guard in services/api.ts.
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();

  if (!refreshToken) {
    return null;
  }

  if (!refreshPromise) {
    refreshPromise = fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
      .then(async (response) => {
        if (!response.ok) return null;
        const data = await response.json();
        const remember = isRemembered();
        saveToken(data.access_token, remember);
        saveRefreshToken(data.refresh_token, remember);
        return data.access_token as string;
      })
      .catch(() => null)
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

const AUTH_ENDPOINTS = ["/auth/login", "/auth/register", "/auth/refresh"];

function isAuthEndpoint(endpoint: string): boolean {
  return AUTH_ENDPOINTS.some((path) => endpoint.includes(path));
}

// See the matching guard in services/api.ts — /users/me 401s are a normal
// "nobody's logged in" outcome, not a session-expired event, so a failed
// refresh here must not force a hard redirect (the caller already handles
// it via a clean client-side navigation).
const SILENT_REDIRECT_ENDPOINTS = ["/users/me"];

function isSilentRedirectEndpoint(endpoint: string): boolean {
  return SILENT_REDIRECT_ENDPOINTS.some((path) => endpoint.includes(path));
}

export async function api<T>(
  endpoint: string,
  options?: RequestInit,
  _retried = false,
): Promise<T> {

  const token = getToken();

  const response = await fetch(
    `${API_URL}${endpoint}`,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options?.headers ?? {}),
      },
    },
  );

  if (response.status === 401 && !_retried && !isAuthEndpoint(endpoint)) {
    const newAccessToken = await refreshAccessToken();

    if (newAccessToken) {
      return api<T>(endpoint, options, true);
    }

    if (!isSilentRedirectEndpoint(endpoint)) {
      redirectToLogin();
    }
  }

  if (!response.ok) {
    throw new Error(
      `API Error: ${response.status}`,
    );
  }

  return response.json();

}
