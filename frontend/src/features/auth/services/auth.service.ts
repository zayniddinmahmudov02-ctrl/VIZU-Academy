import { api } from "@/src/services/api";
import type {
  ForgotPasswordRequest,
  LoginRequest,
  RegisterRequest,
  ResetPasswordRequest,
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

export async function registerService(
  data: RegisterRequest,
): Promise<UserResponse> {

  const response = await api.post<UserResponse>(
    "/auth/register",
    data,
  );

  return response.data;
}

export async function forgotPasswordService(
  data: ForgotPasswordRequest,
): Promise<{ message: string }> {

  const response = await api.post<{ message: string }>(
    "/auth/forgot-password",
    data,
  );

  return response.data;
}

export async function resetPasswordService(
  data: ResetPasswordRequest,
): Promise<{ message: string }> {

  const response = await api.post<{ message: string }>(
    "/auth/reset-password",
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
