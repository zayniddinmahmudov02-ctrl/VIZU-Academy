"use client";

import { useState } from "react";
import { Check, ExternalLink, RotateCcw, X } from "lucide-react";

import type { AdminOrderItem } from "../types/vizu-pay";
import { Badge } from "./badges";
import PaginationBar from "./pagination-bar";
import AdminModal from "./admin-modal";
import DataTable, { type DataTableColumn } from "./data-table";
import { resolveMediaUrl } from "@/lib/media";

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(
    new Date(value),
  );
}

function statusTone(status: string): "success" | "warning" | "danger" | "neutral" {
  if (status === "APPROVED") return "success";
  if (status === "PENDING") return "warning";
  if (status === "REJECTED" || status === "EXPIRED") return "danger";
  return "neutral";
}

interface Props {
  items: AdminOrderItem[];
  loading: boolean;
  page: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
  onApprove: (orderId: string) => Promise<void>;
  onReject: (orderId: string, reason: string) => Promise<void>;
  onRefund: (orderId: string, reason?: string) => Promise<void>;
  actionPending: boolean;
}

export default function OrdersReviewTable({
  items,
  loading,
  page,
  totalPages,
  total,
  onPageChange,
  onApprove,
  onReject,
  onRefund,
  actionPending,
}: Props) {
  const [rejectTarget, setRejectTarget] = useState<AdminOrderItem | null>(null);
  const [refundTarget, setRefundTarget] = useState<AdminOrderItem | null>(null);
  const [reason, setReason] = useState("");

  async function handleReject() {
    if (!rejectTarget || !reason.trim()) return;
    await onReject(rejectTarget.id, reason.trim());
    setRejectTarget(null);
    setReason("");
  }

  async function handleRefund() {
    if (!refundTarget) return;
    await onRefund(refundTarget.id, reason.trim() || undefined);
    setRefundTarget(null);
    setReason("");
  }

  const columns: DataTableColumn<AdminOrderItem>[] = [
    {
      key: "user",
      label: "User",
      render: (order) => (
        <div>
          <p className="truncate text-sm font-semibold text-white">{order.userUsername}</p>
          <p className="truncate text-xs text-[var(--admin-text-muted)]">{order.userEmail}</p>
        </div>
      ),
    },
    { key: "plan", label: "Plan", render: (order) => <span className="text-sm text-white">{order.planLabel}</span> },
    {
      key: "amount",
      label: "Amount",
      render: (order) => (
        <div>
          <p className="text-sm text-white">
            {order.finalAmount} {order.currency}
          </p>
          {order.discountAmount > 0 && (
            <p className="text-[11px] text-[var(--admin-text-muted)] line-through">{order.baseAmount}</p>
          )}
          {order.promoCode && <p className="text-[11px] text-[var(--admin-primary)]">{order.promoCode}</p>}
        </div>
      ),
    },
    {
      key: "method",
      label: "Method",
      render: (order) => <span className="text-sm text-[var(--admin-text-secondary)]">{order.paymentMethod}</span>,
    },
    { key: "status", label: "Status", render: (order) => <Badge label={order.status} tone={statusTone(order.status)} /> },
    {
      key: "proof",
      label: "Proof",
      render: (order) =>
        order.proofUrl ? (
          <a
            href={resolveMediaUrl(order.proofUrl) ?? "#"}
            target="_blank"
            rel="noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="flex items-center gap-1 text-xs font-semibold text-[var(--admin-primary)] hover:underline"
          >
            View <ExternalLink size={11} />
          </a>
        ) : (
          <span className="text-xs text-[var(--admin-text-muted)]">—</span>
        ),
    },
    {
      key: "created",
      label: "Created",
      render: (order) => <span className="text-xs text-[var(--admin-text-secondary)]">{formatDate(order.createdAt)}</span>,
    },
    {
      key: "actions",
      label: "Actions",
      render: (order) => (
        <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
          {order.status === "PENDING" && (
            <>
              <button
                type="button"
                disabled={actionPending}
                onClick={() => onApprove(order.id)}
                title="Approve"
                className="rounded-lg border border-[#22c55e]/30 p-1.5 text-[#22c55e] transition-colors hover:bg-[#22c55e]/10 disabled:opacity-40"
              >
                <Check size={14} />
              </button>
              <button
                type="button"
                disabled={actionPending}
                onClick={() => setRejectTarget(order)}
                title="Reject"
                className="rounded-lg border border-[#ef4444]/30 p-1.5 text-[#ef4444] transition-colors hover:bg-[#ef4444]/10 disabled:opacity-40"
              >
                <X size={14} />
              </button>
            </>
          )}
          {order.status === "APPROVED" && (
            <button
              type="button"
              disabled={actionPending}
              onClick={() => setRefundTarget(order)}
              title="Refund"
              className="rounded-lg border border-[#f59e0b]/30 p-1.5 text-[#f59e0b] transition-colors hover:bg-[#f59e0b]/10 disabled:opacity-40"
            >
              <RotateCcw size={14} />
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <DataTable
        columns={columns}
        rows={items}
        getRowKey={(order) => order.id}
        loading={loading}
        loadingLabel="Loading orders…"
        emptyLabel="No orders match these filters."
        minWidth="960px"
      />

      <PaginationBar page={page} totalPages={totalPages} total={total} onPageChange={onPageChange} />

      <AdminModal open={rejectTarget !== null} onOpenChange={(open) => !open && setRejectTarget(null)} title="Reject Order">
        <p className="mb-2 text-xs text-[var(--admin-text-muted)]">
          Rejecting {rejectTarget?.userEmail}'s {rejectTarget?.planLabel} order. This releases any promo code usage.
        </p>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Reason for rejection…"
          className="h-24 w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
        />
        <button
          type="button"
          onClick={handleReject}
          disabled={!reason.trim() || actionPending}
          className="mt-4 w-full rounded-xl bg-[#ef4444] py-2.5 text-sm font-semibold text-white disabled:opacity-40"
        >
          Confirm Rejection
        </button>
      </AdminModal>

      <AdminModal open={refundTarget !== null} onOpenChange={(open) => !open && setRefundTarget(null)} title="Refund Order">
        <p className="mb-2 text-xs text-[var(--admin-text-muted)]">
          Refunding {refundTarget?.userEmail}'s {refundTarget?.planLabel} order revokes the {refundTarget?.durationDays} days of
          premium access it granted.
        </p>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Reason (optional)…"
          className="h-20 w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
        />
        <button
          type="button"
          onClick={handleRefund}
          disabled={actionPending}
          className="mt-4 w-full rounded-xl bg-[#f59e0b] py-2.5 text-sm font-semibold text-white disabled:opacity-40"
        >
          Confirm Refund
        </button>
      </AdminModal>
    </div>
  );
}
