export interface TeacherOverview {
  assigned_course_count: number;
  student_count: number;
}

export interface TeacherStudent {
  id: string;
  name: string;
  email: string;
  course_title: string;
  course_level: string;
  progress: number;
}
