import { api } from "@/services/api";

import type { AdminDashboardOverview } from "../types/dashboard";

interface RawChartPoint {
  label: string;
  value: number;
}

interface RawOverview {
  server_status: string;
  stats: {
    total_users: number;
    premium_users: number;
    trial_users: number;
    revenue_today: number;
    revenue_month: number;
    revenue_year: number;
    certificates: number;
    courses: number;
    lessons: number;
  };
  revenue_chart: RawChartPoint[];
  user_growth_chart: RawChartPoint[];
  popular_courses: { id: string; title: string; level: string; enrollments: number }[];
  active_users: { id: string; username: string; email: string; last_login: string | null }[];
  recent_registrations: {
    id: string;
    username: string;
    email: string;
    role: string;
    created_at: string;
  }[];
  recent_payments: {
    id: string;
    user_email: string;
    course_title: string;
    amount: number;
    currency: string;
    status: string;
    created_at: string;
  }[];
  recent_certificates: {
    id: string;
    user_email: string;
    course_title: string;
    level: string;
    issued_at: string;
  }[];
  recent_activities: { type: "registration" | "payment" | "certificate"; title: string; timestamp: string }[];
}

export async function getDashboardOverview(): Promise<AdminDashboardOverview> {
  const response = await api.get<RawOverview>("/admin/dashboard/overview");
  const data = response.data;

  return {
    serverStatus: data.server_status,
    stats: {
      totalUsers: data.stats.total_users,
      premiumUsers: data.stats.premium_users,
      trialUsers: data.stats.trial_users,
      revenueToday: data.stats.revenue_today,
      revenueMonth: data.stats.revenue_month,
      revenueYear: data.stats.revenue_year,
      certificates: data.stats.certificates,
      courses: data.stats.courses,
      lessons: data.stats.lessons,
    },
    revenueChart: data.revenue_chart,
    userGrowthChart: data.user_growth_chart,
    popularCourses: data.popular_courses,
    activeUsers: data.active_users.map((u) => ({
      id: u.id,
      username: u.username,
      email: u.email,
      lastLogin: u.last_login,
    })),
    recentRegistrations: data.recent_registrations.map((r) => ({
      id: r.id,
      username: r.username,
      email: r.email,
      role: r.role,
      createdAt: r.created_at,
    })),
    recentPayments: data.recent_payments.map((p) => ({
      id: p.id,
      userEmail: p.user_email,
      courseTitle: p.course_title,
      amount: p.amount,
      currency: p.currency,
      status: p.status,
      createdAt: p.created_at,
    })),
    recentCertificates: data.recent_certificates.map((c) => ({
      id: c.id,
      userEmail: c.user_email,
      courseTitle: c.course_title,
      level: c.level,
      issuedAt: c.issued_at,
    })),
    recentActivities: data.recent_activities,
  };
}
