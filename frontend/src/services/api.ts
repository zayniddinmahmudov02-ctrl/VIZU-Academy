import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

import { API_URL } from "@/src/constants/api";
import {
  getRefreshToken,
  getToken,
  isRemembered,
  removeRefreshToken,
  removeToken,
  saveRefreshToken,
  saveToken,
} from "@/src/lib/token";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = getToken();

  const language =
    typeof window !== "undefined"
      ? localStorage.getItem("vizu-language")
      : "de";

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  config.headers["X-Language"] = language ?? "de";

  return config;
});

// Endpoints where a 401 means "these credentials/tokens were wrong," not
// "the session expired" — attempting a refresh or redirecting would be
// wrong here; the caller's own error handling takes over instead.
const AUTH_ENDPOINTS = ["/auth/login", "/auth/register", "/auth/refresh"];

function isAuthEndpoint(url?: string): boolean {
  if (!url) return false;
  return AUTH_ENDPOINTS.some((endpoint) => url.includes(endpoint));
}

function redirectToLogin() {
  removeToken();
  removeRefreshToken();
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

// Multiple requests can 401 at nearly the same moment (e.g. a page firing
// several queries at once) — this makes sure they all wait on one shared
// refresh call instead of each racing to redeem the same refresh token.
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();

  if (!refreshToken) {
    return null;
  }

  if (!refreshPromise) {
    refreshPromise = axios
      .post<{ access_token: string; refresh_token: string }>(
        `${API_URL}/auth/refresh`,
        { refresh_token: refreshToken },
      )
      .then((response) => {
        const remember = isRemembered();
        saveToken(response.data.access_token, remember);
        saveRefreshToken(response.data.refresh_token, remember);
        return response.data.access_token;
      })
      .catch(() => null)
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as
      | (InternalAxiosRequestConfig & { _retried?: boolean })
      | undefined;

    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retried ||
      isAuthEndpoint(originalRequest.url)
    ) {
      return Promise.reject(error);
    }

    originalRequest._retried = true;

    const newAccessToken = await refreshAccessToken();

    if (!newAccessToken) {
      redirectToLogin();
      return Promise.reject(error);
    }

    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
    return api(originalRequest);
  },
);
