import type { KontrollDetail, KontrollList, Timeline } from "@/features/activity/types";
import { api } from "@/src/services/api";

import type {
  GroupMessages, GroupTask, HomeworkSubmission, MaterialCourse, Roster, RosterFilters, StudentProfile, TeacherCourse, TeacherDashboard,
  TeacherMe, TeacherVideoLessons,
} from "../panel-types";

// /api/v1/teacher/* — require_teacher_panel_access server-side; /teacher/kontroll/* also require_student_control.
const BASE = "/api/v1/teacher";

export async function getTeacherMe() {
  return (await api.get<TeacherMe>(`${BASE}/me`)).data;
}

export async function changeTeacherUsername(username: string) {
  return (await api.put<{ username: string }>(`${BASE}/me/username`, { username })).data;
}

export async function getTeacherDashboard() {
  return (await api.get<TeacherDashboard>(`${BASE}/dashboard`)).data;
}

function clean(filters: RosterFilters): Record<string, string | number> {
  return Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== undefined && v !== "" && v !== null)) as Record<string, string | number>;
}

export async function getRoster(filters: RosterFilters) {
  return (await api.get<Roster>(`${BASE}/roster`, { params: clean(filters) })).data;
}

export async function getRosterStudent(id: string) {
  return (await api.get<StudentProfile>(`${BASE}/roster/${id}`)).data;
}

export async function getTeacherCourses() {
  return (await api.get<TeacherCourse[]>(`${BASE}/courses`)).data;
}

export async function getTeacherVideoLessons() {
  return (await api.get<TeacherVideoLessons>(`${BASE}/video-lessons`)).data;
}

export async function getTeacherTasks() {
  return (await api.get<GroupTask[]>(`${BASE}/tasks`)).data;
}

export async function getTeacherMaterials() {
  return (await api.get<MaterialCourse[]>(`${BASE}/materials`)).data;
}

export async function getTeacherMessages() {
  return (await api.get<GroupMessages[]>(`${BASE}/messages`)).data;
}

export async function getHomeworkSubmissions(status?: string) {
  return (await api.get<HomeworkSubmission[]>(`${BASE}/homework`, { params: status ? { status } : {} })).data;
}

export async function gradeHomework(id: string, body: { score: number; feedback: string; status: "GRADED" | "NEEDS_REVISION" }) {
  return (await api.patch<HomeworkSubmission>(`${BASE}/homework/${id}/grade`, body)).data;
}

export async function getKontrollStudents(params: { search?: string; sort?: string; page?: number; page_size?: number }) {
  return (await api.get<KontrollList>(`${BASE}/kontroll/students`, { params: clean(params) })).data;
}

export async function getKontrollStudent(id: string) {
  return (await api.get<KontrollDetail>(`${BASE}/kontroll/students/${id}`)).data;
}

export async function getKontrollTimeline(id: string, day?: string) {
  return (await api.get<Timeline>(`${BASE}/kontroll/students/${id}/timeline`, { params: day ? { day } : {} })).data;
}
