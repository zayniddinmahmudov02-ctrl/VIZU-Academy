import { api } from "@/src/services/api";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";
import type {
  AdminOrderItem,
  AdminOrderListResponse,
  PromoCodeCreateRequest,
  PromoCodeItem,
  RevenueOverview,
} from "../types/vizu-pay.types";

export async function listOrders(params: {
  page?: number;
  page_size?: number;
  status?: string;
  plan?: string;
  search?: string;
}): Promise<AdminOrderListResponse> {
  const response = await api.get<AdminOrderListResponse>(`${ADMIN_ENDPOINTS.adminVizuPay}/orders`, {
    params,
  });
  return response.data;
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
  return response.data;
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
  return response.data;
}
