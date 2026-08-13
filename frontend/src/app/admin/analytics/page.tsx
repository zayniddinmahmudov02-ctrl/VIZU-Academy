"use client";

import { useQuery } from "@tanstack/react-query";

import { AdminCard, AdminPageHeader } from "@/components/admin/admin-ui";
import MiniBarChart from "@/components/admin/mini-bar-chart";
import { getRevenueOverview } from "@/features/admin/services/vizu-pay-service";

function StatBlock({ label, value }: { label: string; value: string | number }) {
  return (
    <AdminCard>
      <p className="text-xs font-medium uppercase tracking-wide text-[var(--admin-text-muted)]">{label}</p>
      <p className="mt-1 text-xl font-bold text-[var(--admin-text-primary)]">{value}</p>
    </AdminCard>
  );
}

export default function AnalyticsPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["revenue-overview"],
    queryFn: getRevenueOverview,
  });

  return (
    <div>
      <AdminPageHeader title="Analytics" description="Umsatz, Bestellungen und Conversion im Überblick." />

      {isLoading && (
        <div className="flex justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-white/10 border-t-[var(--admin-primary)]" />
        </div>
      )}

      {isError && (
        <AdminCard>
          <p className="text-sm text-[var(--admin-danger)]">Analytics-Daten konnten nicht geladen werden.</p>
        </AdminCard>
      )}

      {data && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatBlock label="Umsatz gesamt" value={data.total_revenue.toLocaleString()} />
            <StatBlock label="Umsatz (Monat)" value={data.revenue_this_month.toLocaleString()} />
            <StatBlock label="Umsatz (Heute)" value={data.revenue_today.toLocaleString()} />
            <StatBlock label="Offene Bestellungen" value={data.pending_orders} />
            <StatBlock label="Bestellungen gesamt" value={data.total_orders} />
          </div>

          <AdminCard>
            <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">
              Monatlicher Umsatz
            </h3>
            {data.monthly_revenue_chart.length > 0 ? (
              <MiniBarChart data={data.monthly_revenue_chart} />
            ) : (
              <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">Noch keine Daten.</p>
            )}
          </AdminCard>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <AdminCard>
              <h3 className="mb-3 text-sm font-semibold text-[var(--admin-text-primary)]">Nach Plan</h3>
              <div className="space-y-2">
                {data.plan_breakdown.map((p) => (
                  <div key={p.plan} className="flex justify-between text-sm">
                    <span className="text-[var(--admin-text-secondary)]">{p.label}</span>
                    <span className="font-semibold text-[var(--admin-text-primary)]">
                      {p.revenue.toLocaleString()} ({p.orders})
                    </span>
                  </div>
                ))}
                {data.plan_breakdown.length === 0 && (
                  <p className="text-sm text-[var(--admin-text-muted)]">Keine Daten.</p>
                )}
              </div>
            </AdminCard>

            <AdminCard>
              <h3 className="mb-3 text-sm font-semibold text-[var(--admin-text-primary)]">Nach Methode</h3>
              <div className="space-y-2">
                {data.method_breakdown.map((m) => (
                  <div key={m.method} className="flex justify-between text-sm">
                    <span className="text-[var(--admin-text-secondary)]">{m.method}</span>
                    <span className="font-semibold text-[var(--admin-text-primary)]">
                      {m.revenue.toLocaleString()} ({m.orders})
                    </span>
                  </div>
                ))}
                {data.method_breakdown.length === 0 && (
                  <p className="text-sm text-[var(--admin-text-muted)]">Keine Daten.</p>
                )}
              </div>
            </AdminCard>

            <AdminCard>
              <h3 className="mb-3 text-sm font-semibold text-[var(--admin-text-primary)]">Nach Status</h3>
              <div className="space-y-2">
                {data.status_breakdown.map((s) => (
                  <div key={s.status} className="flex justify-between text-sm">
                    <span className="text-[var(--admin-text-secondary)]">{s.status}</span>
                    <span className="font-semibold text-[var(--admin-text-primary)]">{s.count}</span>
                  </div>
                ))}
                {data.status_breakdown.length === 0 && (
                  <p className="text-sm text-[var(--admin-text-muted)]">Keine Daten.</p>
                )}
              </div>
            </AdminCard>
          </div>
        </div>
      )}
    </div>
  );
}
