"use client";

import { TeacherCoursesManager } from "@/features/teacher-market/components/teacher-manage";

/** Meine Kurse: the teacher's own courses (create, submit for approval, roster). The LMS courses assigned by admins stay in "Kurse". */
export default function TeacherMyCoursesPage() {
  return <TeacherCoursesManager />;
}
