export interface DashboardStats {
  totalUsers: number;
  premiumUsers: number;
  trialUsers: number;
  revenueToday: number;
  revenueMonth: number;
  revenueYear: number;
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

export interface ActiveUser {
  id: string;
  username: string;
  email: string;
  lastLogin: string | null;
}

export interface RecentRegistration {
  id: string;
  username: string;
  email: string;
  role: string;
  createdAt: string;
}

export interface RecentPayment {
  id: string;
  userEmail: string;
  courseTitle: string;
  amount: number;
  currency: string;
  status: string;
  createdAt: string;
}

export interface RecentCertificate {
  id: string;
  userEmail: string;
  courseTitle: string;
  level: string;
  issuedAt: string;
}

export type ActivityType = "registration" | "payment" | "certificate";

export interface ActivityItem {
  type: ActivityType;
  title: string;
  timestamp: string;
}

export interface AdminDashboardOverview {
  serverStatus: string;
  stats: DashboardStats;
  revenueChart: ChartPoint[];
  userGrowthChart: ChartPoint[];
  popularCourses: PopularCourse[];
  activeUsers: ActiveUser[];
  recentRegistrations: RecentRegistration[];
  recentPayments: RecentPayment[];
  recentCertificates: RecentCertificate[];
  recentActivities: ActivityItem[];
}
