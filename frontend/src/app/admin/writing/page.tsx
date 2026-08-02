"use client";

import { AdminPageHeader } from "@/components/admin/admin-ui";
import WritingManager from "@/features/admin/components/managers/writing-manager";

export default function WritingPage() {
  return (
    <div>
      <AdminPageHeader title="Writing (Schreiben)" description="Alle Schreib-Themen, plattformweit." />
      <WritingManager />
    </div>
  );
}
