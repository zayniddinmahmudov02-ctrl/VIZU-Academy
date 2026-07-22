import { CreditCard } from "lucide-react";

import type { PaymentHistoryItem } from "../types/user";
import { Badge } from "./badges";

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));
}

function statusTone(status: string): "success" | "warning" | "danger" | "neutral" {
  if (status === "approved") return "success";
  if (status === "pending") return "warning";
  if (status === "failed" || status === "rejected") return "danger";
  return "neutral";
}

export default function PaymentHistoryTable({ payments }: { payments: PaymentHistoryItem[] }) {
  return (
    <div className="admin-glass rounded-2xl p-5">
      <p className="mb-4 text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Payment History</p>

      <div className="space-y-1">
        {payments.length === 0 ? (
          <p className="py-6 text-center text-xs text-[var(--admin-text-muted)]">No payments yet.</p>
        ) : (
          payments.map((payment) => (
            <div key={payment.id} className="flex items-center justify-between rounded-xl px-2 py-2 text-sm hover:bg-white/[0.03]">
              <div className="flex items-center gap-2.5">
                <CreditCard size={14} className="text-[var(--admin-text-muted)]" />
                <div>
                  <p className="text-white">{payment.courseTitle || "—"}</p>
                  <p className="text-[11px] text-[var(--admin-text-muted)]">{formatDate(payment.createdAt)}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-white">
                  {payment.amount} {payment.currency}
                </span>
                <Badge label={payment.status} tone={statusTone(payment.status)} />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
