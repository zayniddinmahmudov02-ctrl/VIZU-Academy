import type { Metadata } from "next";

import DownloadView from "@/features/mobile-app/components/download-view";

export const metadata: Metadata = {
  title: "VIZU DEUTSCH APP — Android & iPhone",
  description: "Lerne Deutsch. Überall. Jederzeit. VIZU DEUTSCH für Android (APK) und iPhone (Home-Bildschirm).",
  alternates: { canonical: "/download" },
  openGraph: {
    title: "VIZU DEUTSCH APP",
    description: "Lerne Deutsch. Überall. Jederzeit.",
    url: "/download",
    type: "website",
  },
};

export default function DownloadPage() {
  return <DownloadView />;
}
