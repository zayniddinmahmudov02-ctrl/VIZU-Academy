"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Award, Trophy } from "lucide-react";

import Button from "@/components/ui/button";
import PageHeader from "@/components/dashboard/page-header";
import { useTranslation } from "@/lib/i18n/use-translation";
import { VIZU_MULTILEVEL_SKILLS, stepPath } from "@/features/vizu-multilevel/constants/skills";
import {
  completeVizuMultilevelAttempt,
  getVizuMultilevelAttemptState,
} from "@/features/vizu-multilevel/services/vizu-multilevel-service";
import type {
  VizuMultilevelCompetencyResult,
  VizuMultilevelCompleteResponse,
} from "@/features/vizu-multilevel/types/vizu-multilevel.types";

function httpStatus(error: unknown): number | undefined {
  return (error as { response?: { status?: number } }).response?.status;
}

/** Results step (Ergebnis). Finishing the attempt happens here, once, on the
 * server: a result of A1 or higher is saved, a result below A1 is shown once
 * and NOT kept. Levels are only ever shown for competencies that have really
 * been graded — a competency awaiting teacher review shows as pending, and
 * no level is fabricated while data is missing. */
export default function VizuMultilevelResultsPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { attemptId } = useParams<{ attemptId: string }>();
  const queryClient = useQueryClient();
  const startedRef = useRef(false);

  const completeMutation = useMutation<VizuMultilevelCompleteResponse>({
    mutationFn: () => completeVizuMultilevelAttempt(attemptId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["vizu-multilevel-attempts"] }),
    onError: async (error) => {
      if (httpStatus(error) === 409) {
        // A competency is still open — send the student back to it.
        try {
          const state = await getVizuMultilevelAttemptState(attemptId);
          router.replace(stepPath(attemptId, state.next_skill ?? "lesen"));
        } catch {
          /* stay on the error message */
        }
      }
    },
  });

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    completeMutation.mutate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const outcome = completeMutation.data;
  const notFound = completeMutation.isError && httpStatus(completeMutation.error) === 404;
  const failed = completeMutation.isError && !notFound && httpStatus(completeMutation.error) !== 409;

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <PageHeader icon={Trophy} titleKey="vizuMultilevel.resultsTitle" gradient="from-accent-blue to-accent-purple" />

      {completeMutation.isPending && <p className="text-center text-sm text-text-secondary">{t("common.loading")}</p>}

      {notFound && (
        <div className="rounded-card bg-surface-card p-8 text-center ring-1 ring-surface-border">
          <p className="text-sm text-text-secondary">{t("vizuMultilevel.resultNotKept")}</p>
          <Link href="/vizu-multilevel" className="mt-4 inline-block">
            <Button variant="ghost">{t("vizuMultilevel.backToHub")}</Button>
          </Link>
        </div>
      )}

      {failed && <p className="text-center text-sm text-danger">{t("vizuMultilevel.sectionError")}</p>}

      {outcome && (
        <>
          <div className="grid gap-4 sm:grid-cols-2">
            {VIZU_MULTILEVEL_SKILLS.map((s) => {
              const Icon = s.icon;
              const comp = outcome.result.competencies.find((c) => c.skill === s.skill);
              return (
                <div
                  key={s.skill}
                  className="flex items-center gap-4 rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border"
                >
                  <div
                    className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br text-white shadow ${s.color}`}
                  >
                    <Icon size={18} />
                  </div>
                  <div>
                    <p className="font-semibold text-text-primary">{t(s.labelKey)}</p>
                    <CompetencyLine competency={comp} />
                  </div>
                </div>
              );
            })}
          </div>

          <OverallCard outcome={outcome} />

          <div className="flex flex-wrap justify-center gap-3">
            {outcome.result.overall.status === "FINAL" && outcome.saved && (
              <Link href={`/vizu-multilevel/${attemptId}/sertifikat`}>
                <Button variant="secondary">
                  <Award size={16} />
                  {t("vizuMultilevel.viewCertificate")}
                </Button>
              </Link>
            )}
            <Link href="/vizu-multilevel">
              <Button variant="ghost">{t("vizuMultilevel.backToHub")}</Button>
            </Link>
          </div>
        </>
      )}
    </div>
  );
}

function CompetencyLine({ competency }: { competency: VizuMultilevelCompetencyResult | undefined }) {
  const { t } = useTranslation();

  if (!competency || competency.status === "NO_CONTENT") {
    return <p className="text-sm text-text-muted">{t("vizuMultilevel.notAvailable")}</p>;
  }
  if (competency.status === "PENDING_REVIEW") {
    return <p className="text-sm text-text-muted">{t("vizuMultilevel.pendingReview")}</p>;
  }
  if (competency.status === "NOT_SUBMITTED") {
    return <p className="text-sm text-text-muted">{t("vizuMultilevel.resultsPending")}</p>;
  }

  return (
    <div className="text-sm text-text-muted">
      <p>
        {competency.raw_score ?? 0}/{competency.max_score ?? 0}
        {competency.percentage !== null && ` · ${competency.percentage}%`}
      </p>
      <p className="font-semibold text-text-primary">{competency.level ?? t("vizuMultilevel.belowA1")}</p>
    </div>
  );
}

function OverallCard({ outcome }: { outcome: VizuMultilevelCompleteResponse }) {
  const { t } = useTranslation();
  const overall = outcome.result.overall;

  let headline = "—";
  let note: string | null = null;
  if (overall.status === "FINAL") {
    headline = overall.level ?? "—";
  } else if (overall.status === "BELOW_A1") {
    headline = t("vizuMultilevel.belowA1");
    note = t("vizuMultilevel.belowA1Note");
  } else if (overall.status === "PENDING_REVIEW") {
    note = t("vizuMultilevel.pendingReviewNote");
  } else if (overall.status === "NO_CONTENT") {
    note = t("vizuMultilevel.noContentNote");
  } else {
    note = t("vizuMultilevel.resultsPendingNote");
  }

  return (
    <div className="rounded-card bg-gradient-to-br from-brand-900 via-brand-700 to-accent-blue p-8 text-center text-white shadow-[var(--shadow-lg)]">
      <p className="text-sm font-semibold uppercase tracking-wide text-white/70">{t("vizuMultilevel.resultsOverall")}</p>
      <p className="mt-2 text-4xl font-extrabold">{headline}</p>
      {note && <p className="mt-3 text-sm text-white/70">{note}</p>}
      {!outcome.saved && overall.status === "BELOW_A1" && (
        <p className="mt-2 text-xs text-white/60">{t("vizuMultilevel.notSavedNote")}</p>
      )}
    </div>
  );
}
