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
  created_at: string;
  user_id: string;
  user_email: string;
  user_username: string;
  user_first_name: string | null;
  user_last_name: string | null;
  user_phone_number: string | null;
  reviewed_by_email: string | null;
}

export interface AdminOrderListResponse {
  items: AdminOrderItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PromoCodeItem {
  id: string;
  code: string;
  campaign: string | null;
  discount_type: string;
  discount_value: number;
  max_uses: number | null;
  used_count: number;
  expires_at: string | null;
  is_active: boolean;
  created_at: string;
}

export interface PromoCodeCreateRequest {
  code: string;
  campaign?: string | null;
  discount_type: string;
  discount_value: number;
  max_uses?: number | null;
  expires_at?: string | null;
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
  monthly_revenue_chart: RevenueChartPoint[];
  plan_breakdown: PlanBreakdown[];
  method_breakdown: MethodBreakdown[];
  status_breakdown: StatusBreakdown[];
}
