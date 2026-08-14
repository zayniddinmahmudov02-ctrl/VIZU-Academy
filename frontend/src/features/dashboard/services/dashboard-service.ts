import { api } from "@/lib/api";

export interface DashboardOverview {
  enrolled_courses: number;
  completed_lessons: number;
  completed_modules: number;
  certificates: number;
  study_minutes: number;
  progress: number;
  current_course: string | null;
  current_module: string | null;
  current_lesson: string | null;
  current_lesson_id: string | null;
  current_lesson_score: number | null;
  current_lesson_max_score: number | null;
}

export async function getDashboard(userId: string): Promise<DashboardOverview> {
  return api<DashboardOverview>(`/api/v1/dashboard/${userId}`);
}
