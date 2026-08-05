import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";
import type {
  CertificateMockAnalytics,
  DashboardActivityItem,
  DashboardChartPoint,
  DashboardRange,
  EnterpriseDashboardResponse,
} from "../types/enterprise-dashboard.types";

/** The one optimized dashboard endpoint — every widget on the Phase 5
 * Enterprise Dashboard reads from this single response, never its own
 * request. See backend/app/api/admin/router.py's `GET /admin/dashboard`. */
export async function getEnterpriseDashboard(range: DashboardRange): Promise<EnterpriseDashboardResponse> {
  const response = await api.get<EnterpriseDashboardResponse>("/api/v1/admin/dashboard", { params: { range } });
  const data = response.data;

  return {
    ...data,
    charts: {
      ...data.charts,
      revenue: ensureArray<DashboardChartPoint>(data?.charts?.revenue),
      new_users: ensureArray<DashboardChartPoint>(data?.charts?.new_users),
      learning_progress: ensureArray<DashboardChartPoint>(data?.charts?.learning_progress),
    },
    mock_test_analytics: ensureArray<CertificateMockAnalytics>(data?.mock_test_analytics),
    recent_activity: ensureArray<DashboardActivityItem>(data?.recent_activity),
  };
}
