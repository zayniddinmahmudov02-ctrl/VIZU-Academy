import { api } from "@/src/services/api";
import { ensureArray } from "@/lib/ensure-array";
import { ADMIN_ENDPOINTS } from "../constants/endpoints";

// The legacy/generic `Payment` model (app/models/payment/payment.py) —
// distinct from the vizu-pay `SubscriptionOrder` flow used by the current
// website checkout. "Telegram Payments" reuses this existing, already-
// mounted architecture rather than a new payment entity.
export interface PaymentItem {
  id: string;
  user_id: string;
  course_id: string;
  amount: number;
  currency: string;
  provider: string;
  transaction_id: string | null;
  status: string;
  created_at: string;
  user_email: string | null;
  user_username: string | null;
  course_title: string | null;
}

export interface PaymentListResponse {
  items: PaymentItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export async function listPayments(params: {
  page?: number;
  page_size?: number;
  status?: string;
  year?: number;
  month?: number;
  day?: number;
}): Promise<PaymentListResponse> {
  const response = await api.get<PaymentListResponse>(ADMIN_ENDPOINTS.paymentsPaginated, { params });
  return { ...response.data, items: ensureArray<PaymentItem>(response.data?.items) };
}
