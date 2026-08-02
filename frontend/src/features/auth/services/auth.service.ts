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
