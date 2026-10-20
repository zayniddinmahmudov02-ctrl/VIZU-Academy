"use client";

import { useState } from "react";

import type { ChartPoint } from "@/features/admin/types/dashboard.types";

interface Props {
  data: ChartPoint[];
  valuePrefix?: string;
  /** turns a raw bucket label (e.g. "2026-10-20") into axis / tooltip text */
  formatLabel?: (label: string) => string;
  formatValue?: (value: number) => string;
  /** at most this many axis labels; the rest stay readable in the tooltip */
  maxLabels?: number;
}

/** Dependency-free bar chart — recharts was deliberately removed from this
 * project in an earlier cleanup pass (it was only used by the now-deleted
 * admin panel), so this avoids reintroducing it for a handful of simple
 * trend bars. Handles up to ~100 bars: sparse axis labels, hover tooltip. */
export default function MiniBarChart({
  data,
  valuePrefix = "",
  formatLabel = (label) => label,
  formatValue = (value) => value.toLocaleString("de-DE"),
  maxLabels = 8,
}: Props) {
  const [hovered, setHovered] = useState<number | null>(null);
  const max = Math.max(...data.map((d) => d.value), 1);
  const labelEvery = Math.max(1, Math.ceil(data.length / maxLabels));
  const dense = data.length > 20;
  const active = hovered !== null ? data[hovered] : null;

  return (
    <div className="relative">
      <div className="mb-1 h-4 text-[11px] text-[var(--admin-text-secondary)]" aria-live="polite">
        {active ? (
          <>
            <span className="text-[var(--admin-text-muted)]">{formatLabel(active.label)}: </span>
            <span className="font-semibold text-[var(--admin-text-primary)]">
              {valuePrefix}
              {formatValue(active.value)}
            </span>
          </>
        ) : null}
      </div>
      <div className={`flex h-40 items-end ${dense ? "gap-px" : "gap-2"}`} onMouseLeave={() => setHovered(null)}>
        {data.map((point, index) => (
          <div
            key={point.label}
            className="flex h-full min-w-0 flex-1 items-end"
            onMouseEnter={() => setHovered(index)}
            title={`${formatLabel(point.label)}: ${valuePrefix}${formatValue(point.value)}`}
          >
            <div
              className={`w-full rounded-t-md transition-all ${
                point.value > 0
                  ? "bg-gradient-to-t from-[var(--admin-primary)] to-[var(--admin-primary-hover)]"
                  : "bg-white/5"
              } ${hovered === index ? "opacity-100" : hovered !== null ? "opacity-60" : ""}`}
              style={{ height: `${point.value > 0 ? Math.max((point.value / max) * 100, 3) : 2}%` }}
            />
          </div>
        ))}
      </div>
      <div className={`mt-2 flex ${dense ? "gap-px" : "gap-2"}`}>
        {data.map((point, index) => (
          <span
            key={point.label}
            className="min-w-0 flex-1 overflow-visible whitespace-nowrap text-center text-[10px] font-medium uppercase tracking-wide text-[var(--admin-text-muted)]"
          >
            {index % labelEvery === 0 ? formatLabel(point.label) : ""}
          </span>
        ))}
      </div>
    </div>
  );
}
