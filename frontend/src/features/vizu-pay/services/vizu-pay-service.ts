import { api } from "@/services/api";

import type { OrderItem, OrderListResponse, PlanOption, PromoValidation, SubscriptionStatus } from "../types";

function mapOrder(raw: any): OrderItem {
  return {
    id: raw.id,
    plan: raw.plan,
    planLabel: raw.plan_label,
    durationDays: raw.duration_days,
    baseAmount: raw.base_amount,
    discountAmount: raw.discount_amount,
    finalAmount: raw.final_amount,
    currency: raw.currency,
    paymentMethod: raw.payment_method,
    status: raw.status,
    proofUrl: raw.proof_url,
    proofType: raw.proof_type,
    promoCode: raw.promo_code,
    rejectionReason: raw.rejection_reason,
    expiresAt: raw.expires_at,
    reviewedAt: raw.reviewed_at,
    createdAt: raw.created_at,
  };
}

export async function getPlans(): Promise<PlanOption[]> {
  const response = await api.get("/vizu-pay/plans");
  return response.data;
}

export async function getStatus(): Promise<SubscriptionStatus> {
  const response = await api.get("/vizu-pay/status");
  const data = response.data;
  return {
    isPremium: data.is_premium,
    premiumUntil: data.premium_until,
    isTrial: data.is_trial,
    trialAvailable: data.trial_available,
    trialDaysRemaining: data.trial_days_remaining,
    hasPendingOrder: data.has_pending_order,
  };
}

export async function activateTrial(): Promise<{ premiumUntil: string }> {
  const response = await api.post("/vizu-pay/trial");
  return { premiumUntil: response.data.premium_until };
}

export async function validatePromo(code: string): Promise<PromoValidation> {
  const response = await api.get("/vizu-pay/promo/validate", { params: { code } });
  const data = response.data;
  return {
    valid: data.valid,
    discountType: data.discount_type,
    discountValue: data.discount_value,
    message: data.message,
  };
}

export interface CreateOrderInput {
  plan: string;
  paymentMethod: string;
  promoCode?: string;
  proofFile: File;
}

export async function createOrder(input: CreateOrderInput): Promise<OrderItem> {
  const formData = new FormData();
  formData.append("plan", input.plan);
  formData.append("payment_method", input.paymentMethod);
  if (input.promoCode) formData.append("promo_code", input.promoCode);
  formData.append("proof", input.proofFile);

  const response = await api.post("/vizu-pay/orders", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return mapOrder(response.data);
}

export async function getMyOrders(page = 1, pageSize = 20): Promise<OrderListResponse> {
  const response = await api.get("/vizu-pay/orders", { params: { page, page_size: pageSize } });
  const data = response.data;
  return {
    items: data.items.map(mapOrder),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
    totalPages: data.total_pages,
  };
}
