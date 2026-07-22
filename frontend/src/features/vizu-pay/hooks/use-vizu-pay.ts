"use client";

import { useCallback, useEffect, useState } from "react";

import * as vizuPayService from "../services/vizu-pay-service";
import type { OrderListResponse, PlanOption, SubscriptionStatus } from "../types";

export function useVizuPay() {
  const [plans, setPlans] = useState<PlanOption[]>([]);
  const [status, setStatus] = useState<SubscriptionStatus | null>(null);
  const [orders, setOrders] = useState<OrderListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const [plansRes, statusRes, ordersRes] = await Promise.all([
        vizuPayService.getPlans(),
        vizuPayService.getStatus(),
        vizuPayService.getMyOrders(),
      ]);
      setPlans(plansRes);
      setStatus(statusRes);
      setOrders(ordersRes);
    } catch (err) {
      console.warn("Failed to load VIZU Pay data:", err);
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function activateTrial() {
    await vizuPayService.activateTrial();
    await load();
  }

  async function submitOrder(input: vizuPayService.CreateOrderInput) {
    await vizuPayService.createOrder(input);
    await load();
  }

  return { plans, status, orders, loading, error, refetch: load, activateTrial, submitOrder };
}
