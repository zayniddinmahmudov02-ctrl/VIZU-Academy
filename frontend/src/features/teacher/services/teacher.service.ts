import { api } from "@/src/services/api";

import type { TeacherOverview, TeacherStudent } from "../types";

// /api/v1/teacher/* — gated server-side by require_teacher_panel_access
// (TEACHER or SUPER_ADMIN only, see backend/app/api/dependencies/auth.py).
// Scoped to whatever courses the CURRENT caller has a TeacherAssignment
// row for (backend/app/services/teacher/service.py) — never every
// student in the system.
export async function getTeacherOverview(): Promise<TeacherOverview> {
  const response = await api.get<TeacherOverview>("/api/v1/teacher/overview");
  return response.data;
}

export async function getTeacherStudents(): Promise<TeacherStudent[]> {
  const response = await api.get<TeacherStudent[]>("/api/v1/teacher/students");
  return response.data;
}
