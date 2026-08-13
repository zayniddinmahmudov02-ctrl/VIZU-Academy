"use client";

import { Check, Clock, CreditCard, FileText, Phone, X } from "lucide-react";

import type { AdminOrderItem } from "@/features/admin/types/vizu-pay.types";

const STATUS_STYLE: Record<string, string> = {
  PENDING: "bg-[var(--admin-warning)]/15 text-[var(--admin-warning)]",
  APPROVED: "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]",
  REJECTED: "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]",
  REFUNDED: "bg-white/5 text-[var(--admin-text-muted)]",
};

interface Props {
  order: AdminOrderItem;
  onOpenReceipt: (order: AdminOrderItem) => void;
  onApprove: (order: AdminOrderItem) => void;
  onReject: (order: AdminOrderItem) => void;
  onViewHistory: (order: AdminOrderItem) => void;
  approvePending: boolean;
}

export default function BuyerCard({ order, onOpenReceipt, onApprove, onReject, onViewHistory, approvePending }: Props) {
  const name = [order.user_first_name, order.user_last_name].filter(Boolean).join(" ") || order.user_username;

  return (
    <div className="flex flex-col gap-3 rounded-2xl bg-[var(--admin-card)] p-4 shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-semibold text-[var(--admin-text-primary)]">{name}</p>
          <p className="text-xs text-[var(--admin-text-muted)]">{order.user_email}</p>
          {order.user_phone_number && (
            <p className="mt-1 flex items-center gap-1.5 text-xs text-[var(--admin-text-secondary)]">
              <Phone size={11} />
              {order.user_phone_number}
            </p>
          )}
        </div>
        <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${STATUS_STYLE[order.status] ?? "bg-white/5 text-[var(--admin-text-muted)]"}`}>
          {order.status}
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-[var(--admin-text-secondary)]">
        <span className="flex items-center gap-1.5">
          <CreditCard size={12} />
          {order.payment_method} · {order.plan_label}
        </span>
        <span>{order.final_amount.toLocaleString()} {order.currency}</span>
        <span>Eingereicht: {new Date(order.created_at).toLocaleString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" })}</span>
      </div>

      {order.rejection_count > 0 && (
        <p className="text-xs font-medium text-[var(--admin-warning)]">
          Ablehnungen: {order.rejection_count}/3
        </p>
      )}

      {order.status === "REJECTED" && order.rejection_reason && (
        <p className="rounded-lg bg-[var(--admin-danger)]/10 px-3 py-2 text-xs text-[var(--admin-danger)]">
          Grund: {order.rejection_reason}
        </p>
      )}

      <div className="flex flex-wrap items-center gap-2 border-t border-[var(--admin-border)] pt-3">
        {order.has_proof && (
          <button
            onClick={() => onOpenReceipt(order)}
            className="flex items-center gap-1.5 rounded-lg ring-1 ring-[var(--admin-border-strong)] px-3 py-1.5 text-xs font-semibold text-[var(--admin-text-secondary)] transition hover:bg-[var(--admin-hover)]"
          >
            <FileText size={13} />
            Beleg öffnen
          </button>
        )}

        <button
          onClick={() => onViewHistory(order)}
          className="flex items-center gap-1.5 rounded-lg ring-1 ring-[var(--admin-border-strong)] px-3 py-1.5 text-xs font-semibold text-[var(--admin-text-secondary)] transition hover:bg-[var(--admin-hover)]"
        >
          <Clock size={13} />
          Verlauf
        </button>

        {order.status === "PENDING" && (
          <>
            <button
              onClick={() => onApprove(order)}
              disabled={approvePending}
              className="ml-auto flex items-center gap-1.5 rounded-lg bg-[var(--admin-accent)]/15 px-3 py-1.5 text-xs font-semibold text-[var(--admin-accent)] transition hover:brightness-110 disabled:opacity-50"
            >
              <Check size={13} />
              Genehmigen
            </button>
            <button
              onClick={() => onReject(order)}
              className="flex items-center gap-1.5 rounded-lg bg-[var(--admin-danger)]/15 px-3 py-1.5 text-xs font-semibold text-[var(--admin-danger)] transition hover:brightness-110"
            >
              <X size={13} />
              Ablehnen
            </button>
          </>
        )}
      </div>
    </div>
  );
}
