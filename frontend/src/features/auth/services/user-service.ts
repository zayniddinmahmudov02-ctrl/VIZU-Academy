import { api } from "@/services/api";

import type { CurrentUser } from "../types/user";

interface CurrentUserPayload {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_verified: boolean;
  role: string;
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await api.get<CurrentUserPayload>("/api/v1/users/me");
  const data = response.data;

  return {
    id: data.id,
    email: data.email,
    username: data.username,
    isActive: data.is_active,
    isVerified: data.is_verified,
    role: data.role,
  };
}
