export interface TeacherOverview {
  assigned_course_count: number;
  student_count: number;
  new_homework_count: number;
  to_grade_count: number;
  graded_count: number;
  average_progress: number;
}

export interface TeacherStudent {
  id: string;
  name: string;
  email: string;
  course_title: string;
  course_level: string;
  progress: number;
  last_activity: string | null;
}

export interface TeacherHomeworkSubmission {
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
  status: "SUBMITTED" | "GRADED" | "NEEDS_REVISION";
  submitted_at: string;
  score: number | null;
  feedback: string | null;
  reviewed_at: string | null;
}

export interface TeacherHomeworkFilters {
  status?: string;
  course_id?: string;
  level?: string;
  lesson_id?: string;
  search?: string;
}
