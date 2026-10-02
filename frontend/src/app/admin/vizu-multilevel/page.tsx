import { AdminPageHeader } from "@/components/admin/admin-ui";
import AdminTabs from "@/components/admin/admin-tabs";
import VizuMultilevelContentTab from "@/features/admin/vizu-multilevel/components/content-tab";
import VizuMultilevelHoerenAudioManager from "@/features/admin/vizu-multilevel/components/hoeren-audio-manager";
import VizuMultilevelOverviewTab from "@/features/admin/vizu-multilevel/components/overview-tab";
import VizuMultilevelSchreibenTab from "@/features/admin/vizu-multilevel/components/schreiben-tab";
import VizuMultilevelSprechenTab from "@/features/admin/vizu-multilevel/components/sprechen-tab";
import VizuMultilevelStatisticsTab from "@/features/admin/vizu-multilevel/components/statistics-tab";

export default function VizuMultilevelPage() {
  return (
    <div>
      <AdminPageHeader
        title="VIZU-Multilevel"
        description="Einstufungstest A1–C1 (Lesen, Hören, Schreiben, Sprechen) — eigenständiges System, unabhängig von Kursen, Büchern, Vorbereitung und Modelltests."
      />

      <AdminTabs
        defaultValue="overview"
        tabs={[
          { value: "overview", label: "Overview", content: <VizuMultilevelOverviewTab /> },
          { value: "lesen", label: "Lesen", content: <VizuMultilevelContentTab skill="lesen" /> },
          {
            value: "hoeren",
            label: "Hören",
            content: (
              <div className="space-y-8">
                <VizuMultilevelHoerenAudioManager />
                <VizuMultilevelContentTab skill="hoeren" />
              </div>
            ),
          },
          { value: "schreiben", label: "Schreiben", content: <VizuMultilevelSchreibenTab /> },
          { value: "sprechen", label: "Sprechen", content: <VizuMultilevelSprechenTab /> },
          { value: "statistics", label: "Statistics", content: <VizuMultilevelStatisticsTab /> },
        ]}
      />
    </div>
  );
}
