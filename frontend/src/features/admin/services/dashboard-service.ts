import { api } from "@/src/services/api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type { AdminDashboardOverview } from "../types/dashboard.types";

export async function getAdminDashboardOverview(): Promise<AdminDashboardOverview> {
  const response = await api.get<AdminDashboardOverview>(ADMIN_ENDPOINTS.adminDashboard);
  return response.data;
}
