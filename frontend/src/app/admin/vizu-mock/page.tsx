import { FlaskConical } from "lucide-react";

import { AdminPageHeader } from "@/components/admin/admin-ui";
import AdminEmptySection from "@/components/admin/admin-empty-section";

export default function VizuMockPage() {
  return (
    <div>
      <AdminPageHeader
        title="VIZU-MOCK"
        description="Ein eigenständiges Mock-Test-System, unabhängig von Vorbereitung."
      />

      <AdminEmptySection
        icon={FlaskConical}
        title="Noch nicht eingerichtet"
        description="VIZU-MOCK ist bereit für die zukünftige Entwicklung. Es werden noch keine Mock-Tests oder Testdaten angelegt."
      />
    </div>
  );
}
