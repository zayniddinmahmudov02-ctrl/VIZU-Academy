"use client";

import { AdminPageHeader } from "@/components/admin/admin-ui";
import ListeningManager from "@/features/admin/components/managers/listening-manager";

export default function ListeningPage() {
  return (
    <div>
      <AdminPageHeader title="Listening (Hören)" description="Alle Hörübungen, plattformweit." />
      <ListeningManager />
    </div>
  );
}
