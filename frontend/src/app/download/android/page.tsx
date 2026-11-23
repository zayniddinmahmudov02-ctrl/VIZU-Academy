import type { Metadata } from "next";

import AndroidDownloadView from "@/features/mobile-app/components/android-download-view";

export const metadata: Metadata = {
  title: "VIZU-DEUTSCH Android App (APK)",
  description: "VIZU-DEUTSCH für Android: APK herunterladen, Version, Größe, Installationsanleitung auf Deutsch und Usbekisch.",
  alternates: { canonical: "/download/android" },
  openGraph: { title: "VIZU-DEUTSCH Android App", description: "Lerne Deutsch. Überall. Jederzeit.", url: "/download/android", type: "website" },
};

export default function AndroidDownloadPage() {
  return <AndroidDownloadView />;
}
