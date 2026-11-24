/** My Teacher marketplace — shapes of /api/v1/my-teacher, /special-lessons, /teacher/market and /admin/teacher-market. */

export type Level = "A1" | "A2" | "B1" | "B2" | "C1" | "C2";
export type CourseType = "PAID" | "FREE" | "UPCOMING";
export type CourseStatus = "ANMELDUNG" | "BALD" | "AUSGEBUCHT" | "VORBEREITUNG" | "LAUFEND" | "ABGESCHLOSSEN" | "ABGESAGT";
export type ApprovalStatus = "DRAFT" | "PENDING" | "APPROVED" | "REJECTED" | "UNPUBLISHED";
export type EnrollmentStatus = "PENDING_PAYMENT" | "ACTIVE" | "COMPLETED" | "CANCELLED" | "REJECTED" | "REFUNDED";
export type LessonStatus = "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED" | "ENDED";

export interface TeacherCard {
  id: string;
  name: string;
  photo_url: string | null;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface Certificate {
  id: string;
  title: string;
  issuer: string;
  issued_on: string | null;
  level: string | null;
  file_type: "image" | "pdf";
  file_url: string;
  verified: boolean;
  status?: "pending" | "verified" | "rejected";
  reject_reason?: string | null;
}

export interface RatingSummary {
  avg: number;
  count: number;
  distribution: Record<string, number>;
}

export interface Review {
  id: string;
  rating: number;
  body: string | null;
  created_at: string;
  edited_at: string | null;
  author: string;
  verified_enrollment: boolean;
  course: { id: string; title: string | null };
  status?: "visible" | "hidden";
  reported_by_me?: boolean;
}

export interface MyEnrollment {
  id: string;
  status: EnrollmentStatus;
  created_at: string;
  activated_at: string | null;
  group_id: string | null;
}

export interface CourseItem {
  id: string;
  title: string;
  description: string | null;
  language: string;
  level: Level;
  course_type: CourseType;
  price: number;
  currency: string;
  start_date: string | null;
  end_date: string | null;
  duration_weeks: number | null;
  lessons_per_week: number | null;
  weekdays: string[];
  lesson_time: string | null;
  lesson_minutes: number | null;
  max_students: number;
  enrolled: number;
  seats_left: number;
  enrollment_deadline: string | null;
  image_url: string | null;
  status: CourseStatus;
  teacher: { id: string; name: string; photo_url?: string | null; verified?: boolean };
  can_enroll?: boolean;
  can_interest?: boolean;
  interested?: boolean;
  my_enrollment?: MyEnrollment | null;
}

export interface TeacherProfileView {
  id: string;
  name: string;
  first_name: string | null;
  last_name: string | null;
  photo_url: string | null;
  headline: string | null;
  languages: string[];
  levels: string[];
  verified: boolean;
  experience: {
    years: number | null;
    teaching_since: number | null;
    specialization: string | null;
    methodology: string | null;
    exam_prep: string[];
    bio: string | null;
  };
  stats: { current_students: number; total_students: number };
  certificates: Certificate[];
  rating: RatingSummary;
  courses: CourseItem[];
  review: { can_review: { course_id: string; title: string }[]; my_reviews: Review[] } | null;
}

export interface OwnProfile extends TeacherProfileView {
  admin: { catalog_hidden: boolean; profile_disabled: boolean; verified: boolean; listed: boolean };
  choices: { languages: string[]; levels: string[]; exams: string[] };
}

export interface TeacherCourseItem extends CourseItem {
  teacher_status: CourseStatus;
  approval_status: ApprovalStatus;
  reject_reason: string | null;
  submitted_at: string | null;
  reviewed_at: string | null;
  group_id: string | null;
  enrollment_counts: Partial<Record<EnrollmentStatus, number>>;
  interests: number;
  needs_review?: boolean;
  revenue?: number;
}

export interface RosterItem {
  id: string;
  student: { id: string; name: string };
  status: EnrollmentStatus;
  source: "free" | "payment";
  enrolled_at: string;
  activated_at: string | null;
  price: number;
  payment: { status: string; amount: number } | null;
  attendance: { attended: number; held: number };
}

export interface MyCourse {
  id: string;
  status: EnrollmentStatus;
  created_at: string;
  activated_at: string | null;
  price: number;
  order: { id: string; status: string; rejection_reason: string | null } | null;
  course: { id: string; title: string; level: Level; start_date: string | null; status: CourseStatus; teacher: { id: string; name: string };
    group_id: string | null };
}

export interface PaymentCard {
  label: string;
  number: string;
}

export interface Checkout {
  course: { id: string; title: string; teacher: string; price: number; currency: string };
  cards: PaymentCard[];
  blocked: boolean;
  enrollment: { id: string; status: EnrollmentStatus } | null;
  pending_order: { id: string; final_amount: number; status: string; created_at: string } | null;
  can_pay: boolean;
}

export interface LessonRoom {
  id: string;
  status: "scheduled" | "live" | "ended" | "cancelled";
  started_at: string | null;
  ended_at: string | null;
  hard_end_at: string | null;
  online: number;
  end_reason: string | null;
}

export interface SpecialLesson {
  id: string;
  title: string;
  topic: string;
  description: string | null;
  objectives: string | null;
  language: string;
  level: Level;
  starts_at: string;
  ends_at: string;
  duration_minutes: number;
  max_participants: number;
  status: LessonStatus;
  teacher: TeacherCard;
  signups: number;
  room: LessonRoom | null;
  server_time: string;
  opens_at: string;
  can_open: boolean;
  can_join: boolean;
  signed_up?: boolean;
  reject_reason?: string | null;
  cancel_reason?: string | null;
  participants_total?: number;
}

export interface LessonBoard {
  live: SpecialLesson[];
  upcoming: SpecialLesson[];
  past: SpecialLesson[];
  server_time: string;
}

export interface AdminOverview {
  teachers: { teachers: number; hidden_or_disabled: number; verified: number; pending_certificates: number };
  courses: Record<string, number>;
  special_lessons: Record<string, number>;
  reviews: { open_reports: number; hidden: number; total: number };
  settings: { course_auto_publish: boolean };
}

export interface AdminTeacher {
  id: string;
  name: string;
  username: string;
  photo_url: string | null;
  account_active: boolean;
  catalog_hidden: boolean;
  profile_disabled: boolean;
  verified: boolean;
  listed: boolean;
  rating_avg: number;
  rating_count: number;
  profile_complete: boolean;
  courses: number;
  pending_courses: number;
  pending_certificates: number;
}

export interface AdminCertificate extends Certificate {
  teacher: { id: string; name: string };
  created_at: string;
}

export interface AdminReview extends Review {
  student: { id: string; name: string };
  teacher: { id: string; name: string };
  hidden_reason: string | null;
  open_reports: number;
  reports: { reason: string; status: string; created_at: string }[];
}

export const LEVELS: Level[] = ["A1", "A2", "B1", "B2", "C1", "C2"];
export const LANGUAGES = ["Deutsch", "Usbekisch", "Russisch", "Englisch"] as const;
export const WEEKDAYS = ["MO", "DI", "MI", "DO", "FR", "SA", "SO"] as const;
export const TEACHER_STATUSES: CourseStatus[] = ["VORBEREITUNG", "BALD", "ANMELDUNG", "LAUFEND", "ABGESCHLOSSEN", "ABGESAGT"];
