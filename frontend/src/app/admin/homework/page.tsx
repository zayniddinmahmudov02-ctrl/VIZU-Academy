"use client";

import { AdminPageHeader } from "@/components/admin/admin-ui";
import HomeworkManager from "@/features/admin/components/managers/homework-manager";

export default function HomeworkPage() {
  return (
    <div>
      <AdminPageHeader title="Homework" description="Alle Hausaufgaben, plattformweit." />
      <HomeworkManager />
    </div>
  );
}
