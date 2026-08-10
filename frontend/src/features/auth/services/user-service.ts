import { api } from "@/services/api";

import type { CurrentUser } from "../types/user";

export interface CurrentUserPayload {
  id: string;
  email: string;
  username: string;
  first_name: string | null;
  last_name: string | null;
  phone_number: string | null;
  country: string | null;
  profile_image: string | null;
  preferred_language: string;
  is_active: boolean;
  is_verified: boolean;
  is_banned: boolean;
  suspended_until: string | null;
  role: string;
  created_at: string;
}

export function mapCurrentUser(data: CurrentUserPayload): CurrentUser {
  return {
    id: data.id,
    email: data.email,
    username: data.username,
    firstName: data.first_name,
    lastName: data.last_name,
    phoneNumber: data.phone_number,
    country: data.country,
    profileImage: data.profile_image,
    preferredLanguage: data.preferred_language,
    isActive: data.is_active,
    isVerified: data.is_verified,
    isBanned: data.is_banned,
    suspendedUntil: data.suspended_until,
    role: data.role,
    createdAt: data.created_at,
  };
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await api.get<CurrentUserPayload>("/api/v1/users/me");
  return mapCurrentUser(response.data);
}
