import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type {
  AdminOrderItem,
  AdminOrderListResponse,
  BlockedUserItem,
  MethodBreakdown,
  PlanBreakdown,
  PromoCodeCreateRequest,
  PromoCodeItem,
  RevenueChartPoint,
  RevenueOverview,
  StatusBreakdown,
} from "../types/vizu-pay.types";

export async function listOrders(params: {
  page?: number;
  page_size?: number;
  status?: string;
  plan?: string;
  search?: string;
  user_id?: string;
  year?: number;
  month?: number;
  day?: number;
}): Promise<AdminOrderListResponse> {
  const response = await api.get<AdminOrderListResponse>(`${ADMIN_ENDPOINTS.adminVizuPay}/orders`, {
    params,
  });
  return { ...response.data, items: ensureArray<AdminOrderItem>(response.data?.items) };
}

export async function listBlockedUsers(): Promise<BlockedUserItem[]> {
  const response = await api.get<BlockedUserItem[]>(`${ADMIN_ENDPOINTS.adminVizuPay}/blocked-users`);
  return ensureArray<BlockedUserItem>(response.data);
}

/** Receipts are served from an authenticated endpoint, not a public URL
 * (see backend VizuPayService.get_order_proof) — a plain <a href> would
 * hit it with no Authorization header and get a 401. Fetch it through the
 * shared axios instance (which does attach the bearer token) and hand
 * back a blob URL the caller can window.open(). */
export async function openOrderProof(order: AdminOrderItem): Promise<void> {
  if (!order.proof_download_url) return;
  const response = await api.get(order.proof_download_url, { responseType: "blob" });
  const blobUrl = URL.createObjectURL(response.data);
  window.open(blobUrl, "_blank", "noopener,noreferrer");
  setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
}

export async function approveOrder(id: string): Promise<AdminOrderItem> {
  const response = await api.post<AdminOrderItem>(`${ADMIN_ENDPOINTS.adminVizuPay}/orders/${id}/approve`);
  return response.data;
}

export async function rejectOrder(id: string, reason: string): Promise<AdminOrderItem> {
  const response = await api.post<AdminOrderItem>(`${ADMIN_ENDPOINTS.adminVizuPay}/orders/${id}/reject`, {
    reason,
  });
  return response.data;
}

export async function refundOrder(id: string, reason?: string): Promise<AdminOrderItem> {
  const response = await api.post<AdminOrderItem>(`${ADMIN_ENDPOINTS.adminVizuPay}/orders/${id}/refund`, {
    reason,
  });
  return response.data;
}

export async function listPromoCodes(): Promise<PromoCodeItem[]> {
  const response = await api.get<PromoCodeItem[]>(`${ADMIN_ENDPOINTS.adminVizuPay}/promo-codes`);
  return ensureArray<PromoCodeItem>(response.data);
}

export async function createPromoCode(data: PromoCodeCreateRequest): Promise<PromoCodeItem> {
  const response = await api.post<PromoCodeItem>(`${ADMIN_ENDPOINTS.adminVizuPay}/promo-codes`, data);
  return response.data;
}

export async function togglePromoCode(id: string, isActive: boolean): Promise<PromoCodeItem> {
  const response = await api.patch<PromoCodeItem>(`${ADMIN_ENDPOINTS.adminVizuPay}/promo-codes/${id}`, {
    is_active: isActive,
  });
  return response.data;
}

export async function deletePromoCode(id: string): Promise<void> {
  await api.delete(`${ADMIN_ENDPOINTS.adminVizuPay}/promo-codes/${id}`);
}

export async function getRevenueOverview(): Promise<RevenueOverview> {
  const response = await api.get<RevenueOverview>(`${ADMIN_ENDPOINTS.adminVizuPay}/revenue`);
  const data = response.data;
  return {
    ...data,
    monthly_revenue_chart: ensureArray<RevenueChartPoint>(data?.monthly_revenue_chart),
    plan_breakdown: ensureArray<PlanBreakdown>(data?.plan_breakdown),
    method_breakdown: ensureArray<MethodBreakdown>(data?.method_breakdown),
    status_breakdown: ensureArray<StatusBreakdown>(data?.status_breakdown),
  };
}
