"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Plus, Trash2, X } from "lucide-react";

import { AdminButton, AdminInput, AdminLabel, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import AdminTabs from "@/components/admin/admin-tabs";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FormDialog from "@/components/admin/form-dialog";
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

function OrdersTab() {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-orders", status],
    queryFn: () => listOrders({ status: status || undefined, page_size: 50 }),
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
  return (
    <div>
      <AdminPageHeader title="Payments" description="Zahlungen prüfen, genehmigen und Promo-Codes verwalten." />
      <AdminTabs
        defaultValue="orders"
        tabs={[
          { value: "orders", label: "Bestellungen", content: <OrdersTab /> },
          { value: "promos", label: "Promo-Codes", content: <PromoCodesTab /> },
        ]}
      />
    </div>
  );
}
