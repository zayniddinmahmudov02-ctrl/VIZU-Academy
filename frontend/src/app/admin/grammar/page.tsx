"use client";

import { AdminPageHeader } from "@/components/admin/admin-ui";
import GrammarManager from "@/features/admin/components/managers/grammar-manager";

export default function GrammarPage() {
  return (
    <div>
      <AdminPageHeader title="Grammar" description="Alle Grammatik-Themen, plattformweit." />
      <GrammarManager />
    </div>
  );
}
