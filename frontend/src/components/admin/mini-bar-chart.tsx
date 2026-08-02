"use client";

import type { ChartPoint } from "@/features/admin/types/dashboard.types";

interface Props {
  data: ChartPoint[];
  valuePrefix?: string;
}

/** Dependency-free bar chart — recharts was deliberately removed from this
 * project in an earlier cleanup pass (it was only used by the now-deleted
 * admin panel), so this avoids reintroducing it for a handful of simple
 * trend bars. */
export default function MiniBarChart({ data, valuePrefix = "" }: Props) {
  const max = Math.max(...data.map((d) => d.value), 1);

  return (
    <div className="flex h-40 items-end gap-2">
      {data.map((point) => (
        <div key={point.label} className="flex flex-1 flex-col items-center gap-2">
          <div className="flex h-full w-full items-end">
            <div
              className="w-full rounded-t-md bg-gradient-to-t from-[var(--admin-primary)] to-[var(--admin-primary-hover)] transition-all"
              style={{ height: `${Math.max((point.value / max) * 100, 3)}%` }}
              title={`${valuePrefix}${point.value.toLocaleString()}`}
            />
          </div>
          <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--admin-text-muted)]">
            {point.label}
          </span>
        </div>
      ))}
    </div>
  );
}
