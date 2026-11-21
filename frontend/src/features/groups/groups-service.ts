import { api } from "@/services/api";

const BASE = "/api/v1/groups";

export const LEVELS = ["A1", "A2", "B1", "B2", "C1"] as const;
export type Level = (typeof LEVELS)[number];
export type GroupStatus = "active" | "paused" | "archived" | "blocked";
export type ChatMode = "open" | "teacher_only" | "closed";
/** Monitoring status of a group task for one student (computed from LMS data). */
export type TaskStatus = "not_started" | "in_progress" | "overdue" | "under_review" | "needs_revision" | "completed" | "completed_late";
/** LMS submission status, mapped. */
export type SubmissionStatus = "in_progress" | "under_review" | "needs_revision" | "accepted";

export interface CourseRef { id: string; title: string; level: string }

export interface CodeInfo {
  status: "active" | "paused" | "revoked";
  expires_at: string | null;
  max_uses: number | null;
  use_count: number;
  created_at: string;
  usable: boolean;
  expired: boolean;
  used_up: boolean;
}

export interface GroupSummary {
  id: string;
  name: string;
  description: string | null;
  level: Level;
  mode: "online" | "offline" | "hybrid";
  status: GroupStatus;
  start_date: string | null;
  end_date: string | null;
  capacity: number | null;
  chat_mode: ChatMode;
  teacher: { id: string; name: string };
  courses: CourseRef[];
  student_count: number;
  last_activity_at: string | null;
  created_at: string;
  code?: CodeInfo | null;
}

export interface MyGroup extends GroupSummary {
  unread: number;
  last_message: { body: string; created_at: string; sender: string | null } | null;
  tasks: { total: number; done: number; open: number; overdue: number };
}

export interface GroupDetail extends GroupSummary {
  viewer: { is_manager: boolean; can_post: boolean; unread: number };
}

export interface Paged<T> { items: T[]; total: number; page: number; page_size: number }

export interface Member {
  user_id: string;
  name: string;
  role: "teacher" | "student";
  joined_at: string;
  email?: string;
  status?: "active" | "removed" | "left";
  can_post?: boolean;
  left_at?: string | null;
}

export interface Message {
  id: string;
  kind: "text" | "system";
  body: string | null;
  deleted: boolean;
  is_pinned: boolean;
  created_at: string;
  sender: { id: string; name: string; is_teacher: boolean } | null;
  mine: boolean;
  can_moderate: boolean;
}

export interface MessagePage {
  items: Message[];
  has_more: boolean;
  pinned: Message[];
  can_post: boolean;
  chat_mode: ChatMode;
  unread: number;
}

export interface Announcement {
  id: string;
  title: string;
  body: string;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
  author: string | null;
  archived: boolean;
}

export interface GroupLesson {
  id: string;
  number: number;
  title: string;
  module: string;
  course_id: string;
  course_title: string;
  level: string;
  task: { id: string; due_at: string | null } | null;
}

export interface Dashboard {
  students: number;
  active_students: number;
  lessons_total: number;
  students_completed_all_lessons: number | null;
  students_submitted_all_tasks: number | null;
  tasks: number;
  tasks_submitted: number;
  tasks_missing: number;
  tasks_overdue: number;
  tasks_under_review: number;
  awaiting_teacher_review: number;
  average_lesson_score: number | null;
  average_grade: number | null;
  overall_progress: number | null;
  last_activity_at: string | null;
}

export interface StudentRow {
  user_id: string;
  name: string;
  email: string;
  joined_at: string;
  last_activity_at: string | null;
  active: boolean;
  lessons_completed: number;
  lessons_total: number;
  progress: number | null;
  tasks_total: number;
  tasks_submitted: number;
  tasks_missing: number;
  tasks_overdue: number;
  tasks_under_review: number;
  awaiting_review: number;
  needs_revision: number;
  average_lesson_score: number | null;
  average_grade: number | null;
  graded_count: number;
}

export interface Submission {
  kind: "writing" | "speaking" | "homework";
  id: string;
  lesson_id: string;
  title: string;
  raw_status: string;
  status: SubmissionStatus;
  submitted_at: string | null;
  score: number | null;
  feedback: string | null;
  reviewed_at: string | null;
  deadline: string | null;
  answer_text?: string;
  lesson_title?: string;
  lesson_number?: number;
  course_level?: string;
}

