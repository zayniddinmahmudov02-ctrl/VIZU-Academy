export interface PlanOption {
  plan: string;
  label: string;
  days: number;
  price: number;
  currency: string;
}

/** One Angebote offer — values come from the backend
 * (GET /vizu-pay/offers, app/services/vizu_pay/offers.py), never hard-coded. */
export interface Offer {
  code: string;
  kind: "LEVEL" | "PACKAGE";
  label: string;
  levels: string[];
  originalPrice: number | null;
  salePrice: number | null;
  discountPercent: number | null;
  active: boolean;
  freeLessons: number;
  currency: string;
}

export interface SubscriptionStatus {
  isPremium: boolean;
  premiumUntil: string | null;
  /** CEFR levels unlocked by approved Angebote orders. */
  ownedLevels: string[];
  hasPendingOrder: boolean;
  rejectionCount: number;
  isBlocked: boolean;
  latestRejectionReason: string | null;
}

export interface PaymentCard {
  label: string;
  number: string;
}

export interface PromoRedeemResult {
  premiumUntil: string;
  daysGranted: number;
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
  hasProof: boolean;
  proofDownloadUrl: string | null;
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
