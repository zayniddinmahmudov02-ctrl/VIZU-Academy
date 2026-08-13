"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Calendar, Loader2, Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminInput, AdminLabel, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import AdminTabs from "@/components/admin/admin-tabs";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import BuyerCard from "@/features/admin/components/payments/buyer-card";
import HistoryDialog from "@/features/admin/components/payments/history-dialog";
import ReceiptViewer from "@/features/admin/components/payments/receipt-viewer";
import RejectDialog from "@/features/admin/components/payments/reject-dialog";
import { listPayments, type PaymentItem } from "@/features/admin/services/payment-service";
import {
  approveOrder,
  createPromoCode,
  deletePromoCode,
  listBlockedUsers,
  listOrders,
  listPromoCodes,
  rejectOrder,
  togglePromoCode,
} from "@/features/admin/services/vizu-pay-service";
import type { AdminOrderItem, BlockedUserItem, PromoCodeItem } from "@/features/admin/types/vizu-pay.types";

const STATUS_STYLE: Record<string, string> = {
  pending: "bg-[var(--admin-warning)]/15 text-[var(--admin-warning)]",
  approved: "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]",
  rejected: "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]",
  refunded: "bg-white/5 text-[var(--admin-text-muted)]",
};

interface DateFilter {
  year?: number;
  month?: number;
  day?: number;
}

function DateFilterBar({ filter, onChange }: { filter: DateFilter; onChange: (f: DateFilter) => void }) {
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 6 }, (_, i) => currentYear - i);

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      <Calendar size={15} className="text-[var(--admin-text-muted)]" />
      <AdminSelect
        value={filter.year ?? ""}
        onChange={(e) => onChange({ ...filter, year: e.target.value ? Number(e.target.value) : undefined })}
        className="w-28"
      >
        <option value="">Jahr</option>
        {years.map((y) => (
          <option key={y} value={y}>
            {y}
          </option>
        ))}
      </AdminSelect>
      <AdminSelect
        value={filter.month ?? ""}
        onChange={(e) => onChange({ ...filter, month: e.target.value ? Number(e.target.value) : undefined })}
        className="w-32"
        disabled={!filter.year}
      >
        <option value="">Monat</option>
        {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
          <option key={m} value={m}>
            {String(m).padStart(2, "0")}
          </option>
        ))}
      </AdminSelect>
      <AdminSelect
        value={filter.day ?? ""}
        onChange={(e) => onChange({ ...filter, day: e.target.value ? Number(e.target.value) : undefined })}
        className="w-28"
        disabled={!filter.month}
      >
        <option value="">Tag</option>
        {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
          <option key={d} value={d}>
            {String(d).padStart(2, "0")}
          </option>
        ))}
      </AdminSelect>
      {(filter.year || filter.month || filter.day) && (
        <AdminButton variant="ghost" size="sm" onClick={() => onChange({})}>
          Zurücksetzen
        </AdminButton>
      )}
    </div>
  );
}

const BUYER_SUB_TABS = [
  { value: "PENDING", label: "New Buyers" },
  { value: "APPROVED", label: "Approved" },
  { value: "REJECTED", label: "Rejected" },
  { value: "BLOCKED", label: "Blocked" },
] as const;

type BuyerSubTab = (typeof BUYER_SUB_TABS)[number]["value"];

function BlockedUserCard({ user, onViewHistory }: { user: BlockedUserItem; onViewHistory: () => void }) {
  const name = [user.user_first_name, user.user_last_name].filter(Boolean).join(" ") || user.user_username;

  return (
    <div className="flex flex-col gap-3 rounded-2xl bg-[var(--admin-card)] p-4 shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-danger)]/30">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-semibold text-[var(--admin-text-primary)]">{name}</p>
          <p className="text-xs text-[var(--admin-text-muted)]">{user.user_email}</p>
          {user.user_phone_number && (
            <p className="mt-1 text-xs text-[var(--admin-text-secondary)]">{user.user_phone_number}</p>
          )}
        </div>
        <span className="shrink-0 rounded-full bg-[var(--admin-danger)]/15 px-2.5 py-1 text-xs font-semibold text-[var(--admin-danger)]">
          BLOCKED
        </span>
      </div>

      <p className="text-xs font-medium text-[var(--admin-danger)]">
        {user.rejection_count}/3 Ablehnungen
        {user.last_rejected_at && ` · Zuletzt: ${new Date(user.last_rejected_at).toLocaleDateString("de-DE")}`}
      </p>

      <button
        onClick={onViewHistory}
        className="w-fit rounded-lg ring-1 ring-[var(--admin-border-strong)] px-3 py-1.5 text-xs font-semibold text-[var(--admin-text-secondary)] transition hover:bg-[var(--admin-hover)]"
      >
        Verlauf ansehen
      </button>
    </div>
  );
}

