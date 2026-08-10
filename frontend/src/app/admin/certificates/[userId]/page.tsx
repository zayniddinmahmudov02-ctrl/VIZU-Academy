"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Award, Download } from "lucide-react";

import { AdminButton, AdminPageHeader } from "@/components/admin/admin-ui";
import { downloadCertificate, getUserCertificateProfile } from "@/features/admin/services/certificates-service";
import type { UserCertificateEntry } from "@/features/admin/types/certificate.types";

const SOURCE_LABEL: Record<string, string> = {
  COURSE: "Kursabschluss",
  VORBEREITUNG: "Vorbereitung",
  VIZU_MOCK: "VIZU-MOCK",
};

export default function UserCertificateProfilePage() {
  const { userId } = useParams<{ userId: string }>();
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const { data: certificates, isLoading } = useQuery({
    queryKey: ["user-certificate-profile", userId],
    queryFn: () => getUserCertificateProfile(userId),
  });

  async function handleDownload(cert: UserCertificateEntry) {
    setDownloadingId(cert.id);
    try {
      await downloadCertificate(cert.id, `${cert.certificate_number}.pdf`);
    } finally {
      setDownloadingId(null);
    }
  }

  return (
    <div>
      <Link
        href="/admin/certificates"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]"
      >
        <ArrowLeft size={14} />
        Certificate
      </Link>

      <AdminPageHeader
        title="Zertifikatsprofil"
        description={certificates ? `${certificates.length} Zertifikate` : undefined}
      />

      {isLoading && <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}

      {!isLoading && certificates?.length === 0 && (
        <div className="rounded-2xl bg-[var(--admin-card)] px-6 py-16 text-center shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)]">
          <p className="text-sm text-[var(--admin-text-muted)]">Keine Zertifikate für diesen Nutzer.</p>
        </div>
      )}

      <div className="space-y-3">
        {certificates?.map((cert) => (
          <div
            key={cert.id}
            className="flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-[var(--admin-card)] p-5 shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)]"
          >
            <div className="flex items-center gap-3.5">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]">
                <Award size={20} />
              </div>
              <div>
                <p className="font-semibold text-[var(--admin-text-primary)]">
                  {cert.level} — {SOURCE_LABEL[cert.source] ?? cert.source}
                </p>
                <p className="text-xs text-[var(--admin-text-muted)]">
                  {cert.certificate_number} · {new Date(cert.issued_at).toLocaleDateString("de-DE")} · {cert.score}%
                  {!cert.is_valid && " · Widerrufen"}
                </p>
              </div>
            </div>

            <AdminButton
              size="sm"
              variant="secondary"
              onClick={() => handleDownload(cert)}
              disabled={!cert.pdf_url || downloadingId === cert.id}
            >
              <Download size={14} />
              {downloadingId === cert.id ? "Wird geladen..." : "Download"}
            </AdminButton>
          </div>
        ))}
      </div>
    </div>
  );
}
