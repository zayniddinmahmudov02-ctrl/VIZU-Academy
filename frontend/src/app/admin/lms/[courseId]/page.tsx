"use client";

import { useParams } from "next/navigation";

import CourseStructureClient from "@/features/admin/components/lms/course-structure-client";

export default function LmsCoursePage() {
  const { courseId } = useParams<{ courseId: string }>();
  return <CourseStructureClient courseId={courseId} />;
}
