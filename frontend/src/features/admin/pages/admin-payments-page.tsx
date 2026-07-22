"use client";

import { useEffect, useState } from "react";
import { CreditCard } from "lucide-react";

import { useAdminOrders, usePaymentLogs, useRevenueOverview } from "../hooks/use-admin-vizu-pay";
import RevenueOverviewWidgets from "../components/revenue-overview-widgets";
import OrdersFiltersBar from "../components/orders-filters-bar";
import OrdersReviewTable from "../components/orders-review-table";
import PaymentLogsList from "../components/payment-logs-list";

export default function AdminPaymentsPage() {
  const revenue = useRevenueOverview();
  const orders = useAdminOrders();
  const [logsPage, setLogsPage] = useState(1);
  const logs = usePaymentLogs(logsPage);

  const [searchInput, setSearchInput] = useState("");

  useEffect(() => {
    const timeout = setTimeout(() => orders.setSearch(searchInput || undefined), 350);
    return () => clearTimeout(timeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchInput]);

  async function handleApprove(orderId: string) {
    await orders.approve(orderId);
    revenue.refetch();
    logs.refetch();
  }

  async function handleReject(orderId: string, reason: string) {
    await orders.reject(orderId, reason);
    revenue.refetch();
    logs.refetch();
  }

  async function handleRefund(orderId: string, reason?: string) {
    await orders.refund(orderId, reason);
    revenue.refetch();
    logs.refetch();
  }

  return (
    <div className="space-y-6">
      <div className="admin-glass flex items-center gap-3 rounded-2xl p-6">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--admin-primary)] to-[var(--admin-secondary)] text-white">
          <CreditCard size={20} />
        </div>
        <div>
          <h1 className="text-lg font-bold text-white">Payments</h1>
          <p className="text-xs text-[var(--admin-text-muted)]">VIZU Pay revenue, orders and logs</p>
        </div>
      </div>

      {revenue.data && <RevenueOverviewWidgets revenue={revenue.data} />}

      <OrdersFiltersBar
        search={searchInput}
        onSearchChange={setSearchInput}
        status={orders.query.status}
        onStatusChange={orders.setStatus}
        plan={orders.query.plan}
        onPlanChange={orders.setPlan}
      />

      {orders.error ? (
        <div className="admin-glass rounded-2xl p-8 text-center text-sm text-white">Could not load orders.</div>
      ) : (
        <OrdersReviewTable
          items={orders.data?.items ?? []}
          loading={orders.loading}
          page={orders.data?.page ?? 1}
          totalPages={orders.data?.totalPages ?? 1}
          total={orders.data?.total ?? 0}
          onPageChange={orders.setPage}
          onApprove={handleApprove}
          onReject={handleReject}
          onRefund={handleRefund}
          actionPending={orders.actionPending}
        />
      )}

      {logs.data && <PaymentLogsList logs={logs.data} page={logsPage} onPageChange={setLogsPage} />}
    </div>
  );
}
