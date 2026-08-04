import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type {
  ActiveUser,
  ActivityItem,
  AdminDashboardOverview,
  ChartPoint,
  PopularCourse,
  RecentCertificate,
  RecentPayment,
  RecentRegistration,
} from "../types/dashboard.types";

export async function getAdminDashboardOverview(): Promise<AdminDashboardOverview> {
  const response = await api.get<AdminDashboardOverview>(ADMIN_ENDPOINTS.adminDashboard);
  const data = response.data;

  // Every array field is rendered with a direct `.map()`/`.length` in
  // app/admin/page.tsx — guard each one here, once, rather than at every
  // call site, so a backend response that omits or nulls a field (e.g. no
  // activity yet) degrades to an empty section instead of crashing the
  // whole Dashboard Overview.
  return {
    ...data,
    revenue_chart: ensureArray<ChartPoint>(data?.revenue_chart),
    user_growth_chart: ensureArray<ChartPoint>(data?.user_growth_chart),
    popular_courses: ensureArray<PopularCourse>(data?.popular_courses),
    active_users: ensureArray<ActiveUser>(data?.active_users),
    recent_registrations: ensureArray<RecentRegistration>(data?.recent_registrations),
    recent_payments: ensureArray<RecentPayment>(data?.recent_payments),
    recent_certificates: ensureArray<RecentCertificate>(data?.recent_certificates),
    recent_activities: ensureArray<ActivityItem>(data?.recent_activities),
  };
}
