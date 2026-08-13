"use client";

import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import FormDialog from "@/components/admin/form-dialog";
import { listOrders } from "@/features/admin/services/vizu-pay-service";

const STATUS_STYLE: Record<string, string> = {
  PENDING: "bg-[var(--admin-warning)]/15 text-[var(--admin-warning)]",
  APPROVED: "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]",
  REJECTED: "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]",
  REFUNDED: "bg-white/5 text-[var(--admin-text-muted)]",
};

interface Props {
  userId: string | null;
  userName: string;
  onClose: () => void;
}

/** Full payment-request history for one user, oldest first (Attempt #1,
 * #2, ...) — old requests are never deleted, this is the audit trail. */
export default function HistoryDialog({ userId, userName, onClose }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-orders-by-user", userId],
    queryFn: () => listOrders({ user_id: userId!, page_size: 50 }),
    enabled: !!userId,
  });

  const attempts = [...(data?.items ?? [])].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  );

  return (
    <FormDialog open={!!userId} onOpenChange={(open) => !open && onClose()} title={`Verlauf — ${userName}`} size="lg">
      {isLoading && (
        <div className="flex justify-center py-10">
          <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
        </div>
      )}

      {!isLoading && attempts.length === 0 && (
        <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">Keine Zahlungsanfragen gefunden.</p>
      )}

      <div className="space-y-3">
        {attempts.map((order, i) => (
          <div key={order.id} className="rounded-xl bg-white/[0.02] p-4 ring-1 ring-[var(--admin-border)]">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-[var(--admin-text-primary)]">Versuch #{i + 1}</p>
              <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${STATUS_STYLE[order.status] ?? "bg-white/5 text-[var(--admin-text-muted)]"}`}>
                {order.status}
              </span>
            </div>
            <p className="mt-1.5 text-xs text-[var(--admin-text-secondary)]">
              {order.plan_label} · {order.payment_method} · {order.final_amount.toLocaleString()} {order.currency}
            </p>
            {order.rejection_reason && (
              <p className="mt-1.5 text-xs text-[var(--admin-danger)]">Grund: {order.rejection_reason}</p>
            )}
            <p className="mt-1.5 text-xs text-[var(--admin-text-muted)]">
              Eingereicht: {new Date(order.created_at).toLocaleString("de-DE")}
              {order.reviewed_at && ` · Geprüft: ${new Date(order.reviewed_at).toLocaleString("de-DE")}`}
              {order.reviewed_by_email && ` · Admin: ${order.reviewed_by_email}`}
            </p>
          </div>
        ))}
      </div>
    </FormDialog>
  );
}
