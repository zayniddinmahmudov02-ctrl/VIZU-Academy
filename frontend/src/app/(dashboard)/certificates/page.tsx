"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Award, Download, ExternalLink, Eye, Loader2, ShieldCheck } from "lucide-react";

import Badge from "@/components/ui/badge";
import PageHeader from "@/components/dashboard/page-header";
import { fetchMyCertificatePdf, getMyCertificates, type MyCertificate } from "@/features/certificates/services/my-certificates-service";
import { openBlob } from "@/lib/save-blob";
import { useTranslation } from "@/lib/i18n/use-translation";

const LEVEL_ORDER = ["BELOW_A1", "A1", "A2", "B1", "B2", "C1"];
const TYPE_ORDER: MyCertificate["source"][] = ["VIZU_MULTILEVEL", "COURSE", "VORBEREITUNG"];

function byLevel(a: MyCertificate, b: MyCertificate) {
  return LEVEL_ORDER.indexOf(b.level ?? "") - LEVEL_ORDER.indexOf(a.level ?? "") || (b.issued_at ?? "").localeCompare(a.issued_at ?? "");
}

/** The student's own certificates — course certificates and VIZU-Multilevel
 * — grouped by type, highest level first. */
export default function CertificatesPage() {
  const { t } = useTranslation();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["my-certificates"], queryFn: getMyCertificates });
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function pdf(c: MyCertificate, save: boolean) {
    setBusy(c.id);
    setError(null);
    try {
      openBlob(await fetchMyCertificatePdf(c.id), save ? `Zertifikat-${c.certificate_number ?? c.level ?? "VIZU"}.pdf` : undefined);
    } catch {
      setError(t("certificates.pdfError"));
    } finally {
      setBusy(null);
    }
  }

  const groups = TYPE_ORDER.map((type) => ({ type, items: (data ?? []).filter((c) => c.source === type).sort(byLevel) })).filter((g) => g.items.length);
  const level = (c: MyCertificate) => (c.level === "BELOW_A1" ? t("certificates.belowA1") : c.level ?? "—");

  return (
    <div className="space-y-8">
      <PageHeader icon={Award} titleKey="certificates.title" subtitleKey="certificates.subtitle" gradient="from-warning to-amber-400" />

      {isLoading ? (
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3" aria-busy="true">
          {[0, 1, 2].map((i) => <div key={i} className="h-[196px] animate-pulse rounded-card bg-surface-card ring-1 ring-surface-border" />)}
        </div>
      ) : isError ? (
        <div className="rounded-card bg-surface-card p-6 text-center ring-1 ring-surface-border" role="alert">
          <p className="text-sm text-danger">{t("certificates.loadError")}</p>
          <button onClick={() => refetch()} className="mt-2 text-sm font-semibold text-accent-blue hover:underline">{t("certificates.retry")}</button>
        </div>
      ) : groups.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-card bg-surface-card px-6 py-16 text-center shadow-[var(--shadow-md)] ring-1 ring-surface-border">
          <Award size={44} className="text-text-muted" />
          <h2 className="mt-4 text-lg font-semibold text-text-primary">{t("certificates.emptyTitle")}</h2>
          <p className="mt-2 max-w-md text-sm text-text-secondary">{t("certificates.emptyBody")}</p>
        </div>
      ) : (
        <>
          {error && <p className="rounded-xl bg-danger/10 p-3 text-sm text-danger" role="alert">{error}</p>}
          {groups.map((g) => (
            <section key={g.type} className="space-y-4" data-testid={`certificates-${g.type}`}>
              <h2 className="text-base font-bold text-text-primary">{g.items[0].type_label}</h2>
              <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
                {g.items.map((c) => (
                  <article key={c.id} className="flex flex-col rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border" data-testid="certificate-card">
                    <div className="flex items-start justify-between gap-3">
                      <div className={`flex items-center gap-2 ${c.status === "revoked" ? "text-danger" : "text-warning"}`}>
                        <ShieldCheck size={18} />
                        <span className="text-xs font-semibold uppercase tracking-wide">{c.status === "revoked" ? t("certificates.revoked") : t("certificates.verified")}</span>
                      </div>
                      <Badge variant="warning">{level(c)}</Badge>
                    </div>
                    <h3 className="mt-3 text-lg font-bold text-text-primary">
                      {c.course?.title ?? c.type_label}
                      {c.attempt_number ? <span className="ml-1 text-sm font-medium text-text-muted">· {t("certificates.attempt")} {c.attempt_number}</span> : null}
                    </h3>
                    <dl className="mt-3 space-y-1 text-sm">
                      <div className="flex justify-between gap-3"><dt className="text-text-muted">{t("certificates.issuedAt")}</dt>
                        <dd className="text-text-primary">{c.issued_at ? new Date(c.issued_at).toLocaleDateString("de-DE") : "—"}</dd></div>
                      {c.score !== null && <div className="flex justify-between gap-3"><dt className="text-text-muted">{t("certificates.result")}</dt><dd className="text-text-primary">{c.score}%</dd></div>}
                      <div className="flex justify-between gap-3"><dt className="text-text-muted">{t("certificates.number")}</dt>
                        <dd className="truncate text-right font-mono text-xs text-text-primary">{c.certificate_number ?? t("certificates.numberPending")}</dd></div>
                    </dl>
                    <div className="mt-auto flex flex-wrap gap-2 pt-5">
                      {c.source === "VIZU_MULTILEVEL" && c.attempt_id ? (
                        <Link href={`/vizu-multilevel/${c.attempt_id}/sertifikat`} className="inline-flex items-center gap-1.5 rounded-full bg-accent-blue px-4 py-2 text-sm font-semibold text-white hover:bg-accent-blue-hover">
                          <ExternalLink size={14} /> {t("certificates.open")}
                        </Link>
                      ) : (
                        <button disabled={!c.pdf_available || busy === c.id} onClick={() => pdf(c, false)}
                                className="inline-flex items-center gap-1.5 rounded-full bg-accent-blue px-4 py-2 text-sm font-semibold text-white hover:bg-accent-blue-hover disabled:opacity-50">
                          <Eye size={14} /> {t("certificates.viewPdf")}
                        </button>
                      )}
                      <button disabled={!c.pdf_available || busy === c.id} onClick={() => pdf(c, true)} data-testid="certificate-pdf"
                              className="inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold text-text-primary ring-1 ring-surface-border hover:bg-surface-hover disabled:opacity-50">
                        {busy === c.id ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />} {t("certificates.downloadPdf")}
                      </button>
                    </div>
                    {!c.pdf_available && <p className="mt-2 text-xs text-text-muted">{t("certificates.noPdf")}</p>}
                  </article>
                ))}
              </div>
            </section>
          ))}
        </>
      )}
    </div>
  );
}
