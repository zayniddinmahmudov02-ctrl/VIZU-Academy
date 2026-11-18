"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ChevronLeft, ChevronRight, Loader2, X } from "lucide-react";

import { AdminButton, AdminInput, AdminLabel, AdminSelect } from "@/components/admin/admin-ui";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import {
  getDiscountStatistics, getPromoProducts, listOrders, listPromoCodes, listPromoRequests, reviewCourseRequest, reviewPromoRequest,
} from "@/features/admin/services/vizu-pay-service";
import type { AdminOrderItem, PromoRequestItem } from "@/features/admin/types/vizu-pay.types";

const CATEGORY_LABEL: Record<string, string> = { MULTILEVEL: "Multilevel Premium", COURSES: "Kurs", PACKAGES: "Paket", LEGACY: "Premium (alt)" };

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
  const [kind, setKind] = useState<"" | "course" | "multilevel">(courseOnly ? "course" : "");
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQuery({
    queryKey: ["admin-orders-history", courseOnly, kind, status, plan, search, page, dateFilter],
    queryFn: () => listOrders({ page, page_size: 25, status: status || undefined, plan: plan || undefined, search: search || undefined,
      kind: kind || undefined, ...dateFilter }),
  });
  const columns: DataTableColumn<AdminOrderItem>[] = [
    { key: "user", header: "Nutzer", render: (o) => <div><p className="font-medium">{[o.user_first_name, o.user_last_name].filter(Boolean).join(" ") || o.user_username}</p><p className="text-xs text-[var(--admin-text-muted)]">{o.user_email}</p></div> },
    { key: "plan", header: "Produkt", render: (o) => <div><span className="font-semibold">{o.plan_label}</span>{o.product_category && <p className="text-[11px] text-[var(--admin-text-muted)]">{CATEGORY_LABEL[o.product_category] ?? o.product_category}</p>}</div> },
    { key: "amount", header: "Betrag", render: (o) => <div className="whitespace-nowrap"><p className="font-semibold">{money(o.final_amount)}</p>{o.discount_amount > 0 && <p className="text-xs text-[var(--admin-text-muted)]">−{money(o.discount_amount)}{o.promo_code ? ` · ${o.promo_code}` : ""}</p>}</div> },
    { key: "method", header: "Methode", render: (o) => o.payment_method },
    { key: "status", header: "Status", render: (o) => <Badge status={o.status} /> },
    { key: "created", header: "Erstellt", render: (o) => <span className="whitespace-nowrap text-xs">{date(o.created_at)}</span> },
    { key: "access", header: "Zugang bis", render: (o) => <span className="whitespace-nowrap text-xs">{o.access_end_date ? date(o.access_end_date) : o.status === "APPROVED" && o.product_category === "MULTILEVEL" ? "unbegrenzt" : "—"}</span> },
  ];
  return (
    <div data-testid={courseOnly ? "package-purchases-tab" : "payment-history-tab"}>
      <div className="mb-4 grid gap-2 sm:grid-cols-4">
        <AdminInput placeholder="E-Mail / Benutzername" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
        {!courseOnly && (
          <AdminSelect value={kind} onChange={(e) => { setKind(e.target.value as "" | "course" | "multilevel"); setPage(1); }} aria-label="Produkt" data-testid="history-kind">
            <option value="">Alle Produkte</option>
            <option value="course">Kurse und Pakete</option>
            <option value="multilevel">Multilevel Modelltest Premium</option>
          </AdminSelect>
        )}
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

/** Student requests: "Promo so'rovi" (COURSE_REQUEST — approve creates / attaches a code) and codes with requires_approval
 * (CODE_APPROVAL — approve lets the discount apply). Super Admin, audited. */
export function PromoRequestsTab() {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState("PENDING_APPROVAL");
  const [kind, setKind] = useState("");
  const [search, setSearch] = useState("");
  const [plan, setPlan] = useState("");
  const [page, setPage] = useState(1);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approving, setApproving] = useState<PromoRequestItem | null>(null);
  const { data, isLoading } = useQuery({
    queryKey: ["admin-promo-requests", kind, status, search, plan, page],
    queryFn: () => listPromoRequests({ kind: kind || undefined, status: status || undefined, search: search || undefined, plan: plan || undefined, page, page_size: 25 }),
  });

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["admin-promo-requests"] });
    await queryClient.invalidateQueries({ queryKey: ["promo-codes"] });
    await queryClient.invalidateQueries({ queryKey: ["admin-payments-overview"] });
  }

  async function review(item: PromoRequestItem, approve: boolean) {
    const course = item.kind === "COURSE_REQUEST";
    if (approve && course) {
      setApproving(item);
      return;
    }
    const reason = approve ? undefined : window.prompt(`Grund für die Ablehnung (${item.code || item.plan_label}, ${item.user_email}) — optional:`) ?? undefined;
    if (!approve && reason === undefined) return;
    setBusy(item.id);
    setError(null);
    try {
      if (course) await reviewCourseRequest(item.id, { approve: false, reason });
      else await reviewPromoRequest(item.id, approve, reason);
      await refresh();
    } catch (err) {
      setError(apiErrorMessage(err, "Aktion fehlgeschlagen."));
    } finally {
      setBusy(null);
    }
  }

  const columns: DataTableColumn<PromoRequestItem>[] = [
    { key: "user", header: "Nutzer", render: (r) => <div><p className="font-medium">{r.user_name}</p><p className="text-xs text-[var(--admin-text-muted)]">{r.user_email}</p></div> },
    { key: "kind", header: "Art", render: (r) => <span className="whitespace-nowrap text-xs font-semibold">{r.kind === "COURSE_REQUEST" ? "Promo-Anfrage (Kurs)" : "Code-Freigabe"}</span> },
    { key: "code", header: "Promo-Code", render: (r) => r.code ? <div><p className="font-mono font-bold" data-testid="promo-request-code">{r.code}</p><p className="text-xs text-[var(--admin-text-muted)]">{r.discount_type === "PERCENT" ? `${r.discount_value} %` : r.discount_type === "FREE_ACCESS" ? "kostenlos" : r.discount_value != null ? money(r.discount_value) : ""}</p></div> : <span className="text-xs text-[var(--admin-text-muted)]">noch keiner</span> },
    { key: "plan", header: "Kurs / Paket", render: (r) => <div><p>{r.plan_label}</p>{r.message && <p className="mt-0.5 max-w-56 text-xs text-[var(--admin-text-muted)]" data-testid="promo-request-message">„{r.message}“</p>}</div> },
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
        Promo-Anfragen der Studenten für einen Kurs („Promo so‘rovi“) und Codes mit „Freigabe nötig“. Eine Freigabe kauft oder öffnet nichts: Der Student
        muss den Code beim Kauf einlösen; er gilt nur unter den Bedingungen des Codes.
      </p>
      <div className="mb-4 grid gap-2 sm:grid-cols-4">
        <AdminSelect value={kind} onChange={(e) => { setKind(e.target.value); setPage(1); }} aria-label="Art" data-testid="promo-requests-kind">
          <option value="">Alle Arten</option>
          <option value="COURSE_REQUEST">Promo-Anfragen (Kurse)</option>
          <option value="CODE_APPROVAL">Code-Freigaben</option>
        </AdminSelect>
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
      {approving && <CourseRequestDialog key={approving.id} request={approving} onClose={() => setApproving(null)} onDone={() => { setApproving(null); void refresh(); }} />}
    </div>
  );
}

