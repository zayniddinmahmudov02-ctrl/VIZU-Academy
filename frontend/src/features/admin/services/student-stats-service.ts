import { api } from "@/services/api";

/** Student statistics (backend rule: backend/app/services/admin/student_stats.py). Numbers come from fresh PostgreSQL counts. */

export interface StudentStatsOverview {
  total_students: number;
  active_students: number;
  inactive_students: number;
  blocked_students: number;
  test_takers: number;
  lesson_participants: number;
  students_in_groups: number;
  total_teachers: number;
  total_admins: number;
  total_other_staff: number;
  test_accounts: number;
  total_accounts: number;
  total_groups: number;
  active_groups: number;
  total_registrations_today: number;
  total_registrations_this_month: number;
  active_days: number;
  timezone: string;
  computed_at: string;
  can_list_students: boolean;
}

export type StudentListStatus = "all" | "active" | "inactive" | "blocked" | "test_takers" | "test_accounts";

export interface StudentListItem {
  id: string;
  name: string;
  username: string;
  contact: string | null;
  registered_via: "email" | "phone" | "telegram";
  created_at: string;
  last_login: string | null;
  is_active_student: boolean;
  is_blocked: boolean;
  took_a_test: boolean;
  joined_a_lesson: boolean;
  groups: number;
}

export interface StudentList {
  items: StudentListItem[];
  total: number;
  page: number;
  page_size: number;
  status: StudentListStatus;
}

export const getStudentStats = () => api.get<StudentStatsOverview>("/api/v1/admin/stats/overview").then((r) => r.data);

export const getStudentList = (params: { page: number; page_size: number; status: StudentListStatus; search?: string }) =>
  api.get<StudentList>("/api/v1/admin/stats/students", { params: { ...params, search: params.search || undefined } }).then((r) => r.data);
