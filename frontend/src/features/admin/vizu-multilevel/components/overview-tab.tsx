"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Award,
  BarChart3,
  CalendarDays,
  CalendarRange,
  CheckCircle2,
  Clock,
  Loader2,
  Percent,
  Users,
} from "lucide-react";

import { AdminButton, AdminCard } from "@/components/admin/admin-ui";
import MiniBarChart from "@/components/admin/mini-bar-chart";
import {
  getVizuMultilevelActivity,
  getVizuMultilevelLevelAnalytics,
  getVizuMultilevelOverview,
  listVizuMultilevelAttempts,
} from "@/features/admin/vizu-multilevel/services/vizu-multilevel-admin-service";
import type { ChartPoint } from "@/features/admin/types/dashboard.types";
import VizuMultilevelAttemptsTable from "./attempts-table";
import { ProgressBar, SKILL_LABELS, StatCard, StatsSkeleton } from "./shared";

export default function VizuMultilevelOverviewTab() {
  const [activityDays, setActivityDays] = useState<7 | 30>(7);

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ["vizu-multilevel-admin-overview"],
    queryFn: getVizuMultilevelOverview,
  });

  const { data: activity, isLoading: activityLoading } = useQuery({
    queryKey: ["vizu-multilevel-admin-activity", activityDays],
    queryFn: () => getVizuMultilevelActivity(activityDays),
  });

  const { data: levelAnalytics, isLoading: levelLoading } = useQuery({
    queryKey: ["vizu-multilevel-admin-level-analytics"],
    queryFn: getVizuMultilevelLevelAnalytics,
  });

  const { data: recentAttempts, isLoading: recentLoading } = useQuery({
    queryKey: ["vizu-multilevel-admin-recent-attempts"],
    queryFn: () => listVizuMultilevelAttempts({ page: 1, page_size: 5 }),
  });

  const startedPoints: ChartPoint[] = (activity?.points ?? []).map((p) => ({ label: p.label, value: p.started }));
  const completedPoints: ChartPoint[] = (activity?.points ?? []).map((p) => ({ label: p.label, value: p.completed }));

  return (
    <div className="space-y-6">
      {overviewLoading || !overview ? (
        <StatsSkeleton />
      ) : (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard icon={Users} label="Teilnehmer gesamt" value={overview.total_attempts.toLocaleString("de-DE")} />
          <StatCard icon={CalendarDays} label="Heute" value={overview.today_attempts.toLocaleString("de-DE")} />
          <StatCard icon={CalendarDays} label="Diese Woche" value={overview.week_attempts.toLocaleString("de-DE")} />
          <StatCard icon={CalendarRange} label="Diesen Monat" value={overview.month_attempts.toLocaleString("de-DE")} />
          <StatCard icon={CheckCircle2} label="Abgeschlossen" value={overview.completed_attempts.toLocaleString("de-DE")} />
          <StatCard icon={Loader2} label="In Bearbeitung" value={overview.in_progress_attempts.toLocaleString("de-DE")} />
          <StatCard
            icon={Percent}
            label="Ø Gesamtergebnis"
            value={overview.average_score_percent !== null ? `${overview.average_score_percent}%` : "—"}
          />
          <StatCard icon={Award} label="Häufigstes Niveau" value={overview.most_common_level ?? "—"} />
        </div>
      )}

      <AdminCard>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <BarChart3 size={17} className="text-[var(--admin-primary)]" />
            <h2 className="text-base font-bold text-[var(--admin-text-primary)]">Test-Aktivität</h2>
          </div>
          <div className="flex gap-1.5">
            <AdminButton
              size="sm"
              variant={activityDays === 7 ? "primary" : "secondary"}
              onClick={() => setActivityDays(7)}
            >
              7 Tage
            </AdminButton>
            <AdminButton
              size="sm"
              variant={activityDays === 30 ? "primary" : "secondary"}
              onClick={() => setActivityDays(30)}
            >
              30 Tage
            </AdminButton>
          </div>
        </div>

        {activityLoading || !activity ? (
          <div className="flex h-40 items-center justify-center">
            <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
          </div>
        ) : (
          <>
            <div className="mb-5 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
              <div>
                <p className="text-[var(--admin-text-muted)]">Abschlussrate</p>
                <p className="mt-0.5 font-bold text-[var(--admin-text-primary)]">
                  {activity.completion_rate_percent !== null ? `${activity.completion_rate_percent}%` : "—"}
                </p>
              </div>
              <div>
                <p className="text-[var(--admin-text-muted)]">Ø Dauer</p>
                <p className="mt-0.5 font-bold text-[var(--admin-text-primary)]">
                  {activity.average_duration_minutes !== null ? `${activity.average_duration_minutes} Min.` : "—"}
                </p>
              </div>
            </div>

            <div className="grid gap-6 sm:grid-cols-2">
              <div>
                <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">
                  <Clock size={13} /> Gestartet
                </p>
                <MiniBarChart data={startedPoints} />
              </div>
              <div>
                <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">
                  <CheckCircle2 size={13} /> Abgeschlossen
                </p>
                <MiniBarChart data={completedPoints} />
              </div>
            </div>
          </>
        )}
      </AdminCard>

      <div className="grid gap-6 lg:grid-cols-2">
        <AdminCard>
          <h2 className="mb-4 text-base font-bold text-[var(--admin-text-primary)]">Erkannte Niveaus</h2>
          {levelLoading || !levelAnalytics ? (
            <div className="flex h-32 items-center justify-center">
              <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
            </div>
          ) : levelAnalytics.total_leveled === 0 ? (
            <p className="py-6 text-center text-sm text-[var(--admin-text-muted)]">Noch keine Statistik vorhanden.</p>
          ) : (
            <div className="space-y-4">
              {levelAnalytics.level_distribution.map((bucket) => (
                <ProgressBar
                  key={bucket.level}
                  label={bucket.level}
                  percent={bucket.percent}
                  right={`${bucket.count} · ${bucket.percent}%`}
                />
              ))}
            </div>
          )}
        </AdminCard>

        <AdminCard>
          <h2 className="mb-4 text-base font-bold text-[var(--admin-text-primary)]">Ergebnisse nach Kompetenz</h2>
          {levelLoading || !levelAnalytics ? (
            <div className="flex h-32 items-center justify-center">
              <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
            </div>
          ) : (
            <div className="space-y-4">
              {levelAnalytics.competencies.map((c) => (
                <ProgressBar
                  key={c.skill}
                  label={SKILL_LABELS[c.skill] ?? c.skill}
                  percent={c.average_percent ?? 0}
                  right={
                    c.average_percent !== null
                      ? `Ø ${c.average_percent}% · ${c.submitted_count} Teiln. · ${c.most_common_level ?? "—"}`
                      : `Noch keine Daten (${c.submitted_count})`
                  }
                />
              ))}
            </div>
          )}
        </AdminCard>
      </div>

      <AdminCard className="p-0">
        <div className="p-5 pb-0">
          <h2 className="text-base font-bold text-[var(--admin-text-primary)]">Letzte Tests</h2>
        </div>
        <div className="p-5">
          <VizuMultilevelAttemptsTable
            items={recentAttempts?.items}
            isLoading={recentLoading}
            emptyMessage="Noch keine Tests durchgeführt."
          />
        </div>
      </AdminCard>
    </div>
  );
}