/** Approve a "Promo so'rovi": a new personal code for this student only (approved + ACTIVE at once, 1 use), or an existing approved code. */
function CourseRequestDialog({ request, onClose, onDone }: { request: PromoRequestItem; onClose: () => void; onDone: () => void }) {
  const [mode, setMode] = useState<"create" | "attach">("create");
  const [type, setType] = useState<"PERCENT" | "FIXED" | "FREE_ACCESS">("PERCENT");
  const [value, setValue] = useState(20);
  const [expires, setExpires] = useState("");
  const [promoId, setPromoId] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { data: products } = useQuery({ queryKey: ["promo-products"], queryFn: getPromoProducts });
  const { data: codes = [] } = useQuery({ queryKey: ["promo-codes"], queryFn: listPromoCodes, enabled: mode === "attach" });
  const isPackage = (products?.packages ?? []).some((p) => p.code === request.plan);
  const category = isPackage ? "PACKAGES" : "COURSES";
  const usable = codes.filter((c) => c.approval_status === "ACTIVE" && c.status === "ACTIVE" && (c.product_category ?? "COURSES") === category
    && (!c.assigned_user_id || c.assigned_user_id === request.user_id) && (!isPackage || c.applicable_package_codes.includes(request.plan)));

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await reviewCourseRequest(request.id, mode === "create"
        ? { approve: true, reason: note || null, mode, discount_type: type, discount_value: type === "FREE_ACCESS" ? 100 : value, expires_at: expires ? new Date(expires).toISOString() : null }
        : { approve: true, reason: note || null, mode, promo_code_id: promoId });
      onDone();
    } catch (err) {
      setError(apiErrorMessage(err, "Freigabe fehlgeschlagen."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <FormDialog open onOpenChange={(open) => !open && onClose()} title={`Promo-Anfrage freigeben · ${request.plan_label}`}
      description={`${request.user_name} (${request.user_email})${request.message ? ` — „${request.message}“` : ""}`}
      footer={<>
        <AdminButton variant="ghost" onClick={onClose}>Abbrechen</AdminButton>
        <AdminButton onClick={() => void submit()} disabled={busy || (mode === "attach" && !promoId)} data-testid="course-review-submit">
          {busy ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Freigeben
        </AdminButton>
      </>}>
      <div className="space-y-4" data-testid="course-review-dialog">
        <div className="flex flex-wrap gap-3 text-sm text-[var(--admin-text-primary)]">
          <label className="flex items-center gap-2"><input type="radio" checked={mode === "create"} onChange={() => setMode("create")} data-testid="course-review-create" /> Neuen persönlichen Code erstellen</label>
          <label className="flex items-center gap-2"><input type="radio" checked={mode === "attach"} onChange={() => setMode("attach")} data-testid="course-review-attach" /> Vorhandenen Code zuweisen</label>
        </div>
        {mode === "create" ? (
          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <AdminLabel htmlFor="cr-type">Rabatt</AdminLabel>
              <AdminSelect id="cr-type" value={type} onChange={(e) => setType(e.target.value as "PERCENT" | "FIXED" | "FREE_ACCESS")} data-testid="course-review-type">
                <option value="PERCENT">Prozent</option>
                <option value="FIXED">Betrag (UZS)</option>
                <option value="FREE_ACCESS">Kostenlos (100 %)</option>
              </AdminSelect>
            </div>
            {type !== "FREE_ACCESS" && (
              <div>
                <AdminLabel htmlFor="cr-value">{type === "PERCENT" ? "Prozent (1–100)" : "Betrag (UZS)"}</AdminLabel>
                <AdminInput id="cr-value" type="number" min={1} max={type === "PERCENT" ? 100 : undefined} value={value} onChange={(e) => setValue(Number(e.target.value))} data-testid="course-review-value" />
              </div>
            )}
            <div>
              <AdminLabel htmlFor="cr-expires">Gültig bis (optional)</AdminLabel>
              <AdminInput id="cr-expires" type="datetime-local" value={expires} onChange={(e) => setExpires(e.target.value)} />
            </div>
            <p className="text-xs text-[var(--admin-text-muted)] sm:col-span-3">
              Der Code gilt nur für diesen Studenten und nur für {request.plan_label}, einmal. Mit dieser Freigabe ist er sofort aktiv (Ihre Freigabe ist die Admin-Freigabe).
            </p>
          </div>
        ) : (
          <div>
            <AdminLabel htmlFor="cr-code">Freigegebener, aktiver Code ({category === "PACKAGES" ? "Paket" : "Kurs"})</AdminLabel>
            <AdminSelect id="cr-code" value={promoId} onChange={(e) => setPromoId(e.target.value)} data-testid="course-review-code">
              <option value="">Bitte wählen</option>
              {usable.map((c) => <option key={c.id} value={c.id}>{c.code} · {c.discount_type === "PERCENT" ? `${c.discount_value} %` : c.discount_type}</option>)}
            </AdminSelect>
            {usable.length === 0 && <p className="mt-1 text-xs text-[var(--admin-text-muted)]">Kein passender aktiver Code — einen neuen erstellen.</p>}
          </div>
        )}
        <div>
          <AdminLabel htmlFor="cr-note">Nachricht an den Studenten (optional)</AdminLabel>
          <AdminInput id="cr-note" maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
        {error && <p className="rounded-lg bg-[var(--admin-danger)]/10 p-3 text-sm text-[var(--admin-danger)]" role="alert">{error}</p>}
      </div>
    </FormDialog>
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
