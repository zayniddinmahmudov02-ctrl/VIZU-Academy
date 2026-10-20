"use client";

import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { AlertTriangle, Loader2 } from "lucide-react";

import { AdminCard } from "@/components/admin/admin-ui";
import MiniBarChart from "@/components/admin/mini-bar-chart";
import { getDashboardTrends } from "@/features/admin/services/enterprise-dashboard-service";
import {
  DASHBOARD_RANGES,
  TREND_GRANULARITIES,
  type DashboardChartPoint,
  type DashboardCharts as DashboardChartsType,
  type DashboardRange,
  type TrendGranularity,
} from "@/features/admin/types/enterprise-dashboard.types";

const RANGE_LABELS: Record<DashboardRange, string> = {
  "7d": "7 Tage",
  "30d": "30 Tage",
  "90d": "90 Tage",
  "1y": "1 Jahr",
};

const GRANULARITY_LABELS: Record<TrendGranularity, string> = {
  day: "Täglich",
  week: "Wöchentlich",
  month: "Monatlich",
};

// mirrors ALLOWED_GRANULARITIES / DEFAULT_GRANULARITY in enterprise_dashboard_service.py
const ALLOWED: Record<DashboardRange, TrendGranularity[]> = {
  "7d": ["day"],
  "30d": ["day", "week"],
  "90d": ["day", "week", "month"],
  "1y": ["week", "month"],
};
const DEFAULT_GRANULARITY: Record<DashboardRange, TrendGranularity> = {
  "7d": "day",
  "30d": "day",
  "90d": "week",
  "1y": "month",
};

const MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"];

function bucketLabel(label: string, granularity: TrendGranularity): string {
  const [y, m, d] = label.split("-");
  if (granularity === "month") return `${MONTHS[Number(m) - 1] ?? m} ${y.slice(2)}`;
  if (granularity === "week") return `ab ${d}.${m}.`; // week starting Monday
  return `${d}.${m}.`;
}

function formatUzs(value: number): string {
  return `${value.toLocaleString("de-DE")} UZS`;
}

function ChartCard({
  title,
  data,
  total,
  granularity,
  formatValue,
}: {
  title: string;
  data: DashboardChartPoint[];
  total: number;
  granularity: TrendGranularity;
  formatValue?: (value: number) => string;
}) {
  const fmt = formatValue ?? ((v: number) => v.toLocaleString("de-DE"));
  const hasData = data.some((p) => p.value > 0);
  return (
    <AdminCard>
      <div className="mb-3 flex items-baseline justify-between gap-2">
        <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">{title}</h3>
        <span className="text-sm font-bold text-[var(--admin-text-primary)]">{fmt(total)}</span>
      </div>
      {hasData ? (
        <MiniBarChart
          data={data}
          formatLabel={(label) => bucketLabel(label, granularity)}
          formatValue={fmt}
        />
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
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      {[0, 1, 2, 3].map((i) => (
        <AdminCard key={i} className="h-[240px] animate-pulse">
          <div className="h-3 w-24 rounded bg-white/5" />
          <div className="mt-6 h-32 rounded bg-white/5" />
        </AdminCard>
      ))}
    </div>
  );
}

function Segmented<T extends string>({
  options,
  value,
  labels,
  onChange,
  isDisabled,
}: {
  options: readonly T[];
  value: T;
  labels: Record<T, string>;
  onChange: (value: T) => void;
  isDisabled?: (value: T) => boolean;
}) {
  return (
    <div className="flex gap-1 rounded-lg bg-white/[0.03] p-1 ring-1 ring-[var(--admin-border)]">
      {options.map((option) => {
        const disabled = isDisabled?.(option) ?? false;
        return (
          <button
            key={option}
            type="button"
            disabled={disabled}
            onClick={() => onChange(option)}
            className={`rounded-md px-3 py-1.5 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-30 ${
              value === option
                ? "bg-[var(--admin-primary)] text-white"
                : "text-[var(--admin-text-secondary)] hover:text-[var(--admin-text-primary)]"
            }`}
          >
            {labels[option]}
          </button>
        );
      })}
    </div>
  );
}

/** Trends — new users, course purchases, revenue (finance roles only) and
 * completed lessons over time. The first paint uses the charts of the main
 * dashboard payload (30 days, daily); every filter change loads only
 * GET /admin/dashboard/trends. */
export default function DashboardCharts({
  initialCharts,
  showRevenue = true,
}: {
  initialCharts: DashboardChartsType;
  showRevenue?: boolean;
}) {
  const [range, setRange] = useState<DashboardRange>("30d");
  const [granularity, setGranularity] = useState<TrendGranularity>("day");

  const isInitial =
    range === initialCharts.range && granularity === initialCharts.granularity && initialCharts.new_users.length > 0;

  const { data, isError, isFetching, refetch } = useQuery({
    queryKey: ["admin-dashboard-trends", range, granularity],
    queryFn: () => getDashboardTrends(range, granularity),
    initialData: isInitial ? initialCharts : undefined,
    placeholderData: keepPreviousData,
    staleTime: 60 * 1000,
  });

  function changeRange(next: DashboardRange) {
    setRange(next);
    if (!ALLOWED[next].includes(granularity)) setGranularity(DEFAULT_GRANULARITY[next]);
  }

  const charts = data;
  const g = charts?.granularity ?? granularity;

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <h2 className="text-base font-semibold text-[var(--admin-text-primary)]">Trends</h2>
          {isFetching && <Loader2 size={14} className="animate-spin text-[var(--admin-text-muted)]" />}
        </div>
        <div className="flex flex-wrap gap-2">
          <Segmented
            options={TREND_GRANULARITIES}
            value={granularity}
            labels={GRANULARITY_LABELS}
            onChange={setGranularity}
            isDisabled={(option) => !ALLOWED[range].includes(option)}
          />
          <Segmented options={DASHBOARD_RANGES} value={range} labels={RANGE_LABELS} onChange={changeRange} />
        </div>
      </div>

      {isError && !charts && (
        <AdminCard>
          <div className="flex items-center gap-3">
            <AlertTriangle size={18} className="text-[var(--admin-danger)]" />
            <p className="text-sm text-[var(--admin-text-primary)]">Trends konnten nicht geladen werden.</p>
            <button onClick={() => refetch()} className="text-xs text-[var(--admin-primary)] hover:underline">
              Erneut versuchen
            </button>
          </div>
        </AdminCard>
      )}

      {!charts && !isError && <DashboardChartsSkeleton />}

      {charts && (
        <div className={`grid grid-cols-1 gap-6 lg:grid-cols-2 ${isFetching ? "opacity-70" : ""}`}>
          <ChartCard
            title="Neue Nutzer"
            data={charts.new_users}
            total={charts.totals?.new_users ?? 0}
            granularity={g}
          />
          <ChartCard
            title="Kurskäufe (bestätigt)"
            data={charts.course_purchases}
            total={charts.totals?.course_purchases ?? 0}
            granularity={g}
          />
          {showRevenue && (
            <ChartCard
              title="Umsatz (bestätigt)"
              data={charts.revenue}
              total={charts.totals?.revenue ?? 0}
              granularity={g}
              formatValue={formatUzs}
            />
          )}
          <ChartCard
            title="Abgeschlossene Lektionen"
            data={charts.learning_progress}
            total={charts.totals?.learning_progress ?? 0}
            granularity={g}
          />
        </div>
      )}
    </div>
  );
}
