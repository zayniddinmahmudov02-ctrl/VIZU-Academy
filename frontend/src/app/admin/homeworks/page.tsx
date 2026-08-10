import { ClipboardList } from "lucide-react";

import { AdminPageHeader } from "@/components/admin/admin-ui";
import AdminEmptySection from "@/components/admin/admin-empty-section";

export default function HomeworksPage() {
  return (
    <div>
      <AdminPageHeader
        title="Homeworks"
        description="Zentrale Hausaufgabenverwaltung über alle Kurse hinweg."
      />

      <AdminEmptySection
        icon={ClipboardList}
        title="Noch nicht eingerichtet"
        description="Dieser Bereich ist bereit für die zukünftige Entwicklung. Es werden noch keine Hausaufgaben angelegt."
      />
    </div>
  );
}
