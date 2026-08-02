export interface DashboardStats {
  total_users: number;
  premium_users: number;
  trial_users: number;
  revenue_today: number;
  revenue_month: number;
  revenue_year: number;
  certificates: number;
  courses: number;
  lessons: number;
}

export interface ChartPoint {
  label: string;
  value: number;
}

export interface PopularCourse {
  id: string;
  title: string;
  level: string;
  enrollments: number;
}

export interface RecentRegistration {
  id: string;
  username: string;
  email: string;
  role: string;
  created_at: string;
}

export interface RecentPayment {
  id: string;
  user_email: string;
  course_title: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
}

export interface RecentCertificate {
  id: string;
  user_email: string;
  course_title: string;
  level: string;
  issued_at: string;
}

export interface ActivityItem {
  type: string;
  title: string;
  timestamp: string;
}

export interface AdminDashboardOverview {
  server_status: string;
  stats: DashboardStats;
  revenue_chart: ChartPoint[];
  user_growth_chart: ChartPoint[];
  popular_courses: PopularCourse[];
  recent_registrations: RecentRegistration[];
  recent_payments: RecentPayment[];
  recent_certificates: RecentCertificate[];
  recent_activities: ActivityItem[];
}
