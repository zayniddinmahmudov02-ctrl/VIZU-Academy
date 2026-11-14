"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ChevronLeft, ChevronRight, Loader2, X } from "lucide-react";

import { AdminButton, AdminInput, AdminSelect } from "@/components/admin/admin-ui";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import { getDiscountStatistics, listOrders, listPromoRequests, reviewPromoRequest } from "@/features/admin/services/vizu-pay-service";
import type { AdminOrderItem, PromoRequestItem } from "@/features/admin/types/vizu-pay.types";

const money = (v: number) => `${new Intl.NumberFormat("de-DE").format(v)} UZS`;
const date = (v: string | null) => (v ? new Date(v).toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" }) : "—");
const STATUS_STYLE: Record<string, string> = {
  PENDING: "bg-[var(--admin-warning)]/15 text-[var(--admin-warning)]",
  PENDING_APPROVAL: "bg-[var(--admin-warning)]/15 text-[var(--admin-warning)]",
  APPROVED: "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]",
  USED: "bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]",
  REJECTED: "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]",
  EXPIRED: "bg-white/5 text-[var(--admin-text-muted)]",
  DISABLED: "bg-white/5 text-[var(--admin-text-muted)]",
  REFUNDED: "bg-white/5 text-[var(--admin-text-muted)]",
};
const Badge = ({ status }: { status: string }) => (
  <span className={`whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold ${STATUS_STYLE[status] ?? "bg-white/5 text-[var(--admin-text-muted)]"}`}>{status}</span>
);

function Pager({ page, totalPages, total, onPage }: { page: number; totalPages: number; total: number; onPage: (p: number) => void }) {
  if (totalPages <= 1) return <p className="mt-3 text-xs text-[var(--admin-text-muted)]">{total} Einträge</p>;
  return (
    <div className="mt-3 flex items-center justify-between text-sm text-[var(--admin-text-secondary)]">
      <span>{total} Einträge · {page} / {totalPages}</span>
      <div className="flex gap-2">
        <AdminButton variant="secondary" size="sm" disabled={page <= 1} onClick={() => onPage(page - 1)}><ChevronLeft size={14} /></AdminButton>
        <AdminButton variant="secondary" size="sm" disabled={page >= totalPages} onClick={() => onPage(page + 1)}><ChevronRight size={14} /></AdminButton>
      </div>
    </div>
  );
}

/** Payment history (every order, all statuses) — or, with `courseOnly`, the package purchases. */
export function OrdersHistoryTab({ courseOnly = false, dateFilter }: { courseOnly?: boolean; dateFilter: { year?: number; month?: number; day?: number } }) {
  const [status, setStatus] = useState(courseOnly ? "APPROVED" : "");
  const [plan, setPlan] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQuery({
    queryKey: ["admin-orders-history", courseOnly, status, plan, search, page, dateFilter],
    queryFn: () => listOrders({ page, page_size: 25, status: status || undefined, plan: plan || undefined, search: search || undefined,
      kind: courseOnly ? "course" : undefined, ...dateFilter }),
  });
  const columns: DataTableColumn<AdminOrderItem>[] = [
    { key: "user", header: "Nutzer", render: (o) => <div><p className="font-medium">{[o.user_first_name, o.user_last_name].filter(Boolean).join(" ") || o.user_username}</p><p className="text-xs text-[var(--admin-text-muted)]">{o.user_email}</p></div> },
    { key: "plan", header: "Paket", render: (o) => <span className="font-semibold">{o.plan_label}</span> },
    { key: "amount", header: "Betrag", render: (o) => <div className="whitespace-nowrap"><p className="font-semibold">{money(o.final_amount)}</p>{o.discount_amount > 0 && <p className="text-xs text-[var(--admin-text-muted)]">−{money(o.discount_amount)}{o.promo_code ? ` · ${o.promo_code}` : ""}</p>}</div> },
    { key: "method", header: "Methode", render: (o) => o.payment_method },
    { key: "status", header: "Status", render: (o) => <Badge status={o.status} /> },
    { key: "created", header: "Erstellt", render: (o) => <span className="whitespace-nowrap text-xs">{date(o.created_at)}</span> },
    { key: "access", header: "Zugang bis", render: (o) => <span className="whitespace-nowrap text-xs">{o.access_end_date ? date(o.access_end_date) : "—"}</span> },
  ];
  return (
    <div data-testid={courseOnly ? "package-purchases-tab" : "payment-history-tab"}>
      <div className="mb-4 grid gap-2 sm:grid-cols-4">
        <AdminInput placeholder="E-Mail / Benutzername" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
        <AdminSelect value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} aria-label="Status">
          <option value="">Alle Status</option>
          {["PENDING", "APPROVED", "REJECTED", "EXPIRED", "REFUNDED"].map((s) => <option key={s} value={s}>{s}</option>)}
        </AdminSelect>
        <AdminInput placeholder="Paket-Code (z. B. A1_B1)" value={plan} onChange={(e) => { setPlan(e.target.value.toUpperCase()); setPage(1); }} />
      </div>
      <DataTable columns={columns} data={data?.items} isLoading={isLoading} getRowId={(o) => o.id} emptyMessage="Keine Zahlungen gefunden." />
      {data && <Pager page={data.page} totalPages={data.total_pages} total={data.total} onPage={setPage} />}
    </div>
  );
}

