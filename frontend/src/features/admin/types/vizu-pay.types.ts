export interface AdminOrderItem {
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
  user_id: string;
  user_email: string;
  user_username: string;
  user_first_name: string | null;
  user_last_name: string | null;
  user_phone_number: string | null;
  reviewed_by_email: string | null;
  rejection_count: number;
  /** COURSES / PACKAGES / MULTILEVEL / LEGACY */
  product_category?: string;
  /** Multilevel checkout: transfer date + time given by the student (required with no_receipt) */
  paid_at?: string | null;
  no_receipt?: boolean;
  student_note?: string | null;
  /** the Super Admin's own note, never shown to the student */
  admin_note?: string | null;
}

export type ProductCategory = "COURSES" | "PACKAGES" | "MULTILEVEL";
export type PromoApprovalStatus = "PENDING" | "APPROVED" | "ACTIVE" | "REJECTED" | "DISABLED";
export type PromoReviewAction = "approve" | "approve_activate" | "activate" | "reject" | "disable";

export interface PaymentsOverview {
  payments: { total: number; approved: number; pending: number; rejected: number; expired: number; refunded: number };
  pending: { course: number; multilevel: number };
  course_purchases: number;
  course_buyers: number;
  multilevel_purchases: number;
  multilevel_active: number;
  promo_accesses: { course: number; multilevel: number; total: number };
  revenue: { total: number; multilevel: number; course: number };
  promo_codes: Record<PromoApprovalStatus, number>;
  promo_requests_open: { code_approval: number; course_request: number };
}

export interface PaymentSettings {
  cards: { label: string; number: string }[];
  multilevel: { code: string; label: string; price: number; default_price: number; status: "ACTIVE" | "DISABLED"; currency: string };
  review_window_days: number;
  max_rejections: number;
}

export interface MlEntitlementItem {
  id: string;
  user_id: string;
  user_email: string;
  user_name: string;
  source: "PAYMENT" | "PROMO";
  granted_at: string;
  order_id: string | null;
  promo_code: string | null;
  revoked_at: string | null;
  revoke_reason: string | null;
}

export interface AdminOrderListResponse {
  items: AdminOrderItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface BlockedUserItem {
  user_id: string;
  user_email: string;
  user_username: string;
  user_first_name: string | null;
  user_last_name: string | null;
  user_phone_number: string | null;
  rejection_count: number;
  last_rejected_at: string | null;
}

export interface PromoCodeItem {
  id: string;
  code: string;
  campaign: string | null;
  discount_type: string;
  discount_value: number;
  starts_at: string | null;
  max_uses: number | null;
  used_count: number;
  max_uses_per_user: number;
  applicable_course_ids: string[];
  applicable_package_codes: string[];
  successful_uses: number;
  successful_discount_amount: number;
  remaining_uses: number | null;
  status: string;
  successful_products: { product_code: string; product_name: string; orders: number; discount_amount: number; revenue_amount: number }[];
  /** Revenue from APPROVED orders only; refunded and pending orders excluded. */
  successful_revenue_amount: number;
  expires_at: string | null;
  is_active: boolean;
  /** an admin must approve each student's use before the discount applies */
  requires_approval?: boolean;
  pending_requests?: number;
  created_by_email?: string | null;
  created_at: string;
  product_category?: ProductCategory;
  /** a code works only when ACTIVE (approved by a Super Admin and switched on) */
  approval_status?: PromoApprovalStatus;
  approved_at?: string | null;
  approved_by_email?: string | null;
  review_note?: string | null;
  assigned_user_id?: string | null;
  assigned_user_email?: string | null;
}

export interface PromoRequestItem {
  id: string;
  /** CODE_APPROVAL = a code that needs approval; COURSE_REQUEST = "Promo so'rovi" (no code until approved) */
  kind?: "CODE_APPROVAL" | "COURSE_REQUEST";
  message?: string | null;
  code: string;
  plan: string;
  plan_label: string;
  status: "PENDING_APPROVAL" | "APPROVED" | "REJECTED" | "USED" | "EXPIRED" | "DISABLED";
  reason: string | null;
  created_at: string;
  reviewed_at: string | null;
  order_id: string | null;
  user_id: string;
  user_email: string;
  user_name: string;
  discount_type: string | null;
  discount_value: number | null;
  reviewed_by_email: string | null;
}

export interface PromoRequestList {
  items: PromoRequestItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DiscountStatistics {
  total_discount: number;
  promo_discount: number;
  reward_discount: number;
  orders_with_promo: number;
  requests: Record<"PENDING_APPROVAL" | "APPROVED" | "REJECTED" | "USED", number>;
  by_code: { code: string; orders: number; discount: number; revenue: number }[];
  by_package: { plan: string; label: string; orders: number; discount: number; revenue: number }[];
}

export interface PromoCodeOrder {
  id: string;
  promo_code: string;
  product_code: string;
  product_name: string;
  base_amount: number;
  discount_amount: number;
  final_amount: number;
  status: string;
  user_id: string;
  user_email: string;
  user_name: string;
  created_at: string;
  reviewed_at: string | null;
}

export interface PromoCodeOrderList {
  items: PromoCodeOrder[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PromoCodeCreateRequest {
  code: string;
  campaign?: string | null;
  discount_type: string;
  discount_value: number;
  applicable_course_ids: string[];
  applicable_package_codes: string[];
  starts_at?: string | null;
  max_uses?: number | null;
  max_uses_per_user: number;
  expires_at?: string | null;
  is_active?: boolean;
  requires_approval?: boolean;
  product_category?: ProductCategory;
}

export interface PromoCodeUpdateRequest extends Partial<PromoCodeCreateRequest> {
  is_active?: boolean;
}

export interface PromoProductCatalog {
  courses: { id: string; title: string; level: string }[];
  packages: { code: string; label: string }[];
  multilevel?: { code: string; label: string; price: number };
}

export interface RevenueChartPoint {
  label: string;
  value: number;
}

export interface PlanBreakdown {
  plan: string;
  label: string;
  orders: number;
  revenue: number;
  buyers: number;
  is_course: boolean;
  levels: string[];
}

export interface MethodBreakdown {
  method: string;
  orders: number;
  revenue: number;
}

export interface StatusBreakdown {
  status: string;
  count: number;
}

export interface RevenueOverview {
  total_revenue: number;
  revenue_this_month: number;
  revenue_today: number;
  total_orders: number;
  pending_orders: number;
  course_purchases: number;
  course_buyers: number;
  premium_active: number;
  paying_users: number;
  monthly_revenue_chart: RevenueChartPoint[];
  plan_breakdown: PlanBreakdown[];
  method_breakdown: MethodBreakdown[];
  status_breakdown: StatusBreakdown[];
}
