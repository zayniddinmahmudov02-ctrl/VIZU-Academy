import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { UserDetail, UserListItem, UserListResponse } from "../types/user.types";

export async function listUsers(params: {
  page?: number;
  page_size?: number;
  search?: string;
  role?: string;
}): Promise<UserListResponse> {
  const response = await api.get<UserListResponse>(ADMIN_ENDPOINTS.adminUsers, { params });
  return { ...response.data, items: ensureArray<UserListItem>(response.data?.items) };
}

export async function getUserDetail(id: string): Promise<UserDetail> {
  const response = await api.get<UserDetail>(`${ADMIN_ENDPOINTS.adminUsers}/${id}`);
  return response.data;
}

export async function banUser(id: string, reason: string): Promise<void> {
  await api.post(`${ADMIN_ENDPOINTS.adminUsers}/${id}/ban`, { reason });
}

export async function unbanUser(id: string): Promise<void> {
  await api.post(`${ADMIN_ENDPOINTS.adminUsers}/${id}/unban`);
}

export async function suspendUser(id: string, days: number, reason: string): Promise<void> {
  await api.post(`${ADMIN_ENDPOINTS.adminUsers}/${id}/suspend`, { days, reason });
}

export async function unsuspendUser(id: string): Promise<void> {
  await api.post(`${ADMIN_ENDPOINTS.adminUsers}/${id}/unsuspend`);
}

export async function grantPremium(id: string, days: number): Promise<void> {
  await api.post(`${ADMIN_ENDPOINTS.adminUsers}/${id}/grant-premium`, { days });
}

export async function changeUserRole(id: string, role: string): Promise<void> {
  await api.patch(`${ADMIN_ENDPOINTS.adminUsers}/${id}/role`, { role });
}

export async function resetUserPassword(id: string): Promise<{ temporary_password: string }> {
  const response = await api.post<{ temporary_password: string }>(
    `${ADMIN_ENDPOINTS.adminUsers}/${id}/reset-password`,
  );
  return response.data;
}