/** Promo codes with requires_approval: each student's request, approve / reject (Super Admin, audited). */
export function PromoRequestsTab() {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState("PENDING_APPROVAL");
  const [search, setSearch] = useState("");
  const [plan, setPlan] = useState("");
  const [page, setPage] = useState(1);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { data, isLoading } = useQuery({
    queryKey: ["admin-promo-requests", status, search, plan, page],
    queryFn: () => listPromoRequests({ status: status || undefined, search: search || undefined, plan: plan || undefined, page, page_size: 25 }),
  });

  async function review(item: PromoRequestItem, approve: boolean) {
    const reason = approve ? undefined : window.prompt(`Grund für die Ablehnung von ${item.code} (${item.user_email}) — optional:`) ?? undefined;
    if (!approve && reason === undefined) return;
    setBusy(item.id);
    setError(null);
    try {
      await reviewPromoRequest(item.id, approve, reason);
      await queryClient.invalidateQueries({ queryKey: ["admin-promo-requests"] });
      await queryClient.invalidateQueries({ queryKey: ["promo-codes"] });
    } catch (err) {
      setError(apiErrorMessage(err, "Aktion fehlgeschlagen."));
    } finally {
      setBusy(null);
    }
  }

  const columns: DataTableColumn<PromoRequestItem>[] = [
    { key: "user", header: "Nutzer", render: (r) => <div><p className="font-medium">{r.user_name}</p><p className="text-xs text-[var(--admin-text-muted)]">{r.user_email}</p></div> },
    { key: "code", header: "Promo-Code", render: (r) => <div><p className="font-mono font-bold">{r.code}</p><p className="text-xs text-[var(--admin-text-muted)]">{r.discount_type === "PERCENT" ? `${r.discount_value} %` : r.discount_value != null ? money(r.discount_value) : ""}</p></div> },
    { key: "plan", header: "Paket", render: (r) => r.plan_label },
    { key: "status", header: "Status", render: (r) => <div><Badge status={r.status} />{r.reason && <p className="mt-1 max-w-48 text-xs text-[var(--admin-text-muted)]">{r.reason}</p>}</div> },
    { key: "created", header: "Angefragt", render: (r) => <span className="whitespace-nowrap text-xs">{date(r.created_at)}</span> },
    { key: "reviewed", header: "Geprüft", render: (r) => <span className="whitespace-nowrap text-xs">{r.reviewed_at ? `${date(r.reviewed_at)}${r.reviewed_by_email ? ` · ${r.reviewed_by_email}` : ""}` : "—"}</span> },
    {
      key: "actions", header: "", render: (r) => r.status !== "PENDING_APPROVAL" ? null : (
        <div className="flex gap-1.5">
          <AdminButton size="sm" onClick={() => void review(r, true)} disabled={busy === r.id} data-testid="promo-request-approve">
            {busy === r.id ? <Loader2 size={13} className="animate-spin" /> : <Check size={13} />} Freigeben
          </AdminButton>
          <AdminButton size="sm" variant="danger" onClick={() => void review(r, false)} disabled={busy === r.id} data-testid="promo-request-reject"><X size={13} /> Ablehnen</AdminButton>
        </div>
      ),
    },
  ];
  return (
    <div data-testid="promo-requests-tab">
      <p className="mb-3 text-sm text-[var(--admin-text-secondary)]">
        Promo-Codes mit „Freigabe nötig“: Der Rabatt gilt erst nach der Freigabe — und nur unter den Bedingungen des Codes (Laufzeit, Limits, Pakete).
      </p>
      <div className="mb-4 grid gap-2 sm:grid-cols-4">
        <AdminSelect value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} aria-label="Status">
          <option value="">Alle</option>
          {["PENDING_APPROVAL", "APPROVED", "REJECTED", "USED"].map((s) => <option key={s} value={s}>{s}</option>)}
        </AdminSelect>
        <AdminInput placeholder="E-Mail / Benutzername" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
        <AdminInput placeholder="Paket-Code" value={plan} onChange={(e) => { setPlan(e.target.value.toUpperCase()); setPage(1); }} />
      </div>
      {error && <p className="mb-3 rounded-lg bg-[var(--admin-danger)]/10 p-3 text-sm text-[var(--admin-danger)]">{error}</p>}
      <DataTable columns={columns} data={data?.items} isLoading={isLoading} getRowId={(r) => r.id} emptyMessage="Keine Anfragen." />
      {data && <Pager page={data.page} totalPages={data.total_pages} total={data.total} onPage={setPage} />}
    </div>
  );
}

