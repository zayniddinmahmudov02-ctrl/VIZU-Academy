"use client";

import { Suspense } from "react";
import { useParams } from "next/navigation";

import TeacherGroupView from "@/features/groups/components/teacher-group-view";

export default function TeacherGroupPage() {
  const { groupId } = useParams<{ groupId: string }>();
  return (
    <Suspense fallback={null}>
      <TeacherGroupView groupId={groupId} />
    </Suspense>
  );
}
