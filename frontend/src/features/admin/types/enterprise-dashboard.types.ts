// Mirrors backend/app/schemas/admin/enterprise_dashboard.py exactly.

export const DASHBOARD_RANGES = ["7d", "30d", "90d", "1y"] as const;
export type DashboardRange = (typeof DASHBOARD_RANGES)[number];

export interface DashboardKPIs {
  total_users: number;
  active_users_30d: number;
  premium_members: number;
  total_revenue: number;
  active_courses: number;
  total_model_tests: number;
  certificates_issued: number;
  todays_registrations: number;
}

export interface DashboardChartPoint {
  label: string;
  value: number;
}

export interface DashboardCharts {
  range: DashboardRange;
  revenue: DashboardChartPoint[];
  new_users: DashboardChartPoint[];
  learning_progress: DashboardChartPoint[];
}

export interface NamedCount {
  id: string;
  title: string;
  count: number;
}

export interface LearningAnalytics {
  most_active_course: NamedCount | null;
  most_viewed_lesson: NamedCount | null;
  most_solved_quiz: NamedCount | null;
  most_failed_quiz: NamedCount | null;
  course_completion_percent: number;
  student_completion_percent: number;
}

export interface MockTestSkillAnalytics {
  model_test_id: string;
  title: string;
  attempts: number;
  average_score_percent: number;
  pass_rate_percent: number;
  fail_rate_percent: number;
  average_reading_percent: number | null;
  average_listening_percent: number | null;
  average_writing_percent: number | null;
  average_speaking_percent: number | null;
}

export interface CertificateMockAnalytics {
  provider_id: string;
  code: string;
  name: string;
  total_attempts: number;
  average_score_percent: number;
  pass_rate_percent: number;
  model_tests: MockTestSkillAnalytics[];
}

export interface PaymentsSummary {
  today_revenue: number;
  week_revenue: number;
  month_revenue: number;
  pending_payments: number;
  refunds: number;
  premium_sales: number;
}

export interface ContentCounts {
  languages: number;
  levels: number;
  modules: number;
  lessons: number;
  videos: number;
  vocabulary: number;
  grammar: number;
  reading: number;
  listening: number;
  writing: number;
  speaking: number;
  homework: number;
  quiz: number;
  mock_tests: number;
}

export interface AIStats {
  writing_checked_today: number;
  speaking_checked_today: number;
  pending_ai_reviews: number;
  average_ai_score: number | null;
}

export interface DashboardActivityItem {
  type: string;
  title: string;
  timestamp: string;
}

export interface ServerHealth {
  backend: boolean;
  postgres: boolean;
  postgres_latency_ms: number | null;
  storage_used_percent: number | null;
  disk_used_percent: number | null;
  cpu_percent: number | null;
  ram_percent: number | null;
  uptime_seconds: number;
}

export interface EnterpriseDashboardResponse {
  kpis: DashboardKPIs;
  charts: DashboardCharts;
  learning_analytics: LearningAnalytics;
  mock_test_analytics: CertificateMockAnalytics[];
  payments: PaymentsSummary;
  content: ContentCounts;
  ai: AIStats;
  recent_activity: DashboardActivityItem[];
  server_health: ServerHealth;
}
