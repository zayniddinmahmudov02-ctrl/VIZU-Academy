import type { Crop } from "@/features/profile/utils/photo-crop";
import { api } from "@/services/api";

import {
  mapCurrentUser,
  type CurrentUserPayload,
} from "@/features/auth/services/user-service";
import type { CurrentUser } from "@/features/auth/types/user";

export interface UpdateProfileInput {
  firstName?: string;
  lastName?: string;
  phoneNumber?: string;
  country?: string;
}

export async function updateProfile(input: UpdateProfileInput): Promise<CurrentUser> {
  const response = await api.put<CurrentUserPayload>("/api/v1/users/me", {
    first_name: input.firstName,
    last_name: input.lastName,
    phone_number: input.phoneNumber,
    country: input.country,
  });

  return mapCurrentUser(response.data);
}

export interface ChangePasswordInput {
  currentPassword: string;
  newPassword: string;
}

export async function changePassword(input: ChangePasswordInput): Promise<{ message: string }> {
  const response = await api.put<{ message: string }>("/api/v1/users/me/password", {
    current_password: input.currentPassword,
    new_password: input.newPassword,
  });

  return response.data;
}

export async function updateLanguage(language: "de" | "uz"): Promise<CurrentUser> {
  const response = await api.put<CurrentUserPayload>("/api/v1/users/me/language", {
    language,
  });

  return mapCurrentUser(response.data);
}

/** The server re-encodes the photo; crop = square in fractions (see features/profile/utils/photo-crop.ts). */
export async function uploadProfilePhoto({ file, crop }: { file: File; crop?: Crop | null }): Promise<CurrentUser> {
  const formData = new FormData();
  formData.append("file", file);
  if (crop) {
    formData.append("crop_x", String(crop.x));
    formData.append("crop_y", String(crop.y));
    formData.append("crop_size", String(crop.size));
  }

  const response = await api.post<CurrentUserPayload>("/api/v1/users/me/photo", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return mapCurrentUser(response.data);
}

export async function removeProfilePhoto(): Promise<CurrentUser> {
  const response = await api.delete<CurrentUserPayload>("/api/v1/users/me/photo");
  return mapCurrentUser(response.data);
}
