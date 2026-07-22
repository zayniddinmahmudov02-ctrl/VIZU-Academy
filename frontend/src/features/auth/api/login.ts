import { api } from "@/src/services/api";
import type {
  LoginRequest,
  TokenResponse,
} from "../types/auth.types";

export async function login(
  data: LoginRequest
): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>(
    "/auth/login",
    data
  );

  return response.data;
}