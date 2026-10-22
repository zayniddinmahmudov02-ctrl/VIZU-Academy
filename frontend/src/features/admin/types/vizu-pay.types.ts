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
  successful_products: { product_code: string; product_name: string; orders: number; discount_amount: number }[];
  expires_at: string | null;
  is_active: boolean;
  created_at: string;
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
}

export interface PromoCodeUpdateRequest extends Partial<PromoCodeCreateRequest> {
  is_active?: boolean;
}

export interface PromoProductCatalog {
  courses: { id: string; title: string; level: string }[];
  packages: { code: string; label: string }[];
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