function NewBuyersSection({ dateFilter }: { dateFilter: DateFilter }) {
  const queryClient = useQueryClient();
  const [subTab, setSubTab] = useState<BuyerSubTab>("PENDING");
  const [receiptOrder, setReceiptOrder] = useState<AdminOrderItem | null>(null);
  const [rejectingOrder, setRejectingOrder] = useState<AdminOrderItem | null>(null);
  const [historyTarget, setHistoryTarget] = useState<{ userId: string; userName: string } | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const ordersQuery = useQuery({
    queryKey: ["admin-orders", subTab, dateFilter],
    queryFn: () => listOrders({ status: subTab, page_size: 50, ...dateFilter }),
    enabled: subTab !== "BLOCKED",
  });

  const blockedQuery = useQuery({
    queryKey: ["admin-blocked-users"],
    queryFn: listBlockedUsers,
    enabled: subTab === "BLOCKED",
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["admin-orders"] });
    queryClient.invalidateQueries({ queryKey: ["admin-blocked-users"] });
    queryClient.invalidateQueries({ queryKey: ["admin-orders-by-user"] });
  }

  const approveMutation = useMutation({
    mutationFn: approveOrder,
    onSuccess: invalidate,
    onError: (err: any) => setActionError(err?.response?.data?.message ?? "Genehmigung fehlgeschlagen."),
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => rejectOrder(id, reason),
    onSuccess: () => {
      invalidate();
      setRejectingOrder(null);
    },
    onError: (err: any) => setActionError(err?.response?.data?.message ?? "Ablehnung fehlgeschlagen."),
  });

  function buyerNameFor(order: AdminOrderItem) {
    return [order.user_first_name, order.user_last_name].filter(Boolean).join(" ") || order.user_username;
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2">
        {BUYER_SUB_TABS.map((t) => (
          <button
            key={t.value}
            onClick={() => setSubTab(t.value)}
            className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition ${
              subTab === t.value
                ? "bg-[var(--admin-primary)] text-white"
                : "bg-[var(--admin-card)] text-[var(--admin-text-secondary)] ring-1 ring-[var(--admin-border)]"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {actionError && (
        <div className="mb-4 rounded-xl bg-[var(--admin-danger)]/10 px-4 py-2.5 text-sm text-[var(--admin-danger)]">
          {actionError}
        </div>
      )}

      {subTab !== "BLOCKED" && (
        <>
          {ordersQuery.isLoading && (
            <div className="flex justify-center py-10">
              <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
            </div>
          )}

          {!ordersQuery.isLoading && (ordersQuery.data?.items.length ?? 0) === 0 && (
            <div className="rounded-2xl bg-[var(--admin-card)] px-6 py-16 text-center shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)]">
              <p className="text-sm text-[var(--admin-text-muted)]">Keine Einträge in dieser Ansicht.</p>
            </div>
          )}

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {ordersQuery.data?.items.map((order) => (
              <BuyerCard
                key={order.id}
                order={order}
                onOpenReceipt={setReceiptOrder}
                onApprove={(o) => {
                  setActionError(null);
                  approveMutation.mutate(o.id);
                }}
                onReject={(o) => {
                  setActionError(null);
                  setRejectingOrder(o);
                }}
                onViewHistory={(o) => setHistoryTarget({ userId: o.user_id, userName: buyerNameFor(o) })}
                approvePending={approveMutation.isPending}
              />
            ))}
          </div>
        </>
      )}

      {subTab === "BLOCKED" && (
        <>
          {blockedQuery.isLoading && (
            <div className="flex justify-center py-10">
              <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
            </div>
          )}

          {!blockedQuery.isLoading && (blockedQuery.data?.length ?? 0) === 0 && (
            <div className="rounded-2xl bg-[var(--admin-card)] px-6 py-16 text-center shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)]">
              <p className="text-sm text-[var(--admin-text-muted)]">Keine blockierten Nutzer.</p>
            </div>
          )}

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {blockedQuery.data?.map((user) => (
              <BlockedUserCard
                key={user.user_id}
                user={user}
                onViewHistory={() =>
                  setHistoryTarget({
                    userId: user.user_id,
                    userName: [user.user_first_name, user.user_last_name].filter(Boolean).join(" ") || user.user_username,
                  })
                }
              />
            ))}
          </div>
        </>
      )}

      <ReceiptViewer order={receiptOrder} onClose={() => setReceiptOrder(null)} />

      <RejectDialog
        order={rejectingOrder}
        onClose={() => setRejectingOrder(null)}
        isPending={rejectMutation.isPending}
        onConfirm={(reason) => {
          if (!rejectingOrder) return;
          rejectMutation.mutate({ id: rejectingOrder.id, reason });
        }}
      />

      <HistoryDialog
        userId={historyTarget?.userId ?? null}
        userName={historyTarget?.userName ?? ""}
        onClose={() => setHistoryTarget(null)}
      />
    </div>
  );
}

// The legacy/generic Payment model (course-scoped, provider field) —
// reused as-is for the "Telegram" source view rather than building a
// second payment system. If it currently has 0 rows on this environment,
// that's an honest reflection of no Telegram-sourced payments existing
// here yet, not a bug.
function TelegramTab({ dateFilter }: { dateFilter: DateFilter }) {
  const [status, setStatus] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-telegram-payments", status, dateFilter],
    queryFn: () => listPayments({ status: status || undefined, page_size: 50, ...dateFilter }),
  });

  const columns: DataTableColumn<PaymentItem>[] = [
    {
      key: "user",
      header: "Nutzer",
      render: (item) => (
        <div>
          <p className="font-medium">{item.user_username ?? "—"}</p>
          <p className="text-xs text-[var(--admin-text-muted)]">{item.user_email ?? "—"}</p>
        </div>
      ),
    },
    {
      key: "date",
      header: "Datum",
      render: (item) => new Date(item.created_at).toLocaleDateString("de-DE"),
    },
    {
      key: "time",
      header: "Uhrzeit",
      render: (item) => new Date(item.created_at).toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" }),
    },
    { key: "amount", header: "Betrag", render: (item) => `${item.amount.toLocaleString()} ${item.currency}` },
    { key: "provider", header: "Quelle", render: (item) => item.provider },
    { key: "course", header: "Kurs", render: (item) => item.course_title ?? "—" },
    {
      key: "status",
      header: "Status",
      render: (item) => (
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
            STATUS_STYLE[item.status] ?? "bg-white/5 text-[var(--admin-text-muted)]"
          }`}
        >
          {item.status}
        </span>
      ),
    },
  ];

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2">
        {["", "pending", "approved", "rejected"].map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition ${
              status === s
                ? "bg-[var(--admin-primary)] text-white"
                : "bg-[var(--admin-card)] text-[var(--admin-text-secondary)] ring-1 ring-[var(--admin-border)]"
            }`}
          >
            {s || "Alle"}
          </button>
        ))}
      </div>

      <DataTable
        columns={columns}
        data={data?.items}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        emptyMessage="Keine Telegram-Zahlungen gefunden."
      />

      {data && data.total_pages > 1 && (
        <p className="mt-3 text-xs text-[var(--admin-text-muted)]">
          Seite {data.page} von {data.total_pages} ({data.total} Zahlungen)
        </p>
      )}
    </div>
  );
}

