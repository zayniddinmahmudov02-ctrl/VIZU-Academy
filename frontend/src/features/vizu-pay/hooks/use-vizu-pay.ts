"use client";

import { useCallback, useEffect, useState } from "react";

import * as vizuPayService from "../services/vizu-pay-service";
import type { OrderListResponse, PaymentCard, PlanOption, SubscriptionStatus } from "../types";

export function useVizuPay() {
  const [plans, setPlans] = useState<PlanOption[]>([]);
  const [paymentCards, setPaymentCards] = useState<PaymentCard[]>([]);
  const [status, setStatus] = useState<SubscriptionStatus | null>(null);
  const [orders, setOrders] = useState<OrderListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const [plansRes, cardsRes, statusRes, ordersRes] = await Promise.all([
        vizuPayService.getPlans(),
        vizuPayService.getPaymentCards(),
        vizuPayService.getStatus(),
        vizuPayService.getMyOrders(),
      ]);
      setPlans(plansRes);
      setPaymentCards(cardsRes);
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

  async function redeemPromo(code: string) {
    const result = await vizuPayService.redeemPromo(code);
    await load();
    return result;
  }

  async function submitOrder(input: vizuPayService.CreateOrderInput) {
    await vizuPayService.createOrder(input);
    await load();
  }

  return { plans, paymentCards, status, orders, loading, error, refetch: load, redeemPromo, submitOrder };
}
