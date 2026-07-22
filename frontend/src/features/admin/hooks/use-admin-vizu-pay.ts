"use client";

import { useCallback, useEffect, useState } from "react";

import { useAsyncResource } from "./use-async-resource";
import * as payService from "../services/vizu-pay-service";
import type { AdminOrderQuery } from "../services/vizu-pay-service";

const DEFAULT_QUERY: AdminOrderQuery = { page: 1, pageSize: 20 };

export function useAdminOrders() {
  const [query, setQuery] = useState<AdminOrderQuery>(DEFAULT_QUERY);
  const [data, setData] = useState<Awaited<ReturnType<typeof payService.listOrders>> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [actionPending, setActionPending] = useState(false);

  const fetchList = useCallback(() => {
    setLoading(true);
    setError(false);
    payService
      .listOrders(query)
      .then(setData)
      .catch((err) => {
        console.warn("Failed to load orders:", err);
        setError(true);
      })
      .finally(() => setLoading(false));
  }, [query]);

  useEffect(() => {
    fetchList();
  }, [fetchList]);

  async function approve(orderId: string) {
    setActionPending(true);
    try {
      await payService.approveOrder(orderId);
      fetchList();
    } finally {
      setActionPending(false);
    }
  }

  async function reject(orderId: string, reason: string) {
    setActionPending(true);
    try {
      await payService.rejectOrder(orderId, reason);
      fetchList();
    } finally {
      setActionPending(false);
    }
  }

  async function refund(orderId: string, reason?: string) {
    setActionPending(true);
    try {
      await payService.refundOrder(orderId, reason);
      fetchList();
    } finally {
      setActionPending(false);
    }
  }

  return {
    query,
    setStatus: (status: string | undefined) => setQuery((q) => ({ ...q, status, page: 1 })),
    setPlan: (plan: string | undefined) => setQuery((q) => ({ ...q, plan, page: 1 })),
    setSearch: (search: string | undefined) => setQuery((q) => ({ ...q, search, page: 1 })),
    setPage: (page: number) => setQuery((q) => ({ ...q, page })),
    data,
    loading,
    error,
    actionPending,
    approve,
    reject,
    refund,
  };
}

export function useRevenueOverview() {
  return useAsyncResource(() => payService.getRevenueOverview(), []);
}

export function usePaymentLogs(page: number) {
  return useAsyncResource(() => payService.getPaymentLogs(page), [page]);
}

export function usePromoCodes() {
  const resource = useAsyncResource(() => payService.listPromoCodes(), []);

  async function create(input: payService.CreatePromoInput) {
    await payService.createPromoCode(input);
    resource.refetch();
  }

  async function update(promoId: string, data: { campaign?: string; isActive?: boolean; expiresAt?: string }) {
    await payService.updatePromoCode(promoId, data);
    resource.refetch();
  }

  async function remove(promoId: string) {
    await payService.deletePromoCode(promoId);
    resource.refetch();
  }

  return { ...resource, create, update, remove };
}
