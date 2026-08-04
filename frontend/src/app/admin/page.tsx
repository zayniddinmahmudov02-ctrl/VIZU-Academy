"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
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
import { getEnterpriseDashboard } from "@/features/admin/services/enterprise-dashboard-service";
import type { DashboardRange } from "@/features/admin/types/enterprise-dashboard.types";

export default function AdminDashboardPage() {
  const [range, setRange] = useState<DashboardRange>("30d");

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["admin-enterprise-dashboard", range],
    queryFn: () => getEnterpriseDashboard(range),
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
          <AdminButton variant="secondary" size="sm" onClick={() => refetch()} disabled={isFetching}>
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

          <DashboardCharts charts={data.charts} range={range} onRangeChange={setRange} />

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <DashboardLearningAnalytics data={data.learning_analytics} />
            <DashboardMockTestAnalytics certificates={data.mock_test_analytics} />
          </div>

          <DashboardOperations payments={data.payments} content={data.content} ai={data.ai} />

          <DashboardActivityHealth activity={data.recent_activity} health={data.server_health} />

          <DashboardQuickActions />
        </div>
      )}
    </div>
  );
}
