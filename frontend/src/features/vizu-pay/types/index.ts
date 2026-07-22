export interface PlanOption {
  plan: string;
  label: string;
  days: number;
  price: number;
  currency: string;
}

export interface SubscriptionStatus {
  isPremium: boolean;
  premiumUntil: string | null;
  isTrial: boolean;
  trialAvailable: boolean;
  trialDaysRemaining: number | null;
  hasPendingOrder: boolean;
}

export interface OrderItem {
  id: string;
  plan: string;
  planLabel: string;
  durationDays: number;
  baseAmount: number;
  discountAmount: number;
  finalAmount: number;
  currency: string;
  paymentMethod: string;
  status: string;
  proofUrl: string | null;
  proofType: string | null;
  promoCode: string | null;
  rejectionReason: string | null;
  expiresAt: string | null;
  reviewedAt: string | null;
  createdAt: string;
}

export interface OrderListResponse {
  items: OrderItem[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface PromoValidation {
  valid: boolean;
  discountType: "PERCENT" | "FIXED" | null;
  discountValue: number | null;
  message: string | null;
}

export const PAYMENT_METHODS = ["VISA", "MASTERCARD", "UZCARD", "HUMO", "TELEGRAM"] as const;
export type PaymentMethod = (typeof PAYMENT_METHODS)[number];
