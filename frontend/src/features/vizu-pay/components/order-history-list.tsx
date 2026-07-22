import Badge from "@/components/ui/badge";
import { useTranslation } from "@/lib/i18n/use-translation";
import type { OrderItem } from "../types";

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));
}

function statusVariant(status: string): "success" | "warning" | "danger" | "neutral" {
  if (status === "APPROVED") return "success";
  if (status === "PENDING") return "warning";
  if (status === "REJECTED" || status === "EXPIRED") return "danger";
  return "neutral";
}

export default function OrderHistoryList({ orders }: { orders: OrderItem[] }) {
  const { t } = useTranslation();

  if (orders.length === 0) {
    return (
      <div className="rounded-card bg-surface-card p-6 text-center text-sm text-text-muted shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        {t("vizuPay.historyEmpty")}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {orders.map((order) => (
        <div
          key={order.id}
          className="flex items-center justify-between rounded-card bg-surface-card p-4 shadow-[var(--shadow-md)] ring-1 ring-surface-border"
        >
          <div>
            <p className="text-sm font-semibold text-text-primary">{order.planLabel}</p>
            <p className="text-xs text-text-muted">
              {formatDate(order.createdAt)} · {order.finalAmount} {order.currency} · {order.paymentMethod}
            </p>
            {order.status === "REJECTED" && order.rejectionReason && (
              <p className="mt-1 text-xs text-danger">{order.rejectionReason}</p>
            )}
          </div>
          <Badge variant={statusVariant(order.status)}>{order.status}</Badge>
        </div>
      ))}
    </div>
  );
}
