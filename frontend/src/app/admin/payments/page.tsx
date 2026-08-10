"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Calendar, Check, Plus, Trash2, X } from "lucide-react";

import { AdminButton, AdminInput, AdminLabel, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import AdminTabs from "@/components/admin/admin-tabs";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
import { listPayments, type PaymentItem } from "@/features/admin/services/payment-service";
import {
  approveOrder,
  createPromoCode,
  deletePromoCode,
  listOrders,
  listPromoCodes,
  rejectOrder,
  togglePromoCode,
} from "@/features/admin/services/vizu-pay-service";
import type { AdminOrderItem, PromoCodeItem } from "@/features/admin/types/vizu-pay.types";

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

function OrdersTab({ dateFilter }: { dateFilter: DateFilter }) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-orders", status, dateFilter],
    queryFn: () => listOrders({ status: status || undefined, page_size: 50, ...dateFilter }),
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["admin-orders"] });
  }

  const approveMutation = useMutation({ mutationFn: approveOrder, onSuccess: invalidate });
  const rejectMutation = useMutation({
    mutationFn: (id: string) => rejectOrder(id, window.prompt("Ablehnungsgrund:") ?? ""),
    onSuccess: invalidate,
  });

  const columns: DataTableColumn<AdminOrderItem>[] = [
    {
      key: "user",
      header: "Nutzer",
      render: (item) => (
        <div>
          <p className="font-medium">{item.user_username}</p>
          <p className="text-xs text-[var(--admin-text-muted)]">{item.user_email}</p>
        </div>
      ),
    },
    { key: "plan", header: "Plan", render: (item) => item.plan_label },
    {
      key: "amount",
      header: "Betrag",
      render: (item) => `${item.final_amount.toLocaleString()} ${item.currency}`,
    },
    { key: "method", header: "Methode", render: (item) => item.payment_method },
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
    {
      key: "actions",
      header: "",
      render: (item) =>
        item.status === "pending" ? (
          <div className="flex gap-1.5">
            <button
              onClick={() => approveMutation.mutate(item.id)}
              className="flex h-7 w-7 items-center justify-center rounded-md bg-[var(--admin-accent)]/15 text-[var(--admin-accent)] hover:brightness-110"
              aria-label="Genehmigen"
            >
              <Check size={13} />
            </button>
            <button
              onClick={() => rejectMutation.mutate(item.id)}
              className="flex h-7 w-7 items-center justify-center rounded-md bg-[var(--admin-danger)]/15 text-[var(--admin-danger)] hover:brightness-110"
              aria-label="Ablehnen"
            >
              <X size={13} />
            </button>
          </div>
        ) : (
          item.proof_url && (
            <a
              href={item.proof_url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-[var(--admin-primary)] hover:underline"
            >
              Beleg ansehen
            </a>
          )
        ),
    },
  ];

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2">
        {["", "pending", "approved", "rejected", "refunded"].map((s) => (
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
        emptyMessage="Keine Bestellungen gefunden."
      />

      {data && data.total_pages > 1 && (
        <p className="mt-3 text-xs text-[var(--admin-text-muted)]">
          Seite {data.page} von {data.total_pages} ({data.total} Bestellungen)
        </p>
      )}
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
  const [form, setForm] = useState({ code: "", campaign: "", discount_type: "PERCENT", discount_value: 10 });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["promo-codes"] });
  }

  const createMutation = useMutation({
    mutationFn: () => createPromoCode(form),
    onSuccess: () => {
      invalidate();
      setDialogOpen(false);
      setForm({ code: "", campaign: "", discount_type: "PERCENT", discount_value: 10 });
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
      header: "Rabatt",
      render: (item) =>
        item.discount_type === "PERCENT" ? `${item.discount_value}%` : `${item.discount_value}`,
    },
    { key: "used", header: "Genutzt", render: (item) => `${item.used_count}${item.max_uses ? `/${item.max_uses}` : ""}` },
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
              <AdminLabel>Rabatt-Typ</AdminLabel>
              <AdminSelect
                value={form.discount_type}
                onChange={(e) => setForm({ ...form, discount_type: e.target.value })}
              >
                <option value="PERCENT">Prozent</option>
                <option value="FIXED">Fixbetrag</option>
              </AdminSelect>
            </div>
            <div>
              <AdminLabel>Wert</AdminLabel>
              <AdminInput
                type="number"
                value={form.discount_value}
                onChange={(e) => setForm({ ...form, discount_value: Number(e.target.value) })}
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
        defaultValue="website"
        tabs={[
          { value: "website", label: "Website", content: <OrdersTab dateFilter={dateFilter} /> },
          { value: "telegram", label: "Telegram", content: <TelegramTab dateFilter={dateFilter} /> },
          { value: "promos", label: "Promo-Codes", content: <PromoCodesTab /> },
        ]}
      />
    </div>
  );
}
