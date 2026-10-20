"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, RefreshCw } from "lucide-react";

import { AdminButton, AdminCard, AdminPageHeader } from "@/components/admin/admin-ui";
import DashboardActivityHealth, {
  ActivityHealthSkeleton,
} from "@/features/admin/components/dashboard/dashboard-activity-health";
import DashboardCharts, { DashboardChartsSkeleton } from "@/features/admin/components/dashboard/dashboard-charts";
import DashboardKpiCards, { KpiCardsSkeleton } from "@/features/admin/components/dashboard/dashboard-kpis";
import DashboardLearningAnalytics, {
  LearningAnalyticsSkeleton,
} from "@/features/admin/components/dashboard/dashboard-learning-analytics";
import DashboardMockTestAnalytics, {
  MockTestAnalyticsSkeleton,
} from "@/features/admin/components/dashboard/dashboard-mock-test-analytics";
import DashboardOperations, { OperationsSkeleton } from "@/features/admin/components/dashboard/dashboard-operations";
import DashboardQuickActions from "@/features/admin/components/dashboard/dashboard-quick-actions";
import DashboardVizuMultilevel from "@/features/admin/components/dashboard/dashboard-vizu-multilevel";
import { getEnterpriseDashboard } from "@/features/admin/services/enterprise-dashboard-service";

export default function AdminDashboardPage() {
  const queryClient = useQueryClient();
  // Trends has its own filters + endpoint; this payload always carries the 30-day view
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["admin-enterprise-dashboard"],
    queryFn: () => getEnterpriseDashboard("30d"),
    // KPIs/charts/activity change with real usage, not every second —
    // avoid re-fetching the one big payload on every tab focus.
    staleTime: 60 * 1000,
  });

  return (
    <div>
      <AdminPageHeader
        title="Dashboard"
        description="Das Kontrollzentrum der gesamten VIZU Academy Plattform."
        action={
          <AdminButton
            variant="secondary"
            size="sm"
            onClick={() => {
              refetch();
              queryClient.invalidateQueries({ queryKey: ["admin-dashboard-trends"] });
            }}
            disabled={isFetching}
          >
            <RefreshCw size={14} className={isFetching ? "animate-spin" : ""} />
            Aktualisieren
          </AdminButton>
        }
      />

      {isError && (
        <AdminCard className="mb-6">
          <div className="flex items-center gap-3">
            <AlertTriangle size={18} className="text-[var(--admin-danger)]" />
            <div>
              <p className="text-sm font-medium text-[var(--admin-text-primary)]">
                Dashboard-Daten konnten nicht geladen werden.
              </p>
              <button onClick={() => refetch()} className="mt-1 text-xs text-[var(--admin-primary)] hover:underline">
                Erneut versuchen
              </button>
            </div>
          </div>
        </AdminCard>
      )}

      {isLoading && (
        <div className="space-y-6">
          <KpiCardsSkeleton />
          <DashboardChartsSkeleton />
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <LearningAnalyticsSkeleton />
            <MockTestAnalyticsSkeleton />
          </div>
          <OperationsSkeleton />
          <ActivityHealthSkeleton />
        </div>
      )}

      {data && !isLoading && (
        <div className="space-y-6">
          <DashboardKpiCards kpis={data.kpis} />

          <DashboardCharts initialCharts={data.charts} showRevenue={data.can_see_finance !== false} />

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <DashboardLearningAnalytics data={data.learning_analytics} />
            <DashboardMockTestAnalytics certificates={data.mock_test_analytics} />
          </div>

          {data.vizu_multilevel && <DashboardVizuMultilevel data={data.vizu_multilevel} />}

          <DashboardOperations payments={data.payments} content={data.content} ai={data.ai} />

          <DashboardActivityHealth activity={data.recent_activity} health={data.server_health} />

          <DashboardQuickActions />
        </div>
      )}
    </div>
  );
}
