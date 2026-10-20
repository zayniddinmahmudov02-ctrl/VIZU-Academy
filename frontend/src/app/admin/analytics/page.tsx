"use client";

import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { AdminButton, AdminCard, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import MiniBarChart from "@/components/admin/mini-bar-chart";
import { getRevenueOverview, listOrders } from "@/features/admin/services/vizu-pay-service";
import type { AdminOrderItem } from "@/features/admin/types/vizu-pay.types";

const ORDERS_PAGE_SIZE = 20;

const STATUS_STYLES: Record<string, { label: string; className: string }> = {
  APPROVED: { label: "Bestätigt", className: "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]" },
  PENDING: { label: "Offen", className: "bg-[var(--admin-warning)]/15 text-[var(--admin-warning)]" },
  REJECTED: { label: "Abgelehnt", className: "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]" },
  REFUNDED: { label: "Erstattet", className: "bg-white/10 text-[var(--admin-text-secondary)]" },
  EXPIRED: { label: "Abgelaufen", className: "bg-white/10 text-[var(--admin-text-muted)]" },
};

function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? { label: status, className: "bg-white/10 text-[var(--admin-text-secondary)]" };
  return <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${style.className}`}>{style.label}</span>;
}

function StatBlock({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <AdminCard>
      <p className="text-xs font-medium uppercase tracking-wide text-[var(--admin-text-muted)]">{label}</p>
      <p className="mt-1 text-xl font-bold text-[var(--admin-text-primary)]">{value}</p>
      {hint && <p className="mt-0.5 text-[11px] text-[var(--admin-text-muted)]">{hint}</p>}
    </AdminCard>
  );
}

function fmtDate(value: string | null): string {
  return value ? new Date(value).toLocaleDateString("de-DE") : "—";
}

function CoursePurchasesTable() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("APPROVED");

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-course-orders", page, status],
    queryFn: () => listOrders({ page, page_size: ORDERS_PAGE_SIZE, kind: "course", status: status || undefined }),
    placeholderData: keepPreviousData,
  });

  const columns: DataTableColumn<AdminOrderItem>[] = [
    {
      key: "student",
      header: "Student",
      render: (o) => (
        <div>
          <p className="font-medium">
            {[o.user_first_name, o.user_last_name].filter(Boolean).join(" ") || o.user_username}
          </p>
          <p className="text-xs text-[var(--admin-text-muted)]">{o.user_email}</p>
        </div>
      ),
    },
    { key: "course", header: "Kurs / Level", render: (o) => <span className="font-medium">Kurs {o.plan_label}</span> },
    { key: "created_at", header: "Bestellt", render: (o) => fmtDate(o.created_at) },
    {
      key: "purchased_at",
      header: "Kaufdatum (bestätigt)",
      render: (o) => (o.status === "APPROVED" ? fmtDate(o.reviewed_at) : "—"),
    },
    {
      key: "amount",
      header: "Betrag",
      render: (o) => `${o.final_amount.toLocaleString("de-DE")} ${o.currency}`,
    },
    { key: "status", header: "Zahlungsstatus", render: (o) => <StatusBadge status={o.status} /> },
  ];

  return (
    <AdminCard>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">Kurskäufe</h3>
          <p className="text-xs text-[var(--admin-text-muted)]">
            Nur bestätigte Bestellungen zählen als Kauf und Umsatz.
          </p>
        </div>
        <AdminSelect
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
          }}
          className="w-48"
          aria-label="Zahlungsstatus"
        >
          <option value="APPROVED">Bestätigt (Käufe)</option>
          <option value="PENDING">Offen</option>
          <option value="REJECTED">Abgelehnt</option>
          <option value="REFUNDED">Erstattet</option>
          <option value="EXPIRED">Abgelaufen</option>
          <option value="">Alle Bestellungen</option>
        </AdminSelect>
      </div>

      {isError ? (
        <p className="text-sm text-[var(--admin-danger)]">
          Kurskäufe konnten nicht geladen werden.{" "}
          <button onClick={() => refetch()} className="text-xs text-[var(--admin-primary)] hover:underline">
            Erneut versuchen
          </button>
        </p>
      ) : (
        <DataTable
          columns={columns}
          data={data?.items}
          isLoading={isLoading}
          getRowId={(o) => o.id}
          emptyMessage="Keine Kurs-Bestellungen mit diesem Status."
        />
      )}

      {data && data.total_pages > 1 && (
        <div className="mt-4 flex items-center justify-between text-sm text-[var(--admin-text-secondary)]">
          <span>
            Seite {data.page} von {data.total_pages} ({data.total} Bestellungen)
          </span>
          <div className="flex gap-2">
            <AdminButton variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              <ChevronLeft size={14} />
            </AdminButton>
            <AdminButton
              variant="secondary"
              size="sm"
              disabled={page >= data.total_pages}
              onClick={() => setPage((p) => p + 1)}
            >
              <ChevronRight size={14} />
            </AdminButton>
          </div>
        </div>
      )}
    </AdminCard>
  );
}

export default function AnalyticsPage() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["revenue-overview"],
    queryFn: getRevenueOverview,
  });

  const uzs = (value: number) => `${value.toLocaleString("de-DE")} UZS`;

  return (
    <div>
      <AdminPageHeader
        title="Analytics"
        description="Umsatz, Kurskäufe und zahlende Nutzer — nur bestätigte Zahlungen zählen."
      />

      {isLoading && (
        <div className="flex justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-white/10 border-t-[var(--admin-primary)]" />
        </div>
      )}

      {isError && (
        <AdminCard>
          <p className="text-sm text-[var(--admin-danger)]">Analytics-Daten konnten nicht geladen werden.</p>
          <button onClick={() => refetch()} className="mt-1 text-xs text-[var(--admin-primary)] hover:underline">
            Erneut versuchen
          </button>
        </AdminCard>
      )}

      {data && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatBlock label="Umsatz gesamt" value={uzs(data.total_revenue)} hint="bestätigte Zahlungen" />
            <StatBlock label="Umsatz (Monat)" value={uzs(data.revenue_this_month)} />
            <StatBlock label="Umsatz (Heute)" value={uzs(data.revenue_today)} />
            <StatBlock label="Offene Bestellungen" value={data.pending_orders} hint="nicht im Umsatz" />
            <StatBlock label="Zahlende Nutzer" value={data.paying_users ?? 0} hint="Kurskäufer oder Premium aktiv" />
            <StatBlock label="Kurskäufer" value={data.course_buyers ?? 0} hint="Studenten mit bestätigtem Kurs" />
            <StatBlock label="Kurskäufe" value={data.course_purchases ?? 0} hint="bestätigte Kurs-Bestellungen" />
            <StatBlock label="Premium aktiv" value={data.premium_active ?? 0} hint={`${data.total_orders} Bestellungen gesamt`} />
          </div>

          <AdminCard>
            <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">Monatlicher Umsatz</h3>
            {data.monthly_revenue_chart.length > 0 ? (
              <MiniBarChart data={data.monthly_revenue_chart} formatValue={uzs} />
            ) : (
              <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">Noch keine Daten.</p>
            )}
          </AdminCard>

          <CoursePurchasesTable />

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <AdminCard>
              <h3 className="mb-3 text-sm font-semibold text-[var(--admin-text-primary)]">Nach Kurs / Plan</h3>
              <div className="space-y-2">
                {data.plan_breakdown.map((p) => (
                  <div key={p.plan} className="flex justify-between gap-2 text-sm">
                    <span className="text-[var(--admin-text-secondary)]">
                      {p.is_course ? `Kurs ${p.label}` : p.label}
                      {p.is_course && p.levels?.length > 0 && (
                        <span className="ml-1 text-xs text-[var(--admin-text-muted)]">({p.levels.join(", ")})</span>
                      )}
                    </span>
                    <span className="text-right font-semibold text-[var(--admin-text-primary)]">
                      {p.revenue.toLocaleString("de-DE")}
                      <span className="block text-[11px] font-normal text-[var(--admin-text-muted)]">
                        {p.orders} Käufe · {p.buyers ?? 0} Studenten
                      </span>
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
                      {m.revenue.toLocaleString("de-DE")} ({m.orders})
                    </span>
                  </div>
                ))}
                {data.method_breakdown.length === 0 && (
                  <p className="text-sm text-[var(--admin-text-muted)]">Keine Daten.</p>
                )}
              </div>
            </AdminCard>

            <AdminCard>
              <h3 className="mb-3 text-sm font-semibold text-[var(--admin-text-primary)]">Bestellungen nach Status</h3>
              <div className="space-y-2">
                {data.status_breakdown.map((s) => (
                  <div key={s.status} className="flex items-center justify-between text-sm">
                    <StatusBadge status={s.status} />
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
