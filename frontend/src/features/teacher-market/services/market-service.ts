import { api } from "@/src/services/api";

import type {
  AdminCertificate, AdminOverview, AdminReview, AdminTeacher, Checkout, CourseItem, LessonBoard, MyCourse, OwnProfile, Page, Review, RosterItem,
  SpecialLesson, TeacherCard, TeacherCourseItem, TeacherProfileView,
} from "../types";

// Students / everyone: get_current_user server-side (enroll, pay, review = STUDENT accounts only).
const MT = "/api/v1/my-teacher";
const SL = "/api/v1/special-lessons";
// Teacher panel: require_teacher_panel_access. Admin: reads require_admin_panel_access, changes require_super_admin.
const TM = "/api/v1/teacher/market";
const AD = "/api/v1/admin/teacher-market";
// the shared axios instance defaults to JSON: uploads must say multipart (axios then adds the boundary)
const MULTIPART = { headers: { "Content-Type": "multipart/form-data" } };

export interface CatalogFilters {
  q?: string;
  language?: string;
  level?: string;
  courses?: "open" | "any";
  activity?: "teaching";
  page?: number;
  page_size?: number;
}

function clean<T extends object>(params: T): Record<string, string | number> {
  return Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== "" && v !== null)) as Record<string, string | number>;
}

// ---------- students ----------

export async function getCatalog(filters: CatalogFilters) {
  return (await api.get<Page<TeacherCard>>(`${MT}/teachers`, { params: clean(filters) })).data;
}

export async function getTeacherProfile(id: string) {
  return (await api.get<TeacherProfileView>(`${MT}/teachers/${id}`)).data;
}

export async function getTeacherReviews(id: string, page = 1) {
  return (await api.get<Page<Review>>(`${MT}/teachers/${id}/reviews`, { params: { page, page_size: 10 } })).data;
}

export async function getCourse(id: string) {
  return (await api.get<CourseItem>(`${MT}/courses/${id}`)).data;
}

export async function enrollFree(id: string) {
  return (await api.post<{ enrollment_id: string; status: string; group_id: string | null }>(`${MT}/courses/${id}/enroll`)).data;
}

export async function setInterest(id: string, on: boolean) {
  return (await api.post<{ interested: boolean }>(`${MT}/courses/${id}/interest`, { on })).data;
}

export async function getCheckout(id: string) {
  return (await api.get<Checkout>(`${MT}/courses/${id}/checkout`)).data;
}

export async function payCourse(id: string, input: { noReceipt: boolean; paidDate?: string; paidTime?: string; note?: string; proof?: File | null }) {
  const form = new FormData();
  form.append("no_receipt", String(input.noReceipt));
  if (input.paidDate) form.append("paid_date", input.paidDate);
  if (input.paidTime) form.append("paid_time", input.paidTime);
  if (input.note) form.append("note", input.note);
  if (input.proof) form.append("proof", input.proof);
  return (await api.post(`${MT}/courses/${id}/order`, form, MULTIPART)).data;
}

export async function getMyCourses() {
  return (await api.get<MyCourse[]>(`${MT}/my-courses`)).data;
}

export async function createReview(input: { course_id: string; rating: number; body?: string }) {
  return (await api.post<Review>(`${MT}/reviews`, input)).data;
}

export async function updateReview(id: string, input: { rating?: number; body?: string }) {
  return (await api.patch<Review>(`${MT}/reviews/${id}`, input)).data;
}

export async function reportReview(id: string, reason: string) {
  return (await api.post(`${MT}/reviews/${id}/report`, { reason })).data;
}

export async function getLessonBoard() {
  return (await api.get<LessonBoard>(`${SL}/board`)).data;
}

export async function setLessonSignup(id: string, on: boolean) {
  return (await api.post<{ signed_up: boolean }>(`${SL}/${id}/signup`, { on })).data;
}

/** Certificate files are protected: fetched with the session and shown from a blob URL (never a public link). */
export async function certificateBlobUrl(fileUrl: string) {
  const res = await api.get<Blob>(fileUrl, { responseType: "blob" });
  return URL.createObjectURL(res.data);
}

// ---------- teacher panel ----------

export async function getOwnProfile() {
  return (await api.get<OwnProfile>(`${TM}/profile`)).data;
}

export async function updateOwnProfile(input: Partial<{
  first_name: string; last_name: string; headline: string; bio: string; specialization: string; methodology: string;
  experience_years: number | null; teaching_since: number | null; exam_prep: string[]; languages: string[]; levels: string[];
}>) {
  return (await api.put<OwnProfile>(`${TM}/profile`, input)).data;
}

export async function uploadPhoto(file: Blob, crop: { x: number; y: number; w: number } | null) {
  const form = new FormData();
  form.append("file", file, (file as File).name || "photo.jpg");
  if (crop) {
    form.append("x", String(crop.x));
    form.append("y", String(crop.y));
    form.append("w", String(crop.w));
  }
  return (await api.post<{ photo_url: string }>(`${TM}/profile/photo`, form, MULTIPART)).data;
}

export async function deletePhoto() {
  return (await api.delete(`${TM}/profile/photo`)).data;
}

export async function uploadCertificate(input: { title: string; issuer: string; issued_on?: string; level?: string; file: File }) {
  const form = new FormData();
  form.append("title", input.title);
  form.append("issuer", input.issuer);
  if (input.issued_on) form.append("issued_on", input.issued_on);
  if (input.level) form.append("level", input.level);
  form.append("file", input.file);
  return (await api.post(`${TM}/certificates`, form, MULTIPART)).data;
}

