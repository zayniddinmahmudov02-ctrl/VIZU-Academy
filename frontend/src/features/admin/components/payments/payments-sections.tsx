"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Save } from "lucide-react";

import { AdminButton, AdminInput, AdminLabel, AdminSelect } from "@/components/admin/admin-ui";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import { getPaymentSettings, getPaymentsOverview, listMlEntitlements, updatePaymentSettings } from "@/features/admin/services/vizu-pay-service";
import type { MlEntitlementItem, PaymentSettings } from "@/features/admin/types/vizu-pay.types";

import { DiscountStatsTab } from "./payment-tabs";

const money = (v: number) => `${new Intl.NumberFormat("de-DE").format(v)} UZS`;
const date = (v: string | null) => (v ? new Date(v).toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" }) : "—");

function Tile({ label, value, testId, tone }: { label: string; value: string | number; testId?: string; tone?: "warning" | "success" }) {
  const color = tone === "warning" ? "text-[var(--admin-warning)]" : tone === "success" ? "text-[var(--admin-success)]" : "text-[var(--admin-text-primary)]";
  return (
    <div className="min-w-0 rounded-2xl bg-[var(--admin-card)] p-3.5 ring-1 ring-[var(--admin-border)]" data-testid={testId}>
      <p className="text-xs text-[var(--admin-text-muted)]">{label}</p>
      <p className={`mt-1.5 truncate text-lg font-bold ${color}`} title={String(value)}>{value}</p>
    </div>
  );
}

/** Admin -> Payments -> Overview: every figure counted from the database on each load (GET /admin/vizu-pay/overview). */
export function PaymentsOverviewTab() {
  const { data, isLoading, isError, error } = useQuery({ queryKey: ["admin-payments-overview"], queryFn: getPaymentsOverview });
  if (isLoading) return <Loader2 className="animate-spin text-[var(--admin-text-muted)]" />;
  if (isError || !data) return <p className="rounded-xl bg-[var(--admin-danger)]/10 p-4 text-sm text-[var(--admin-danger)]">{apiErrorMessage(error, "Übersicht konnte nicht geladen werden.")}</p>;
  return (
    <div className="space-y-6" data-testid="payments-overview">
      <section>
        <h3 className="mb-2 text-sm font-semibold text-[var(--admin-text-primary)]">Zahlungen</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
          <Tile label="Zahlungen gesamt" value={data.payments.total} testId="ov-total" />
          <Tile label="Genehmigt" value={data.payments.approved} tone="success" testId="ov-approved" />
          <Tile label="Wartend" value={data.payments.pending} tone="warning" testId="ov-pending" />
          <Tile label="Abgelehnt" value={data.payments.rejected} testId="ov-rejected" />
          <Tile label="Abgelaufen" value={data.payments.expired} />
          <Tile label="Erstattet" value={data.payments.refunded} />
        </div>
      </section>
      <section>
        <h3 className="mb-2 text-sm font-semibold text-[var(--admin-text-primary)]">Käufe und Zugänge</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
          <Tile label="Kurskäufe (genehmigt)" value={data.course_purchases} testId="ov-course" />
          <Tile label="Kurs-Käufer" value={data.course_buyers} />
          <Tile label="Modelltest Premium (bezahlt)" value={data.multilevel_purchases} testId="ov-ml" />
          <Tile label="Modelltest Premium aktiv" value={data.multilevel_active} tone="success" testId="ov-ml-active" />
          <Tile label="Zugänge per Promo-Code" value={data.promo_accesses.total} testId="ov-promo" />
          <Tile label="… davon Kurse / Multilevel" value={`${data.promo_accesses.course} / ${data.promo_accesses.multilevel}`} />
        </div>
      </section>
      <section>
        <h3 className="mb-2 text-sm font-semibold text-[var(--admin-text-primary)]">Umsatz und offene Aufgaben</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
          <Tile label="Umsatz gesamt" value={money(data.revenue.total)} />
          <Tile label="Umsatz Kurse" value={money(data.revenue.course)} />
          <Tile label="Umsatz Modelltest Premium" value={money(data.revenue.multilevel)} />
          <Tile label="Wartend: Kurse / Multilevel" value={`${data.pending.course} / ${data.pending.multilevel}`} tone="warning" />
          <Tile label="Promo-Codes zur Freigabe" value={data.promo_codes.PENDING} tone="warning" testId="ov-promo-pending" />
          <Tile label="Offene Promo-Anfragen" value={data.promo_requests_open.code_approval + data.promo_requests_open.course_request} tone="warning" />
        </div>
      </section>
      <section>
        <h3 className="mb-2 text-sm font-semibold text-[var(--admin-text-primary)]">Rabatte</h3>
        <DiscountStatsTab />
      </section>
    </div>
  );
}

/** Students with an active (or, optionally, revoked) Multilevel Modelltest Premium. */
export function MlEntitlementsList() {
  const [search, setSearch] = useState("");
  const [revoked, setRevoked] = useState(false);
  const { data, isLoading } = useQuery({
    queryKey: ["admin-ml-entitlements", search, revoked],
    queryFn: () => listMlEntitlements({ search: search || undefined, include_revoked: revoked }),
  });
  const columns: DataTableColumn<MlEntitlementItem>[] = [
    { key: "user", header: "Student", render: (e) => <div><p className="font-medium">{e.user_name}</p><p className="text-xs text-[var(--admin-text-muted)]">{e.user_email}</p></div> },
    { key: "source", header: "Quelle", render: (e) => (e.source === "PROMO" ? `Promo-Code${e.promo_code ? ` · ${e.promo_code}` : ""}` : "Zahlung (genehmigt)") },
    { key: "granted", header: "Seit", render: (e) => <span className="whitespace-nowrap text-xs">{date(e.granted_at)}</span> },
    { key: "state", header: "Status", render: (e) => (e.revoked_at ? <span className="text-xs text-[var(--admin-danger)]">Entzogen {date(e.revoked_at)}{e.revoke_reason ? ` · ${e.revoke_reason}` : ""}</span> : <span className="text-xs font-semibold text-[var(--admin-success)]">Aktiv · unbegrenzt</span>) },
  ];
  return (
    <section className="space-y-3" data-testid="ml-entitlements">
      <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">Premium-Inhaber (alle 10 Modelltests)</h3>
      <div className="grid gap-2 sm:grid-cols-[minmax(0,20rem)_auto] sm:items-center">
        <AdminInput placeholder="E-Mail / Benutzername" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Premium-Inhaber suchen" />
        <label className="flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]">
          <input type="checkbox" checked={revoked} onChange={(e) => setRevoked(e.target.checked)} /> auch entzogene zeigen
        </label>
      </div>
      <DataTable columns={columns} data={data} isLoading={isLoading} getRowId={(e) => e.id} emptyMessage="Noch niemand hat den Multilevel Premium." />
    </section>
  );
}

/** Admin -> Payments -> Payment Settings: the card (read only — plans.PAYMENT_CARDS) and the Multilevel Premium price / sale status. */
export function PaymentSettingsTab() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["admin-payment-settings"], queryFn: getPaymentSettings });
  if (isLoading || !data) return <Loader2 className="animate-spin text-[var(--admin-text-muted)]" />;
  return <SettingsForm key={`${data.multilevel.price}:${data.multilevel.status}`} data={data} onSaved={() => {
    void queryClient.invalidateQueries({ queryKey: ["admin-payment-settings"] });
    void queryClient.invalidateQueries({ queryKey: ["promo-products"] });
    void queryClient.invalidateQueries({ queryKey: ["admin-payments-overview"] });
  }} />;
}

