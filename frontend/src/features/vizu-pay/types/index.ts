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
  /** server decision: active, priced and (single level) the level is available */
  purchasable: boolean;
  /** levels of the offer students can open today ("Tez orada" levels are not) */
  availableLevels: string[];
  /** levels approved for sale (Admin -> Angebote); the others show "Tez orada" */
  salesLevels: string[];
  durationMonths: number;
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
  courseAccesses: CourseAccess[];
}

export interface CourseAccess {
  orderId: string;
  plan: string;
  planLabel: string;
  levels: string[];
  purchaseDate: string | null;
  accessStartDate: string | null;
  accessEndDate: string | null;
  status: "ACTIVE" | "EXPIRED";
  remainingSeconds: number;
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
  purchaseDate: string | null;
  accessStartDate: string | null;
  accessEndDate: string | null;
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

export const PAYMENT_METHODS = ["UZCARD", "HUMO", "TELEGRAM"] as const;
export type PaymentMethod = (typeof PAYMENT_METHODS)[number];
