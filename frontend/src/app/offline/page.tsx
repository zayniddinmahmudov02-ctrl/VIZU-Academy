import { WifiOff } from "lucide-react";

export const metadata = {
  title: "Offline — VIZU Academy",
};

// Served by the service worker (see public/sw.js) as the fallback for
// any navigation request that fails while offline — cached at install
// time so it's always available even on a device's very first offline
// moment.
export default function OfflinePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-surface-bg p-6 text-center">
      <WifiOff size={40} className="text-text-muted" />
      <h1 className="text-xl font-bold text-text-primary">Keine Internetverbindung</h1>
      <p className="max-w-sm text-sm text-text-secondary">
        Für diese Seite ist eine Internetverbindung erforderlich. Bitte überprüfe deine Verbindung und
        versuche es erneut.
      </p>
      <p className="max-w-sm text-xs text-text-muted">Internet connection required.</p>
    </div>
  );
}
