"use client";

import { AdminCard } from "@/components/admin/admin-ui";
import MiniBarChart from "@/components/admin/mini-bar-chart";
import {
  DASHBOARD_RANGES,
  type DashboardCharts as DashboardChartsType,
  type DashboardRange,
} from "@/features/admin/types/enterprise-dashboard.types";

const RANGE_LABELS: Record<DashboardRange, string> = {
  "7d": "7 Days",
  "30d": "30 Days",
  "90d": "90 Days",
  "1y": "1 Year",
};

function ChartCard({ title, data, prefix }: { title: string; data: { label: string; value: number }[]; prefix?: string }) {
  return (
    <AdminCard>
      <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">{title}</h3>
      {data.length > 0 ? (
        <MiniBarChart data={data} valuePrefix={prefix} />
      ) : (
        <p className="py-14 text-center text-sm text-[var(--admin-text-muted)]">
          Noch keine Daten für diesen Zeitraum.
        </p>
      )}
    </AdminCard>
  );
}

export function DashboardChartsSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      {[0, 1, 2].map((i) => (
        <AdminCard key={i} className="h-[220px] animate-pulse">
          <div className="h-3 w-24 rounded bg-white/5" />
          <div className="mt-6 h-32 rounded bg-white/5" />
        </AdminCard>
      ))}
    </div>
  );
}

export default function DashboardCharts({
  charts,
  range,
  onRangeChange,
}: {
  charts: DashboardChartsType;
  range: DashboardRange;
  onRangeChange: (range: DashboardRange) => void;
}) {
  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-semibold text-[var(--admin-text-primary)]">Trends</h2>
        <div className="flex gap-1 rounded-lg bg-white/[0.03] p-1 ring-1 ring-[var(--admin-border)]">
          {DASHBOARD_RANGES.map((r) => (
            <button
              key={r}
              onClick={() => onRangeChange(r)}
              className={`rounded-md px-3 py-1.5 text-xs font-semibold transition ${
                range === r
                  ? "bg-[var(--admin-primary)] text-white"
                  : "text-[var(--admin-text-secondary)] hover:text-[var(--admin-text-primary)]"
              }`}
            >
              {RANGE_LABELS[r]}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <ChartCard title="Revenue" data={charts.revenue} />
        <ChartCard title="New Users" data={charts.new_users} />
        <ChartCard title="Learning Progress" data={charts.learning_progress} />
      </div>
    </div>
  );
}
