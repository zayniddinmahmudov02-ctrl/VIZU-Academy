import { BarChart3, Clock, CreditCard, TrendingUp, Wallet } from "lucide-react";

import type { RevenueOverview } from "../types/vizu-pay";
import StatCard from "./stat-card";
import RevenueChart from "./revenue-chart";
import ListCard from "./list-card";

function formatCurrency(value: number): string {
  return `${new Intl.NumberFormat("de-DE").format(value)} UZS`;
}

export default function RevenueOverviewWidgets({ revenue }: { revenue: RevenueOverview }) {
  const statCards = [
    { label: "Total Revenue", value: formatCurrency(revenue.totalRevenue), icon: Wallet, gradient: "from-[#5b5bf8] to-[#7c3aed]" },
    { label: "Revenue This Month", value: formatCurrency(revenue.revenueThisMonth), icon: TrendingUp, gradient: "from-[#7c3aed] to-purple-400" },
    { label: "Revenue Today", value: formatCurrency(revenue.revenueToday), icon: BarChart3, gradient: "from-[#5b5bf8] to-blue-400" },
    { label: "Pending Orders", value: String(revenue.pendingOrders), icon: Clock, gradient: "from-[#f59e0b] to-amber-400" },
    {
      label: "Trial Conversion",
      value: `${revenue.trialConversionRate}%`,
      icon: CreditCard,
      gradient: "from-[#22c55e] to-emerald-400",
    },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-5">
        {statCards.map((card) => (
          <StatCard key={card.label} {...card} />
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <RevenueChart data={revenue.monthlyRevenueChart} />

        <ListCard title="Orders by Status" isEmpty={revenue.statusBreakdown.length === 0} emptyLabel="No orders yet.">
          {revenue.statusBreakdown.map((s) => (
            <div key={s.status} className="flex items-center justify-between rounded-xl px-2 py-2 text-sm hover:bg-white/[0.03]">
              <span className="text-white">{s.status}</span>
              <span className="rounded-full bg-white/5 px-2.5 py-1 text-xs font-semibold text-[var(--admin-text-secondary)]">
                {s.count}
              </span>
            </div>
          ))}
        </ListCard>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ListCard title="Revenue by Plan" isEmpty={revenue.planBreakdown.length === 0} emptyLabel="No approved orders yet.">
          {revenue.planBreakdown.map((p) => (
            <div key={p.plan} className="flex items-center justify-between rounded-xl px-2 py-2 text-sm hover:bg-white/[0.03]">
              <div>
                <p className="text-white">{p.label}</p>
                <p className="text-[11px] text-[var(--admin-text-muted)]">{p.orders} orders</p>
              </div>
              <span className="text-sm font-semibold text-white">{formatCurrency(p.revenue)}</span>
            </div>
          ))}
        </ListCard>

        <ListCard title="Revenue by Payment Method" isEmpty={revenue.methodBreakdown.length === 0} emptyLabel="No approved orders yet.">
          {revenue.methodBreakdown.map((m) => (
            <div key={m.method} className="flex items-center justify-between rounded-xl px-2 py-2 text-sm hover:bg-white/[0.03]">
              <div>
                <p className="text-white">{m.method}</p>
                <p className="text-[11px] text-[var(--admin-text-muted)]">{m.orders} orders</p>
              </div>
              <span className="text-sm font-semibold text-white">{formatCurrency(m.revenue)}</span>
            </div>
          ))}
        </ListCard>
      </div>
    </div>
  );
}
