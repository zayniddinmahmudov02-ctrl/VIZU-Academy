import { Mic, PenLine } from "lucide-react";

import { AdminPageHeader } from "@/components/admin/admin-ui";
import AdminTabs from "@/components/admin/admin-tabs";
import AdminEmptySection from "@/components/admin/admin-empty-section";
import VizuMockAnalyticsTab from "@/features/admin/components/vizu-mock/analytics-tab";
import VizuMockAudioTab from "@/features/admin/components/vizu-mock/audio-tab";
import VizuMockHoerenTab from "@/features/admin/components/vizu-mock/hoeren-tab";
import VizuMockLesenTab from "@/features/admin/components/vizu-mock/lesen-tab";
import VizuMockOverviewTab from "@/features/admin/components/vizu-mock/overview-tab";
import VizuMockResultsTab from "@/features/admin/components/vizu-mock/results-tab";

export default function VizuMockPage() {
  return (
    <div>
      <AdminPageHeader
        title="VIZU-MOCK"
        description="Darajani aniqlash testi boshqaruvi va statistika — eigenständiges Mock-Test-System, unabhängig von Vorbereitung."
      />

      <AdminTabs
        defaultValue="overview"
        tabs={[
          { value: "overview", label: "Overview", content: <VizuMockOverviewTab /> },
          { value: "audio", label: "Hören Audio", content: <VizuMockAudioTab /> },
          { value: "lesen", label: "Lesen", content: <VizuMockLesenTab /> },
          { value: "hoeren", label: "Hören", content: <VizuMockHoerenTab /> },
          {
            value: "schreiben",
            label: "Schreiben",
            content: (
              <AdminEmptySection
                icon={PenLine}
                title="Noch nicht eingerichtet"
                description="Schreiben-Testinhalte werden in einer späteren Phase hinzugefügt."
              />
            ),
          },
          {
            value: "sprechen",
            label: "Sprechen",
            content: (
              <AdminEmptySection
                icon={Mic}
                title="Noch nicht eingerichtet"
                description="Sprechen-Testinhalte werden in einer späteren Phase hinzugefügt."
              />
            ),
          },
          { value: "results", label: "Results", content: <VizuMockResultsTab /> },
          { value: "analytics", label: "Analytics", content: <VizuMockAnalyticsTab /> },
        ]}
      />
    </div>
  );
}
