"use client";

import { useQuery } from "@tanstack/react-query";
import { Clock, Flame } from "lucide-react";

import { getLearningActivity } from "@/features/dashboard/services/learning-activity-service";
import { useTranslation } from "@/lib/i18n/use-translation";

type T = (key: string, vars?: Record<string, string | number>) => string;

function duration(t: T, seconds: number): string {
  const total = Math.floor(seconds / 60);
  const h = Math.floor(total / 60);
  const m = total % 60;
  if (h === 0 && m === 0) return t("dashboard.hours", { h: 0 });
  if (h === 0) return t("dashboard.minutes", { m });
  return m === 0 ? t("dashboard.hours", { h }) : t("dashboard.hoursMinutes", { h, m });
}

/** "Lernserie": streak (local days), total learning time, last activity and
 * the last 7 days — all server-confirmed (no client-side numbers). */
export default function LearningStreakCard() {
  const { t, language } = useTranslation();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["dashboard", "learning-activity"], queryFn: getLearningActivity, staleTime: 60_000 });
  const locale = language === "uz" ? "uz-UZ" : "de-DE";
  const max = Math.max(1, ...(data?.week ?? []).map((d) => d.seconds));

  return (
    <section className="flex h-full flex-col rounded-card bg-surface-card p-5 shadow-[var(--shadow-card)] ring-1 ring-surface-border" aria-labelledby="streak-title" data-testid="dashboard-streak">
      <div className="flex items-center gap-2">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-orange-500/15 text-orange-500"><Flame size={18} aria-hidden="true" /></span>
        <h2 id="streak-title" className="font-bold text-text-primary">{t("dashboard.streakTitle")}</h2>
      </div>

      {isLoading ? (
        <div className="mt-4 h-24 animate-pulse rounded-xl bg-surface-hover" aria-busy="true" aria-label={t("dashboard.loading")} />
      ) : isError || !data ? (
        <p className="mt-4 text-sm text-text-secondary">
          {t("dashboard.loadError")}{" "}
          <button type="button" onClick={() => refetch()} className="font-semibold text-accent-blue hover:underline">{t("dashboard.retry")}</button>
        </p>
      ) : (
        <>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div>
              <p className="text-2xl font-extrabold text-text-primary" data-testid="streak-days">
                {data.streak_days === 1 ? t("dashboard.streakDay") : t("dashboard.streakDays", { n: data.streak_days })}
              </p>
              <p className="text-xs text-text-muted">{t("dashboard.streakInARow")}</p>
            </div>
            <div>
              <p className="text-2xl font-extrabold text-text-primary" data-testid="streak-time">{duration(t, data.total_seconds)}</p>
              <p className="text-xs text-text-muted">{t("dashboard.totalTime")}</p>
            </div>
          </div>

          <div className="mt-4 flex h-12 items-end gap-1.5" role="img" aria-label={t("dashboard.weekChart")}>
            {data.week.map((d) => (
              <div key={d.date} className="flex flex-1 flex-col items-center gap-1">
                <div className={`w-full rounded-t ${d.seconds > 0 ? "bg-orange-500" : "bg-surface-hover"}`}
                     style={{ height: `${d.seconds > 0 ? Math.max(15, (d.seconds / max) * 100) : 12}%` }}
                     title={`${new Date(d.date).toLocaleDateString(locale, { weekday: "short", day: "2-digit", month: "2-digit" })}: ${duration(t, d.seconds)}`} />
              </div>
            ))}
          </div>
          <p className="mt-2 text-xs text-text-secondary">{t("dashboard.weekActive", { n: data.active_days_week })}</p>

          <p className="mt-auto flex items-center gap-1.5 pt-3 text-xs text-text-muted">
            <Clock size={12} aria-hidden="true" />
            {data.last_activity_at
              ? `${t("dashboard.lastActivity")}: ${new Date(data.last_activity_at).toLocaleString(locale, { dateStyle: "medium", timeStyle: "short" })}`
              : t("dashboard.noActivity")}
          </p>
        </>
      )}
    </section>
  );
}