function PromoCodesTab() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["promo-codes"], queryFn: listPromoCodes });

  const [dialogOpen, setDialogOpen] = useState(false);
  const EMPTY_FORM = {
    code: "",
    campaign: "",
    discount_type: "FREE_DAYS",
    discount_value: 7,
    max_uses: 100,
    expires_at: "",
  };
  const [form, setForm] = useState(EMPTY_FORM);

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["promo-codes"] });
  }

  const createMutation = useMutation({
    mutationFn: () =>
      createPromoCode({
        ...form,
        max_uses: form.max_uses || null,
        expires_at: form.expires_at ? new Date(form.expires_at).toISOString() : null,
      }),
    onSuccess: () => {
      invalidate();
      setDialogOpen(false);
      setForm(EMPTY_FORM);
    },
  });
  const toggleMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) => togglePromoCode(id, isActive),
    onSuccess: invalidate,
  });
  const deleteMutation = useMutation({ mutationFn: deletePromoCode, onSuccess: invalidate });

  const columns: DataTableColumn<PromoCodeItem>[] = [
    { key: "code", header: "Code", render: (item) => <span className="font-mono">{item.code}</span> },
    { key: "campaign", header: "Kampagne", render: (item) => item.campaign ?? "—" },
    {
      key: "discount",
      header: "Wirkung",
      render: (item) =>
        item.discount_type === "PERCENT"
          ? `${item.discount_value}% Rabatt`
          : item.discount_type === "FIXED"
            ? `${item.discount_value} Rabatt`
            : `+${item.discount_value} Tage Premium`,
    },
    { key: "used", header: "Genutzt", render: (item) => `${item.used_count}${item.max_uses ? `/${item.max_uses}` : ""}` },
    {
      key: "expires",
      header: "Läuft ab",
      render: (item) => (item.expires_at ? new Date(item.expires_at).toLocaleDateString("de-DE") : "—"),
    },
    {
      key: "is_active",
      header: "Status",
      render: (item) => (
        <button
          onClick={() => toggleMutation.mutate({ id: item.id, isActive: !item.is_active })}
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
            item.is_active
              ? "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]"
              : "bg-white/5 text-[var(--admin-text-muted)]"
          }`}
        >
          {item.is_active ? "Aktiv" : "Inaktiv"}
        </button>
      ),
    },
    {
      key: "delete",
      header: "",
      render: (item) => (
        <button
          onClick={() => deleteMutation.mutate(item.id)}
          className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--admin-text-secondary)] hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
        >
          <Trash2 size={13} />
        </button>
      ),
    },
  ];

  return (
    <div>
      <div className="mb-4 flex justify-end">
        <AdminButton onClick={() => setDialogOpen(true)}>
          <Plus size={16} />
          Neuer Code
        </AdminButton>
      </div>

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        emptyMessage="Noch keine Promo-Codes angelegt."
      />

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title="Neuer Promo-Code"
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setDialogOpen(false)}>
              Abbrechen
            </AdminButton>
            <AdminButton
              onClick={() => createMutation.mutate()}
              disabled={createMutation.isPending || !form.code}
            >
              Erstellen
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <AdminLabel>Code</AdminLabel>
            <AdminInput
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
              placeholder="SOMMER2026"
            />
          </div>
          <div>
            <AdminLabel>Kampagne (optional)</AdminLabel>
            <AdminInput
              value={form.campaign}
              onChange={(e) => setForm({ ...form, campaign: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <AdminLabel>Typ</AdminLabel>
              <AdminSelect
                value={form.discount_type}
                onChange={(e) => setForm({ ...form, discount_type: e.target.value })}
              >
                <option value="FREE_DAYS">Premium freischalten (Tage)</option>
                <option value="PERCENT">Rabatt — Prozent</option>
                <option value="FIXED">Rabatt — Fixbetrag</option>
              </AdminSelect>
            </div>
            <div>
              <AdminLabel>{form.discount_type === "FREE_DAYS" ? "Dauer (Tage)" : "Wert"}</AdminLabel>
              <AdminInput
                type="number"
                value={form.discount_value}
                onChange={(e) => setForm({ ...form, discount_value: Number(e.target.value) })}
              />
            </div>
          </div>

          {form.discount_type === "FREE_DAYS" && (
            <div className="flex gap-2">
              {[1, 3, 7, 30].map((days) => (
                <button
                  key={days}
                  type="button"
                  onClick={() => setForm({ ...form, discount_value: days })}
                  className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                    form.discount_value === days
                      ? "bg-[var(--admin-primary)] text-white"
                      : "bg-[var(--admin-card)] text-[var(--admin-text-secondary)] ring-1 ring-[var(--admin-border)]"
                  }`}
                >
                  {days} Tage
                </button>
              ))}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <AdminLabel>Maximale Nutzer</AdminLabel>
              <AdminInput
                type="number"
                value={form.max_uses}
                onChange={(e) => setForm({ ...form, max_uses: Number(e.target.value) })}
                placeholder="100"
              />
            </div>
            <div>
              <AdminLabel>Gültig bis (optional)</AdminLabel>
              <AdminInput
                type="date"
                value={form.expires_at}
                onChange={(e) => setForm({ ...form, expires_at: e.target.value })}
              />
            </div>
          </div>
        </div>
      </FormDialog>
    </div>
  );
}

export default function PaymentsPage() {
  const [dateFilter, setDateFilter] = useState<DateFilter>({});

  return (
    <div>
      <AdminPageHeader title="Payments" description="Zahlungen prüfen, genehmigen und Promo-Codes verwalten." />
      <DateFilterBar filter={dateFilter} onChange={setDateFilter} />
      <AdminTabs
        defaultValue="new-buyers"
        tabs={[
          { value: "new-buyers", label: "New Buyers", content: <NewBuyersSection dateFilter={dateFilter} /> },
          { value: "telegram", label: "Telegram", content: <TelegramTab dateFilter={dateFilter} /> },
          { value: "promos", label: "Promo-Codes", content: <PromoCodesTab /> },
        ]}
      />
    </div>
  );
}
