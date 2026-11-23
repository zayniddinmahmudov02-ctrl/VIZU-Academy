"use client";

import { useState } from "react";

import { cn } from "@/lib/utils";

import { formatDate, formatDuration } from "../lib/format";
import type { DailyRow } from "../types";

/** One fixed colour per area (colour follows the entity, never its rank). Validated (dataviz validator, light on #ffffff and
 * dark on #111827): adjacent stacking order COURSE, WORTSCHATZ, MUSIC, BOOK, FILM, EXAM passes CVD + normal-vision checks;
 * three light colours are below 3:1, so the legend, the hover values and the table view are always there. */
export const AREA_COLORS: Record<string, string> = {
  COURSE: "bg-[#2a78d6] dark:bg-[#3987e5]",
  WORTSCHATZ: "bg-[#eb6834] dark:bg-[#d95926]",
  MUSIC: "bg-[#1baf7a] dark:bg-[#199e70]",
  BOOK: "bg-[#eda100] dark:bg-[#c98500]",
  FILM: "bg-[#e87ba4] dark:bg-[#d55181]",
  EXAM: "bg-[#6250d6] dark:bg-[#9085e9]",
};

const HEIGHT = 140;

interface Props {
  days: DailyRow[];
  series: { key: string; label: string }[];
  language: string;
  title: string;
  tableLabel: string;
  emptyLabel: string;
  testId?: string;
}

/** Stacked daily bars (seconds per area) with a legend, a per-day hover / focus tooltip and a table view. */
export default function ActivityBars({ days, series, language, title, tableLabel, emptyLabel, testId }: Props) {
  const [hover, setHover] = useState<number | null>(null);
  const totals = days.map((d) => series.reduce((sum, s) => sum + Number(d[s.key] ?? 0), 0));
  const max = Math.max(0, ...totals);
  const shown = hover !== null ? days[hover] : null;

  return (
    <figure className="rounded-2xl bg-surface-card p-4 ring-1 ring-surface-border sm:p-5" data-testid={testId}>
      <figcaption className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-sm font-semibold text-text-primary">{title}</span>
        <span className="flex flex-wrap gap-3" aria-label="Legende">
          {series.map((s) => (
            <span key={s.key} className="inline-flex items-center gap-1.5 text-xs text-text-secondary">
              <span className={cn("h-2.5 w-2.5 rounded-sm", AREA_COLORS[s.key])} aria-hidden />
              {s.label}
            </span>
          ))}
        </span>
      </figcaption>

      {max === 0 ? (
        <p className="mt-6 py-8 text-center text-sm text-text-muted">{emptyLabel}</p>
      ) : (
        <div className="relative mt-4">
          {shown && (
            <div role="status" className="pointer-events-none absolute -top-2 left-1/2 z-10 min-w-44 -translate-x-1/2 -translate-y-full rounded-xl bg-surface-card px-3 py-2 text-xs shadow-[var(--shadow-lg)] ring-1 ring-surface-border">
              <p className="font-semibold text-text-primary">{formatDate(String(shown.date), language)}</p>
              {series.map((s) => (
                <p key={s.key} className="mt-0.5 flex items-center justify-between gap-3 text-text-secondary">
                  <span className="inline-flex items-center gap-1.5"><span className={cn("h-2 w-2 rounded-sm", AREA_COLORS[s.key])} aria-hidden />{s.label}</span>
                  <span className="font-medium text-text-primary">{formatDuration(Number(shown[s.key] ?? 0), language)}</span>
                </p>
              ))}
            </div>
          )}
          <div className="flex items-end gap-1 border-b border-surface-border" style={{ height: HEIGHT }} onMouseLeave={() => setHover(null)}>
            {days.map((d, i) => (
              <button
                key={String(d.date)}
                type="button"
                className="group flex h-full min-w-0 flex-1 flex-col-reverse items-stretch rounded-t-[4px] outline-none focus-visible:ring-2 focus-visible:ring-accent-blue"
                onMouseEnter={() => setHover(i)}
                onFocus={() => setHover(i)}
                onBlur={() => setHover(null)}
                aria-label={`${formatDate(String(d.date), language)}: ${formatDuration(totals[i], language)}`}
              >
                {series.map((s, j) => {
                  const value = Number(d[s.key] ?? 0);
                  if (!value) return null;
                  const h = Math.max(2, Math.round((value / max) * (HEIGHT - 4)));
                  const top = series.slice(j + 1).every((other) => !Number(d[other.key] ?? 0));
                  return (
                    <span
                      key={s.key}
                      className={cn("block w-full", AREA_COLORS[s.key], top && "rounded-t-[4px]", hover === i && "brightness-110")}
                      style={{ height: h, marginTop: top ? 0 : 2 }}
                    />
                  );
                })}
              </button>
            ))}
          </div>
          <div className="mt-1 flex justify-between text-[10px] text-text-muted">
            <span>{formatDate(String(days[0]?.date), language)}</span>
            <span>{formatDate(String(days[days.length - 1]?.date), language)}</span>
          </div>
        </div>
      )}

      <details className="mt-3 text-xs text-text-secondary">
        <summary className="cursor-pointer select-none font-medium">{tableLabel}</summary>
        <div className="mt-2 overflow-x-auto">
          <table className="w-full min-w-[320px] text-left">
            <thead>
              <tr className="text-text-muted">
                <th className="py-1 pr-2 font-medium">—</th>
                {series.map((s) => <th key={s.key} className="py-1 pr-2 font-medium">{s.label}</th>)}
              </tr>
            </thead>
            <tbody>
              {days.map((d) => (
                <tr key={String(d.date)} className="border-t border-surface-border">
                  <td className="py-1 pr-2">{formatDate(String(d.date), language)}</td>
                  {series.map((s) => <td key={s.key} className="py-1 pr-2 text-text-primary">{formatDuration(Number(d[s.key] ?? 0), language)}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </figure>
  );
}
