import { api } from "@/services/api";

/** Admin → Team (backend app/api/admin/team_router.py, SUPER_ADMIN only). */
const BASE = "/api/v1/admin/team";

export interface TeamOverview {
  total: number;
  active: number;
  inactive: number;
  with_control: number;
  without_control: number;
  new: number;
  new_days: number;
}

export interface TeamTeacher {
  id: string;
  name: string;
  first_name: string | null;
  last_name: string | null;
  username: string;
  email: string | null;
  status: "active" | "inactive" | "blocked";
  can_access_student_control: boolean;
  group_count: number;
  course_count: number;
  created_at: string;
  last_login_at: string | null;
  must_change_password: boolean;
}

export interface TeamTeacherDetail extends TeamTeacher {
  groups: { id: string; name: string; level: string; status: string }[];
  courses: { assignment_id: string; course_id: string; title: string; level: string }[];
  history: { id: string; action: string; details: string | null; actor: string | null; at: string }[];
  control_changed_at: string | null;
}

export interface TeamChoices {
  groups: { id: string; name: string; level: string; status: string; teacher_id: string; teacher: string | null }[];
  courses: { id: string; title: string; level: string }[];
}

export interface TeamPage {
  items: TeamTeacher[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreateTeacherInput {
  full_name: string;
  username: string;
  email?: string | null;
  password?: string | null;
  can_access_student_control: boolean;
}

export async function getTeamOverview() {
  return (await api.get<TeamOverview>(`${BASE}/overview`)).data;
}

export async function listTeamTeachers(params: { search?: string; status?: string; control?: string; page?: number; page_size?: number }) {
  const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== ""));
  return (await api.get<TeamPage>(`${BASE}/teachers`, { params: clean })).data;
}

export async function getTeamChoices() {
  return (await api.get<TeamChoices>(`${BASE}/choices`)).data;
}

export async function getTeamTeacher(id: string) {
  return (await api.get<TeamTeacherDetail>(`${BASE}/teachers/${id}`)).data;
}

export async function createTeamTeacher(input: CreateTeacherInput) {
  return (await api.post<{ teacher: TeamTeacherDetail; temporary_password: string }>(`${BASE}/teachers`, input)).data;
}

export async function updateTeamTeacher(id: string, input: { full_name?: string; username?: string; email?: string | null }) {
  return (await api.patch<TeamTeacherDetail>(`${BASE}/teachers/${id}`, input)).data;
}

export async function setTeamControl(id: string, enabled: boolean) {
  return (await api.put<TeamTeacherDetail>(`${BASE}/teachers/${id}/control`, { enabled })).data;
}

export async function setTeamStatus(id: string, active: boolean) {
  return (await api.put<TeamTeacherDetail>(`${BASE}/teachers/${id}/status`, { active })).data;
}

export async function resetTeamPassword(id: string, password?: string) {
  return (await api.post<{ teacher: TeamTeacherDetail; temporary_password: string }>(`${BASE}/teachers/${id}/reset-password`, { password: password || null })).data;
}

export async function assignTeamGroup(id: string, groupId: string) {
  return (await api.put<TeamTeacherDetail>(`${BASE}/teachers/${id}/groups/${groupId}`)).data;
}

export async function removeTeamGroup(id: string, groupId: string) {
  return (await api.delete<TeamTeacherDetail>(`${BASE}/teachers/${id}/groups/${groupId}`)).data;
}

export async function assignTeamCourse(id: string, courseId: string) {
  return (await api.put<TeamTeacherDetail>(`${BASE}/teachers/${id}/courses/${courseId}`)).data;
}

export async function removeTeamCourse(id: string, courseId: string) {
  return (await api.delete<TeamTeacherDetail>(`${BASE}/teachers/${id}/courses/${courseId}`)).data;
}
