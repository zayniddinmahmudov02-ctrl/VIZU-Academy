import { api } from "@/src/services/api";
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UserResponse,
  VerifyAdminPasswordRequest,
} from "../types/auth.types";

export async function loginService(
  data: LoginRequest,
): Promise<TokenResponse> {

  const response = await api.post<TokenResponse>(
    "/auth/login",
    data,
  );

  return response.data;
}

// Same Token response shape as loginService — a new login METHOD, not a
// new auth system. initData is Telegram's own signed string
// (window.Telegram.WebApp.initData); the backend re-verifies it via
// HMAC-SHA256 before ever trusting anything in it (see
// backend/app/core/security/telegram.py) — nothing here sends the
// unverified initDataUnsafe.
export async function telegramLoginService(
  initData: string,
): Promise<TokenResponse> {

  const response = await api.post<TokenResponse>(
    "/auth/telegram",
    { init_data: initData },
  );

  return response.data;
}

/** Creates an active account right away (no confirmation code). The form
 * then logs in with the same credentials. */
export async function registerService(
  data: RegisterRequest,
): Promise<UserResponse> {

  const response = await api.post<UserResponse>(
    "/auth/register",
    data,
  );

  return response.data;
}

export async function verifyAdminPasswordService(
  data: VerifyAdminPasswordRequest,
): Promise<{ message: string }> {

  const response = await api.post<{ message: string }>(
    "/auth/verify-admin-password",
    data,
  );

  return response.data;
}

export async function logoutService(refreshToken: string): Promise<void> {
  await api.post("/auth/logout", { refresh_token: refreshToken });
}