function SettingsForm({ data, onSaved }: { data: PaymentSettings; onSaved: () => void }) {
  const [price, setPrice] = useState(data.multilevel.price);
  const [status, setStatus] = useState(data.multilevel.status);
  const save = useMutation({ mutationFn: () => updatePaymentSettings({ multilevel_price: price, multilevel_status: status }), onSuccess: onSaved });
  const changed = price !== data.multilevel.price || status !== data.multilevel.status;
  return (
    <div className="grid gap-4 lg:grid-cols-2" data-testid="payment-settings">
      <section className="space-y-3 rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)]">
        <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">Zahlungskarte</h3>
        {data.cards.map((card) => (
          <div key={card.number} className="rounded-xl bg-white/5 px-3 py-2">
            <p className="text-xs text-[var(--admin-text-muted)]">{card.label}</p>
            <p className="font-mono text-base font-bold text-[var(--admin-text-primary)]" data-testid="settings-card">{card.number.replace(/(\d{4})(?=\d)/g, "$1 ")}</p>
          </div>
        ))}
        <p className="text-xs text-[var(--admin-text-muted)]">
          Die Karte ist im Code festgelegt (identisch mit dem Telegram-Bot) und wird hier nur angezeigt. Kurs-Anfragen verfallen nach {data.review_window_days} Tagen ohne Prüfung;
          nach {data.max_rejections} Ablehnungen sind neue Anfragen gesperrt. Kurspreise: Admin → Angebote.
        </p>
      </section>
      <section className="space-y-3 rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)]">
        <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">{data.multilevel.label}</h3>
        <p className="text-xs text-[var(--admin-text-muted)]">Ein Kauf öffnet alle 10 Multilevel-Modelltests, unbegrenzt. Bestehende Anfragen behalten ihren Betrag.</p>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <AdminLabel htmlFor="ml-price">Preis (UZS)</AdminLabel>
            <AdminInput id="ml-price" type="number" min={1000} max={10_000_000} step={1000} value={price} data-testid="settings-ml-price"
              onChange={(e) => setPrice(Number(e.target.value))} />
            <p className="mt-1 text-[11px] text-[var(--admin-text-muted)]">Standard: {money(data.multilevel.default_price)}</p>
          </div>
          <div>
            <AdminLabel htmlFor="ml-status">Verkauf</AdminLabel>
            <AdminSelect id="ml-status" value={status} onChange={(e) => setStatus(e.target.value as "ACTIVE" | "DISABLED")} data-testid="settings-ml-status">
              <option value="ACTIVE">Aktiv (wird verkauft)</option>
              <option value="DISABLED">Gestoppt</option>
            </AdminSelect>
          </div>
        </div>
        {save.isError && <p className="text-sm text-[var(--admin-danger)]" role="alert">{apiErrorMessage(save.error, "Speichern fehlgeschlagen.")}</p>}
        <AdminButton onClick={() => save.mutate()} disabled={!changed || save.isPending || !(price >= 1000 && price <= 10_000_000)} data-testid="settings-save">
          {save.isPending ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />} Speichern (Audit-Log)
        </AdminButton>
      </section>
    </div>
  );
}