/** Discounts granted on paid (APPROVED) orders: promo codes, medal rewards, per code and per package. */
export function DiscountStatsTab() {
  const { data, isLoading } = useQuery({ queryKey: ["admin-discount-stats"], queryFn: getDiscountStatistics });
  if (isLoading || !data) return <Loader2 className="animate-spin text-[var(--admin-text-muted)]" />;
  const tiles: [string, string | number][] = [
    ["Rabatte gesamt", money(data.total_discount)],
    ["davon Promo-Codes", money(data.promo_discount)],
    ["davon Medaillen", money(data.reward_discount)],
    ["Bestellungen mit Promo", data.orders_with_promo],
    ["Anfragen offen", data.requests.PENDING_APPROVAL],
    ["Anfragen freigegeben", data.requests.APPROVED + data.requests.USED],
    ["Anfragen abgelehnt", data.requests.REJECTED],
  ];
  return (
    <div className="space-y-5" data-testid="discount-stats-tab">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 xl:grid-cols-7">
        {tiles.map(([label, value]) => (
          <div key={label} className="rounded-2xl bg-[var(--admin-card)] p-3.5 ring-1 ring-[var(--admin-border)]">
            <p className="text-xs text-[var(--admin-text-muted)]">{label}</p>
            <p className="mt-1.5 truncate text-lg font-bold text-[var(--admin-text-primary)]">{value}</p>
          </div>
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {[
          { title: "Nach Promo-Code", rows: data.by_code.map((r) => [r.code, r.orders, money(r.discount), money(r.revenue)]) },
          { title: "Nach Paket", rows: data.by_package.map((r) => [r.label, r.orders, money(r.discount), money(r.revenue)]) },
        ].map(({ title, rows }) => (
          <div key={title} className="overflow-x-auto rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)]">
            <h3 className="mb-2 text-sm font-semibold text-[var(--admin-text-primary)]">{title}</h3>
            <table className="w-full min-w-[380px] text-left text-sm text-[var(--admin-text-primary)]">
              <thead className="text-xs text-[var(--admin-text-muted)]"><tr><th className="py-1.5">Name</th><th>Bestellungen</th><th>Rabatt</th><th>Umsatz</th></tr></thead>
              <tbody>
                {rows.length === 0 && <tr><td colSpan={4} className="py-3 text-xs text-[var(--admin-text-muted)]">Noch keine Daten.</td></tr>}
                {rows.map((r) => <tr key={String(r[0])} className="border-t border-[var(--admin-border)]">{r.map((c, i) => <td key={i} className="py-1.5">{c}</td>)}</tr>)}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    </div>
  );
}
