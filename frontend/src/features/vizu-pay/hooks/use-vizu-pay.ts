"use client";

import { useCallback, useEffect, useState } from "react";

import * as vizuPayService from "../services/vizu-pay-service";
import type { Offer, OrderListResponse, PaymentCard, SubscriptionStatus } from "../types";

export function useVizuPay() {
  const [offers, setOffers] = useState<Offer[]>([]);
  const [paymentCards, setPaymentCards] = useState<PaymentCard[]>([]);
  const [status, setStatus] = useState<SubscriptionStatus | null>(null);
  const [orders, setOrders] = useState<OrderListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const [offersRes, cardsRes, statusRes, ordersRes] = await Promise.all([
        vizuPayService.getOffers(),
        vizuPayService.getPaymentCards(),
        vizuPayService.getStatus(),
        vizuPayService.getMyOrders(),
      ]);
      setOffers(offersRes);
      setPaymentCards(cardsRes);
      setStatus(statusRes);
      setOrders(ordersRes);
    } catch (err) {
      console.warn("Failed to load Angebote data:", err);
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

  return { offers, paymentCards, status, orders, loading, error, refetch: load, redeemPromo, submitOrder };
}
