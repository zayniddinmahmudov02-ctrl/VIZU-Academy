import { AdminPageHeader } from "@/components/admin/admin-ui";
import WerbungBannerManager from "@/features/admin/advertisements/werbung-banner-manager";

export default function WerbungBannerPage() {
  return (
    <div>
      <AdminPageHeader
        title="Werbung-Banner"
        description="Werbung oben im Studenten-Dashboard verwalten — mit Vorschau, Zeitraum, Priorität und echter Auswertung (Aufrufe, Klicks, CTR)."
      />
      <WerbungBannerManager />
    </div>
  );
}
