"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Download, Loader2 } from "lucide-react";

import { AdminButton } from "@/components/admin/admin-ui";
import {
  downloadVizuMultilevelAttemptCertificatePdf,
  getVizuMultilevelAttemptCertificate,
} from "@/features/admin/vizu-multilevel/services/vizu-multilevel-admin-service";

const REASON: Record<string, string> = {
  NOT_COMPLETED: "Test noch nicht abgeschlossen",
  BELOW_A1: "Unter A1 — kein Zertifikat",
  NOT_FINAL: "Ergebnis noch nicht endgültig",
};

function germanDate(value: string | null): string {
  return value ? new Date(value).toLocaleDateString("de-DE", { day: "2-digit", month: "long", year: "numeric" }) : "—";
}

/** Certificate info for one attempt in the admin result dialog: availability,
 * number, level, Gesamtergebnis, completion date, and the same PDF the
 * student downloads. */
export default function CertificateAdminSection({ attemptId }: { attemptId: string }) {
  const [pending, setPending] = useState(false);
  const [failed, setFailed] = useState(false);
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["vizu-multilevel-admin-certificate", attemptId],
    queryFn: () => getVizuMultilevelAttemptCertificate(attemptId),
  });

  async function download() {
    setPending(true);
    setFailed(false);
    try {
      await downloadVizuMultilevelAttemptCertificatePdf(attemptId);
      void refetch(); // the number is issued on the first download
    } catch {
      setFailed(true);
    } finally {
      setPending(false);
    }
  }

  if (isLoading || !data) {
    return <Loader2 size={16} className="animate-spin text-[var(--admin-primary)]" />;
  }

  const rows: [string, string][] = [
    ["Student", data.student_name],
    ["Zertifikat", data.available ? "verfügbar" : REASON[data.reason ?? ""] ?? "nicht verfügbar"],
    ["Zertifikatsnummer", data.certificate_number ?? (data.available ? "wird beim ersten Download vergeben" : "—")],
    ["Niveau", data.level ? `Niveau ${data.level}` : "—"],
    ["Gesamtergebnis", data.total_score !== null ? `${data.total_score} / 100 Punkte` : "—"],
    ["Abgeschlossen am", germanDate(data.completed_at)],
  ];

  return (
    <div className="space-y-3" data-testid="admin-certificate">
      <div className="overflow-hidden rounded-xl ring-1 ring-[var(--admin-border)]">
        <table className="w-full text-left text-sm">
          <tbody className="divide-y divide-[var(--admin-border)]">
            {rows.map(([label, value]) => (
              <tr key={label}>
                <td className="px-4 py-2 text-[var(--admin-text-secondary)]">{label}</td>
                <td className="px-4 py-2 text-right font-semibold text-[var(--admin-text-primary)]">{value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data.available && (
        <div className="flex items-center gap-3">
          <AdminButton size="sm" onClick={download} disabled={pending}>
            {pending ? <Loader2 size={13} className="animate-spin" /> : <Download size={13} />}
            {pending ? "Zertifikat wird erstellt..." : "Zertifikat herunterladen"}
          </AdminButton>
          {failed && <span className="text-xs text-[var(--admin-danger)]">Das Zertifikat konnte nicht erstellt werden.</span>}
        </div>
      )}
    </div>
  );
}
