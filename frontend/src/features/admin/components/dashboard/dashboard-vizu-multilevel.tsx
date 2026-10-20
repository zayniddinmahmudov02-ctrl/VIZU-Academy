"use client";

import Link from "next/link";
import { Award, CheckCircle2, ClipboardList, Gauge } from "lucide-react";

import { AdminCard } from "@/components/admin/admin-ui";
import type { VizuMultilevelStats } from "@/features/admin/types/enterprise-dashboard.types";

const LEVELS = ["BELOW_A1", "A1", "A2", "B1", "B2", "C1"];

/** VIZU-Multilevel (free level check): attempts, final results and
 * certificates — all from the stored attempt columns. */
export default function DashboardVizuMultilevel({ data }: { data: VizuMultilevelStats }) {
  const levels = Object.entries(data.by_level).sort(([a], [b]) => LEVELS.indexOf(a) - LEVELS.indexOf(b));
  const max = Math.max(1, ...levels.map(([, n]) => n));
  return (
    <AdminCard>
      <div className="mb-4 flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">VIZU-Multilevel</h3>
        <Link href="/admin/certificates?source=VIZU_MULTILEVEL" className="text-xs font-semibold text-[var(--admin-primary)] hover:underline">Zertifikate →</Link>
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {[
          { icon: ClipboardList, label: "Versuche", value: data.attempts },
          { icon: CheckCircle2, label: "Abgeschlossen", value: data.completed },
          { icon: Award, label: "Zertifikate", value: data.final_results },
          { icon: Gauge, label: "Ø Ergebnis", value: data.average_result !== null ? `${data.average_result}%` : "—" },
        ].map(({ icon: Icon, label, value }) => (
          <div key={label} className="flex items-center gap-3 rounded-lg bg-white/[0.02] p-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]"><Icon size={16} /></div>
            <div className="min-w-0">
              <p className="truncate text-sm font-bold text-[var(--admin-text-primary)]">{value}</p>
              <p className="truncate text-[10px] uppercase tracking-wide text-[var(--admin-text-muted)]">{label}</p>
            </div>
          </div>
        ))}
      </div>
      {levels.length > 0 ? (
        <div className="mt-4 space-y-1.5">
          {levels.map(([level, n]) => (
            <div key={level} className="flex items-center gap-3 text-xs">
              <span className="w-16 shrink-0 font-semibold text-[var(--admin-text-secondary)]">{level === "BELOW_A1" ? "unter A1" : level}</span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/5">
                <div className="h-full rounded-full bg-[var(--admin-primary)]" style={{ width: `${(n / max) * 100}%` }} />
              </div>
              <span className="w-8 text-right text-[var(--admin-text-secondary)]">{n}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-xs text-[var(--admin-text-muted)]">Noch keine abgeschlossenen Ergebnisse.</p>
      )}
      <p className="mt-3 text-[11px] text-[var(--admin-text-muted)]">
        {data.certificates_issued} Zertifikatsnummern vergeben (die Nummer entsteht beim ersten Öffnen des Zertifikats).
      </p>
    </AdminCard>
  );
}
