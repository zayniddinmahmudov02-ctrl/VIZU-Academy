/** Teacher Panel sections (backend app/services/teacher/panel.py). Dates ISO, times in seconds. */
import type { CourseStat, StudentStatus } from "@/features/activity/types";

export interface TeacherMe {
  id: string;
  name: string;
  username: string;
  role: string;
  can_access_student_control: boolean;
}

export interface GroupRef {
  id: string;
  name: string;
  level: string;
  status?: string;
  joined_at?: string | null;
}

export interface CourseRef {
  id: string;
  title: string;
  level: string;
}

export interface VideoLesson {
  id: string;
  group_id: string;
  group: string | null;
  title: string;
  status: string;
  scheduled_at: string | null;
  started_at: string | null;
  ended_at: string | null;
}

export interface GroupTask {
  id: string;
  group_id: string;
  group: string;
  lesson_id: string;
  title: string;
  lesson: string;
  note: string | null;
  assigned_at: string | null;
  due_at: string | null;
  students: number;
  completed: number;
}

export interface TeacherDashboard {
  stats: { students: number; groups: number; courses: number; lessons: number; lessons_upcoming: number; homework: number; new_submissions: number };
  groups: { id: string; name: string; level: string; status: string; students: number; capacity: number | null; last_activity_at: string | null }[];
  upcoming_lessons: VideoLesson[];
  recent_activity: { student_id: string; student: string | null; lesson: string; completed: boolean; at: string | null }[];
  students_activity: { active_7d: number; inactive: number };
  tasks_due: GroupTask[];
  has_groups: boolean;
}

export interface RosterRow {
  id: string;
  name: string;
  email: string;
  groups: GroupRef[];
  courses: CourseRef[];
  levels: string[];
  registered_at: string;
  status: StudentStatus;
  last_activity_at: string | null;
}

export interface Roster {
  items: RosterRow[];
  total: number;
  page: number;
  page_size: number;
  filters: { groups: GroupRef[]; courses: CourseRef[] };
}

export interface RosterFilters {
  search?: string;
  group_id?: string;
  course_id?: string;
  level?: string;
  status?: string;
  activity?: string;
  registered_from?: string;
  registered_to?: string;
  page?: number;
  page_size?: number;
}

export interface StudentProfile {
  student: { id: string; name: string; email: string; username: string; registered_at: string; status: StudentStatus; last_login_at: string | null; last_activity_at: string | null };
  groups: GroupRef[];
  courses: CourseRef[];
  progress: CourseStat[];
  homework: { id: string; title: string; lesson: string; status: string; score: number | null; max_score: number | null; submitted_at: string | null }[];
  exams: { id: string; title: string; status: string; total_score: number | null; max_score: number | null; level: string | null; started_at: string | null; submitted_at: string | null }[];
  results: { homework_graded: number; homework_average: number | null; exams_finished: number; best_level: string | null };
  recent_activity: { area: string; title: string | null; at: string; seconds: number }[];
}

export interface TeacherCourse {
  id: string;
  title: string;
  level: string;
  lessons: number;
  students: number;
  assigned: boolean;
  groups: string[];
}

export interface TeacherVideoLessons {
  live: VideoLesson[];
  upcoming: VideoLesson[];
  past: VideoLesson[];
  groups: { id: string; name: string }[];
}

export interface MaterialCourse {
  course_id: string;
  title: string;
  level: string;
  lessons: { id: string; number: number; title: string }[];
}

export interface GroupMessages {
  group_id: string;
  group: string;
  level: string;
  unread: number;
  last_message: { body: string; at: string; sender: string | null; kind: string } | null;
}

export interface HomeworkSubmission {
  id: string;
  student_id: string;
  student_name: string;
  student_email: string;
  course_title: string;
  course_level: string;
  lesson_title: string;
  lesson_number: number;
  homework_title: string;
  text_content: string;
  status: string;
  submitted_at: string;
  score: number | null;
  feedback: string | null;
  reviewed_at: string | null;
}