export interface StudentDetail {
  student: { id: string; name: string; email: string; joined_at: string; member_status: string };
  summary: StudentRow;
  lessons: {
    id: string; number: number; title: string; module: string; level: string; course_title: string;
    status: "not_started" | "in_progress" | "completed"; started_at: string | null; completed_at: string | null;
    progress: number | null; score: number | null; last_activity_at: string | null;
  }[];
  tasks: {
    id: string; lesson_id: string; title: string; lesson_title: string | null; module: string | null; note: string | null;
    assigned_at: string; due_at: string | null; status: TaskStatus; submissions: Submission[];
  }[];
  submissions: Submission[];
  skills: { skill: string; lessons_total: number; completed: number; average_score: number | null }[];
  activity: {
    last_login: string | null; last_lesson_activity: string | null; last_submission: string | null;
    recent_reviews: { kind: string; title: string; score: number | null; reviewed_at: string }[];
    chat_messages: number; last_chat_message: string | null;
  };
}

export interface TaskBoard {
  tasks: {
    id: string; lesson_id: string; title: string; lesson_title: string | null; module: string | null; note: string | null;
    assigned_at: string; due_at: string | null; counts: Partial<Record<TaskStatus, number>>;
    students: { user_id: string; name: string; status: TaskStatus; submissions: Pick<Submission, "kind" | "id" | "title" | "status" | "submitted_at" | "score">[] }[];
  }[];
}

export interface GroupOptions {
  levels: Level[];
  courses: CourseRef[];
  teachers: { id: string; name: string; email: string }[];
}

export interface GroupInput {
  name: string;
  description?: string | null;
  level: Level;
  mode: "online" | "offline" | "hybrid";
  status?: GroupStatus;
  start_date?: string | null;
  end_date?: string | null;
  capacity?: number | null;
  course_ids: string[];
  teacher_id?: string | null;
  chat_mode?: ChatMode;
  code_expires_at?: string | null;
  code_max_uses?: number | null;
}

export interface JoinPreview {
  id: string;
  name: string;
  level: string;
  teacher: { id: string; name: string };
  courses: CourseRef[];
  student_count: number;
  capacity: number | null;
  already_member: boolean;
}

/** The backend's error code (detail / message), e.g. "invalid_code". */
export function errorCode(err: unknown): string | null {
  const data = (err as { response?: { data?: { detail?: unknown; message?: unknown } } })?.response?.data;
  const code = data?.detail ?? data?.message;
  return typeof code === "string" ? code : null;
}

const clean = (p: Record<string, unknown>) => Object.fromEntries(Object.entries(p).filter(([, v]) => v !== undefined && v !== "" && v !== null));

// lists
export const getMyGroups = async () => (await api.get<MyGroup[]>(`${BASE}/my`)).data ?? [];
export const getTeachingGroups = async (params: { search?: string; level?: string; status?: string; page?: number }) =>
  (await api.get<Paged<GroupSummary>>(`${BASE}/teaching`, { params: clean(params) })).data;
export const getAllGroups = async (params: { search?: string; level?: string; status?: string; teacher_id?: string; course_id?: string; created_from?: string; created_to?: string; page?: number }) =>
  (await api.get<Paged<GroupSummary>>(`${BASE}/admin/all`, { params: clean(params) })).data;
export const getAdminStats = async () =>
  (await api.get<{ groups: number; by_status: Record<string, number>; students: number; teachers: number; messages_7d: number }>(`${BASE}/admin/stats`)).data;
export const getGroupOptions = async () => (await api.get<GroupOptions>(`${BASE}/options`)).data;

// group
export const createGroup = async (data: GroupInput) => (await api.post<{ group: GroupSummary; code: string }>(BASE, data)).data;
export const getGroup = async (id: string) => (await api.get<GroupDetail>(`${BASE}/${id}`)).data;
export const updateGroup = async (id: string, data: Partial<GroupInput>) => (await api.patch<GroupSummary>(`${BASE}/${id}`, data)).data;
export const leaveGroup = async (id: string) => api.post(`${BASE}/${id}/leave`);

// codes and joining
export const regenerateCode = async (id: string, data: { expires_at?: string | null; max_uses?: number | null }) =>
  (await api.post<CodeInfo & { code: string }>(`${BASE}/${id}/code`, clean(data))).data;
