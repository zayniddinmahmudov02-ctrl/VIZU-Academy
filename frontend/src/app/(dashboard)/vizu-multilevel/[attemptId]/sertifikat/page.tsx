"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Award } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { VIZU_MULTILEVEL_SKILLS } from "@/features/vizu-multilevel/constants/skills";
import { getVizuMultilevelCertificate } from "@/features/vizu-multilevel/services/vizu-multilevel-service";

/** VIZU-Multilevel's own certificate. Data comes from the backend, which
 * only issues it for a completed attempt whose overall level is final and
 * at least A1 — for anything else the request is a 404 and no certificate
 * is shown (nothing is fabricated client-side). */
export default function VizuMultilevelCertificatePage() {
  const { t } = useTranslation();
  const { attemptId } = useParams<{ attemptId: string }>();

  const { data: cert, isLoading, isError } = useQuery({
    queryKey: ["vizu-multilevel-certificate", attemptId],
    queryFn: () => getVizuMultilevelCertificate(attemptId),
    retry: false,
  });

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <Link
        href={`/vizu-multilevel/${attemptId}/natijalar`}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary transition-colors hover:text-accent-blue"
      >
        <ArrowLeft size={16} />
        {t("vizuMultilevel.resultsTitle")}
      </Link>

      {isLoading && <p className="text-sm text-text-secondary">{t("common.loading")}</p>}

      {isError && (
        <div className="rounded-card bg-surface-card p-8 text-center ring-1 ring-surface-border">
          <p className="text-sm text-text-secondary">{t("vizuMultilevel.certificateUnavailable")}</p>
        </div>
      )}

      {cert && (
        <div className="relative overflow-hidden rounded-card border-4 border-double border-accent-gold/60 bg-surface-card p-8 text-center shadow-[var(--shadow-lg)] sm:p-12">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--accent-gold)_0%,transparent_70%)] opacity-[0.06]"
          />

          <div className="relative">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-accent-gold to-warning text-white shadow-md">
              <Award size={28} />
            </div>

            <h1 className="mt-5 text-2xl font-extrabold tracking-tight text-text-primary sm:text-3xl">
              {t("vizuMultilevel.title")}
            </h1>
            <p className="mt-1 text-sm font-semibold uppercase tracking-widest text-text-muted">
              {t("vizuMultilevel.certificateSubject")}
            </p>

            <div className="mx-auto mt-8 h-px w-24 bg-surface-border" />

            <p className="mt-8 text-xs font-semibold uppercase tracking-wide text-text-muted">
              {t("vizuMultilevel.certificateStudent")}
            </p>
            <p className="mt-1 text-xl font-bold text-text-primary">{cert.student_name || "—"}</p>

            <div className="mx-auto mt-8 grid max-w-md grid-cols-2 gap-4 text-left">
              {VIZU_MULTILEVEL_SKILLS.map((s) => {
                const comp = cert.competencies.find((c) => c.skill === s.skill);
                return (
                  <div key={s.skill} className="rounded-xl bg-surface-hover/60 px-4 py-3 ring-1 ring-surface-border">
                    <p className="text-xs font-medium text-text-muted">{t(s.labelKey)}</p>
                    <p className="text-base font-bold text-text-primary">
                      {comp && comp.status === "GRADED" ? (comp.level ?? t("vizuMultilevel.belowA1")) : "—"}
                    </p>
                    {comp && comp.percentage !== null && (
                      <p className="text-xs text-text-muted">{comp.percentage}%</p>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="mx-auto mt-8 max-w-md rounded-xl bg-accent-blue/5 px-5 py-4 ring-1 ring-accent-blue/20">
              <p className="text-xs font-semibold uppercase tracking-wide text-accent-blue">
                {t("vizuMultilevel.certificateOverallLevel")}
              </p>
              <p className="mt-1 text-2xl font-extrabold text-text-primary">{cert.overall_level}</p>
            </div>

            <p className="mt-8 text-xs text-text-muted">
              {t("vizuMultilevel.certificateDate")}: {cert.issued_at ? new Date(cert.issued_at).toLocaleDateString() : "—"}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