export async function deleteCertificate(id: string) {
  return (await api.delete(`${TM}/certificates/${id}`)).data;
}

export type CourseInput = Partial<Omit<TeacherCourseItem, "id" | "teacher" | "status">> & { status?: string };

export async function getOwnCourses() {
  return (await api.get<TeacherCourseItem[]>(`${TM}/courses`)).data;
}

export async function createCourse(input: CourseInput) {
  return (await api.post<TeacherCourseItem>(`${TM}/courses`, input)).data;
}

export async function updateCourse(id: string, input: CourseInput) {
  return (await api.patch<TeacherCourseItem>(`${TM}/courses/${id}`, input)).data;
}

export async function submitCourse(id: string) {
  return (await api.post<TeacherCourseItem>(`${TM}/courses/${id}/submit`)).data;
}

export async function uploadCourseImage(id: string, file: Blob, crop: { x: number; y: number; w: number } | null) {
  const form = new FormData();
  form.append("file", file, (file as File).name || "course.jpg");
  if (crop) {
    form.append("x", String(crop.x));
    form.append("y", String(crop.y));
    form.append("w", String(crop.w));
  }
  return (await api.post<{ image_url: string }>(`${TM}/courses/${id}/image`, form, MULTIPART)).data;
}

export async function getCourseStudents(id: string) {
  return (await api.get<{ course: TeacherCourseItem; items: RosterItem[] }>(`${TM}/courses/${id}/students`)).data;
}

export async function getOwnReviews() {
  return (await api.get<{ rating: { avg: number; count: number; distribution: Record<string, number> }; items: Review[] }>(`${TM}/reviews`)).data;
}

export async function teacherReportReview(id: string, reason: string) {
  return (await api.post(`${TM}/reviews/${id}/report`, { reason })).data;
}

export interface LessonInput {
  title?: string;
  topic?: string;
  description?: string;
  objectives?: string;
  language?: string;
  level?: string;
  starts_at?: string;
  duration_minutes?: number;
  max_participants?: number;
}

export async function getOwnLessons() {
  return (await api.get<SpecialLesson[]>(`${TM}/special-lessons`)).data;
}

export async function requestLesson(input: LessonInput) {
  return (await api.post<SpecialLesson>(`${TM}/special-lessons`, input)).data;
}

export async function updateLesson(id: string, input: LessonInput) {
  return (await api.patch<SpecialLesson>(`${TM}/special-lessons/${id}`, input)).data;
}

export async function cancelLesson(id: string, reason?: string) {
  return (await api.post<SpecialLesson>(`${TM}/special-lessons/${id}/cancel`, { reason: reason || null })).data;
}

export async function openLessonRoom(id: string) {
  return (await api.post<{ room_id: string; hard_end_at: string }>(`${TM}/special-lessons/${id}/open`)).data;
}

// ---------- admin ----------

export async function adminOverview() {
  return (await api.get<AdminOverview>(`${AD}/overview`)).data;
}

export async function adminTeachers(params: { q?: string; flag?: string; page?: number }) {
  return (await api.get<Page<AdminTeacher>>(`${AD}/teachers`, { params: clean({ ...params, page_size: 50 }) })).data;
}

export async function adminUpdateTeacher(id: string, input: Partial<{ catalog_hidden: boolean; profile_disabled: boolean; verified: boolean }>) {
  return (await api.patch(`${AD}/teachers/${id}`, input)).data;
}

export async function adminCertificates(status?: string) {
  return (await api.get<AdminCertificate[]>(`${AD}/certificates`, { params: clean({ status }) })).data;
}

export async function adminReviewCertificate(id: string, decision: "verify" | "reject", reason?: string) {
  return (await api.post(`${AD}/certificates/${id}/review`, { decision, reason: reason || null })).data;
}

export async function adminCourses(approval?: string) {
  return (await api.get<TeacherCourseItem[]>(`${AD}/courses`, { params: clean({ approval }) })).data;
}

export async function adminReviewCourse(id: string, decision: "approve" | "reject" | "unpublish", reason?: string) {
  return (await api.post<TeacherCourseItem>(`${AD}/courses/${id}/review`, { decision, reason: reason || null })).data;
}

export async function adminLessons(status?: string) {
  return (await api.get<SpecialLesson[]>(`${AD}/special-lessons`, { params: clean({ status }) })).data;
}

export async function adminReviewLesson(id: string, decision: "approve" | "reject", reason?: string, startsAt?: string) {
  return (await api.post<SpecialLesson>(`${AD}/special-lessons/${id}/review`, { decision, reason: reason || null, starts_at: startsAt || null })).data;
}

export async function adminCancelLesson(id: string, reason: string) {
  return (await api.post<SpecialLesson>(`${AD}/special-lessons/${id}/cancel`, { reason })).data;
}

export async function adminReviews(view: "reported" | "hidden" | "all") {
  return (await api.get<AdminReview[]>(`${AD}/reviews`, { params: { view } })).data;
}

export async function adminModerateReview(id: string, action: "hide" | "show" | "dismiss", reason?: string) {
  return (await api.post(`${AD}/reviews/${id}/moderate`, { action, reason: reason || null })).data;
}

export async function adminSaveSettings(courseAutoPublish: boolean) {
  return (await api.put<{ course_auto_publish: boolean }>(`${AD}/settings`, { course_auto_publish: courseAutoPublish })).data;
}
