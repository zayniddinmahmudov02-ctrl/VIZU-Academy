"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Award } from "lucide-react";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { useTranslation } from "@/lib/i18n/use-translation";
import { VIZU_MOCK_SKILLS } from "@/features/vizu-mock/constants/skills";
import { getVizuMockAttempt } from "@/features/vizu-mock/services/vizu-mock-service";
import type { VizuMockAttempt } from "@/features/vizu-mock/types/vizu-mock.types";

const SKILL_LEVEL_KEY: Record<string, keyof VizuMockAttempt> = {
  lesen: "lesen_level",
  hoeren: "hoeren_level",
  schreiben: "schreiben_level",
  sprechen: "sprechen_level",
};

/** VIZU-Mock certificate template — UI/layout only, per spec ("real
 * sertifikatga real baho qo'yish yoki PDF generation shart emas").
 * Every level is null until a future phase computes real results, shown
 * here as "—" rather than a fabricated value. */
export default function VizuMockCertificatePage() {
  const { t } = useTranslation();
  const { attemptId } = useParams<{ attemptId: string }>();
  const { user } = useCurrentUser();

  const { data: attempt, isLoading } = useQuery({
    queryKey: ["vizu-mock-attempt", attemptId],
    queryFn: () => getVizuMockAttempt(attemptId),
  });

  const studentName = user ? [user.firstName, user.lastName].filter(Boolean).join(" ") || user.username : "";
  const date = attempt?.completed_at ?? attempt?.started_at;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <Link
        href={`/vizu-mock/${attemptId}/natijalar`}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary transition-colors hover:text-accent-blue"
      >
        <ArrowLeft size={16} />
        {t("vizuMock.resultsTitle")}
      </Link>

      {isLoading && <p className="text-sm text-text-secondary">{t("common.loading")}</p>}

      {attempt && (
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
              {t("vizuMock.title")}
            </h1>
            <p className="mt-1 text-sm font-semibold uppercase tracking-widest text-text-muted">
              {t("vizuMock.certificateSubject")}
            </p>

            <div className="mx-auto mt-8 h-px w-24 bg-surface-border" />

            <p className="mt-8 text-xs font-semibold uppercase tracking-wide text-text-muted">
              {t("vizuMock.certificateStudent")}
            </p>
            <p className="mt-1 text-xl font-bold text-text-primary">{studentName || "—"}</p>

            <div className="mx-auto mt-8 grid max-w-md grid-cols-2 gap-4 text-left">
              {VIZU_MOCK_SKILLS.map((s) => (
                <div key={s.skill} className="rounded-xl bg-surface-hover/60 px-4 py-3 ring-1 ring-surface-border">
                  <p className="text-xs font-medium text-text-muted">{t(s.labelKey)}</p>
                  <p className="text-base font-bold text-text-primary">
                    {(attempt[SKILL_LEVEL_KEY[s.skill]] as string | null) ?? "—"}
                  </p>
                </div>
              ))}
            </div>

            <div className="mx-auto mt-8 max-w-md rounded-xl bg-accent-blue/5 px-5 py-4 ring-1 ring-accent-blue/20">
              <p className="text-xs font-semibold uppercase tracking-wide text-accent-blue">
                {t("vizuMock.certificateOverallLevel")}
              </p>
              <p className="mt-1 text-2xl font-extrabold text-text-primary">{attempt.overall_level ?? "—"}</p>
            </div>

            <p className="mt-8 text-xs text-text-muted">
              {t("vizuMock.certificateDate")}: {date ? new Date(date).toLocaleDateString() : "—"}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
