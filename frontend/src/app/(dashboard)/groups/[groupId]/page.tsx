"use client";

import { Suspense } from "react";
import { useParams } from "next/navigation";

import StudentGroupView from "@/features/groups/components/student-group-view";

export default function GroupPage() {
  const { groupId } = useParams<{ groupId: string }>();
  return (
    <Suspense fallback={null}>
      <StudentGroupView groupId={groupId} />
    </Suspense>
  );
}
