"use client";

import { AdminPageHeader } from "@/components/admin/admin-ui";
import SpeakingManager from "@/features/admin/components/managers/speaking-manager";

export default function SpeakingPage() {
  return (
    <div>
      <AdminPageHeader title="Speaking (Sprechen)" description="Alle Sprechübungen, plattformweit." />
      <SpeakingManager />
    </div>
  );
}
