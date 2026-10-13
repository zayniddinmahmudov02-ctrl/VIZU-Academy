"use client";

import { useParams } from "next/navigation";

import LessonEditor from "@/features/admin/components/lms-course/lesson-editor";

export default function AdminKursLessonPage() {
  const { lessonId } = useParams<{ lessonId: string }>();
  return <LessonEditor lessonId={lessonId} />;
}
