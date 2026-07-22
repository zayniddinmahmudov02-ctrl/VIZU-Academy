import type { SubscriptionInfo } from "../types/user";

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "long", year: "numeric" }).format(new Date(value));
}

export default function SubscriptionCard({ subscription }: { subscription: SubscriptionInfo }) {
  return (
    <div className="admin-glass rounded-2xl p-5">
      <p className="mb-4 text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Subscription</p>

      <div className="flex items-center justify-between">
        <span className="text-sm text-[var(--admin-text-secondary)]">Status</span>
        <span className={`text-sm font-bold ${subscription.isPremium ? "text-[#22c55e]" : "text-[var(--admin-text-muted)]"}`}>
          {subscription.isPremium ? "Premium" : "Trial"}
        </span>
      </div>

      {subscription.isPremium && (
        <div className="mt-2 flex items-center justify-between">
          <span className="text-sm text-[var(--admin-text-secondary)]">Valid until</span>
          <span className="text-sm font-semibold text-white">{formatDate(subscription.premiumUntil)}</span>
        </div>
      )}

      <div className="mt-2 flex items-center justify-between">
        <span className="text-sm text-[var(--admin-text-secondary)]">Total paid</span>
        <span className="text-sm font-semibold text-white">
          {new Intl.NumberFormat("de-DE").format(subscription.totalPaid)} UZS
        </span>
      </div>

      <div className="mt-2 flex items-center justify-between">
        <span className="text-sm text-[var(--admin-text-secondary)]">Payments</span>
        <span className="text-sm font-semibold text-white">{subscription.paymentsCount}</span>
      </div>
    </div>
  );
}
