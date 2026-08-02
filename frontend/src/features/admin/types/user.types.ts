export interface UserTagItem {
  id: string;
  label: string;
}

export interface UserListItem {
  id: string;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  is_banned: boolean;
  is_suspended: boolean;
  is_premium: boolean;
  premium_until: string | null;
  last_login: string | null;
  created_at: string;
  tags: UserTagItem[];
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
  payments_total: number;
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
