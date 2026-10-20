export interface UserTagItem {
  id: string;
  label: string;
}

/** One APPROVED course order — backend app/services/vizu_pay/purchases.py. */
export interface CoursePurchaseItem {
  order_id: string;
  plan: string;
  label: string;
  levels: string[];
  amount: number;
  currency: string;
  /** approval time = purchase date */
  purchased_at: string | null;
  status: string;
}

export interface UserListItem {
  id: string;
  email: string;
  username: string;
  first_name: string | null;
  last_name: string | null;
  profile_image: string | null;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  is_banned: boolean;
  is_suspended: boolean;
  is_premium: boolean;
  premium_until: string | null;
  last_login: string | null;
  is_online: boolean;
  usage_minutes: number;
  has_password: boolean;
  created_at: string;
  tags: UserTagItem[];
  has_course_purchase: boolean;
  course_purchases: CoursePurchaseItem[];
  /** orders still waiting for approval — never a purchase */
  pending_orders: number;
}

export interface UserListResponse {
  items: UserListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface UserDetail extends UserListItem {
  ban_reason: string | null;
  banned_at: string | null;
  suspended_until: string | null;
  suspend_reason: string | null;
  enrollments_count: number;
  certificates_count: number;
  /** approved revenue of this user (UZS) */
  payments_total: number;
  approved_orders: number;
}

export const ALL_ROLES = [
  "STUDENT",
  "TEACHER",
  "SUPPORT",
  "CONTENT_MANAGER",
  "PAYMENT_MANAGER",
  "ADMIN",
  "SUPER_ADMIN",
] as const;
