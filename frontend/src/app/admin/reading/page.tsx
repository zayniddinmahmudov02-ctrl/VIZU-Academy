"use client";

import { AdminPageHeader } from "@/components/admin/admin-ui";
import ReadingManager from "@/features/admin/components/managers/reading-manager";

export default function ReadingPage() {
  return (
    <div>
      <AdminPageHeader title="Reading (Lesen)" description="Alle Lesetexte, plattformweit." />
      <ReadingManager />
    </div>
  );
}
