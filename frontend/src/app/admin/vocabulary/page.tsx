"use client";

import { AdminPageHeader } from "@/components/admin/admin-ui";
import VocabularyManager from "@/features/admin/components/managers/vocabulary-manager";

export default function VocabularyPage() {
  return (
    <div>
      <AdminPageHeader title="Vocabulary" description="Alle Vokabeln, plattformweit." />
      <VocabularyManager />
    </div>
  );
}
