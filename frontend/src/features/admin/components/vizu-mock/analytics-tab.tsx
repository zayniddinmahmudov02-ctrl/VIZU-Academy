"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, AlertTriangle, Award, BarChart3, Clock, Loader2, Percent, Users } from "lucide-react";

import { AdminCard } from "@/components/admin/admin-ui";
import MiniBarChart from "@/components/admin/mini-bar-chart";
import { getVizuMockAnalytics } from "@/features/admin/services/vizu-mock-admin-service";
import type { ChartPoint } from "@/features/admin/types/dashboard.types";
import { ProgressBar, SKILL_LABELS, StatCard, StatsSkeleton } from "./shared";

export default function VizuMockAnalyticsTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["vizu-mock-admin-analytics"],
    queryFn: getVizuMockAnalytics,
  });

  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <StatsSkeleton count={4} />
        <div className="flex h-40 items-center justify-center">
          <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
        </div>
      </div>
    );
  }

  const { overview, activity_30d, level_analytics, time_analytics } = data;

  const started30: ChartPoint[] = activity_30d.points.map((p) => ({ label: p.label, value: p.started }));
  const completed30: ChartPoint[] = activity_30d.points.map((p) => ({ label: p.label, value: p.completed }));

  return (
    <div className="space-y-6">
      {/* General */}
      <section>
        <h2 className="mb-3 flex items-center gap-2 text-base font-bold text-[var(--admin-text-primary)]">
          <Users size={17} className="text-[var(--admin-primary)]" /> Allgemein
        </h2>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard icon={Users} label="Tests gesamt" value={overview.total_attempts.toLocaleString("de-DE")} />
          <StatCard
            icon={Award}
            label="Abgeschlossen"
            value={overview.completed_attempts.toLocaleString("de-DE")}
          />
          <StatCard
            icon={Percent}
            label="Abschlussrate (30 Tage)"
            value={activity_30d.completion_rate_percent !== null ? `${activity_30d.completion_rate_percent}%` : "—"}
          />
          <StatCard
            icon={Percent}
            label="Ø Gesamtergebnis"
            value={overview.average_score_percent !== null ? `${overview.average_score_percent}%` : "—"}
          />
        </div>
      </section>

      {/* Competency */}
      <section>
        <AdminCard>
          <h2 className="mb-4 text-base font-bold text-[var(--admin-text-primary)]">Kompetenz-Analyse</h2>
          <div className="space-y-4">
            {level_analytics.competencies.map((c) => (
              <ProgressBar
                key={c.skill}
                label={SKILL_LABELS[c.skill] ?? c.skill}
                percent={c.average_percent ?? 0}
                right={
                  c.average_percent !== null
                    ? `Ø ${c.average_percent}% · ${c.submitted_count} Teiln. · häufigstes Niveau: ${c.most_common_level ?? "—"}`
                    : `Noch keine Daten (${c.submitted_count} Teiln.)`
                }
              />
            ))}
          </div>
        </AdminCard>
      </section>

      {/* Level distribution */}
      <section>
        <AdminCard>
          <h2 className="mb-4 text-base font-bold text-[var(--admin-text-primary)]">Niveau-Verteilung</h2>
          {level_analytics.total_leveled === 0 ? (
            <p className="py-6 text-center text-sm text-[var(--admin-text-muted)]">Noch keine Statistik vorhanden.</p>
          ) : (
            <div className="space-y-4">
              {level_analytics.level_distribution.map((bucket) => (
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
      </section>

      {/* Time analytics */}
      <section>
        <h2 className="mb-3 flex items-center gap-2 text-base font-bold text-[var(--admin-text-primary)]">
          <Clock size={17} className="text-[var(--admin-primary)]" /> Zeit-Analyse
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <StatCard
            icon={Clock}
            label="Ø Bearbeitungszeit"
            value={
              time_analytics.average_completion_minutes !== null
                ? `${time_analytics.average_completion_minutes} Min.`
                : "—"
            }
          />
          <StatCard
            icon={AlertTriangle}
            label="Abbruchrate"
            value={
              time_analytics.abandonment_rate_percent !== null ? `${time_analytics.abandonment_rate_percent}%` : "—"
            }
          />
        </div>
      </section>

      {/* Activity */}
      <section>
        <AdminCard>
          <h2 className="mb-4 flex items-center gap-2 text-base font-bold text-[var(--admin-text-primary)]">
            <Activity size={17} className="text-[var(--admin-primary)]" /> Aktivität (30 Tage)
          </h2>
          <div className="grid gap-6 sm:grid-cols-2">
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">
                Gestartet
              </p>
              <MiniBarChart data={started30} />
            </div>
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">
                Abgeschlossen
              </p>
              <MiniBarChart data={completed30} />
            </div>
          </div>
        </AdminCard>
      </section>

      {/* Popularity note — VIZU-Mock is a single test product today, so there is
          no meaningful multi-test ranking to show; General already covers
          started/completed counts. */}
      <section>
        <AdminCard className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]">
            <BarChart3 size={17} />
          </div>
          <p className="text-sm text-[var(--admin-text-secondary)]">
            VIZU-MOCK ist aktuell ein einzelner Test (kein Modelltest-Katalog) — eine separate
            &quot;Beliebtheit&quot;-Rangliste ist daher nicht aussagekräftig. Gestartete/abgeschlossene Zahlen finden
            Sie oben unter &quot;Allgemein&quot;.
          </p>
        </AdminCard>
      </section>
    </div>
  );
}
