"use client";

import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Clock, Hourglass, Percent, TrendingUp, UserX, Users } from "lucide-react";

import { AdminCard } from "@/components/admin/admin-ui";
import { getVizuMultilevelStatistics } from "@/features/admin/vizu-multilevel/services/vizu-multilevel-admin-service";

import VizuMultilevelResultsTab from "./results-tab";
import { ProgressBar, SKILL_LABELS, StatCard, StatsSkeleton } from "./shared";

const RESULT_LABELS: Record<string, string> = { BELOW_A1: "Below A1" };

/** Real aggregates only — with no data every number is 0 (nothing is
 * faked). Below-A1 and abandoned attempts are not kept per student; they
 * are counted through anonymous tally rows, so these numbers stay truthful. */
export default function VizuMultilevelStatisticsTab() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["vizu-multilevel-admin-statistics"],
    queryFn: getVizuMultilevelStatistics,
  });

  const maxResult = Math.max(1, ...(stats?.results ?? []).map((r) => r.count));

  return (
    <div className="space-y-6">
      {isLoading || !stats ? (
        <StatsSkeleton />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard icon={Users} label="Versuche gesamt" value={String(stats.total_attempts)} />
            <StatCard icon={CheckCircle2} label="Abgeschlossen" value={String(stats.completed_attempts)} />
            <StatCard icon={UserX} label="Abgebrochen" value={String(stats.abandoned_attempts)} />
            <StatCard icon={Clock} label="Laufend" value={String(stats.in_progress_attempts)} />
            <StatCard icon={Hourglass} label="Wartet auf Bewertung" value={String(stats.pending_review_attempts)} />
            <StatCard icon={TrendingUp} label="Ø Ergebnis" value={`${stats.average_score_percent}%`} />
            <StatCard icon={Percent} label="Abschlussquote" value={`${stats.completion_rate_percent}%`} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <AdminCard>
              <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">Ergebnisse nach Niveau</h3>
              <div className="space-y-3.5">
                {stats.results.map((r) => (
                  <ProgressBar
                    key={r.result}
                    label={RESULT_LABELS[r.result] ?? r.result}
                    percent={(r.count / maxResult) * 100}
                    right={String(r.count)}
                  />
                ))}
              </div>
            </AdminCard>

            <AdminCard>
              <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">Ø Ergebnis je Kompetenz</h3>
              <div className="space-y-3.5">
                {stats.competency_averages.map((c) => (
                  <ProgressBar
                    key={c.skill}
                    label={SKILL_LABELS[c.skill] ?? c.skill}
                    percent={c.average_percent}
                    right={`${c.average_percent}% · ${c.finished_count} Versuch(e)`}
                  />
                ))}
              </div>
            </AdminCard>
          </div>
        </>
      )}

      <VizuMultilevelResultsTab />
    </div>
  );
}
