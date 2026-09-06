export interface TeacherCandidate {
  id: string;
  name: string;
  email: string;
}

export interface TeacherAssignment {
  id: string;
  teacher_id: string;
  course_id: string;
  teacher_name: string;
  teacher_email: string;
  course_title: string;
  course_level: string;
}