export const changeCode = async (id: string, data: { paused?: boolean; revoke?: boolean; expires_at?: string | null; max_uses?: number | null }) =>
  (await api.patch<CodeInfo | null>(`${BASE}/${id}/code`, data)).data;
export const previewJoin = async (code: string) => (await api.post<JoinPreview>(`${BASE}/join/preview`, { code })).data;
export const joinGroup = async (code: string) => (await api.post<{ group: GroupSummary; already_member: boolean }>(`${BASE}/join`, { code })).data;

// members
export const getMembers = async (id: string) => (await api.get<Member[]>(`${BASE}/${id}/members`)).data ?? [];
export const updateMember = async (id: string, userId: string, data: { remove?: boolean; restore?: boolean; can_post?: boolean }) =>
  (await api.patch(`${BASE}/${id}/members/${userId}`, data)).data;

// chat
export const getMessages = async (id: string, params: { before?: string; after?: string; limit?: number } = {}) =>
  (await api.get<MessagePage>(`${BASE}/${id}/messages`, { params: clean(params) })).data;
export const postMessage = async (id: string, body: string) => (await api.post<Message>(`${BASE}/${id}/messages`, { body })).data;
export const markRead = async (id: string) => api.post(`${BASE}/${id}/read`);
export const moderateMessage = async (id: string, messageId: string, data: { delete?: boolean; pinned?: boolean; reason?: string }) =>
  (await api.patch<Message>(`${BASE}/${id}/messages/${messageId}`, data)).data;
export const setChatMode = async (id: string, chat_mode: ChatMode) => (await api.put(`${BASE}/${id}/chat`, { chat_mode })).data;

// announcements
export const getAnnouncements = async (id: string, includeArchived = false) =>
  (await api.get<Announcement[]>(`${BASE}/${id}/announcements`, { params: includeArchived ? { include_archived: true } : {} })).data ?? [];
export const createAnnouncement = async (id: string, data: { title: string; body: string; is_pinned?: boolean }) =>
  (await api.post<Announcement>(`${BASE}/${id}/announcements`, data)).data;
export const updateAnnouncement = async (id: string, aid: string, data: { is_pinned?: boolean; archived?: boolean; title?: string; body?: string }) =>
  (await api.patch<Announcement>(`${BASE}/${id}/announcements/${aid}`, data)).data;

// lessons, tasks, monitoring
export const getGroupLessons = async (id: string) => (await api.get<GroupLesson[]>(`${BASE}/${id}/lessons`)).data ?? [];
export const saveTask = async (id: string, data: { lesson_id: string; title?: string | null; note?: string | null; due_at?: string | null }) =>
  (await api.put(`${BASE}/${id}/tasks`, data)).data;
export const deleteTask = async (id: string, taskId: string) => api.delete(`${BASE}/${id}/tasks/${taskId}`);
export const getTaskBoard = async (id: string) => (await api.get<TaskBoard>(`${BASE}/${id}/tasks`)).data;
export const getDashboard = async (id: string) => (await api.get<Dashboard>(`${BASE}/${id}/dashboard`)).data;
export const getStudents = async (id: string, params: { filter?: string; sort?: string; search?: string; page?: number }) =>
  (await api.get<Paged<StudentRow> & { courses: CourseRef[] }>(`${BASE}/${id}/students`, { params: clean(params) })).data;
export const getStudentDetail = async (id: string, studentId: string) => (await api.get<StudentDetail>(`${BASE}/${id}/students/${studentId}`)).data;
export const getMyProgress = async (id: string) => (await api.get<StudentDetail | null>(`${BASE}/${id}/me`)).data;
export const getAuditLog = async (id: string, page = 1) =>
  (await api.get<Paged<{ id: string; action: string; actor: string | null; target_type: string | null; meta: Record<string, unknown> | null; created_at: string }>>(`${BASE}/${id}/audit`, { params: { page } })).data;

// grading goes through the existing teacher endpoints (the backend lets a group's teacher reach their students' work)
export const gradeSubmission = async (kind: Submission["kind"], submissionId: string, data: { score: number; feedback: string; status: "GRADED" | "NEEDS_REVISION" }) =>
  (await api.patch(`/api/v1/teacher/${kind}/${submissionId}/grade`, data)).data;
