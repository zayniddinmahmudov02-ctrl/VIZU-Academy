import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type {
  AdminOrderItem,
  AdminOrderListResponse,
  BlockedUserItem,
  DiscountStatistics,
  MethodBreakdown,
  MlEntitlementItem,
  PaymentSettings,
  PaymentsOverview,
  PromoReviewAction,
  PromoRequestItem,
  PromoRequestList,
  PlanBreakdown,
  PromoCodeCreateRequest,
  PromoCodeItem,
  PromoCodeOrderList,
  PromoCodeUpdateRequest,
  PromoProductCatalog,
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
  /** "course" = Angebote course orders only, "multilevel" = Multilevel Modelltest Premium */
  kind?: "course" | "multilevel";
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

export async function extendOrderAccess(id: string, months: number, reason: string): Promise<AdminOrderItem> {
  const response = await api.post<AdminOrderItem>(`${ADMIN_ENDPOINTS.adminVizuPay}/orders/${id}/extend`, {
    months,
    reason,
  });
  return response.data;
}

export async function listPromoCodes(): Promise<PromoCodeItem[]> {
  const response = await api.get<PromoCodeItem[]>(`${ADMIN_ENDPOINTS.adminVizuPay}/promo-codes`);
  return ensureArray<PromoCodeItem>(response.data);
}

export async function listPromoCodeOrders(id: string, page = 1, pageSize = 20, filters: { search?: string; plan?: string } = {}): Promise<PromoCodeOrderList> {
  const response = await api.get<PromoCodeOrderList>(`${ADMIN_ENDPOINTS.adminVizuPay}/promo-codes/${id}/orders`, {
    params: { page, page_size: pageSize, search: filters.search || undefined, plan: filters.plan || undefined },
  });
  return response.data;
}

export async function listPromoRequests(params: { status?: string; promo_id?: string; search?: string; plan?: string; kind?: string; page?: number; page_size?: number } = {}): Promise<PromoRequestList> {
  const response = await api.get<PromoRequestList>(`${ADMIN_ENDPOINTS.adminVizuPay}/promo-requests`, { params });
  return { ...response.data, items: ensureArray<PromoRequestItem>(response.data?.items) };
}

/** "Promo so'rovi": reject, or approve with a new personal code (create) / an existing approved ACTIVE code (attach). */
export async function reviewCourseRequest(id: string, body: {
  approve: boolean; reason?: string | null; mode?: "create" | "attach"; discount_type?: "PERCENT" | "FIXED" | "FREE_ACCESS";
  discount_value?: number | null; expires_at?: string | null; promo_code_id?: string | null;
}): Promise<PromoRequestItem> {
  return (await api.post<PromoRequestItem>(`${ADMIN_ENDPOINTS.adminVizuPay}/promo-requests/${id}/course-review`, body)).data;
}

/** The approval every promo code needs before it works. */
export async function reviewPromoCode(id: string, action: PromoReviewAction, note?: string): Promise<PromoCodeItem> {
  return (await api.post<PromoCodeItem>(`${ADMIN_ENDPOINTS.adminVizuPay}/promo-codes/${id}/review`, { action, note: note || null })).data;
}

export async function setOrderNote(id: string, note: string): Promise<AdminOrderItem> {
  return (await api.patch<AdminOrderItem>(`${ADMIN_ENDPOINTS.adminVizuPay}/orders/${id}/note`, { note: note || null })).data;
}

export async function getPaymentsOverview(): Promise<PaymentsOverview> {
  return (await api.get<PaymentsOverview>(`${ADMIN_ENDPOINTS.adminVizuPay}/overview`)).data;
}

export async function getPaymentSettings(): Promise<PaymentSettings> {
  return (await api.get<PaymentSettings>(`${ADMIN_ENDPOINTS.adminVizuPay}/payment-settings`)).data;
}

export async function updatePaymentSettings(body: { multilevel_price?: number; multilevel_status?: "ACTIVE" | "DISABLED" }): Promise<PaymentSettings> {
  return (await api.put<PaymentSettings>(`${ADMIN_ENDPOINTS.adminVizuPay}/payment-settings`, body)).data;
}

export async function listMlEntitlements(params: { search?: string; include_revoked?: boolean } = {}): Promise<MlEntitlementItem[]> {
  const response = await api.get<MlEntitlementItem[]>(`${ADMIN_ENDPOINTS.adminVizuPay}/multilevel-entitlements`, { params });
  return ensureArray<MlEntitlementItem>(response.data);
}

export async function reviewPromoRequest(id: string, approve: boolean, reason?: string) {
  return (await api.post(`${ADMIN_ENDPOINTS.adminVizuPay}/promo-requests/${id}/review`, { approve, reason: reason || null })).data;
}

export async function getDiscountStatistics(): Promise<DiscountStatistics> {
  return (await api.get<DiscountStatistics>(`${ADMIN_ENDPOINTS.adminVizuPay}/discount-statistics`)).data;
}

export async function getPromoProducts(): Promise<PromoProductCatalog> {
  const response = await api.get<PromoProductCatalog>(`${ADMIN_ENDPOINTS.adminVizuPay}/promo-products`);
  return response.data;
}

export async function createPromoCode(data: PromoCodeCreateRequest): Promise<PromoCodeItem> {
  const response = await api.post<PromoCodeItem>(`${ADMIN_ENDPOINTS.adminVizuPay}/promo-codes`, data);
  return response.data;
}

export async function updatePromoCode(id: string, data: PromoCodeUpdateRequest): Promise<PromoCodeItem> {
  const response = await api.patch<PromoCodeItem>(`${ADMIN_ENDPOINTS.adminVizuPay}/promo-codes/${id}`, data);
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
