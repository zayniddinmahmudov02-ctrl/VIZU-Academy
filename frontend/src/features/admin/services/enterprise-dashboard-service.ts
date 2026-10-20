import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";
import type {
  CertificateMockAnalytics,
  DashboardActivityItem,
  DashboardChartPoint,
  DashboardCharts,
  DashboardRange,
  EnterpriseDashboardResponse,
  TrendGranularity,
} from "../types/enterprise-dashboard.types";

function normalizeCharts(charts: DashboardCharts | undefined, range: DashboardRange): DashboardCharts {
  return {
    range: charts?.range ?? range,
    granularity: charts?.granularity ?? "day",
    allowed_granularities: ensureArray<TrendGranularity>(charts?.allowed_granularities),
    revenue: ensureArray<DashboardChartPoint>(charts?.revenue),
    new_users: ensureArray<DashboardChartPoint>(charts?.new_users),
    course_purchases: ensureArray<DashboardChartPoint>(charts?.course_purchases),
    learning_progress: ensureArray<DashboardChartPoint>(charts?.learning_progress),
    totals: charts?.totals ?? null,
  };
}

/** The one optimized dashboard endpoint — every widget on the Phase 5
 * Enterprise Dashboard reads from this single response, except Trends,
 * whose filters load only GET /admin/dashboard/trends (getDashboardTrends).
 * See backend/app/api/admin/router.py. */
export async function getEnterpriseDashboard(range: DashboardRange = "30d"): Promise<EnterpriseDashboardResponse> {
  const response = await api.get<EnterpriseDashboardResponse>("/api/v1/admin/dashboard", { params: { range } });
  const data = response.data;

  return {
    ...data,
    charts: normalizeCharts(data?.charts, range),
    mock_test_analytics: ensureArray<CertificateMockAnalytics>(data?.mock_test_analytics),
    recent_activity: ensureArray<DashboardActivityItem>(data?.recent_activity),
  };
}

export async function getDashboardTrends(range: DashboardRange, granularity?: TrendGranularity): Promise<DashboardCharts> {
  const response = await api.get<DashboardCharts>("/api/v1/admin/dashboard/trends", {
    params: { range, granularity },
  });
  return normalizeCharts(response.data, range);
}
