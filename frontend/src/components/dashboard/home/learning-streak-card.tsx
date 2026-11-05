"use client";

import { useQuery } from "@tanstack/react-query";
import { Flame } from "lucide-react";

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

/** Compact "Lernserie" summary; all displayed statistics are server-confirmed. */
export default function LearningStreakCard() {
  const { t, language } = useTranslation();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["dashboard", "learning-activity"], queryFn: getLearningActivity, staleTime: 60_000 });
  const locale = language === "uz" ? "uz-UZ" : "de-DE";

  return (
    <section className="rounded-card bg-surface-card p-4 shadow-[var(--shadow-card)] ring-1 ring-surface-border sm:p-5" aria-labelledby="streak-title" data-testid="dashboard-streak">
      <div className="flex items-center gap-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-500/15 text-orange-500"><Flame size={16} aria-hidden="true" /></span>
        <h2 id="streak-title" className="font-bold text-text-primary">{t("dashboard.streakTitle")}</h2>
      </div>

      {isLoading ? (
        <div className="mt-3 h-12 animate-pulse rounded-xl bg-surface-hover" aria-busy="true" aria-label={t("dashboard.loading")} />
      ) : isError || !data ? (
        <p className="mt-4 text-sm text-text-secondary">
          {t("dashboard.loadError")}{" "}
          <button type="button" onClick={() => refetch()} className="font-semibold text-accent-blue hover:underline">{t("dashboard.retry")}</button>
        </p>
      ) : (
        <div className="mt-3 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <div className="min-w-0">
            <p className="text-lg font-extrabold text-text-primary sm:text-xl" data-testid="streak-days">
              {data.streak_days === 1 ? t("dashboard.streakDay") : t("dashboard.streakDays", { n: data.streak_days })}
            </p>
            <p className="text-xs text-text-muted">{t("dashboard.streakCurrent")}</p>
          </div>
          <div className="min-w-0">
            <p className="text-lg font-extrabold text-text-primary sm:text-xl" data-testid="streak-active-days">
              {data.active_days_week} / 7
            </p>
            <p className="text-xs text-text-muted">{t("dashboard.streakActiveDays")}</p>
          </div>
          <div className="min-w-0">
            <p className="text-lg font-extrabold text-text-primary sm:text-xl" data-testid="streak-time">{duration(t, data.total_seconds)}</p>
            <p className="text-xs text-text-muted">{t("dashboard.totalTime")}</p>
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-text-primary">
              {data.last_activity_at
                ? new Date(data.last_activity_at).toLocaleString(locale, { dateStyle: "medium", timeStyle: "short" })
                : t("dashboard.noActivity")}
            </p>
            <p className="text-xs text-text-muted">{t("dashboard.lastActivity")}</p>
          </div>
        </div>
      )}
    </section>
  );
}
