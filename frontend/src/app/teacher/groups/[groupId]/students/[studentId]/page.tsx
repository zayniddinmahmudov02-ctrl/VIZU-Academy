"use client";

import { useParams } from "next/navigation";

import TeacherStudentView from "@/features/groups/components/teacher-student-view";

export default function TeacherGroupStudentPage() {
  const { groupId, studentId } = useParams<{ groupId: string; studentId: string }>();
  return <TeacherStudentView groupId={groupId} studentId={studentId} />;
}
