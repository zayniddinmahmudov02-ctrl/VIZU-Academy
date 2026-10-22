import { api } from "@/services/api";

interface OrderPayload {
  id: string;
  plan: string;
  plan_label: string;
  duration_days: number;
  base_amount: number;
  discount_amount: number;
  final_amount: number;
  currency: string;
  payment_method: string;
  status: string;
  has_proof: boolean;
  proof_download_url: string | null;
  promo_code: string | null;
  rejection_reason: string | null;
  expires_at: string | null;
  reviewed_at: string | null;
  purchase_date: string | null;
  access_start_date: string | null;
  access_end_date: string | null;
  created_at: string;
}

interface CourseAccessPayload {
  order_id: string;
  plan: string;
  plan_label: string;
  levels: string[];
  purchase_date: string | null;
  access_start_date: string | null;
  access_end_date: string | null;
  status: "ACTIVE" | "EXPIRED";
  remaining_seconds: number;
}

interface SubscriptionStatusPayload {
  is_premium: boolean;
  premium_until: string | null;
  owned_levels: string[];
  has_pending_order: boolean;
  rejection_count: number;
  is_blocked: boolean;
  latest_rejection_reason: string | null;
  course_accesses?: CourseAccessPayload[];
}

import type {
  Offer,
  OrderItem,
  OrderListResponse,
  PaymentCard,
  PlanOption,
  PromoRedeemResult,
  PromoValidation,
  SubscriptionStatus,
} from "../types";

function mapOrder(raw: OrderPayload): OrderItem {
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
    hasProof: raw.has_proof,
    proofDownloadUrl: raw.proof_download_url,
    promoCode: raw.promo_code,
    rejectionReason: raw.rejection_reason,
    expiresAt: raw.expires_at,
    reviewedAt: raw.reviewed_at,
    purchaseDate: raw.purchase_date,
    accessStartDate: raw.access_start_date,
    accessEndDate: raw.access_end_date,
    createdAt: raw.created_at,
  };
}

export async function getPlans(): Promise<PlanOption[]> {
  const response = await api.get("/api/v1/vizu-pay/plans");
  return response.data;
}

interface OfferPayload {
  code: string;
  kind: Offer["kind"];
  label: string;
  levels: string[] | null;
  original_price: number | null;
  sale_price: number | null;
  discount_percent: number | null;
  active: boolean;
  purchasable?: boolean;
  available_levels?: string[];
  sales_levels?: string[];
  duration_months: number;
  free_lessons: number;
  currency: string;
}

export async function getOffers(): Promise<Offer[]> {
  const response = await api.get<OfferPayload[]>("/api/v1/vizu-pay/offers");
  return (Array.isArray(response.data) ? response.data : []).map((o) => ({
    code: o.code,
    kind: o.kind,
    label: o.label,
    levels: o.levels ?? [],
    originalPrice: o.original_price,
    salePrice: o.sale_price,
    discountPercent: o.discount_percent,
    active: !!o.active,
    // the server decides; an older backend without the field: nothing is sold
    purchasable: !!o.purchasable,
    availableLevels: o.available_levels ?? o.levels ?? [],
    salesLevels: o.sales_levels ?? [],
    durationMonths: o.duration_months,
    freeLessons: o.free_lessons,
    currency: o.currency,
  }));
}

/** The caller's checkout price (sale price, promo, medal reward) — computed
 * by the server exactly like the order itself; only displayed here. */
export interface CheckoutQuote {
  plan: string;
  currency: string;
  original_price: number | null;
  base_amount: number;
  promo_discount: number;
  promo_error: string | null;
  reward_discount: number;
  reward_name: { de: string; uz: string } | null;
  final_amount: number;
}

export async function getCheckoutQuote(plan: string, promoCode?: string): Promise<CheckoutQuote> {
  const params: Record<string, string> = { plan };
  if (promoCode) params.promo_code = promoCode;
  return (await api.get<CheckoutQuote>("/api/v1/vizu-pay/quote", { params })).data;
}

export async function getPaymentCards(): Promise<PaymentCard[]> {
  const response = await api.get<PaymentCard[]>("/api/v1/vizu-pay/payment-cards");
  return response.data.map((c) => ({ label: c.label, number: c.number }));
}

export async function getStatus(): Promise<SubscriptionStatus> {
  const response = await api.get<SubscriptionStatusPayload>("/api/v1/vizu-pay/status");
  const data = response.data;
  return {
    isPremium: data.is_premium,
    premiumUntil: data.premium_until,
    ownedLevels: Array.isArray(data.owned_levels) ? data.owned_levels : [],
    hasPendingOrder: data.has_pending_order,
    rejectionCount: data.rejection_count,
    isBlocked: data.is_blocked,
    latestRejectionReason: data.latest_rejection_reason,
    courseAccesses: Array.isArray(data.course_accesses)
      ? data.course_accesses.map((item) => ({
          orderId: item.order_id,
          plan: item.plan,
          planLabel: item.plan_label,
          levels: item.levels,
          purchaseDate: item.purchase_date,
          accessStartDate: item.access_start_date,
          accessEndDate: item.access_end_date,
          status: item.status,
          remainingSeconds: item.remaining_seconds,
        }))
      : [],
  };
}

export async function validatePromo(code: string, plan: string): Promise<PromoValidation> {
  const response = await api.get("/api/v1/vizu-pay/promo/validate", { params: { code, plan } });
  const data = response.data;
  return {
    valid: data.valid,
    discountType: data.discount_type,
    discountValue: data.discount_value,
    message: data.message,
    discountAmount: data.discount_amount,
    finalAmount: data.final_amount,
  };
}

export async function redeemPromo(code: string): Promise<PromoRedeemResult> {
  const response = await api.post("/api/v1/vizu-pay/promo/redeem", { code });
  const grantedOffers: string[] = Array.isArray(response.data.granted_offers) ? response.data.granted_offers : [];
  return { premiumUntil: response.data.premium_until ?? null, daysGranted: response.data.days_granted ?? 0, grantedOffers };
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

  const response = await api.post("/api/v1/vizu-pay/orders", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return mapOrder(response.data);
}

export async function getMyOrders(page = 1, pageSize = 20): Promise<OrderListResponse> {
  const response = await api.get("/api/v1/vizu-pay/orders", { params: { page, page_size: pageSize } });
  const data = response.data;
  return {
    items: data.items.map(mapOrder),
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
    totalPages: data.total_pages,
  };
}
