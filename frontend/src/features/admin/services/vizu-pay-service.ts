import { api } from "@/services/api";

import type {
  AdminOrderItem,
  AdminOrderListResponse,
  PaymentLogResponse,
  PromoCodeItem,
  RevenueOverview,
} from "../types/vizu-pay";

function mapOrder(raw: any): AdminOrderItem {
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
    userId: raw.user_id,
    userEmail: raw.user_email,
    userUsername: raw.user_username,
    reviewedByEmail: raw.reviewed_by_email,
  };
}

function mapPromo(raw: any): PromoCodeItem {
  return {
    id: raw.id,
    code: raw.code,
    campaign: raw.campaign,
    discountType: raw.discount_type,
    discountValue: raw.discount_value,
    maxUses: raw.max_uses,
    usedCount: raw.used_count,
    expiresAt: raw.expires_at,
    isActive: raw.is_active,
    createdAt: raw.created_at,
  };
}

export interface AdminOrderQuery {
  page: number;
  pageSize: number;
  status?: string;
  plan?: string;
  search?: string;
}

export async function listOrders(query: AdminOrderQuery): Promise<AdminOrderListResponse> {
  const response = await api.get("/admin/vizu-pay/orders", {
    params: {
      page: query.page,
      page_size: query.pageSize,
      status: query.status || undefined,
      plan: query.plan || undefined,
      search: query.search || undefined,
    },
  });
  const data = response.data;
  return {
    items: data.items.map(mapOrder),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
    totalPages: data.total_pages,
  };
}

export async function approveOrder(orderId: string): Promise<AdminOrderItem> {
  const response = await api.post(`/admin/vizu-pay/orders/${orderId}/approve`);
  return mapOrder(response.data);
}

export async function rejectOrder(orderId: string, reason: string): Promise<AdminOrderItem> {
  const response = await api.post(`/admin/vizu-pay/orders/${orderId}/reject`, { reason });
  return mapOrder(response.data);
}

export async function refundOrder(orderId: string, reason?: string): Promise<AdminOrderItem> {
  const response = await api.post(`/admin/vizu-pay/orders/${orderId}/refund`, { reason: reason ?? null });
  return mapOrder(response.data);
}

export async function listPromoCodes(): Promise<PromoCodeItem[]> {
  const response = await api.get("/admin/vizu-pay/promo-codes");
  return response.data.map(mapPromo);
}

export interface CreatePromoInput {
  code: string;
  campaign?: string;
  discountType: "PERCENT" | "FIXED";
  discountValue: number;
  maxUses?: number;
  expiresAt?: string;
}

export async function createPromoCode(input: CreatePromoInput): Promise<PromoCodeItem> {
  const response = await api.post("/admin/vizu-pay/promo-codes", {
    code: input.code,
    campaign: input.campaign || null,
    discount_type: input.discountType,
    discount_value: input.discountValue,
    max_uses: input.maxUses ?? null,
    expires_at: input.expiresAt ?? null,
  });
  return mapPromo(response.data);
}

export async function updatePromoCode(
  promoId: string,
  data: { campaign?: string; isActive?: boolean; expiresAt?: string },
): Promise<PromoCodeItem> {
  const response = await api.patch(`/admin/vizu-pay/promo-codes/${promoId}`, {
    campaign: data.campaign,
    is_active: data.isActive,
    expires_at: data.expiresAt,
  });
  return mapPromo(response.data);
}

export async function deletePromoCode(promoId: string): Promise<void> {
  await api.delete(`/admin/vizu-pay/promo-codes/${promoId}`);
}

export async function getRevenueOverview(): Promise<RevenueOverview> {
  const response = await api.get("/admin/vizu-pay/revenue");
  const data = response.data;
  return {
    totalRevenue: data.total_revenue,
    revenueThisMonth: data.revenue_this_month,
    revenueToday: data.revenue_today,
    totalOrders: data.total_orders,
    pendingOrders: data.pending_orders,
    trialsStarted: data.trials_started,
    trialsConverted: data.trials_converted,
    trialConversionRate: data.trial_conversion_rate,
    monthlyRevenueChart: data.monthly_revenue_chart,
    planBreakdown: data.plan_breakdown.map((p: any) => ({ plan: p.plan, label: p.label, orders: p.orders, revenue: p.revenue })),
    methodBreakdown: data.method_breakdown.map((m: any) => ({ method: m.method, orders: m.orders, revenue: m.revenue })),
    statusBreakdown: data.status_breakdown.map((s: any) => ({ status: s.status, count: s.count })),
  };
}

export async function getPaymentLogs(page = 1, pageSize = 20): Promise<PaymentLogResponse> {
  const response = await api.get("/admin/vizu-pay/logs", { params: { page, page_size: pageSize } });
  const data = response.data;
  return {
    items: data.items.map((i: any) => ({
      id: i.id,
      actorEmail: i.actor_email,
      action: i.action,
      details: i.details,
      ipAddress: i.ip_address,
      createdAt: i.created_at,
    })),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
    totalPages: data.total_pages,
  };
}
